import os

is_mock = False


def get_envs():
    global is_mock
    is_mock = False


def get_base_path():
    return os.path.abspath(__file__) + "//..//../"
