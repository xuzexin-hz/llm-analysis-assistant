import time

from utils.environ_utils import my_printBody
from utils.logs_utils import write_httplog


def create_staticData(num, model, res_type):
    # 生成接口
    if res_type == 1:
        completion = [
            '{ "id" : "chatcmpl-1111", "object" : "text_completion", "created" : ' + str(
                time.time()) + ', "model" : "' + model + '", "system_fingerprint" : "fp_ollama", "choices" : [ { "index" : 0, "text" : "我是一个AI助手，属于llm-logs-analysis。", "finish_reason" : "stop" } ], "usage" : { "prompt_tokens" : 62, "completion_tokens" : 11, "total_tokens" : 73 } }\n\n'
        ]
    # 聊天接口
    elif res_type == 2:
        completion = [
            '{ "id" : "chatcmpl-1111", "object" : "chat.completion", "created" : ' + str(
                time.time()) + ', "model" : "' + model + '", "system_fingerprint" : "fp_ollama", "choices" : [ { "index" : 0, "message" : { "role" : "assistant", "content" : "我是一个AI助手，属于llm-logs-analysis。" }, "finish_reason" : "stop" } ], "usage" : { "prompt_tokens" : 62, "completion_tokens" : 11, "total_tokens" : 73 } }\n\n'
        ]
    # 在一个循环中发送数据
    for _ in range(1):
        # 遍历 completion 列表
        for chunk in completion:
            my_printBody(chunk)
            write_httplog(chunk, num)


def create_staticStream(num, model, res_type):
    if res_type == 1:
        completion = [
            'data: {"id":"chatcmpl-1111","object":"text.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"text":"hello","finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-1111","object":"text.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"text":" world","finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-1111","object":"text.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"text":"! ","finish_reason":null}]}\n\n'
        ]
    elif res_type == 2:
        completion = [
            'data: {"id":"chatcmpl-1111","object":"chat.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":"hello"},"finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-1111","object":"chat.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":" world"},"finish_reason":null}]}\n\n',
            'data: {"id":"chatcmpl-1111","object":"chat.completion.chunk","created":' + str(
                time.time()) + ',"model":"' + model + '","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":"! "},"finish_reason":null}]}\n\n'
        ]
    # 在一个循环中发送数据
    for _ in range(3):
        # 遍历 completion 列表
        for chunk in completion:
            my_printBody(chunk)
            write_httplog(chunk, num)
            time.sleep(1)  # 模拟一个长时间运行的过程
