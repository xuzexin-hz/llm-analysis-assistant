import json
import os

from openai import OpenAI

from utils.environ_utils import get_path, streamHeader, get_apikey, get_base_url, my_printHeader, my_printBody, \
    get_request_json
from utils.logs_utils import get_num, write_httplog
from utils.mock_utils import create_streamData


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
    temperature = post_json.get('temperature')
    tools = post_json.get('tools')
    if stream is None:
        stream = False
    req_str = json.dumps(post_json, ensure_ascii=False)
    write_httplog(req_str, num)
    obj_key = ''
    obj_value = ''
    completion = None
    is_completions = False

    def get_one(llm_res):
        tool_calls = None
        if llm_res.tool_calls is not None:
            tool_calls = [{
                "id": tool.id,
                "index": tool.index,
                "type": tool.type,
                "function": {"name": tool.function.name, "arguments": tool.function.arguments}
            } for tool in llm_res.tool_calls]
        v = {
            "role": llm_res.role,
            "content": llm_res.content
        }
        if tool_calls is not None:
            v.setdefault('tool_calls', tool_calls)
        return v

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
    # 生成接口
    if res_type == 1:
        is_completions = True
        prompt = post_json['prompt']
        obj_key = 'text'
        completion = client.completions.create(
            model=model,
            prompt=prompt,
            stream=stream,
            temperature=temperature
        )
        if not stream:
            obj_value = completion.choices[0].text

    # 聊天接口
    if res_type == 2:
        messages = post_json['messages']
        obj_key = 'message'
        if stream and is_mock == True:
            completion = None
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                tools=tools
            )
        if not stream:
            obj_value = get_one(completion.choices[0].message)
    if res_type == 1 or res_type == 2:
        if not stream:
            my_printHeader({"Content-Type": "application/json"})
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
            my_printBody(payload)
        else:
            streamHeader()

            def echoChunk():
                all_msg = ''
                # 迭代输出流
                for chunk in completion:
                    if chunk.choices[0].finish_reason == 'stop':
                        payload_chunk = '[DONE]'
                    else:
                        if is_completions is False:
                            k = "delta"
                            v = get_one(chunk.choices[0].delta)
                            all_msg = all_msg + v['content']
                        else:
                            k = obj_key
                            v = chunk.choices[0].text
                            all_msg = all_msg + v
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
                    my_printBody(data)
                if all_msg != '':
                    write_httplog(all_msg, num)

            if is_mock == 'True':
                create_streamData(num)
            else:
                echoChunk()
            write_httplog('\n\n----------end----------', num)
    elif res_type == 3:
        my_printHeader({"Content-Type": "application/json"})
        input = post_json['input']
        embeddings = client.embeddings.create(
            model=model,
            input=input,
        )
        payload = json.dumps({
            "object": embeddings.object,
            "data": [
                {
                    "object": data.object,
                    "embedding": data.embedding,
                    "index": data.index,
                } for data in embeddings.data
            ],
            "model": embeddings.model,
            "usage": {
                "prompt_tokens": embeddings.usage.prompt_tokens,
                "total_tokens": embeddings.usage.total_tokens
            }
        }, ensure_ascii=False)
        write_httplog(payload + '\n\n----------end----------', num)
        my_printBody(payload)
