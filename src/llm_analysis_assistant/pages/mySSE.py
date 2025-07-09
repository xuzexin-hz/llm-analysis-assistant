import asyncio
import json
import os

from llm_analysis_assistant.pages.myMCP import my_json
from llm_analysis_assistant.utils.environ_utils import get_query, my_printBody, get_md5, GlobalVal
from llm_analysis_assistant.utils.http_clientx import http_clientx
from llm_analysis_assistant.utils.logs_utils import write_httplog, LogType, LOG_END_SYMBOL


async def mySSE_sse(is_http, send, num, http_url):
    os.environ["MCP_HTTP_URL"] = http_url
    try:
        write_httplog(LogType.SSEQ, http_url, num)
        if http_url is None:
            return
        client = http_clientx(http_url)
        client.HTTP_TYPE = 'SSE'
        response = await client.http_get(headers=None, stream=True)
        async for chunk in response:
            data = chunk.decode()
            if ': ping' in data:
                # 非浏览器请求，还是要发送ping的，保持和sse本身一样
                if is_http:
                    if send.__self__.disconnected:
                        break
                    await send({
                        'type': 'http.response.body',
                        'body': data.encode('utf-8'),
                        'more_body': True
                    })
                    await asyncio.sleep(1)
            if ': ping' not in data and data != '':
                jj = my_json(data)
                if jj is not None:
                    # sse 请求日志放到一起
                    j = json.loads(jj)
                    if j.get('event') and j.get('event') == 'endpoint':
                        md5_str = get_md5(j.get('data'))
                        GlobalVal.logsNumList[md5_str] = num
                    # 非浏览器请求
                    if is_http:
                        await send({
                            'type': 'http.response.body',
                            'body': data.encode('utf-8'),
                            'more_body': True
                        })
                        write_httplog(LogType.SSES, data + '\n\n', num)
                        await asyncio.sleep(0)
                        continue
                    try:
                        await send({
                            "type": "websocket.send",
                            'text': jj
                        })
                    except Exception as e:
                        break
                    write_httplog(LogType.SSES, jj + '\n\n', num)
                    await asyncio.sleep(0)
    except Exception as e:
        print(f"Connection error: {e}")
        await send({
            "type": "websocket.send",
            'text': f"Connection error: {e}"
        })
        await asyncio.sleep(0)
        asyncio.current_task().cancel()


async def mySSE_receive(receive_message, task):
    try:
        while True:
            message = await receive_message()
            if message['type'] == 'websocket.disconnect':
                task.cancel()
                asyncio.current_task().cancel()
                break
    except Exception as e:
        task.cancel()
        print(f"Connection error: {e}")


async def mySSE_init(scope, receive_message, send, num):
    http_url = get_query('url')
    sse_task = asyncio.create_task(mySSE_sse(False, send, num, http_url))
    receive_task = asyncio.create_task(mySSE_receive(receive_message, sse_task))
    try:
        while True:
            await asyncio.sleep(1)
            # web端主动断或者sse连接异常，这里都结束
            if sse_task.done() or receive_task.done():
                break
    except Exception as e:
        print(f"Connection error: {e}")


async def mySSE_msg(data, num, has_same_log, http_url):
    if http_url is None:
        return
    client = http_clientx(http_url)
    if data['method'] in ['initialize', 'notifications/initialized', 'tools/list', 'prompts/list', 'resources/list',
                          'tools/call', 'prompts/get', 'resources/read', 'resources/templates/list']:
        if 'url' in data:
            del data['url']
        headers = {'Content-Type': 'application/json'}
        try:
            response = await client.http_post(headers=headers, data=data)
            write_httplog(LogType.RES, response.text, num)
            if not has_same_log:
                write_httplog(LogType.END, '\n\n' + LOG_END_SYMBOL, num)
            await my_printBody(response.text, True)
        except Exception as e:
            pass
