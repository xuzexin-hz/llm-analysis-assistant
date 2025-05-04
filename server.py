import argparse
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from pages.execGET import my_GET
from pages.execPost import my_POST
from utils.environ_utils import GlobalVal
from utils.logs_utils import app_init, write_app_log, is_first_open

# 定义一个信号量，最大并发线程数为 50
MAX_CONCURRENT_THREADS = 50
semaphore = threading.BoundedSemaphore(value=MAX_CONCURRENT_THREADS)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass


class MyHandler(BaseHTTPRequestHandler):

    # 明确指定参数类型
    def __init__(self, request: socket.socket, client_address: tuple[str, int], server: ThreadedHTTPServer):
        super().__init__(request, client_address, server)

    def finish(self):
        super().finish()
        thread_id = threading.get_ident()
        if GlobalVal.myHandlerList.get(thread_id):
            del GlobalVal.myHandlerList[thread_id]

    def parse_request(self):
        ret = super().parse_request()
        set_my_environ(self)
        thread_id = threading.get_ident()
        GlobalVal.myHandlerList[thread_id] = self
        return ret

    def do_GET(self):
        with semaphore:
            my_GET()

    def do_POST(self):
        with semaphore:
            my_POST()

    def log_message(self, format, *args):
        message = format % args
        if hasattr(self, "_control_char_table"):
            msg_format = message.translate(self._control_char_table)
        else:
            msg_format = message
        msg = ("%s - %s" % (self.address_string(), msg_format))
        write_app_log(msg)


##MyHandler类结束

def set_my_environ(self: MyHandler):
    self.server.PATH_INFO = self.path
    authorization = self.headers.get("authorization")
    if authorization:
        authorization = authorization.split()
        if len(authorization) == 2:
            self.server.API_KEY = authorization[1]
    if self.command == 'POST':
        self.server.HTTP_REQUEST_BODY = self.rfile.read(int(self.headers['content-length']))


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
                                                                                                    
    v0.0.8 - building the best open-source LLM logs analysis system.
    
    https://github.com/xuzexin-hz/llm-logs-analysis
    """
    print(logo)


def __is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('localhost', port))
            return True
        except ConnectionRefusedError:
            return False


def run_server(port=8000):
    if __is_port_in_use(port):
        print(f"Port {port} is already in use. Please choose a different port.")
        return
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
    parser.add_argument('-bu', '--base_url', type=str, default='http://127.0.0.1:11434',
                        help='The OpenAi base_url (default: http://127.0.0.1:11434)')
    parser.add_argument('-mock', '--is_mock', type=str, default='False',
                        help='Control whether to enable the mock function for testing streaming output')
    args = parser.parse_args()
    os.environ["OPENAI_BASE_URL"] = args.base_url
    if args.is_mock.lower() == 'true' or args.is_mock.lower() == '1':
        os.environ["IS_MOCK"] = 'True'
    else:
        os.environ["IS_MOCK"] = 'False'
    run_server(args.port)
