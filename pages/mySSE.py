import asyncio
import json
import os
import re

from utils.environ_utils import get_query, my_printBody, get_md5, GlobalVal
from utils.http_clientx import http_clientx
from utils.logs_utils import write_httplog, LogType, LOG_END_SYMBOL


def my_json(data):
    # 使用正则表达式提取 event 和 data
    pattern = r'event:\s*(?P<event>.*?)\s*data:\s*(?P<data>.*)'
    match = re.match(pattern, data)
    if match:
        # 提取 event 和 data
        event = match.group('event').strip()
        data_field = match.group('data').strip()
        # 创建 JSON 对象
        json_output = {
            "event": event,
            "data": data_field
        }
        # 将 JSON 对象转换为字符串
        return json.dumps(json_output)
    else:
        return None


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
        pass


async def mySSE_init(scope, receive_message, send, num):
    http_url = get_query('url')
    task = asyncio.create_task(mySSE_sse(False, send, num, http_url))
    try:
        while True:
            message = await receive_message()
            if message['type'] == 'websocket.disconnect':
                task.cancel()
                break
    except Exception as e:
        task.cancel()
        print(f"Connection error: {e}")


async def mySSE_msg(data, num, has_same_log, http_url):
    if http_url is None:
        return
    client = http_clientx(http_url)
    if data['method'] in ['initialize', 'notifications/initialized', 'tools/list', 'prompts/list', 'resources/list',
                          'tools/call', 'prompts/get', 'resources/read']:
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
