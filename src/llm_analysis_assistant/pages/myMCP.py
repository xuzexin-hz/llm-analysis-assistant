import json
import re
from urllib.parse import urlparse

from llm_analysis_assistant.utils.environ_utils import get_query, my_printBody, my_printHeader, get_real_url
from llm_analysis_assistant.utils.http_clientx import http_clientx
from llm_analysis_assistant.utils.logs_utils import write_httplog, LogType, LOG_END_SYMBOL


def my_json(data):
    # 使用正则表达式提取 event 和 data
    pattern = r'event:\s*(?P<event>.*?)\s*(?:.*\n)*?data:\s*(?P<data>.*)'
    match = re.search(pattern, data)
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


async def myMCP_msg(data, num, has_same_log):
    try:
        http_url = get_query('url')
        if http_url is None:
            return
        http_url = http_url.replace('  ', '++')
        headers, http_url = get_real_url(http_url)
        parsed_url = urlparse(http_url)
        url = parsed_url.scheme + "://" + parsed_url.netloc + '/mcp/'
        client = http_clientx(url)
        headers['accept'] = 'application/json,text/event-stream'
        headers['content-type'] = 'application/json'
        response = await client.http_post(headers=headers, data=data)
        jj = response.text
        write_httplog(LogType.RES, jj, num)
        if jj is not None:
            try:
                j = my_json(jj)
                if j:
                    jj = json.loads(j)['data']
            except Exception as e:
                pass
        my_header_res = response.header
        headers_res = {"Content-Type": "application/json; charset=utf-8"}
        if my_header_res.get('mcp-session-id') is not None:
            headers_res['mcp-session-id'] = my_header_res.get('mcp-session-id')
        await my_printHeader(headers_res)
        if not has_same_log:
            write_httplog(LogType.END, '\n\n' + LOG_END_SYMBOL, num)
        await my_printBody(jj, True)
    except Exception as e:
        pass
