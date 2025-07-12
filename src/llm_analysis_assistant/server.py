import argparse
import asyncio
import importlib.metadata
import os
import signal
import socket
import sys
import webbrowser

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.append(root_dir)
import uvicorn

from llm_analysis_assistant.pages.execGET import my_GET
from llm_analysis_assistant.pages.execPost import my_POST
from llm_analysis_assistant.pages.mySSE import mySSE_init
from llm_analysis_assistant.pages.myStdio import myStdio_msg
from llm_analysis_assistant.utils.environ_utils import GlobalVal, get_base_path, get_query, get_project_name, \
    get_project_version
from llm_analysis_assistant.utils.logs_utils import app_init, is_first_open, logs_stream_show, get_num


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
            if scope['path'] == '/logs_ws':
                # 调用 WebSocket 应用程序进行处理
                latest_time = get_query('tt')
                await logs_stream_show(float(latest_time))
            elif scope['path'] == '/sse_ws':
                num = get_num()
                myself.server.num = num
                GlobalVal.myHandlerList[coroutine_id] = myself
                command = get_query('command')
                if command is not None:
                    await myStdio_msg(command, receive, send, num)
                else:
                    await mySSE_init(scope, receive, send, num)
                await send({
                    'type': 'websocket.close',
                })
                await asyncio.sleep(0)


async def set_my_environ(myself):
    if 'path' in myself.server.scope:
        query_string = ''
        # 记录完整url，目前是mcp协议中使用
        if (myself.server.scope['query_string'].decode() != ""):
            query_string = "?" + myself.server.scope['query_string'].decode()
        myself.server.PATH_INFO = myself.server.scope['path'] + query_string
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
    logo = fr"""
                                                                                               
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
                                                                                                    
    {os.environ["PROJECT_VERSION"]} - building the best open-source LLM analysis assistant.
    
    https://github.com/xuzexin-hz/llm-analysis-assistant
    """
    print(logo)


def __is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(('localhost', port))
            return True
        except ConnectionRefusedError:
            return False


def run_server(port):
    if __is_port_in_use(port):
        print(f"Port {port} is already in use. Please choose a different port.")
        return
    print(f"Starting server on port {port}...")
    print_logo()
    app_init()
    if not is_first_open() and os.environ.get('LAA-NO-HI') is None:
        url = f"http://127.0.0.1:{port}"
        webbrowser.open(url)
    # 启动 Uvicorn 服务器
    base_path = get_base_path()
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
            },
            "access": {
                "()": os.environ["PROJECT_NAME"] + ".utils.logs_utils.CustomJsonFormatter",
                "fmt": "{'asctime':'%(asctime)s','name':'%(name)s','level':'%(levelname)s','data':%(message_json)s}",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": base_path + 'logs/app.log',
            },
            "access": {
                "formatter": "access",
                "class": "logging.FileHandler",
                "filename": base_path + 'logs/app.log',
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }
    # uvicorn.run("server:App", factory=True, host='0.0.0.0', port=port, log_level="info", workers=4,
    #             ws_ping_interval=0.5, ws_ping_timeout=1.0, log_config=LOGGING_CONFIG)

    app = App()
    config = uvicorn.Config(app, host='0.0.0.0', port=port, log_level="info", ws_ping_interval=0.5,
                            ws_ping_timeout=1.0, log_config=LOGGING_CONFIG)
    server = uvicorn.Server(config)
    server.run()


def main():
    try:
        if __package__ is not None and __package__ != '':
            os.environ["PROJECT_NAME"] = __package__
            version = importlib.metadata.version(__package__)
            os.environ["PROJECT_VERSION"] = 'v' + version
    except importlib.metadata.PackageNotFoundError:
        pass
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)
    os.environ["PROJECT_NAME"] = get_project_name()
    os.environ["PROJECT_VERSION"] = get_project_version()
    parser = argparse.ArgumentParser(description='HTTP server.')
    parser.add_argument('--port', type=int, default=8000, help='Port number to listen on (default: 8000)')
    parser.add_argument('--base_url', type=str, default='http://127.0.0.1:11434',
                        help='The OpenAi base_url (default: http://127.0.0.1:11434)')
    parser.add_argument('--is_mock', type=str, default='False',
                        help='Control whether to enable the mock function for testing streaming output')
    parser.add_argument('--single_word', type=str, default='False',
                        help='Is the streaming output mock data displayed word for word')
    parser.add_argument('--mock_string', type=str, default=None,
                        help='mock data of OpenAI and OLAM')
    parser.add_argument('--mock_count', type=int, default=3,
                        help='mock data loop count')
    parser.add_argument('--looptime', type=float, default=0.35,
                        help='Simulated data loop tentative time (second)')
    args, argv = parser.parse_known_args()
    if len(argv) == 0:
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
        if args.single_word.lower() == 'true' or args.single_word.lower() == '1':
            os.environ["single_word"] = 'True'
        else:
            os.environ["single_word"] = 'False'
        os.environ["looptime"] = str(args.looptime)
        run_server(args.port)
    else:
        args = sys.argv
        if len(args) == 2:
            command = args[1]
            num = get_num()
            asyncio.run(myStdio_msg(command, None, None, num))


def graceful_exit(signum, frame):
    print(f"Please wait, the system is exiting")


if __name__ == '__main__':
    main()
