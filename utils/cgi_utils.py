import json
import os
import sys

from utils.env_utils import get_base_path


def get_request_body():
    return os.environ.get("HTTP_REQUEST_BODY", "{}")


def get_request_json():
    return json.loads(get_request_body())


def get_path():
    return os.environ.get('PATH_INFO')


def get_apikey():
    return os.environ.get('API_KEY', 'API_KEY')


def streamHeader():
    """
    Output the HTTP headers for SSE (Server-Sent Events), including:

    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - Connection: keep-alive

    This function is used to begin an SSE response, and is called before outputting
    any data in the stream.
    """
    print("Content-Type: text/event-stream")
    # 输出一个空行，表示头部结束
    print()


def get_base_url():
    return os.environ.get("OPENAI_BASE_URL", "")


def get_favicon():
    base_path = get_base_path()
    image_path = f'{base_path}/cgi-bin/html/imgs/favicon.ico'
    if os.path.exists(image_path):
        # 打开并读取图片文件
        with open(image_path, 'rb') as image_file:
            sys.stdout.buffer.write(image_file.read())
