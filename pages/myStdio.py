import asyncio
import json
import os
import re
import shlex
import subprocess

from utils.logs_utils import write_httplog, LogType


async def myStdio_msg(command, receive_message, send, num):
    write_httplog(LogType.SSEQ, command + '\n\n', num)
    # 1. Create a subprocess to run the server
    commands = []
    # 会匹配以引号包围的路径或者不带引号的路径
    match = re.match(r'("(.*?)"|([^"\s]+))', command)
    if match:
        # 如果路径被引号包围，使用 group(2)，否则使用 group(3)
        first_path = match.group(2) if match.group(2) else match.group(3)
        commands.append(first_path)
        # 获取剩余的部分
        commands.append(command[match.end():].strip())

    executable_path = None
    if not os.path.exists(commands[0].strip("'\"")):
        result = subprocess.run(['where', commands[0].replace('"', '').replace("'", "")], capture_output=True, text=True, check=True)
        # 获取输出结果
        executable_paths = result.stdout.splitlines()
        if commands[0].lower() == 'python':
            if len(executable_paths) > 1:
                executable_paths.pop(0)
                for path in executable_paths:
                    if path.lower().endswith('.cmd') or path.lower().endswith('.exe'):
                        executable_path = path
                        break
            elif len(executable_paths) == 1:
                executable_path = executable_paths[0]
        else:
            if len(executable_paths) > 0:
                for path in executable_paths:
                    if path.lower().endswith('.cmd') or path.lower().endswith('.exe'):
                        executable_path = path
                        break

    env = os.environ
    # 获取参数
    args = parse_string_to_args(command)
    if args is not None:
        for key, value in args.items():
            env[key] = value

    # 去除参数
    commands[1] = remove_args_after(commands[1])

    try:
        new_command = [commands[0]]
        new_command = new_command + shlex.split(commands[1].replace('\\', '\\\\'))
        process = await asyncio.create_subprocess_exec(
            *new_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ,
            executable=executable_path
        )

        stdin = process.stdin
        std_server_task = asyncio.create_task(connect_to_server(process, send, num))
        while True:
            message = await receive_message()
            if message['type'] == 'websocket.receive':
                # stdio input
                text = message.get('text')
                data=json.loads(text)
                if 'url' in data:
                    del data['url']
                stdin.write(json.dumps(data).encode() + b'\n\n')
                write_httplog(LogType.SSEQ, text + '\n\n', num)
                await stdin.drain()
            elif message['type'] == 'websocket.disconnect':
                std_server_task.cancel()
                break
    except Exception as e:
        std_server_task.cancel()


async def connect_to_server(process, send, num):
    stdout_task = asyncio.create_task(read_stream(process.stdout, send, num, 'stdout'))
    stderr_task = asyncio.create_task(read_stream(process.stderr, send), num, 'stderr')

    # 等待进程结束和输出读取完毕
    return_code = await process.wait()
    await send({
        "type": "websocket.send",
        'text': f"Process exited with code: {return_code}"
    })
    write_httplog(LogType.SSES, f"Process exited with code: {return_code}" + '\n\n', num)
    await asyncio.sleep(0)

    stdout_task.cancel()  # 取消 stdout 任务
    stderr_task.cancel()  # 取消 stderr 任务

    try:
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)  # 等待任务完成或取消，捕获异常
    except asyncio.CancelledError as ee:
        print("Stdout/Stderr tasks were cancelled.")


async def read_stream(reader, send, num, prefix=""):
    # Main loop to receive and process messages
    while True:
        try:
            line = await reader.readline()
            if not line:
                await asyncio.sleep(0.35)
                continue
            line_str = line.decode().strip()
            json.loads(line_str)
            # stdio out
            await send({
                "type": "websocket.send",
                'text': line_str
            })
            write_httplog(LogType.SSES, line_str + '\n\n', num)
        except Exception as e:
            # stdio out
            text = json.dumps({"logger": "info", "msg": line_str})
            await send({
                "type": "websocket.send",
                'text': text
            })
            write_httplog(LogType.SSES, text + '\n\n', num)
        await asyncio.sleep(0)


def remove_args_after(argument_string):
    # 查找 '--' 的位置
    index = argument_string.find('--')
    if index != -1:
        # 如果找到了 '--'，则返回截取 '--' 之前的部分
        return argument_string[:index].strip()
    return argument_string.strip()


def parse_string_to_args(input_string):
    """
    解析类似 "python --user=xzx" 这样的字符串，提取参数和值。

    Args:
        input_string:  包含参数的字符串。例如 "python --user=xzx"

    Returns:
        一个字典，包含解析出的参数和值。  如果解析失败，返回 None。
    """
    args_dict = {}
    # 使用正则表达式匹配参数和值
    matches = re.findall(r'--(\w+)=([^ ]+)', input_string)  # 匹配 --key=value，并提取 key 和 value
    if not matches:
        return None  # 如果没有找到参数，返回 None

    for match in matches:
        key, value = match
        args_dict[key] = value  # 添加到字典中

    return args_dict
