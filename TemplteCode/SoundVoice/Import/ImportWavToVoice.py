#!/usr/bin/env python3
import shutil
import json
from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException
from pathlib import Path, PureWindowsPath

WAAPI_URL = "ws://127.0.0.1:8080/waapi"

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

# =========================
# 工具函数
# =========================


def normalize_path(path_str: str) -> str:
    """统一路径为正斜杠格式"""
    if not path_str:
        return ""
    try:
        if "\\" in path_str or (len(path_str) > 1 and path_str[1] == ":"):
            return str(PureWindowsPath(path_str).as_posix())
        return path_str
    except Exception:
        return path_str.replace("\\", "/")


# =========================
# 初始化函数
# =========================
def IninData():
    """初始化 Wwise 工程路径与语言信息"""
    global root_path, originals_path, json_path, voice_path
    global languages, languages_path

    try:
        with WaapiClient(WAAPI_URL) as client:
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

    except CannotConnectToWaapiException:
        print("WAAPI 连接失败")
        return False


# =========================
# Voice Source 收集
# =========================
def CollectVoiceSourcePath(input_path: str):
    """
    在输入路径中查找语言目录并记录路径
    """
    global VoiceSource_Paths

    VoiceSource_Paths.clear()
    base_path = Path(normalize_path(input_path))

    if not base_path.exists():
        raise FileNotFoundError(f"路径不存在: {base_path}")

    for lang in languages:
        lang_dir = base_path / lang
        if lang_dir.exists() and lang_dir.is_dir():
            VoiceSource_Paths[lang] = lang_dir

    return VoiceSource_Paths


def RemovePath(Ori: str, target: str) -> Path:
    a = Path(target).resolve()
    b = Path(Ori).resolve()

    return b.relative_to(a)


def CopyVoiceSourceToWwiseVoices():
    wwiseoriginalsVoiceWav_paths.clear()
    for lang, src_root in VoiceSource_Paths.items():
        if lang not in languages_path:
            continue

        dst_root = languages_path[lang]
        dst_root.mkdir(parents=True, exist_ok=True)

        print(f"\n[{lang}]")
        print(f"  Source: {src_root}")
        print(f"  Target: {dst_root}")

        for file in src_root.rglob("*"):
            if not file.is_file():
                continue

            relative_path = file.relative_to(src_root)
            target_file = dst_root / relative_path

            target_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(file, target_file)
            # print(f"Source: {file}")
            # print(f"Ori {target_file}")
            # wavPath = RemovePath(target_file,voice_path)
            wwiseoriginalsVoiceWav_paths.append(target_file)


def WriteWavToJson(wav_paths, json_path: Path):
    """
    将 wav 路径列表写入 json 文件（覆盖）
    """
    json_path.parent.mkdir(parents=True, exist_ok=True)

    data = [str(p.as_posix()) for p in wav_paths]

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"已写入 {len(data)} 条 wav 路径到 {json_path}")


# =========================
# 示例用法
# =========================
if __name__ == "__main__":
    if IninData():
        source_root = input("请输入 Voice Source 根路径: ").strip()
        result = CollectVoiceSourcePath(source_root)

        print("\n收集到的 VoiceSource_Paths:")
        for lang, path in result.items():
            print(f"{lang} -> {path}")

        print("\n开始复制 Voice Source...")
        CopyVoiceSourceToWwiseVoices()

        for wav in wwiseoriginalsVoiceWav_paths:
            print(wav)

        WriteWavToJson(wwiseoriginalsVoiceWav_paths, json_path)
