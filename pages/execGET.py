import time

from utils.environ_utils import get_path, get_favicon, streamHeader, get_apikey, get_base_url, my_printHeader, \
    my_printBody
from utils.http_clientx import http_clientx
from utils.logs_utils import write_httplog, get_num, logs_stream_show


def my_GET():
    url_path = get_path()
    if url_path == '/favicon.ico':
        my_printHeader({"Content-Type": "image/jpeg",
                        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                        "Pragma": "no-cache",
                        "Expires": "0"})
        get_favicon()
    elif url_path == '/':
        my_printHeader({"Content-Type": "text/plain"})
        my_printBody('Hello AGI!')

    elif url_path == '/stream':
        streamHeader()
        for i in range(35):
            my_printBody(f"hello {i + 1}\n")
            time.sleep(1)  # 模拟长时间操作
    elif url_path == '/logs':
        logs_stream_show()
    elif '/v1/models' in url_path or '/models' in url_path:
        num = get_num()
        write_httplog(url_path, num)
        api_key = get_apikey()
        base_url = get_base_url()
        headers = {'Authorization': f'Bearer {api_key}'}
        client = http_clientx(base_url + '/v1/models')
        response = client.http_get(headers=headers)
        payload = response.text
        write_httplog(payload + '\n\n----------end----------', num)
        my_printHeader({"Content-Type": "application/json"})
        my_printBody(payload)
