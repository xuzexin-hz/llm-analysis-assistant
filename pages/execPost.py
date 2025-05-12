import json
import os

from utils.environ_utils import get_path, streamHeader, get_apikey, get_base_url, my_printHeader, my_printBody, \
    get_request_json
from utils.http_clientx import http_clientx
from utils.logs_utils import get_num, write_httplog
from utils.mock_utils import create_staticStream, create_staticData


def my_POST():
    api_key = get_apikey()
    base_url = get_base_url()
    url_path = get_path()
    num = get_num()
    write_httplog(url_path, num)
    post_json = get_request_json()
    model = post_json.get('model')
    stream = post_json.get('stream')
    if stream is None:
        stream = False
    req_str = json.dumps(post_json, ensure_ascii=False)
    write_httplog(req_str, num)

    is_mock_str = os.environ.get("IS_MOCK")
    res_type = None
    if '/v1/completions' in url_path:
        res_type = 1
    elif '/v1/chat/completions' in url_path or '/chat/completions' in url_path:
        res_type = 2
    elif '/completions' in url_path:
        res_type = 1
    elif 'v1/embeddings' in url_path:
        res_type = 3
    elif '/api/generate' in url_path:
        res_type = 4
    elif '/api/chat' in url_path:
        res_type = 5
    elif '/api/show' in url_path:
        res_type = 6
    elif '/api/embed' in url_path:
        res_type = 7
    headers = {'Authorization': f'Bearer {api_key}'}
    http_url = None
    is_mock = False
    if is_mock_str == 'True' and res_type in [1, 2, 4, 5]:
        is_mock = True
    if res_type in [4, 5]:
        if stream is None:
            stream = True
            post_json['stream'] = True
    # 生成接口
    if res_type == 1:
        http_url = base_url + '/v1/completions'
    # 聊天接口
    elif res_type == 2:
        http_url = base_url + '/v1/chat/completions'
    # embedding接口
    elif res_type == 3:
        http_url = base_url + '/v1/embeddings'
    # ollama的生成接口
    elif res_type == 4:
        http_url = base_url + '/api/generate'
    # ollama的聊天接口
    elif res_type == 5:
        http_url = base_url + '/api/chat'
    elif res_type == 6:
        http_url = base_url + '/api/show'
    elif res_type == 7:
        http_url = base_url + '/api/embed'
    # 模拟openai数据接口
    if is_mock:
        pass
    else:
        client = http_clientx(http_url)
        response = client.http_post(headers=headers, data=post_json)
    if not stream:
        my_printHeader({"Content-Type": "application/json; charset=utf-8"})
        if is_mock:
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
                if res_type in [4, 5]:
                    pre_data = ''
                    data = data + '\n'
                else:
                    pre_data = 'data: '
                    data = data + '\n\n'
                write_httplog(data, num)
                my_printBody(pre_data + data)
                try:
                    v = json.loads(data)
                    if res_type == 1:
                        all_msg = all_msg + v['choices'][0]['text']
                    elif res_type == 2:
                        all_msg = all_msg + v['choices'][0]['delta']['content']
                    elif res_type in [4, 5]:
                        all_msg = all_msg + v['response']
                except Exception as e:
                    pass
            if all_msg != '':
                write_httplog(all_msg, num)

        if is_mock:
            create_staticStream(num, model, res_type)
        else:
            echoChunk()
        write_httplog('\n\n----------end----------', num)
