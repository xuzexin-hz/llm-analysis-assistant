import asyncio
import os
import time
from datetime import datetime, timedelta, timezone

from llm_analysis_assistant.utils.environ_utils import my_printBody
from llm_analysis_assistant.utils.logs_utils import write_httplog, LogType


async def create_staticData(num, model, res_type):
    content = '我是一个AI助手，属于' + os.environ["PROJECT_NAME"] + '。'
    if os.environ.get('mock_string') is not None:
        content = os.environ.get('mock_string')
    my_time = int(time.time())
    utc_time = datetime.fromtimestamp(my_time, tz=timezone.utc)
    beijing_timezone = timezone(timedelta(hours=8))
    beijing_time = utc_time.astimezone(beijing_timezone)
    # 格式化输出
    formatted_time = beijing_time.isoformat()
    # openai生成接口
    if res_type == 1:
        completion = [
            f'{{ "id": "chatcmpl-1111", "object": "text_completion", "created": {my_time}, "model": "{model}", "system_fingerprint": "fp_openai", "choices": [ {{ "index": 0, "text": "{content} -- by openai", "finish_reason": "stop" }} ], "usage": {{ "prompt_tokens": 62, "completion_tokens": 11, "total_tokens": 73 }} }}\n\n'
        ]
    # openai聊天接口
    elif res_type == 2:
        completion = [
            f'{{ "id": "chatcmpl-1111", "object": "chat.completion", "created": {my_time}, "model": "{model}", "system_fingerprint": "fp_openai", "choices": [ {{ "index": 0, "message": {{ "role": "assistant", "content": "{content} -- by openai" }}, "finish_reason": "stop" }} ], "usage": {{ "prompt_tokens": 62, "completion_tokens": 11, "total_tokens": 73 }} }}\n\n'
        ]
    # ollama生成接口
    elif res_type == 4:
        completion = [
            f'{{ "model": "{model}", "created_at": "{formatted_time}", "response": "{content} -- by ollama", "done": true, "done_reason": "stop", "context": [ ], "total_duration": 3175221600, "load_duration": 22682100, "prompt_eval_count": 43, "prompt_eval_duration": 424109000, "eval_count": 57, "eval_duration": 2726840000 }}\n\n'
        ]
    # ollama聊天接口
    elif res_type == 5:
        completion = [
            f'{{ "model": "{model}", "created_at": "{formatted_time}", "message": {{ "role": "assistant", "content": "{content} -- by ollama" }}, "done": true, "total_duration": 5191566416, "load_duration": 2154458, "prompt_eval_count": 26, "prompt_eval_duration": 383809000, "eval_count": 298, "eval_duration": 4799921000 }}\n\n'
        ]
    elif res_type == 8:
        completion = [
            f'{{ "id": "", "object": "response", "created_at": {my_time}, "status": "completed", "error": null, "incomplete_details": null, "instructions": null, "max_output_tokens": null, "model": "{model}", "output": [ {{ "type": "message", "id": "", "status": "completed", "role": "assistant", "content": [ {{ "type": "output_text", "text": "{content} -- by openai", "annotations": [] }} ] }} ], "parallel_tool_calls": true, "previous_response_id": null, "reasoning": {{ "effort": null, "summary": null }}, "store": true, "temperature": 1.0, "text": {{ "format": {{ "type": "text" }} }}, "tool_choice": "auto", "tools": [], "top_p": 1.0, "truncation": "disabled", "usage": {{"input_tokens": 1, "input_tokens_details": {{"cached_tokens": 0 }}, "output_tokens": 1, "output_tokens_details": {{"reasoning_tokens": 0 }}, "total_tokens": 1 }}, "user": null, "metadata": {{}} }}\n\n'
        ]

    for chunk in completion:
        await my_printBody(chunk)
        write_httplog(LogType.REC, chunk, num)
    await my_printBody('', True)


async def create_staticStream(num, model, res_type):
    my_time = int(time.time())
    utc_time = datetime.fromtimestamp(my_time, tz=timezone.utc)
    beijing_timezone = timezone(timedelta(hours=8))
    beijing_time = utc_time.astimezone(beijing_timezone)
    # 格式化输出
    formatted_time = beijing_time.isoformat()
    content = ['', '', '']
    if os.environ.get('mock_string') is not None:
        content = __split_string(os.environ.get('mock_string'))
        content[2] = content[2] + "! "
    else:
        content[0] = 'hello'
        if res_type in [1, 2]:
            content[1] = ' openai'
        else:
            content[1] = ' ollama'
        content[2] = '! '

    if res_type == 1:
        one_completion = f'data: {{ "id": "chatcmpl-1111", "object": "text.completion.chunk", "created": {my_time}, "model": "{model}", "system_fingerprint": "fp_openai", "choices": [{{ "index": 0, "text": "%s", "finish_reason": null }}]}}\n\n',
    elif res_type == 2:
        one_completion = f'data: {{ "id": "chatcmpl-1111", "object": "chat.completion.chunk", "created": {my_time}, "model": "{model}", "system_fingerprint": "fp_openai","choices": [{{"index": 0, "delta": {{"role": "assistant", "content": "%s" }}, "finish_reason": null }}]}}\n\n'
    elif res_type == 4:
        one_completion = f'{{ "model": "{model}", "created_at": "{formatted_time}", "response": "%s", "done": false }}\n'
    elif res_type == 5:
        one_completion = f'{{ "model": "{model}", "created_at": "{formatted_time}", "message": {{ "role": "assistant", "content": "%s", "images": null }}, "done": false }}\n'
    # 在一个循环中发送数据
    completion = []
    if os.environ.get("single_word") == "True":
        word = content[0] + content[1] + content[2]
        for char in word:
            completion.append(one_completion % char)
    else:
        completion = [
            one_completion % content[0],
            one_completion % content[1],
            one_completion % content[2]
        ]
    ts = float(os.environ["looptime"])
    for _ in range(int(os.environ.get("mock_count"))):
        # 遍历 completion 列表
        for chunk in completion:
            await my_printBody(chunk)
            write_httplog(LogType.REC, chunk, num)
            await asyncio.sleep(ts)  # 模拟一个长时间运行的过程

    await my_printBody('', True)


def __split_string(s):
    total_length = len(s)

    # 根据比例（2:5:3）计算各部分的长度
    if total_length == 0:
        return ["", "", ""]  # 返回三个空字符串
    elif total_length == 1:
        return [s, "", ""]  # 只返回第一个部分，其余为空
    elif total_length == 2:
        return [s[:1], s[1:], ""]  # 前1个字符和后1个字符
    elif total_length == 3:
        return [s[:1], s[1:2], s[2:]]  # 每个部分各取1个字符

    # 计算各部分的长度比例
    part1_length = total_length * 2 // 10
    part2_length = total_length * 5 // 10
    part3_length = total_length * 3 // 10

    # 在总长度减去前两部分长度后，给予第三部分所需的剩余部分
    part1_length = min(part1_length, total_length)  # 防止超出长度
    part2_length = min(part2_length, total_length - part1_length)  # 防止超出剩余长度
    part3_length = total_length - part1_length - part2_length  # 剩余部分

    # 切分字符串
    part1 = s[:part1_length]
    part2 = s[part1_length:part1_length + part2_length]
    part3 = s[part1_length + part2_length:total_length]

    return [part1, part2, part3]
