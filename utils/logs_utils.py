import os
from datetime import datetime
import glob
import time


def get_folder_path():
    num = 0
    num_path = f"./config/num"
    day = datetime.now().strftime("%Y-%m-%d")
    folder_path = f"./logs/{day}"
    if not os.path.exists(folder_path):
        # 如果不存在，创建文件夹
        os.makedirs(folder_path)
        with open(f"{num_path}", "w") as file:
            file.write(f"{num}")
    return folder_path


def app_init():
    num = 0
    num_path = f"./config/num"
    folder_path = get_folder_path()
    if not os.path.exists(num_path):
        with open(f"{num_path}", "w") as file:
            file.write(f"{num}")


def is_first_open():
    config_path = f"./config/first_open"
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


def write_app_log(msg):
    path = f"./logs"
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(f"{path}/app.log", "a") as file:
        file.write(f"{start_time}, - {msg}")


def get_num():
    num_path = f"./config/num"
    with open(num_path, 'r') as file:
        # 使用 strip() 去掉可能的换行符和空格
        line = file.readline().strip()
        # 将读取的内容转化为数字
        num = int(line) + 1
    with open(f"{num_path}", "w") as file:
        file.write(f"{num}")
    return num


def write_httplog(msg, num):
    folder_path = get_folder_path()
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(f"{folder_path}/{num}.log", "a") as file:
        file.write(f"\n{start_time}, - {msg}\n")


def logs_stream_show():
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
        latest_time_out = None
        if len(sorted_log_files) > 0:
            latest_time_out = max(log_files_with_times, key=lambda x: x[1])[1]
            return [log_file[0] for log_file in sorted_log_files], latest_time_out
        else:
            return None, latest_time

    def scroll_one_file(log_file, file_end, line_num):
        with open(log_file, 'r') as file:
            line_num_this = 0
            for line in file:
                line_num_this = line_num_this + 1
                if line_num_this > line_num:
                    line_num = line_num + 1
                    print(str(line_num) + ': ' + line + "<br>")
                    if line == '----------end----------\n':
                        print("<br>")
                        file_end = True
                    if ', - data:' not in line and line is not '\n':
                        time.sleep(0.2)
        return file_end, line_num

    def logs_scroll_show(latest_time_input):
        sorted_log_files, latest_time_this = get_logs_file(latest_time_input)
        if latest_time_this is not None:
            latest_time_input = latest_time_this
            for log_file in sorted_log_files:
                print(log_file)
                line_num = 0
                file_end = False
                wait_num = 0
                while not file_end:
                    if wait_num > 15:
                        break
                    line_num_old = line_num
                    file_end, line_num = scroll_one_file(log_file, file_end, line_num)
                    if file_end:
                        break
                    else:
                        # 单个文件未读取完，等待2秒，再继续读取
                        time.sleep(2)
                        if line_num_old == line_num:
                            wait_num = wait_num + 1
        # 所有文件读完后，等待5秒
        time.sleep(5)
        logs_scroll_show(latest_time_input)

    js = ''
    with open('./cgi-bin/html/js/logs_scroll_show.js', 'r') as file:
        js = file.readlines()
    print(f"<script>{''.join(js)}</script>")
    latest_time = None
    logs_scroll_show(latest_time)
