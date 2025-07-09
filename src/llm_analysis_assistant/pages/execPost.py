import asyncio
import json
import os
from urllib.parse import urlparse

from llm_analysis_assistant.pages.myMCP import myMCP_msg
from llm_analysis_assistant.pages.mySSE import mySSE_msg
from llm_analysis_assistant.utils.environ_utils import get_path, streamHeader, get_apikey, get_base_url, \
    my_printHeader, my_printBody, \
    get_request_json, get_md5, GlobalVal
from llm_analysis_assistant.utils.http_clientx import http_clientx
from llm_analysis_assistant.utils.logs_utils import get_num, write_httplog, LOG_END_SYMBOL, LogType
from llm_analysis_assistant.utils.mock_utils import create_staticStream, create_staticData


async def my_POST():
    api_key = get_apikey()
    base_url = get_base_url()
    url_path = get_path()
    post_json = get_request_json()
    model = post_json.get('model')
    stream = post_json.get('stream')
    if stream is None:
        stream = False
    req_str = json.dumps(post_json, ensure_ascii=False)
    # mcp sse的调用
    if '/sse_msg' in url_path or '/messages/' in url_path or '/message?' in url_path:
        await my_printHeader({"Content-Type": "application/json; charset=utf-8"})
        http_url = post_json.get('url')
        # llm调用mcp时候
        if http_url is None and os.environ.get("MCP_HTTP_URL") is not None:
            parsed_url = urlparse(os.environ.get("MCP_HTTP_URL"))
            http_url = parsed_url.scheme + "://" + parsed_url.netloc + '' + url_path
        # llm调用mcp时候
        if '/messages/' in url_path or '/message?' in url_path:
            md5_str = get_md5(url_path)
        elif '/sse_msg' in url_path:
            parsed_url = urlparse(post_json.get('url'))
            md5_str = get_md5(parsed_url.path + "?" + parsed_url.query)
        has_same_log = False
        if GlobalVal.logsNumList.get(md5_str) is not None:
            same_num = GlobalVal.logsNumList.get(md5_str)
            has_same_log = True
        else:
            same_num = get_num()
        write_httplog(LogType.POST, http_url, same_num)
        write_httplog(LogType.REQ, req_str, same_num)
        await mySSE_msg(post_json, same_num, has_same_log, http_url)
        return
    num = get_num()
    write_httplog(LogType.POST, url_path, num)
    write_httplog(LogType.REQ, req_str, num)
    # mcp streamable-http的调用
    if '/mcp' in url_path:
        await myMCP_msg(post_json, num)
        return
    is_mock_str = os.environ.get("IS_MOCK")
    res_type = None
    if '/v1/completions' in url_path:
        res_type = 1
    elif '/v1/chat/completions' in url_path or '/chat/completions' in url_path:
        res_type = 2
    elif '/completions' in url_path:
        res_type = 1
    elif '/v1/embeddings' in url_path:
        res_type = 3
    elif '/api/generate' in url_path:
        res_type = 4
    elif '/api/chat' in url_path:
        res_type = 5
    elif '/api/show' in url_path:
        res_type = 6
    elif '/api/embed' in url_path:
        res_type = 7
    elif '/v1/responses' in url_path:
        res_type = 8
    headers = {'Authorization': f'Bearer {api_key}'}
    http_url = None
    is_mock = False
    if is_mock_str == 'True' and res_type in [1, 2, 4, 5, 8]:
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
    elif res_type == 8:
        http_url = base_url + '/v1/responses'
    # 模拟openai数据接口

    if is_mock:
        pass
    else:
        client = http_clientx(http_url)
        response = await client.http_post(headers=headers, data=post_json)
    if not stream:
        await my_printHeader({"Content-Type": "application/json; charset=utf-8"})
        if is_mock:
            await create_staticData(num, model, res_type)
        else:
            payload = response.text
            await my_printBody(payload, True)
            write_httplog(LogType.RES, payload, num)
            write_httplog(LogType.END, '\n\n' + LOG_END_SYMBOL, num)
    else:
        await streamHeader()

        async def echoChunk():
            all_msg = ''
            # 迭代输出流
            async for chunk in response:
                data = chunk.decode()
                if res_type in [4, 5]:
                    pre_data = ''
                    data = data + '\n'
                else:
                    pre_data = 'data: '
                    data = data + '\n\n'
                write_httplog(LogType.REC, data, num)
                await my_printBody(pre_data + data)
                # 让出CPU，让事件循环有机会刷新和发送当前的数据
                await asyncio.sleep(0)
                try:
                    v = json.loads(data)
                    if res_type == 1:
                        all_msg = all_msg + v['choices'][0]['text']
                    elif res_type == 2:
                        all_msg = all_msg + v['choices'][0]['delta']['content']
                    elif res_type == 4:
                        all_msg = all_msg + v['response']
                    elif res_type == 5:
                        all_msg = all_msg + v['message']['content']
                except Exception as e:
                    pass
            await my_printBody('', True)
            if all_msg != '':
                write_httplog(LogType.REM, all_msg, num)

        if is_mock:
            await create_staticStream(num, model, res_type)
        else:
            await echoChunk()
        write_httplog(LogType.END, '\n\n' + LOG_END_SYMBOL, num)
