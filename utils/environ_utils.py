import asyncio
import json
import os
from typing import Dict


class GlobalVal:
    myHandlerList = {}

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
    except (Exception):
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


async def my_printHeader(headers_dict: Dict):
    self = GlobalVal.myHandler()
    headers_list = [(key.lower().encode('utf-8'), value.encode('utf-8')) for key, value in headers_dict.items()]
    await self.server.send({
        'type': 'http.response.start',
        'status': 200,
        'headers': headers_list
    })


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
