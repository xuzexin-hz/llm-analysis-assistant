import argparse
from http.server import CGIHTTPRequestHandler, HTTPServer, _url_collapse_path
import socket
import os


class MyHandler(CGIHTTPRequestHandler):

    # 明确指定参数类型
    def __init__(self, request: socket.socket, client_address: tuple[str, int], server: HTTPServer):
        super().__init__(request, client_address, server)  # 调用父类的构造函数

    def is_cgi(self):
        self.cgi_info = '/cgi-bin', 'execPost.py' + self.path
        return True

    def do_POST(self):
        get_apikey(self)
        super().do_POST()


def get_apikey(self: MyHandler):
    authorization = self.headers.get("authorization")
    if authorization:
        authorization = authorization.split()
        if len(authorization) == 2:
            os.environ['API_KEY'] = authorization[1]

def print_logo():
    """Prints a logo to the console."""
    logo = "\033[97m" + """
                                                                                               
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
                                                                                                    
    v0.0.2 - building the best open-source LLM logs analysis system.
    
    https://github.com/xuzexin-hz/llm-logs-analysis
    """ + "\033[0m"
    print(logo)

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"Starting server on port {port}...")
    print_logo()
    httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP server.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port number to listen on (default: 8000)')
    args = parser.parse_args()
    run_server(args.port)
