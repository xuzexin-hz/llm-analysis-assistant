import argparse
import asyncio
import logging
import os
import re
import socket

import uvicorn

from pages.execGET import my_GET
from pages.execPost import my_POST
from pages.mySSE import mySSE_init
from utils.environ_utils import GlobalVal, get_base_path
from utils.logs_utils import app_init, is_first_open, logs_stream_show, get_num


class App:

    async def __call__(self, scope, receive, send):
        coroutine_id = id(asyncio.current_task())
        myself = type('DynamicAttr', (object,), {})()
        myself.server = type('DynamicAttr', (object,), {})()
        myself.server.scope = scope
        myself.server.receive = receive
        myself.server.send = send
        GlobalVal.myHandlerList[coroutine_id] = myself
        if scope['type'] == 'http':
            await set_my_environ(myself)
            if scope['method'] == 'GET':
                await my_GET()
            elif scope['method'] == 'POST':
                await my_POST()
        elif scope['type'] == 'websocket':
            # WebSocket 处理
            await send({
                'type': 'websocket.accept',
            })

            # 用于处理接收消息
            async def receive_message():
                while True:
                    message = await receive()
                    if message['type'] == 'websocket.receive':
                        return message

            if scope['path'] == '/logs_ws':
                # 调用 WebSocket 应用程序进行处理
                await logs_stream_show()
            elif scope['path'] == '/sse_ws':
                num = get_num()
                myself.server.num = num
                GlobalVal.myHandlerList[coroutine_id] = myself
                await mySSE_init(scope, receive_message, send, num)


async def set_my_environ(myself):
    if 'path' in myself.server.scope:
        myself.server.PATH_INFO = myself.server.scope['path']
        authorization_headers = [item for item in myself.server.scope['headers'] if item[0] == b'authorization']
        if authorization_headers:
            authorization_header = authorization_headers[0]
            if len(authorization_header) == 2:
                authorization = authorization_header[1].split()
                if len(authorization) == 2:
                    myself.server.API_KEY = authorization[1].decode()
        if myself.server.scope['method'] == 'POST':
            body = await read_body(myself.server.receive)
            myself.server.HTTP_REQUEST_BODY = body.decode()


async def read_body(receive):
    """
    Read and return the entire body from an incoming ASGI message.
    """
    body = b''
    more_body = True

    while more_body:
        message = await receive()
        body += message.get('body', b'')
        more_body = message.get('more_body', False)

    return body


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
                                                                                                    
    v0.1.0 - building the best open-source LLM logs analysis system.
    
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


class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Define the regex pattern to extract log components
        pattern = r'(?P<ip>[^ ]+) - "(?P<method>[^ ]+) (?P<path>[^ ]+) (?P<protocol>[^"]+)" (?P<status>\d+)'
        match = re.match(pattern, record.getMessage())

        # If the log message matches the expected format, extract the components
        if match:
            log_data = {
                'ip': match.group('ip'),
                'method': match.group('method'),
                'path': match.group('path'),
                'protocol': match.group('protocol'),
                'status': match.group('status')
            }
            record.message_json = log_data
        return super().format(record)


class CustomLogger(logging.getLoggerClass()):
    def __my_init__(self):
        base_path = get_base_path()
        file_handler = logging.FileHandler(base_path + 'logs/app.log')
        formatter = CustomJsonFormatter(
            "{'asctime':'%(asctime)s','name':'%(name)s','level':'%(levelname)s','data':%(message_json)s}")
        file_handler.setFormatter(formatter)
        self.handlers = []
        self.addHandler(file_handler)

    def __init__(self, name):
        super().__init__(name)

    def info(self, msg, *args, **kwargs):
        self.__my_init__()
        super().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.__my_init__()
        super().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.__my_init__()
        super().error(msg, *args, **kwargs)


def run_server(port=8000):
    # 使用自定义Logger类
    logging.setLoggerClass(CustomLogger)

    if __is_port_in_use(port):
        print(f"Port {port} is already in use. Please choose a different port.")
        return
    print(f"Starting server on port {port}...")
    print_logo()
    app_init()
    if not is_first_open():
        import webbrowser
        url = f"http://127.0.0.1:{port}"
        webbrowser.open(url)
    # 启动 Uvicorn 服务器
    uvicorn.run("server:App", factory=True, host='0.0.0.0', port=port, log_level="info", workers=4,
                ws_ping_interval=0.5, ws_ping_timeout=1.0)
    # app = App()
    # config = uvicorn.Config(app,factory=True, host='0.0.0.0', port=port, log_level="info", workers=4, ws_ping_interval=0.5,ws_ping_timeout=1.0)
    # server = uvicorn.Server(config)
    # server.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP server.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port number to listen on (default: 8000)')
    parser.add_argument('-bu', '--base_url', type=str, default='http://127.0.0.1:11434',
                        help='The OpenAi base_url (default: http://127.0.0.1:11434)')
    parser.add_argument('-mock', '--is_mock', type=str, default='False',
                        help='Control whether to enable the mock function for testing streaming output')
    parser.add_argument('-single_word', '--is_single_word', type=str, default='False',
                        help='Is the streaming output mock data displayed word for word')
    parser.add_argument('-ms', '--mock_string', type=str, default=None,
                        help='mock data of OpenAI and OLAM')
    parser.add_argument('-msc', '--mock_count', type=int, default=3,
                        help='mock data loop count')
    parser.add_argument('-looptime', '--looptime', type=float, default=0.35,
                        help='Simulated data loop tentative time (second)')
    args = parser.parse_args()
    os.environ["OPENAI_BASE_URL"] = args.base_url
    if args.is_mock.lower() == 'true' or args.is_mock.lower() == '1':
        os.environ["IS_MOCK"] = 'True'
    else:
        os.environ["IS_MOCK"] = 'False'
    if args.mock_string is not None:
        os.environ["mock_string"] = args.mock_string
    os.environ["mock_count"] = str(args.mock_count)
    os.environ["port"] = str(args.port)
    if args.is_single_word.lower() == 'true' or args.is_single_word.lower() == '1':
        os.environ["single_word"] = 'True'
    else:
        os.environ["single_word"] = 'False'
    os.environ["looptime"] = str(args.looptime)
    run_server(args.port)
