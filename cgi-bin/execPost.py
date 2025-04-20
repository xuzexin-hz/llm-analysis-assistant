import json

from openai import OpenAI

from utils import cgi_utils
from utils.env_utils import get_envs
from utils.logs_utils import get_num, write_httplog
from utils.mock_utils import create_streamData


def my_POST():
    get_envs()
    api_key = cgi_utils.get_apikey()
    base_url = cgi_utils.get_base_url()
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    url_path = cgi_utils.get_path()
    num = get_num()
    write_httplog(url_path, num)
    post_json = cgi_utils.get_request_json()
    model = post_json['model']
    stream = post_json.get('stream')
    if stream is None:
        stream = True
    req_str = json.dumps(post_json, ensure_ascii=False)
    write_httplog(req_str, num)
    obj_key = ''
    obj_value = ''
    completion = None
    is_completions = False
    # 生成接口
    if '/v1/completions' in url_path or '/api/completions' in url_path or '/completions' == url_path:
        is_completions = True
        prompt = post_json['prompt']
        obj_key = 'text'
        completion = client.completions.create(
            model=model,
            prompt=prompt,
            stream=stream
        )
        if not stream:
            obj_value = completion.choices[0].text
    from utils.env_utils import is_mock
    # 聊天接口
    if '/v1/chat/completions' in url_path or '/api/chat' in url_path or '/chat/completions' in url_path:
        messages = post_json['messages']
        obj_key = 'message'
        if stream and is_mock == True:
            completion = None
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
        if not stream:
            obj_value = {
                "role": completion.choices[0].message.role,
                "content": completion.choices[0].message.content
            }
    if not stream:
        print("Content-Type: application/json")
        # 输出一个空行，表示头部结束
        print()
        payload = json.dumps({
            "id": completion.id,
            "object": completion.object,
            "created": completion.created,
            "model": completion.model,
            "system_fingerprint": completion.system_fingerprint,
            "choices": [
                {
                    "index": completion.choices[0].index,
                    obj_key: obj_value,
                    "finish_reason": completion.choices[0].finish_reason
                }
            ],
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens
            }
        }, ensure_ascii=False)
        write_httplog(payload + '\n\n----------end----------', num)
        print(payload)
    else:
        cgi_utils.streamHeader()

        def echoChunk():
            # 迭代输出流
            for chunk in completion:
                if chunk.choices[0].finish_reason == 'stop':
                    payload_chunk = '[DONE]'
                else:
                    if is_completions is False:
                        k = "delta"
                        v = {
                            "role": chunk.choices[0].delta.role,
                            "content": chunk.choices[0].delta.content
                        }
                    else:
                        k = obj_key
                        v = chunk.choices[0].text
                    payload_chunk = json.dumps({
                        "id": chunk.id,
                        "object": chunk.object,
                        "created": chunk.created,
                        "model": chunk.model,
                        "system_fingerprint": chunk.system_fingerprint,
                        "choices": [
                            {
                                "index": chunk.choices[0].index,
                                k: v,
                                "finish_reason": chunk.choices[0].finish_reason
                            }
                        ]
                    }, ensure_ascii=False)
                # 不加ensure_ascii=False,有些客户端不会显示中文
                data = 'data: ' + payload_chunk + '\n\n'
                write_httplog(data, num)
                print(data)

        if is_mock:
            create_streamData(num)
        else:
            echoChunk()
        write_httplog('\n\n----------end----------', num)


my_POST()
