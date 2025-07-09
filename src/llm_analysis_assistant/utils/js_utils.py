import os

from llm_analysis_assistant.utils.environ_utils import my_printHeader, my_printBody
from llm_analysis_assistant.utils.logs_utils import base_path


async def js_show_page(js_name):
    await my_printHeader({"Content-Type": "text/html;charset=utf-8"})
    with open(f'{base_path}/pages/html/js/{js_name}.js', 'r') as files:
        lines = files.readlines()
    port = os.environ.get("port")
    js = ''.join(lines)
    project_name = os.environ["PROJECT_NAME"]
    project_version = os.environ["PROJECT_VERSION"]
    await my_printBody(
        f"<html><body><script>var project_name='{project_name}';var project_version='{project_version}';var ws_port={port};{js}</script></body></html>",
        True)
