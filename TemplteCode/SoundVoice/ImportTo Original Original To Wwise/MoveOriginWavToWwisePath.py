from pathlib import Path, PureWindowsPath
import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint
from pathlib import Path
import shutil
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
TARGET_TYPE = "Sound"
WWISE_Root = r"\Actor-Mixer Hierarchy"
root_path = None
originals_path = None
json_path = None
voice_path = None
languages = []
languages_path = {}
VoiceSource_Paths = {}
wwiseoriginalsVoiceWav_paths = []
Wavdata = []


def RemovePath(Ori: str, target: str) -> Path:
    a = Path(target).resolve()
    b = Path(Ori).resolve()

    return b.relative_to(a)




def move_wav_file(old_path: str, new_path: str, overwrite: bool = False) -> tuple[bool, str]:
    try:
        old_file = Path(old_path)
        new_file = Path(new_path)

        # 源文件不存在 → 跳过
        if not old_file.exists():
            return False, f"Skip: source not found -> {old_file}"

        # 不是 wav → 跳过
        if old_file.suffix.lower() != ".wav":
            return False, f"Skip: not a wav file -> {old_file}"

        # 创建目标目录
        new_file.parent.mkdir(parents=True, exist_ok=True)

        # 处理覆盖
        if new_file.exists():
            if overwrite:
                new_file.unlink()
            else:
                return False, f"Skip: target exists -> {new_file}"

        shutil.move(str(old_file), str(new_file))

        return True, str(new_file)

    except Exception as e:
        return False, f"Error: {e}"
    


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

def get_prefix_until_folder(full_path: str, folder_name: str) -> str:
    """
    将路径按指定文件夹名拆分，只返回包含该文件夹在内的前半段路径
    """
    p = Path(full_path)

    parts = p.parts

    # full_path Voices\zh_CN\Voice_Player\1005\100503\FAtk\zh_Montage_100501_FAtk03\Montage_100501_FAtk03_04.wav
    # folder_name Voice_Player

    # full_path Voices\zh_CN\Voice_Character\101301\FAtk\zh_Montage_101301_FAtk01\zh_Montage_101301_FAtk01_01.wav
    # folder_name Voice_Player
    # print(f'full_path {full_path}')
    # print(f'folder_name {folder_name}')
    if folder_name not in parts:
        raise ValueError(f"Folder '{folder_name}' not found in path")

    index = parts.index(folder_name)

    # +1 是为了包含该文件夹本身
    prefix_parts = parts[:index + 1]

    return str(Path(*prefix_parts))


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

def GenPaths(pathStr,originalPathStr,language):
    # pprint(obj)
    treePath = Path(pathStr)
    # 去掉  'Actor-Mixer Hierarchy'
    treePathStr = RemovePath(treePath, WWISE_Root)
    WavPathC = f"{originals_path}\{originalPathStr}"
    
    # Voices\zh_CN
    originalMiddlePath =  get_prefix_until_folder(originalPathStr,language)

    WavPathN = f"{originals_path}\{originalMiddlePath}\{treePathStr}.wav"

    # print(f'originalMiddlePath {originalMiddlePath}')
    # print(f"treePathStr  {treePathStr }")
    # print(originalPathStr)
    # print(WavPathC)
    # print(WavPathN)

    return  WavPathC ,WavPathN


def deleteWwiseObject(client, object_id):
    result = client.call("ak.wwise.core.object.delete", {
        "object": object_id
    })
    return result





def file_Set(client, sound_id, language, wav_path):
    client.call(
        "ak.wwise.core.object.set",
        {
            "objects": [
                {
                    "object": sound_id,
                    "import": {
                        "files": [
                            {
                                "audioFile": wav_path,
                                "language": language
                            }
                        ]
                    }
                }
            ]
        }
    )

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

if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:

            selected = client.call("ak.wwise.ui.getSelectedObjects", options={
                "return": ['id', "type", "name", "childrenCount", "IsVoice"]})
            IninData(client)
            # pprint(selected)
            for obj in selected["objects"]:
                guid = obj["id"]
                print(f"选中: {obj['name']} ({guid})")

                # 2. 查询所有后代
                args = {
                    # 'waql': '$ from type sound'
                    'waql': f'$ "{guid}" select descendants where (type = "Sound" and IsVoice = true) select children'
                }
                options = {
                    'return': ['name', 'id',"path", "type", 
                               'Parent.id','Parent.type','Parent.name','Parent.path', 
                               "originalRelativeFilePath", "audioSourceLanguage"]
                }
                descendants = client.call(
                    "ak.wwise.core.object.get", args, options=options)

                print(f"  下级对象数量: {len(descendants['return'])}")
                # pprint(descendants['return'])
                for obj in descendants['return']:
                    # pprint(obj)
                    wwise_rootPath =  obj['path']
                    AudioFileSource_id = obj['id']
                    language = obj['audioSourceLanguage']['name']
                    originalRelativeFilePath = obj['originalRelativeFilePath']
                    
                    SoundVoice_id = obj['Parent.id']
                    SoundVoice_Path = obj['Parent.path']
                    currentWavPath, NewWavPath =  GenPaths(SoundVoice_Path,originalRelativeFilePath,language)

                    # print(f"language {language}  Sound Voice id {SoundVoice_id}")
                    # print(f"Wav NewWavPath {NewWavPath} ")
                    move_wav_file(currentWavPath,NewWavPath)
                    deleteWwiseObject(client,AudioFileSource_id)
                    file_Set(client, SoundVoice_id, language, NewWavPath)
                    wwise_log(client, f"{obj['name']}  {language} ", "info")
                    wwise_log(client, f"Path: {NewWavPath} ", "info")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
