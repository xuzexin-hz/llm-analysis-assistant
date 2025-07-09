import asyncio
import glob
import json
import logging
import os
import re
from datetime import datetime
from enum import Enum

from llm_analysis_assistant.utils.environ_utils import get_base_path, my_printBodyWS

base_path = get_base_path()
LOG_END_SYMBOL = '----------end----------'


class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Define the regex pattern to extract log components
        pattern = r'(?P<ip>[^ ]+) - "(?P<method>[^ ]+) (?P<path>[^ ]+) (?P<protocol>[^"]+)" (?P<status>\d+)'
        match = re.match(pattern, record.getMessage())

        # If the log message matches the expected format, extract the components
        if match:
            log_data = {
                'ip': match.group('ip'),
                'method': match.group('method'),
                'path': match.group('path'),
                'protocol': match.group('protocol'),
                'status': match.group('status')
            }
            record.message_json = log_data
        else:
            # 防止初始化时候没有ip格式日志出错
            record.message_json = {}
        return super().format(record)


class LogType(Enum):
    GET = 1  # 请求url
    POST = 1  # 请求url
    REQ = 2  # post请求参数
    RES = 3  # 返回参数
    REC = 4  # 流式输出
    REM = 5  # 流式输出结果
    END = 6  # 输出结束
    SSEQ = 7  # SSE请求
    SSES = 8  # SSE返回

    def __str__(self):
        return self.name.lower()


def get_folder_path():
    num = 0
    num_path = f"{base_path}/config/num"
    day = datetime.now().strftime("%Y-%m-%d")
    folder_path = f"{base_path}/logs/{day}"
    if not os.path.exists(folder_path):
        # 如果不存在，创建文件夹
        os.makedirs(folder_path)
        with open(f"{num_path}", "w") as file:
            file.write(f"{num}")
    return folder_path


def app_init():
    num = 0
    folder_path = get_folder_path()
    num_path = f"{base_path}/config/num"
    if not os.path.exists(num_path):
        with open(f"{num_path}", "w") as file:
            file.write(f"{num}")


def is_first_open():
    config_path = f"{base_path}/config/first_open"
    if not os.path.exists(config_path):
        with open(f"{config_path}", "w") as file:
            file.write(f"{datetime.now().ctime()}")
        return False
    creation_time = os.path.getmtime(config_path)
    creation_date = datetime.fromtimestamp(creation_time).date()
    today_date = datetime.today().date()
    if creation_date == today_date:
        return True
    with open(f"{config_path}", "w") as file:
        file.write(f"{creation_time}")
    return False


def get_num():
    num_path = f"{base_path}/config/num"
    with open(num_path, 'r') as file:
        # 使用 strip() 去掉可能的换行符和空格
        line = file.readline().strip()
        # 将读取的内容转化为数字
        num = int(line) + 1
    with open(f"{num_path}", "w") as file:
        file.write(f"{num}")
    return num


def write_httplog(enum: LogType, msg, num):
    folder_path = get_folder_path()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    if enum != LogType.END:
        log = {
            'asctime': start_time,
            'level': 'INFO',
            'type': str(enum),
            'data': {'data': msg},
        }
        msg = json.dumps(log)
    with open(f"{folder_path}/{num}.log", "a") as file:
        file.write(f"\n{msg}\n")


async def logs_stream_show(latest_time: float = 0):
    def get_logs_file(latest_time_input):
        folder_path = get_folder_path()
        log_files = glob.glob(os.path.join(folder_path, '*.log'))
        if latest_time_input is None:
            log_files_with_times = [(log_file, os.path.getctime(log_file)) for log_file in log_files]
        else:
            # 过滤出创建时间大于 latest_time_input 的文件
            log_files_with_times = [
                (log_file, os.path.getctime(log_file))
                for log_file in log_files
                if os.path.getctime(log_file) > latest_time_input
            ]
        sorted_log_files = sorted(log_files_with_times, key=lambda x: x[1])
        if len(sorted_log_files) > 0:
            latest_time_out = max(log_files_with_times, key=lambda x: x[1])[1]
            return [log_file[0] for log_file in sorted_log_files], latest_time_out
        else:
            return None, latest_time

    def is_valid_json(string):
        try:
            return json.loads(string)
        except ValueError:
            return False

    async def scroll_one_file(log_file, file_end, line_num):
        with open(log_file, 'r') as onefile:
            line_num_this = 0
            for line in onefile:
                line_num_this = line_num_this + 1
                if line_num_this > line_num:
                    line_num = line_num + 1
                    jj = is_valid_json(line)
                    if jj:
                        jj['line_num'] = line_num;
                        await my_printBodyWS(json.dumps(jj))
                    else:
                        if line == '\n':
                            await my_printBodyWS(line + "<br>")
                        else:
                            await my_printBodyWS(str(line_num) + ': ' + line + "<br>")
                    if line == LOG_END_SYMBOL + '\n':
                        await my_printBodyWS("<br>")
                        file_end = True
                    if ', - data:' not in line and line != '\n':
                        await asyncio.sleep(0.2)
        return file_end, line_num

    async def logs_scroll_show(latest_time_input):
        sorted_log_files, latest_time_this = get_logs_file(latest_time_input)
        if latest_time_this is not None:
            latest_time_input = latest_time_this
            for log_file in sorted_log_files:
                f = {
                    "file": os.path.basename(log_file),
                    'ctime': os.path.getctime(log_file)
                }
                await my_printBodyWS(json.dumps(f))
                await my_printBodyWS("<br>")
                line_num = 0
                file_end = False
                wait_num = 0
                while not file_end:
                    if wait_num > 15:
                        break
                    line_num_old = line_num
                    file_end, line_num = await scroll_one_file(log_file, file_end, line_num)
                    if file_end:
                        break
                    else:
                        # 单个文件未读取完，等待2秒，再继续读取
                        await asyncio.sleep(2)
                        if line_num_old == line_num:
                            wait_num = wait_num + 1
        # 所有文件读完后，等待5秒
        await asyncio.sleep(5)
        await logs_scroll_show(latest_time_input)

    await logs_scroll_show(latest_time)
