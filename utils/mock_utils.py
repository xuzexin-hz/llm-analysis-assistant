import time

from utils.environ_utils import my_printBody
from utils.logs_utils import write_httplog


def create_streamData(num):
    completion = [
        b'data: {"id":"chatcmpl-901","object":"chat.completion.chunk","created":1744963885,"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":"hello"},"finish_reason":null}]}\n\n',
        b'data: {"id":"chatcmpl-901","object":"chat.completion.chunk","created":1744963885,"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":" world"},"finish_reason":null}]}\n\n',
        b'data: {"id":"chatcmpl-901","object":"chat.completion.chunk","created":1744963885,"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":"! "},"finish_reason":null}]}\n\n'

        # b'data: {"id":"chatcmpl-183","object":"chat.completion.chunk","created":1745033859,"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":"hh"},"finish_reason":null}]}\n\n',
        # b'data: {"id":"chatcmpl-183","object":"chat.completion.chunk","created":1745033859,"model":"qwen2.5-coder:1.5b","system_fingerprint":"fp_ollama","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":"stop"}]}\n\n',
        # b'data: [DONE]\n\n'
    ]
    # 在一个循环中发送数据
    for _ in range(3):
        # 遍历 completion 列表
        for chunk in completion:
            my_printBody(chunk.decode('utf-8'))  # 根据需要解码并输出
            write_httplog(chunk, num)
            time.sleep(1)  # 模拟一个长时间运行的过程
