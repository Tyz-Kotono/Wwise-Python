#!/usr/bin/env python3
from ast import List
import json
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from pathlib import Path, PureWindowsPath
import os

WAAPI_URL = "ws://127.0.0.1:8080/waapi"
WWISE_ROOTHIERARCHY = r"\Actor-Mixer Hierarchy"
# =========================
# 全局数据
# =========================
root_path = None
originals_path = None
json_path = None
voice_path = None
languages = []
languages_path = {}
VoiceSource_Paths = {}
wwiseoriginalsVoiceWav_paths = []
Wavdata = []


def wwise_log(client, text, level="info"):
    color = ""
    severity = "Message"

    if level == "info":
        color = "\033[92m"
        severity = "Message"
    elif level == "warning":
        color = "\033[93m"
        severity = "Warning"
    elif level == "error":
        color = "\033[91m"
        severity = "Error"
    elif level == "fatal":
        color = "\033[95m"
        severity = "Fatal Error"

    print(f"{color}{text}\033[0m")

    try:
        client.call("ak.wwise.core.log.addItem", {
            "severity": severity,
            "message": text
        })
    except Exception:
        pass


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


def get_category_alternative(num, length):
    """根据数字和长度返回对应的分类"""

    if not isinstance(num, int) or not isinstance(length, int):
        return "Invalid input: both must be integers"

    if num == 0:
        return "<Physical Folder>"
    elif num == 1:
        return "<Work Unit>"
    elif 1 <= num <= length - 3:
        return "<ActorMixer>"
    elif num == length - 2:
        return "<Random Container>"
    elif num == length - 1:
        return "<Sound Voice>"

    else:
        return f"Invalid input: number {num} out of range for length {length}"


# =========================
# 初始化函数
# =========================


def IninData(client):
    """初始化 Wwise 工程路径与语言信息"""
    global root_path, originals_path, json_path, voice_path
    global languages, languages_path  # 添加 Wwiseclient 到全局声明

    result = client.call("ak.wwise.core.getProjectInfo")
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

    # 收集语言
    languages = []
    for language in result['languages']:
        key = language['name']

        languages_path[key] = voice_path/key
        languages.append(key)

        print(f"{key} : {voice_path/key}")

    return True


def ReadWavFromJson(json_path: Path):
    """
    从 json 文件读取 wav 路径列表
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 将字符串转换回 Path 对象
        wav_paths = [Path(p) for p in data]
        print(f"从 {json_path} 读取了 {len(wav_paths)} 条 wav 路径")
        return wav_paths

    except FileNotFoundError:
        print(f"文件不存在: {json_path}")
        return []
    except json.JSONDecodeError:
        print(f"JSON 格式错误: {json_path}")
        return []
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []


def RemovePath(Ori: str, target: str) -> Path:
    a = Path(target).resolve()
    b = Path(Ori).resolve()

    return b.relative_to(a)


# 去除Wav前面的 zh ko
def remove_prefix(text: str, prefix: str) -> str:
    """去除字符串前缀（如果存在）"""
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

# 去除Wav前面的 zh ko


def Removelanguages_wavFilter(Ori: str, language: str):
    wavFilter = language.split('_')[0] + "_"
    return remove_prefix(Ori, wavFilter)


def WwiseProjectExplorer(splitPath) -> Path:
    wwise_path = f"{WWISE_ROOTHIERARCHY}\\{'\\'.join(splitPath)}"
    return wwise_path


def build_wwise_object_path(folder_parts):
    path = Path(WWISE_ROOTHIERARCHY)
    for i in range(len(folder_parts)):
        obj_type = get_category_alternative(i, len(folder_parts))
        # print(obj_type)
        path /= obj_type + folder_parts[i]
    # print(path)
    return path


def CheckAudioSourceLanguageByPath(Clinet, objectPath):
    result = Clinet.call("ak.wwise.core.object.get", {
        "from": {"path": [f"{objectPath}"]},
        "transform": [
            {"select": ["children"]}
        ],
        "options": {
            "return": ["id", "path", "type", "name", "audioSourceLanguage"]
        }
    })
    return result


def deleteWwiseObject(client, Id):
    result = client.call("ak.wwise.core.object.delete", {
        "object":  Id,
    })
    return result


def file_import(client, language, file_path, object_Path):
    # print(f"language {language}")
    # print(f"wav {file_path}")
    # print(f"object_path {object_Path}")

    args_import = {
        "importOperation": "useExisting",
        "imports": [
            {
                'importLanguage': f"{language}",
                "audioFile": f"{file_path}",
                "objectPath": f"{object_Path}"
            }
        ]
    }
    opts = {
        "platform": "Windows",
        "return": [
            "path", "id", "name",
        ]
    }

    return client.call("ak.wwise.core.audio.import", args_import, options=opts)


def WwiseCheckOrCreate(client, wavPath, parts):
    # print(parts)
    language = parts[0]
    wavFile = parts[len(parts) - 1]
    soundVoice = os.path.splitext(wavFile)[0]
    # 去掉语言 ko 等影响
    soundVoice = Removelanguages_wavFilter(soundVoice, language)
    # print(f"language {language}")
    # print(f"wavFile {wavFile}")
    # print(f"soundVoice {soundVoice}")
    # print(f"wav {wavPath}")

    folder_parts = parts[1:-1]
    folder_pathStr = list(folder_parts)
    # 直接只想wav,但是去掉wav尾缀
    folder_pathStr.append(soundVoice)
    folder_path = Path(*folder_pathStr)
    # print(f"folder_pathStr {folder_pathStr}")
    # print(f'folder_parts {folder_parts}')
    # folder_path = WWISE_ROOTHIERARCHY / folder_path
    # print(f'folder_path {folder_path}')

    # 构建创建的目录
    object_path = build_wwise_object_path(folder_pathStr)

    # print(f"lang {language}")

    # print(f"object_path {object_path}")
    check_Path = WWISE_ROOTHIERARCHY / folder_path

    # 直接指向wav 为Sound Voice,但是去掉wav尾缀
    print(f"Check {check_Path}")

    result = CheckAudioSourceLanguageByPath(client, check_Path)
    # pprint(result)
    if (result != None):
        for audioSounrce in result['return']:
            audioSourceLanguage = audioSounrce['audioSourceLanguage']
            if (audioSourceLanguage):
                if audioSourceLanguage['name'] == language:
                    deleteResult = deleteWwiseObject(
                        client, audioSounrce['id'])
                    print(f"删除：{language}  {deleteResult}")
    else:
        print(f"不存在直接创建")
    wwise_log(
        client, f"语言：{language}   Sound Voice：{soundVoice}         资产: {wavFile} ", "warning")
    wwise_log(
        client, f"WwiseRoot:{object_path} ", "info")
    wwise_log(
        client, f"wavPath:{wavPath} ", "info")
    file_import(client, language, wavPath, object_path)


# =========================
# 示例用法
# =========================
if __name__ == "__main__":

    try:
        with WaapiClient(WAAPI_URL) as client:
            if IninData(client):
                print(json_path)
                Wavdata = ReadWavFromJson(json_path)
                for wav in Wavdata:
                    wwisePath = Path(RemovePath(wav, voice_path))
                    parts = wwisePath.parts
                    WwiseCheckOrCreate(client, wav, parts)

    except CannotConnectToWaapiException:
        print("WAAPI 连接失败")
