from openai import OpenAI

import json
import datetime
import os
import cgi_utils

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1/",
    api_key="api_key"
)
postJson = cgi_utils.get_request_json()
url_path = cgi_utils.get_path()
model = postJson['model']
req_str = json.dumps(postJson)
start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
day = datetime.datetime.now().strftime("%Y-%m-%d")
num = 1
folder_path = f"./logs/{day}"
num_path = f"./config/num"
start = False
if not os.path.exists(folder_path):
    # 如果不存在，创建文件夹
    os.makedirs(folder_path)
    with open(f"{num_path}", "w") as file:
        file.write(f"{num}")
        start = True
if not os.path.exists(num_path):
    with open(f"{num_path}", "w") as file:
        file.write(f"{num}")
        start = True
else:
    if start is False:
        with open(num_path, 'r') as file:
            # 使用 strip() 去掉可能的换行符和空格
            line = file.readline().strip()
            # 将读取的内容转化为数字
            num = int(line) + 1
        with open(f"{num_path}", "w") as file:
            file.write(f"{num}")
with open(f"{folder_path}/{num}.json", "a") as file:
    file.write(f"\n{url_path}\n")
    file.write(f"{start_time}, - {req_str}\n")
obj_key = ''
obj_value = ''
completion = None
msg = ''
# 生成接口
if url_path == '/v1/completions' or url_path == '/api/completions':
    prompt = postJson['prompt']
    obj_key = 'text'
    completion = client.completions.create(
        model=model,
        prompt=prompt
    )
    obj_value = completion.choices[0].text
    msg = obj_value
# 聊天接口
if url_path == '/v1/chat/completions' or url_path == '/api/chat' or url_path == '/chat/completions':
    messages = postJson['messages']
    obj_key = 'message'
    completion = client.chat.completions.create(
        model=model,
        messages=messages
    )
    obj_value = {
        "role": completion.choices[0].message.role,
        "content": completion.choices[0].message.content
    }
    msg = obj_value['content']
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
})
end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(f"{folder_path}/{num}.json", "a") as file:
    file.write(f"\n{end_time}, - {payload}\n")
print(payload)
