#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from pathlib import Path, PureWindowsPath
import subprocess

def open_folder_safely(path):
    """安全地打开文件夹"""
    try:
        # 方法1：使用 explorer 命令
        subprocess.run(['explorer', str(path)], 
                      shell=True, 
                      creationflags=subprocess.CREATE_NO_WINDOW)
        
        # 或方法2：使用 start 命令
        # subprocess.run(['start', '', str(path)], shell=True)
        
    except Exception as e:
        print(f"无法打开文件夹: {e}")
        # 回退到只显示路径
        print(f"请手动打开: {path}")

WAAPI_URL = "ws://127.0.0.1:8080/waapi"
root_path = ''
originals_path = ''
json_path = ''
voice_path = ''
languages = []
languages_path = {}

def normalize_path(path_str):
    """将路径转换为安全的正斜杠格式"""
    if not path_str:
        return ""
    try:
        if '\\' in path_str or (len(path_str) > 1 and path_str[1] == ':'):
            return str(PureWindowsPath(path_str).as_posix())
        else:
            return path_str
    except Exception:
        return path_str.replace('\\', '/')

try:
    with WaapiClient(WAAPI_URL) as client:
        result = client.call("ak.wwise.core.getProjectInfo")

        pprint(result)
        root_str = normalize_path(result['directories']['root'])
        originals_str = normalize_path(result['directories']['originals'])
        
        root_path = Path(root_str)
        originals_path = Path(originals_str)
        json_path = root_path / 'Json' / 'imported_files.json'
        voice_path = originals_path / 'Voices'
        
        print(f"Root: {root_path}")
        print(f"Originals: {originals_path}")
        print(f"JSON path: {json_path}")
        print(f"Voice path: {voice_path}")
        # pprint(result['languages'])
        # 收集语言
        languages = []
        for language in result['languages']:
            key = language['name']
            languages_path[key] = voice_path/key
            languages.append(key)
            print(f"{key} : {voice_path/key}")

        open_folder_safely(result['directories']['commands'])
except CannotConnectToWaapiException:
    print("Connection error")