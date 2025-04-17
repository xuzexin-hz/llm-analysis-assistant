# -*- coding: utf-8 -*-
import codecs
import json
import os
import sys

sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
sys.stdin = codecs.getreader('utf8')(sys.stdin.detach())


def get_request_body():
    if os.environ["CONTENT_LENGTH"] != '':
        return sys.stdin.read(int(os.environ["CONTENT_LENGTH"]))
    else:
        return '{}'


def get_request_json():
    return json.loads(get_request_body())


def get_path():
    return os.environ.get('PATH_INFO')


def get_apikey():
    if os.environ.get('API_KEY') is not None:
        return os.environ.get('API_KEY')
    return 'API_KEY'
