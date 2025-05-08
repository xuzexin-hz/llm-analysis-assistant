import json
import re
import socket
import ssl
from urllib.parse import urlparse


class http_clientx:
    IS_STREAM = False
    ITER_CHUNK_SIZE = 4096
    # RE_PATTERN = rb'data:\s*(\{.*?\})\s*\n\n'
    # 兼容ollama格式
    RE_PATTERN = rb'(?:data:\s*)?(\{.*?\})\s*\n{1,2}'

    def __init__(self, url):
        self.url = url
        parsed_url = urlparse(url)
        self.hostname = parsed_url.hostname
        self.scheme = parsed_url.scheme
        self.port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        self.path = parsed_url.path if parsed_url.path else '/'
        self.headers = [f'Host: {self.hostname}', 'Connection: close']

    @property
    def text(self):
        if not hasattr(self, "_text"):
            content = self.content
            if not content:
                self._text = ""
            else:
                self._text = content
        return self._text

    def json(self):
        if not hasattr(self, "_json"):
            try:
                json_str = self.text
                json_data = json.loads(json_str)  # 解析JSON
                self._json = json_data
            except json.JSONDecodeError:
                print("JSON解析失败，返回的内容不合法。")
        return self._json

    def http_get(self, headers=None):
        # 创建 HTTP 请求行
        request_line = f'GET {self.path} HTTP/1.1\r\n'
        return self.__private_method(headers, request_line, "\r\n\r\n")

    def http_post(self, headers=None, data=None):
        # 创建 HTTP 请求行
        request_line = f'POST {self.path} HTTP/1.1\r\n'
        json_data = json.dumps(data)
        data_line = f"\r\nContent-Length: {len(json_data)}\r\n" \
                    f"\r\n" \
                    f"{json_data}"
        stream = False
        if 'stream' in data:
            stream = data['stream']
        if stream:
            return self.__private_method_stream(headers, request_line, data_line)
        return self.__private_method(headers, request_line, data_line)

    def __private_method_stream(self, headers, request_line, data_line):
        # 构建请求头
        custom_headers = self.headers
        # 添加自定义头
        if headers:
            for key, value in headers.items():
                custom_headers.append(f'{key}: {value}')
        # 把所有头信息连接成一个字符串
        headers_string = '\r\n'.join(custom_headers)
        # 创建一个 TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if self.scheme == 'https':
                # 使用 SSL 包装 socket
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.hostname)
            # 连接到服务器
            sock.connect((self.hostname, self.port))
            headers_line = request_line.encode('utf-8') + headers_string.encode('utf-8') + data_line.encode(
                'utf-8')
            # 发送header
            sock.sendall(headers_line)
            res_data = b''
            # 接收响应
            while True:
                data = sock.recv(self.ITER_CHUNK_SIZE)
                if not data:
                    break
                res_data = self.__stream(res_data + data)
                # 使用re.search来查找匹配项
                matches = re.findall(self.RE_PATTERN, res_data, re.DOTALL)
                if matches:
                    for match in matches:
                        res_data = re.sub(self.RE_PATTERN, b'', res_data, count=1)
                        yield match
                if b'data: [DONE]' in res_data:
                    res_data = b''
                    # yield b'data: [DONE]'

    def __stream(self, data):
        if not hasattr(self, "response_headers"):
            # 找到正文部分的开始位置
            res_headers, body = data.split(b'\r\n\r\n', 1)
            self.response_headers = res_headers.decode()
        else:
            body = data
        # 处理分块响应
        if b'Transfer-Encoding: chunked' in data or self.IS_STREAM:
            self.IS_STREAM = True
            # 解析分块
            chunks = []
            while body:
                if b'data: [DONE]' in body:
                    chunks.append(b'data: [DONE]')
                    break
                # 找到下一个分块长度
                length_pos = body.find(b'\r\n')
                if length_pos == -1:
                    break
                # 获取块长度并解析为整数
                chunk_length_hex = body[:length_pos]
                chunk_length = int(chunk_length_hex, 16)  # 转换为十进制
                if chunk_length == 0:
                    break  # 0 表示结束
                # 读取分块
                chunk = body[length_pos + 2:length_pos + 2 + chunk_length]  # +2 是为了 skip '\r\n'
                # 使用re.search来查找匹配项
                matches = re.findall(self.RE_PATTERN, chunk, re.DOTALL)
                if (len(matches) == 0):
                    chunk = chunk_length_hex + b'\r\n' + chunk
                chunks.append(chunk)
                # 更新 body，去掉已处理的分块和换行符
                body = body[length_pos + 2 + chunk_length + 2:]
            # 将所有分块合为最终响应
            response_body = b''.join(chunks)
            return response_body
        else:
            # 如果不是分块编码，直接打印响应
            return body.decode()

    def __private_method(self, headers, request_line, data_line):
        # 构建请求头
        custom_headers = self.headers
        # 添加自定义头
        if headers:
            for key, value in headers.items():
                custom_headers.append(f'{key}: {value}')
        # 把所有头信息连接成一个字符串
        headers_string = '\r\n'.join(custom_headers)
        # 创建一个 TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if self.scheme == 'https':  # HTTPS连接
                # 使用 SSL 包装 socket
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=self.hostname)
            # 连接到服务器
            sock.connect((self.hostname, self.port))
            headers_line = request_line.encode('utf-8') + headers_string.encode('utf-8') + data_line.encode(
                'utf-8')
            # 发送header
            sock.sendall(headers_line)
            # 接收响应
            response = b""
            while True:
                data = sock.recv(self.ITER_CHUNK_SIZE)
                if not data:
                    break
                response += data
        # 找到正文部分的开始位置
        res_headers, body = response.split(b'\r\n\r\n', 1)
        # 处理分块响应
        if b'Transfer-Encoding: chunked' in response:
            # 解析分块
            chunks = []
            while body:
                # 找到下一个分块长度
                length_pos = body.find(b'\r\n')
                if length_pos == -1:
                    break
                # 获取块长度并解析为整数
                chunk_length_hex = body[:length_pos]
                chunk_length = int(chunk_length_hex, 16)  # 转换为十进制
                if chunk_length == 0:
                    break  # 0 表示结束
                # 读取分块
                chunk = body[length_pos + 2:length_pos + 2 + chunk_length]  # +2 是为了 skip '\r\n'
                chunks.append(chunk)
                # 更新 body，去掉已处理的分块和换行符
                body = body[length_pos + 2 + chunk_length + 2:]
            # 将所有分块合为最终响应
            response_body = b''.join(chunks)
            self.content = response_body.decode()
        else:
            # 如果不是分块编码，直接打印响应
            self.content = body.decode()
        self.response_headers = res_headers.decode()
        return self
