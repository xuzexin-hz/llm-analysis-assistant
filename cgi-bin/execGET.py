import json
import time

from openai import OpenAI

from utils import cgi_utils
from utils.logs_utils import write_httplog, get_num, logs_stream_show


def my_GET():
    url_path = cgi_utils.get_path()
    if url_path == '/favicon.ico':
        print("Content-Type: image/jpeg")
        print("Cache-Control: no-store, no-cache, must-revalidate, max-age=0")
        print("Pragma: no-cache")
        print("Expires: 0")
        # 输出一个空行，表示头部结束
        print()
        cgi_utils.get_favicon()
    if url_path == '/':
        print("Content-Type: text/plain")
        # 输出一个空行，表示头部结束
        print()
        print('Hello AGI!')

    if url_path == '/stream':
        print("Content-Type: text/event-stream")
        cgi_utils.streamHeader()
        for i in range(10):
            print(f"hello {i + 1}")
            time.sleep(1)  # 模拟长时间操作
    if url_path == '/logs':
        print('Content-Type: text/html; charset=utf-8')
        cgi_utils.streamHeader()
    if '/v1/models' in url_path or '/models' in url_path:
        num = get_num()
        write_httplog(url_path, num)
        api_key = cgi_utils.get_apikey()
        base_url = cgi_utils.get_base_url()
        client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        completion = client.models.list()
        model_list = [
            {
                "id": model.id,
                "object": model.object,
                "created": model.created,
                "owned_by": model.owned_by
            }
            for model in completion.data
        ]
        print("Content-Type: application/json")
        # 输出一个空行，表示头部结束
        print()
        payload = json.dumps({
            "object": completion.object,
            "data": model_list
        }, ensure_ascii=False)
        write_httplog(payload + '\n\n----------end----------', num)
        print(payload)


my_GET()
