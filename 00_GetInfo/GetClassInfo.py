#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from pathlib import Path, PureWindowsPath
import os

WAAPI_URL = "ws://127.0.0.1:8080/waapi"
root_path = ''
originals_path = ''
languages = []

def normalize_path(path_str):
    """将路径转换为安全的正斜杠格式"""
    if not path_str:
        return ""
    
    # 使用 pathlib 处理路径
    try:
        # 如果是 Windows 路径
        if '\\' in path_str or (len(path_str) > 1 and path_str[1] == ':'):
            return str(PureWindowsPath(path_str).as_posix())
        else:
            # 如果是 Unix 风格路径，直接返回
            return path_str
    except Exception:
        # 备用方案：简单的替换
        return path_str.replace('\\', '/')

try:
    # Connecting to Waapi using default URL
    with WaapiClient(WAAPI_URL) as client:
        result = client.call("ak.wwise.core.getProjectInfo")

        # pprint(result)
        # pprint(result['directories'])

        root_path = normalize_path(result['directories']['root'])
        pprint(root_path)
        originals_path = normalize_path(result['directories']['originals'])
        pprint(originals_path)

        for language in result['languages']:
            languages.append(language['name'])

        pprint(languages)
except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")