import asyncio
import json
import re
import socket
import ssl
from urllib.parse import urlparse


class http_clientx:
    IS_STREAM = False
    ITER_CHUNK_SIZE = 40960
    # RE_PATTERN = rb'data:\s*(\{.*?\})\s*\n\n'
    # 兼容ollama格式
    RE_PATTERN = rb'(?:data:\s*)?(\{.*?\})\s*\n{1,2}'
    HTTP_TYPE = "HTTP"

    def __init__(self, url):
        self.url = url
        parsed_url = urlparse(url)
        self.hostname = parsed_url.hostname
        self.scheme = parsed_url.scheme
        self.port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        # self.path = parsed_url.path if parsed_url.path else '/'
        hostname = url.split("//")[-1].split("/")[0]  # 获取主机名
        # 兼容post的url中带参数
        self.path = url.split(hostname, 1)[1]
        self.headers = [f'host: {self.hostname}', 'connection: close']

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
                return None
                print("JSON解析失败，返回的内容不合法。")
        return self._json

    @property
    def header(self):
        if not hasattr(self, "_header"):
            header = self.response_headers
            if not header:
                self._header = []
            else:
                headers = {}
                # 将原始字符串按行分割
                lines = header.strip().split('\r\n')
                # 跳过第一行（状态行）
                for line in lines[1:]:
                    # 分割 key 和 value
                    key, value = line.split(': ', 1)
                    headers[key.lower()] = value  # 转换为小写以便统一处理
                self._header = headers
        return self._header

    async def http_get(self, headers=None, stream=False):
        # 创建 HTTP 请求行
        request_line = f'GET {self.path} HTTP/1.1\r\n'
        data_line = "\r\n\r\n"
        if stream:
            return self.__private_method_stream(headers, request_line, data_line)
        return await self.__private_method(headers, request_line, data_line)

    async def http_post(self, headers=None, data=None):
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
        return await self.__private_method(headers, request_line, data_line)

    async def __private_method_stream(self, headers, request_line, data_line):
        # 构建请求头
        custom_headers = self.headers
        # 添加自定义头
        if headers:
            for key, value in headers.items():
                if key.lower() in ['host', 'connection', 'content-length']:
                    continue
                custom_headers.append(f'{key}: {value}')
        # 把所有头信息连接成一个字符串
        headers_string = '\r\n'.join(custom_headers)
        # 创建一个 TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if self.scheme == 'https':
                # 使用 SSL 包装 socket
                try:
                    context = ssl.create_default_context()
                    reader, writer = await asyncio.open_connection(host=self.hostname, port=self.port, ssl=context)
                except Exception as e:
                    pass
            else:
                reader, writer = await asyncio.open_connection(host=self.hostname, port=self.port)
            headers_line = request_line.encode('utf-8') + headers_string.encode('utf-8') + data_line.encode(
                'utf-8')
            # 发送header
            writer.write(headers_line)
            res_data = b''
            # 接收响应
            while True:
                data = await reader.read(self.ITER_CHUNK_SIZE)
                if not data:
                    break
                res_data = self.__stream(res_data + data)
                if self.HTTP_TYPE == "SSE":
                    yield res_data
                    res_data = b''
                    continue
                # 使用re.search来查找匹配项
                matches = re.findall(self.RE_PATTERN, res_data, re.DOTALL)
                if matches:
                    for match in matches:
                        res_data = re.sub(self.RE_PATTERN, b'', res_data, count=1)
                        yield match
                if b'data: [DONE]' in res_data:
                    res_data = b''
                    yield b'[DONE]'

    def __stream(self, data):
        if not hasattr(self, "response_headers"):
            # 找到正文部分的开始位置
            res_headers, body = data.split(b'\r\n\r\n', 1)
            self.response_headers = res_headers.decode()
        else:
            body = data
        # 处理分块响应
        if b'transfer-encoding: chunked' in data.lower() or self.IS_STREAM:
            self.IS_STREAM = True
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
                if self.HTTP_TYPE == "SSE":
                    return chunk
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
            return body

    async def __private_method(self, headers, request_line, data_line):
        # 构建请求头
        custom_headers = self.headers
        # 添加自定义头
        if headers:
            for key, value in headers.items():
                if key.lower() in ['host', 'connection', 'content-length']:
                    continue
                custom_headers.append(f'{key}: {value}')
        # 把所有头信息连接成一个字符串
        headers_string = '\r\n'.join(custom_headers)
        # 创建一个 TCP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if self.scheme == 'https':
                # 使用 SSL 包装 socket
                try:
                    context = ssl.create_default_context()
                    reader, writer = await asyncio.open_connection(host=self.hostname, port=self.port, ssl=context)
                except Exception as e:
                    pass
            else:
                reader, writer = await asyncio.open_connection(host=self.hostname, port=self.port)
            headers_line = request_line.encode('utf-8') + headers_string.encode('utf-8') + data_line.encode(
                'utf-8')
            # 发送header
            writer.write(headers_line)
            # 接收响应
            response = b""
            while True:
                data = await reader.read(self.ITER_CHUNK_SIZE)
                if not data:
                    break
                response += data
        # 找到正文部分的开始位置
        res_headers, body = response.split(b'\r\n\r\n', 1)
        # 处理分块响应
        if b'transfer-encoding: chunked' in response.lower():
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
