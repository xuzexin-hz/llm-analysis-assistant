import argparse
import copy
import json
import os
import socket
import sys
import threading
import urllib.parse
from http import HTTPStatus
from http.server import CGIHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import select

from utils.env_utils import get_base_path
from utils.logs_utils import app_init, write_app_log, is_first_open

# 定义一个信号量，最大并发线程数为 5
MAX_CONCURRENT_THREADS = 5
semaphore = threading.BoundedSemaphore(value=MAX_CONCURRENT_THREADS)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass


class MyHandler(CGIHTTPRequestHandler):

    # 明确指定参数类型
    def __init__(self, request: socket.socket, client_address: tuple[str, int], server: ThreadedHTTPServer):
        super().__init__(request, client_address, server)

    def run_cgi(self):
        """Execute a CGI script."""
        dir, rest = self.cgi_info
        path = dir + '/' + rest
        i = path.find('/', len(dir) + 1)
        while i >= 0:
            nextdir = path[:i]
            nextrest = path[i + 1:]

            scriptdir = self.translate_path(nextdir)
            if os.path.isdir(scriptdir):
                dir, rest = nextdir, nextrest
                i = path.find('/', len(dir) + 1)
            else:
                break

        # find an explicit query string, if present.
        rest, _, query = rest.partition('?')

        # dissect the part after the directory name into a script name &
        # a possible additional path, to be stored in PATH_INFO.
        i = rest.find('/')
        if i >= 0:
            script, rest = rest[:i], rest[i:]
        else:
            script, rest = rest, ''

        scriptname = dir + '\\' + script
        scriptfile = get_base_path() + "\\" + scriptname
        if not os.path.exists(scriptfile):
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No such CGI script (%r)" % scriptname)
            return
        if not os.path.isfile(scriptfile):
            self.send_error(
                HTTPStatus.FORBIDDEN,
                "CGI script is not a plain file (%r)" % scriptname)
            return
        ispy = self.is_python(scriptname)
        if self.have_fork or not ispy:
            if not self.is_executable(scriptfile):
                self.send_error(
                    HTTPStatus.FORBIDDEN,
                    "CGI script is not executable (%r)" % scriptname)
                return

        # Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
        # XXX Much of the following could be prepared ahead of time!
        env = copy.deepcopy(os.environ)
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.parse.unquote(rest)
        env['PATH_INFO'] = uqrest
        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = scriptname
        env['QUERY_STRING'] = query
        env['REMOTE_ADDR'] = self.client_address[0]
        authorization = self.headers.get("authorization")
        if authorization:
            authorization = authorization.split()
            if len(authorization) == 2:
                import base64, binascii
                env['AUTH_TYPE'] = authorization[0]
                if authorization[0].lower() == "basic":
                    try:
                        authorization = authorization[1].encode('ascii')
                        authorization = base64.decodebytes(authorization). \
                            decode('ascii')
                    except (binascii.Error, UnicodeError):
                        pass
                    else:
                        authorization = authorization.split(':')
                        if len(authorization) == 2:
                            env['REMOTE_USER'] = authorization[0]
        # XXX REMOTE_IDENT
        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']
        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        referer = self.headers.get('referer')
        if referer:
            env['HTTP_REFERER'] = referer
        accept = self.headers.get_all('accept', ())
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.get('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        co = filter(None, self.headers.get_all('cookie', []))
        cookie_str = ', '.join(co)
        if cookie_str:
            env['HTTP_COOKIE'] = cookie_str
        # XXX Other HTTP_* headers
        # Since we're setting the env in the parent, provide empty
        # values to override previously set values
        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
                  'HTTP_USER_AGENT', 'HTTP_COOKIE', 'HTTP_REFERER'):
            env.setdefault(k, "")

        self.send_response(HTTPStatus.OK, "Script output follows")
        self.flush_headers()

        decoded_query = query.replace('+', ' ')
        # Non-Unix -- use subprocess
        import subprocess
        cmdline = [scriptfile]
        if self.is_python(scriptfile):
            interp = sys.executable
            if getattr(sys, 'frozen', False):
              base_path = get_base_path()
              interp = f"{base_path}/py3.11/python"
            if interp.lower().endswith("w.exe"):
                # On Windows, use python.exe, not pythonw.exe
                interp = interp[:-5] + interp[-4:]
            cmdline = [interp, '-u'] + cmdline
        if '=' not in query:
            cmdline.append(query)
        self.log_message("command: %s", subprocess.list2cmdline(cmdline))
        try:
            nbytes = int(length)
        except (TypeError, ValueError):
            nbytes = 0
        if self.command.lower() == "post" and nbytes > 0:
            data = self.rfile.read(nbytes)
            env['HTTP_REQUEST_BODY'] = data.decode('utf-8')
        else:
            data = None
        p = subprocess.Popen(cmdline,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=env
                             )
        # throw away additional data [see bug #427345]
        while select.select([self.rfile._sock], [], [], 0)[0]:
            if not self.rfile._sock.recv(1):
                break

        # 支持流式输出
        stream = False
        if self.path == '/stream' or self.path == '/logs':
            stream = True
        if self.command == 'POST':
            post_json = json.loads(data.decode('utf-8'))
            stream = post_json.get('stream')
            if stream is None:
                stream = False
        if not stream:
            stdout, stderr = p.communicate(data)
            self.wfile.write(stdout)
            if stderr:
                self.log_error('%s', stderr)
        else:
            # 发送数据到子进程的标准输入
            if data:
                p.stdin.write(data)
                p.stdin.close()
            # 实时读取标准输出并写入到响应中
            while True:
                output = p.stdout.readline()
                if output == b'' and p.poll() is not None:
                    break
                if output:
                    try:
                        self.wfile.write(output)
                        self.wfile.flush()  # 确保数据立即发送给客户端
                    except Exception:
                        pass

        p.stderr.close()
        p.stdout.close()
        status = p.returncode
        if status:
            self.log_error("CGI script exit status %#x", status)
        else:
            self.log_message("CGI script exited OK")

    def is_cgi(self):
        if self.command == 'POST':
            self.cgi_info = 'cgi-bin', 'execPost.py' + self.path
        else:
            self.cgi_info = 'cgi-bin', 'execGET.py' + self.path
        return True

    def do_GET(self):
        with semaphore:
            set_apikey(self)
            super().do_GET()

    def do_POST(self):
        with semaphore:
            set_apikey(self)
            super().do_POST()

    def log_message(self, format, *args):
        message = format % args
        msg = ("%s - - [%s] %s" %
               (self.address_string(),
                self.log_date_time_string(),
                message.translate(self._control_char_table)))
        write_app_log(msg)


##MyHandler类结束

def set_apikey(self: MyHandler):
    authorization = self.headers.get("authorization")
    if authorization:
        authorization = authorization.split()
        if len(authorization) == 2:
            os.environ['API_KEY'] = authorization[1]


def print_logo():
    """Prints a logo to the console."""
    logo = """
                                                                                               
      ,---,                  ,--,      ,--,                          ,---,          ,----..       ,---, 
    ,--.' |                ,--.'|    ,--.'|                         '  .' \        /   /   \   ,`--.' | 
    |  |  :                |  | :    |  | :       ,---.            /  ;    '.     |   :     :  |   :  : 
    :  :  :                :  : '    :  : '      '   ,'\          :  :       \    .   |  ;. /  :   |  ' 
    :  |  |,--.    ,---.   |  ' |    |  ' |     /   /   |         :  |   /\   \   .   ; /--`   |   :  | 
    |  :  '   |   /     \  '  | |    '  | |    .   ; ,. :         |  :  ' ;.   :  ;   | ;  __  '   '  ; 
    |  |   /' :  /    /  | |  | :    |  | :    '   | |: :         |  |  ;/  \   \ |   : |.' .' |   |  | 
    '  :  | | | .    ' / | '  : |__  '  : |__  '   | .; :         '  :  | \  \ ,' .   | '_.' : '   :  ; 
    |  |  ' | : '   ;   /| |  | '.'| |  | '.'| |   :    |         |  |  '  '--'   '   ; : \  | |   |  ' 
    |  :  :_:,' '   |  / | ;  :    ; ;  :    ;  \   \  /          |  :  :         '   | '/  .' '   :  | 
    |  | ,'     |   :    | |  ,   /  |  ,   /    `----'           |  | ,'         |   :    /   ;   |.'  
    `--''        \   \  /   ---`-'    ---`-'                      `--''            \   \ .'    '---'    
                  `----'                                                            `---`               
                                                                                                    
    v0.0.6 - building the best open-source LLM logs analysis system.
    
    https://github.com/xuzexin-hz/llm-logs-analysis
    """
    print(logo)


def run_server(port=8000):
    server_address = ('', port)
    # httpd = HTTPServer(server_address, MyHandler)
    httpd = ThreadedHTTPServer(server_address, MyHandler)
    print(f"Starting server on port {port}...")
    print_logo()
    app_init()
    if not is_first_open():
        import webbrowser
        url = f"http://127.0.0.1:{port}"
        webbrowser.open(url)
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP server.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port number to listen on (default: 8000)')
    parser.add_argument('-bu', '--base_url', type=str, default='http://127.0.0.1:11434/v1/',
                        help='The OpenAi base_url (default: http://127.0.0.1:11434/v1/)')
    args = parser.parse_args()
    os.environ.setdefault("OPENAI_BASE_URL", args.base_url)
    run_server(args.port)
