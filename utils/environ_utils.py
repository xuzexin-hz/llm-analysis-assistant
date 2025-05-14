import json
import os
import threading
from typing import Dict


class GlobalVal:
    myHandlerList = {}

    @staticmethod
    def myHandler():
        if GlobalVal.myHandlerList:
            thread_id = threading.get_ident()
            return GlobalVal.myHandlerList[thread_id]


def get_base_path():
    return os.path.abspath(__file__) + "//..//../"


def my_printBody(body: str):
    self = GlobalVal.myHandler()
    try:
        self.wfile.write(body.encode('utf-8'))
    except (Exception):
        pass


def my_printBodyBytes(body: bytes):
    self = GlobalVal.myHandler()
    try:
        self.wfile.write(body)
    except (Exception):
        pass


def my_printHeader(data: Dict):
    self = GlobalVal.myHandler()
    self.send_response(200)
    for name, value in data.items():
        self.send_header(name, value)
    self.end_headers()


def get_request_json():
    self = GlobalVal.myHandler()
    body = self.server.HTTP_REQUEST_BODY
    return json.loads(body)


def get_path():
    self = GlobalVal.myHandler()
    return self.server.PATH_INFO


def get_apikey():
    self = GlobalVal.myHandler()
    if hasattr(self.server, 'API_KEY'):
        return self.server.API_KEY
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
    my_printHeader({"Content-Type": "text/event-stream"})


def get_base_url():
    return os.environ.get("OPENAI_BASE_URL", "")


def get_favicon():
    base_path = get_base_path()
    image_path = f'{base_path}/pages/html/imgs/favicon.ico'
    if os.path.exists(image_path):
        # 打开并读取图片文件
        with open(image_path, 'rb') as image_file:
            my_printBodyBytes(image_file.read())
