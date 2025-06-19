import asyncio
import hashlib
import json
import os
from typing import Dict
from urllib.parse import parse_qs


class GlobalVal:
    myHandlerList = {}
    # 检测客户端sse时候日志记录到同一个文件中
    logsNumList = {}

    @staticmethod
    def myHandler():
        if GlobalVal.myHandlerList:
            coroutine_id = id(asyncio.current_task())
            return GlobalVal.myHandlerList[coroutine_id]


def get_base_path():
    return os.path.abspath(__file__) + "//..//../"


async def my_printBody(body: str, end_body=False):
    self = GlobalVal.myHandler()
    try:
        await self.server.send({
            'type': 'http.response.body',
            'body': body.encode('utf-8'),
            'more_body': True
        })
        if end_body:
            await self.server.send({
                'type': 'http.response.body',
                'body': b'',
            })
    except Exception as e:
        pass


async def my_printBytes(body: bytes, end_body=False):
    self = GlobalVal.myHandler()
    try:
        await self.server.send({
            'type': 'http.response.body',
            'body': body,
            'more_body': True
        })
        if (end_body == True):
            await self.server.send({
                'type': 'http.response.body',
                'body': b'',
            })
    except (Exception):
        pass


async def my_printBodyWS(body: str):
    self = GlobalVal.myHandler()
    try:
        await self.server.send({
            "type": "websocket.send",
            'text': body
        })
    except (Exception):
        pass


async def my_printHeader(headers_dict: Dict):
    self = GlobalVal.myHandler()
    headers_list = [(key.lower().encode('utf-8'), value.encode('utf-8')) for key, value in headers_dict.items()]
    await self.server.send({
        'type': 'http.response.start',
        'status': 200,
        'headers': headers_list
    })


def get_Res_Header(name: str):
    self = GlobalVal.myHandler()
    headers_dict = dict(self.server.scope['headers'])
    headers = {key.decode('utf-8'): value.decode('utf-8') for key, value in headers_dict.items()}
    return headers.get(name)


def get_request_json():
    self = GlobalVal.myHandler()
    body = self.server.HTTP_REQUEST_BODY
    return json.loads(body)


def get_path():
    self = GlobalVal.myHandler()
    return self.server.PATH_INFO


def get_query(name):
    self = GlobalVal.myHandler()
    query_string = self.server.scope['query_string']
    # 先将字节串解码为字符串
    query_string_str = query_string.decode('utf-8')
    # 使用 parse_qs 解析查询字符串
    params = parse_qs(query_string_str)
    # 获取 url 参数
    url = params.get(name, [None])[0]  # get 方法返回一个列表，取第一个元素
    return url


def get_request_num():
    self = GlobalVal.myHandler()
    return self.server.num


def get_request_server():
    self = GlobalVal.myHandler()
    return self.server


def get_apikey():
    self = GlobalVal.myHandler()
    if hasattr(self.server, 'API_KEY'):
        return self.server.API_KEY
    return 'API_KEY'


async def streamHeader():
    """
    Output the HTTP headers for SSE (Server-Sent Events), including:

    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - Connection: keep-alive

    This function is used to begin an SSE response, and is called before outputting
    any data in the stream.
    """
    await my_printHeader({"Content-Type": "text/event-stream"})


def get_base_url():
    return os.environ.get("OPENAI_BASE_URL", "")


async def get_favicon():
    base_path = get_base_path()
    image_path = f'{base_path}/pages/html/imgs/favicon.ico'
    if os.path.exists(image_path):
        # 打开并读取图片文件
        with open(image_path, 'rb') as image_file:
            await my_printBytes(image_file.read(), True)


def get_md5(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.hexdigest()
