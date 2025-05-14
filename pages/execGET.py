import asyncio

from utils.environ_utils import get_path, get_favicon, streamHeader, get_apikey, get_base_url, my_printHeader, \
    my_printBody
from utils.http_clientx import http_clientx
from utils.logs_utils import write_httplog, get_num, logs_stream_show


async def my_GET():
    url_path = get_path()
    if url_path == '/favicon.ico':
        await my_printHeader({"Content-Type": "image/x-icon",
                              "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                              "Pragma": "no-cache",
                              "Expires": "0"})
        await get_favicon()
    elif url_path == '/':
        await streamHeader()
        str = 'Hello AGI!'
        str_length = len(str)
        for i in range(str_length):
            await my_printBody(str[i], True if i == str_length - 1 else False)
            await asyncio.sleep(0.35)

    elif url_path == '/stream':
        await streamHeader()
        for i in range(35):
            await my_printBody(f"hello {i + 1}\n", True if i == 34 else False)
            await asyncio.sleep(1)  # 模拟长时间操作
    elif url_path == '/logs':
        await logs_stream_show()
    base_url = get_base_url()
    http_url = None
    if '/v1/models' in url_path or '/models' in url_path:
        http_url = base_url + '/v1/models'
    elif '/api/version' in url_path:
        http_url = base_url + '/api/version'
    elif '/api/tags' in url_path:
        http_url = base_url + '/api/tags'
    if http_url is not None:
        num = get_num()
        write_httplog(url_path, num)
        api_key = get_apikey()
        headers = {'Authorization': f'Bearer {api_key}'}
        client = http_clientx(http_url)
        response = client.http_get(headers=headers)
        payload = response.text
        write_httplog(payload + '\n\n----------end----------', num)
        await my_printHeader({"Content-Type": "application/json"})
        await my_printBody(payload, True)
