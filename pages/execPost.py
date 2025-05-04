import json
import os

from openai import OpenAI

from utils.environ_utils import get_path, streamHeader, get_apikey, get_base_url, my_printHeader, my_printBody, \
    get_request_json
from utils.http_clientx import http_clientx
from utils.logs_utils import get_num, write_httplog
from utils.mock_utils import create_staticStream, create_staticData


def my_POST():
    api_key = get_apikey()
    base_url = get_base_url()
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    url_path = get_path()
    num = get_num()
    write_httplog(url_path, num)
    post_json = get_request_json()
    model = post_json['model']
    stream = post_json.get('stream')
    if stream is None:
        stream = False
    req_str = json.dumps(post_json, ensure_ascii=False)
    write_httplog(req_str, num)

    is_mock = os.environ.get("IS_MOCK")
    res_type = None
    if '/v1/completions' in url_path:
        res_type = 1
    elif '/v1/chat/completions' in url_path or '/chat/completions' in url_path:
        res_type = 2
    elif '/completions' in url_path:
        res_type = 1
    elif 'v1/embeddings' in url_path:
        res_type = 3

    headers = {'Authorization': f'Bearer {api_key}'}
    http_url = None
    # 生成接口
    if res_type == 1:
        http_url = base_url + '/v1/completions'
    # 聊天接口
    if res_type == 2:
        http_url = base_url + '/v1/chat/completions'
    # embedding接口
    if res_type == 3:
        http_url = base_url + '/v1/embeddings'
    # 模拟数据接口
    if (not stream and is_mock == 'True' and res_type != 3) or (stream and is_mock == 'True'):
        pass
    else:
        client = http_clientx(http_url)
        response = client.http_post(headers=headers, data=post_json)
    if not stream:
        my_printHeader({"Content-Type": "application/json"})
        if is_mock == 'True' and res_type != 3:
            create_staticData(num, model, res_type)
        else:
            payload = response.text
            my_printBody(payload)
            write_httplog(payload + '\n\n----------end----------', num)
    else:
        streamHeader()

        def echoChunk():
            all_msg = ''
            # 迭代输出流
            for chunk in response:
                data = chunk.decode()
                data = data + '\n\n'
                write_httplog(data, num)
                my_printBody('data: ' + data)
                try:
                    v = json.loads(data)
                    if res_type == 1:
                        all_msg = all_msg + v['choices'][0]['text']
                    elif res_type == 2:
                        all_msg = all_msg + v['choices'][0]['delta']['content']
                except Exception as e:
                    pass
            if all_msg != '':
                write_httplog(all_msg, num)

        if is_mock == 'True':
            create_staticStream(num, model, res_type)
        else:
            echoChunk()
        write_httplog('\n\n----------end----------', num)
