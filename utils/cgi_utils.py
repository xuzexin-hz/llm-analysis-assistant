import json
import os
import sys


def get_request_body():
    if os.environ.get("HTTP_REQUEST_BODY") is not None:
        return os.environ["HTTP_REQUEST_BODY"]
    else:
        return "{}"


def get_request_json():
    return json.loads(get_request_body())


def get_path():
    return os.environ.get('PATH_INFO')


def get_apikey():
    if os.environ.get('API_KEY') is not None:
        return os.environ.get('API_KEY')
    return 'API_KEY'


def streamHeader():
    """
    Output the HTTP headers for SSE (Server-Sent Events), including:

    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - Connection: keep-alive

    This function is used to begin an SSE response, and is called before outputting
    any data in the stream.
    """
    # if os.environ.get('HTTP_USER_AGENT') is not None and 'aiohttp' in os.environ.get('HTTP_USER_AGENT'):
    # 上面判断是为了解决open webui的异常的bug，但是根据aiohttp太过武断
    # 下面这种判断更加严谨，只需要open webui配置api地址为:http://127.0.0.1:8000/Open WebUI
    if '/openwebui/' in os.environ.get('PATH_INFO').lower().replace(" ", ""):
        # open webui 需要此头部
        print("Content-Type: text/event-stream")
        # 输出一个空行，表示头部结束
        print()
    else:
        # 向客户端发送 HTTP 头
        # 流式输出时候加表头就会错误，why？
        # print('Content-Type: application/json')
        # 输出一个空行，表示头部结束
        print()


def get_base_url():
    if os.environ.get("OPENAI_BASE_URL") is not None:
        return os.environ.get("OPENAI_BASE_URL")
    else:
        return ""


def get_favicon():
    image_path = './cgi-bin/html/imgs/favicon.ico'
    if os.path.exists(image_path):
        # 打开并读取图片文件
        with open(image_path, 'rb') as image_file:
            sys.stdout.buffer.write(image_file.read())
