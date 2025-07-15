import asyncio
import os

from llm_analysis_assistant.pages.mySSE import mySSE_sse
from llm_analysis_assistant.utils.environ_utils import get_path, get_favicon, streamHeader, get_apikey, \
    get_base_url, my_printHeader, \
    my_printBody, get_Res_Header, get_query, get_request_server, get_real_url
from llm_analysis_assistant.utils.http_clientx import http_clientx
from llm_analysis_assistant.utils.js_utils import js_show_page
from llm_analysis_assistant.utils.logs_utils import write_httplog, get_num, LOG_END_SYMBOL, LogType


async def my_GET():
    url_path = get_path()
    num = get_num()
    if url_path == '/favicon.ico':
        await my_printHeader({"Content-Type": "image/x-icon",
                              "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                              "Pragma": "no-cache",
                              "Expires": "0"})
        await get_favicon()
    elif url_path == '/' or url_path == '/?stream=true':
        sse = get_query('stream')
        if sse is None:
            await js_show_page("index")
        else:
            await streamHeader()
            str = 'Hello AGI!'
            str_length = len(str)
            for i in range(str_length):
                await my_printBody(str[i], True if i == str_length - 1 else False)
                await asyncio.sleep(0.35)

    elif url_path == '/stream':
        await streamHeader()
        for i in range(35):
            await my_printBody(f"hello {i + 1}\n", True if i == 34 else False)
            await asyncio.sleep(1)  # 模拟长时间操作
    elif url_path == '/logs':
        await js_show_page("logs_scroll_show")
    base_url = get_base_url()
    http_url = None
    if '/v1/models' in url_path or '/models' in url_path:
        http_url = base_url + '/v1/models'
    elif '/api/version' in url_path:
        http_url = base_url + '/api/version'
    elif '/api/tags' in url_path:
        http_url = base_url + '/api/tags'
    elif '/mcp' in url_path:
        user_agent = get_Res_Header("user-agent")
        # 浏览器请求
        if user_agent is not None and user_agent.startswith("Mozilla"):
            await js_show_page("mcp")
        else:
            http_url = get_query('url')
            server = get_request_server()
            await streamHeader()
            http_url = http_url.replace('  ', '++')
            os.environ["MCP_SSE_URL"] = http_url
            headers, http_url = get_real_url(http_url)
            await mySSE_sse(True, server.send, num, http_url, headers)
        return
    if http_url is not None:
        write_httplog(LogType.GET, url_path, num)
        api_key = get_apikey()
        headers = {'Authorization': f'Bearer {api_key}'}
        client = http_clientx(http_url)
        response = await client.http_get(headers=headers)
        payload = response.text
        write_httplog(LogType.RES, payload + '\n\n', num)
        write_httplog(LogType.END, LOG_END_SYMBOL, num)
        await my_printHeader({"Content-Type": "application/json"})
        await my_printBody(payload, True)
