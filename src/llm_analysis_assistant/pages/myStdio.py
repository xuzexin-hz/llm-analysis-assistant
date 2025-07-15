import asyncio
import json
import os
import queue
import re
import shlex
import subprocess
import sys
import threading

from llm_analysis_assistant.utils.environ_utils import parse_string_to_args, remove_args_after
from llm_analysis_assistant.utils.logs_utils import write_httplog, LogType


async def myStdio_msg(command, receive, send, num):
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
        result = subprocess.run(['where', commands[0].replace('"', '').replace("'", "")], capture_output=True,
                                text=True, check=True)
        # 获取输出结果
        executable_paths = result.stdout.splitlines()
        if commands[0].lower() == 'python':
            # 解决用开发工具运行时候，它默认先选择开发工具中的python
            if len(executable_paths) > 1:
                executable_paths.pop(0)
                executable_path = get_executable_path(executable_path, executable_paths)
            elif len(executable_paths) == 1:
                executable_path = executable_paths[0]
        else:
            if len(executable_paths) > 0:
                executable_path = get_executable_path(executable_path, executable_paths)

    env = os.environ
    # 获取参数
    args = parse_string_to_args(command)
    if args is not None:
        for key, value in args.items():
            env[key] = value

    # 去除参数
    commands[1] = remove_args_after(commands[1])
    new_command = [commands[0]]
    new_command = new_command + shlex.split(commands[1].replace('\\', '\\\\'))
    # web 客户端
    if receive is not None:
        try:
            process = await asyncio.create_subprocess_exec(
                *new_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ,
                executable=executable_path
            )
            stdout_task = asyncio.create_task(read_stream(process.stdout, send, num, 'stdout'))
            stderr_task = asyncio.create_task(read_stream(process.stderr, send, num, 'stderr'))
            receive_task = asyncio.create_task(
                scoket_receive_message(process, receive, num, stdout_task, stderr_task))
            # 等待进程结束和输出读取完毕
            return_code = await process.wait()
            await send({
                "type": "websocket.send",
                'text': f"Process exited with code: {return_code}"
            })
            write_httplog(LogType.SSES, f"Process exited with code: {return_code}" + '\n\n', num)
            await asyncio.sleep(0)
            try:
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)  # 等待任务完成或取消，捕获异常
            except asyncio.CancelledError as ee:
                print("Stdout/Stderr tasks were cancelled.")
            receive_task.cancel()
        except Exception as e:
            receive_task.cancel()
    else:
        process = subprocess.Popen(
            new_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,
            executable=executable_path,
            text=True,
            bufsize=1
        )
        input_queue = queue.Queue()
        # 启动读写线程
        t_reader = threading.Thread(target=reader_thread, args=(process.stdout, print, num), daemon=True)
        t_writer = threading.Thread(target=writer_thread, args=(process.stdin, input_queue, num), daemon=True)
        t_reader.start()
        t_writer.start()
        try:
            loop = asyncio.get_event_loop()
            while True:
                try:
                    message = sys.stdin.readline()
                    line = message.strip()
                    if line.strip().lower() == 'exit':
                        break
                    input_queue.put(line + '\n')
                except queue.Empty:
                    pass
        except Exception as e:
            print(e)
        finally:
            if process.poll() is None:
                process.terminate()


async def scoket_receive_message(process, receive, num, stdout_task, stderr_task):
    while True:
        message = await receive()
        if message['type'] == 'websocket.receive':
            # stdio input
            text = message.get('text')
            data = json.loads(text)
            if 'url' in data:
                del data['url']
            process.stdin.write(json.dumps(data).encode() + b'\n\n')
            write_httplog(LogType.SSEQ, text + '\n\n', num)
            await process.stdin.drain()
        elif message['type'] == 'websocket.disconnect':
            stdout_task.cancel()
            stderr_task.cancel()
            asyncio.current_task().cancel()
            break


async def read_stream(reader, send, num, prefix=""):
    # Main loop to receive and process messages
    while True:
        try:
            line = await reader.readline()
            if not line:
                if reader.at_eof():
                    asyncio.current_task().cancel()
                    break
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


# 读取线程
def reader_thread(stdout, myPrint, num):
    try:
        for line in iter(stdout.readline, ''):
            if line:
                message = line.strip()
                write_httplog(LogType.SSES, message + '\n\n', num)
                myPrint(message, flush=True)
    except Exception as e:
        print(f"[读取异常] {e}")
    finally:
        stdout.close()


# 写入线程
def writer_thread(stdin, input_queue, num):
    try:
        while True:
            message = input_queue.get()
            if message is None:
                break
            write_httplog(LogType.SSEQ, message + '\n\n', num)
            stdin.write(message)
            stdin.flush()
    except Exception as e:
        print(f"[写入异常] {e}")
    finally:
        stdin.close()


def get_executable_path(executable_path, executable_paths):
    for path in executable_paths:
        if path.lower().endswith('.cmd') or path.lower().endswith('.bat') or path.lower().endswith(
                '.exe') or path.lower().endswith('.ps1'):
            executable_path = path
            break
    return executable_path
