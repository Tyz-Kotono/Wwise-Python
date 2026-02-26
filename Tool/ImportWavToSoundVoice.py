
from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException


#!/usr/bin/env python3

WAAPI_URL = "ws://127.0.0.1:8080/waapi"


def file_import(client, language, file_path, object_Path, object_id=None):
    # print(f"language {language}")
    # print(f"wav {file_path}")
    # print(f"object_path {object_Path}")

    if object_id:
        args_import = {
            "importOperation": "useExisting",
            "imports": [
                {
                    'importLanguage': f"{language}",
                    "audioFile": f"{file_path}",
                    "objectId": object_id
                }
            ]
        }
    else:
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


try:
    # Connecting to Waapi using default URL
    with WaapiClient(WAAPI_URL) as client:
        # 先删除 AudioFileSource
        sound_path = r'\Actor-Mixer Hierarchy\Voice_Player\1005\100502\FAtk\zh_Montage_100501_FAtk03\Montage_100501_FAtk03_03'

        # 获取 AudioFileSource ID
        result = client.call('ak.wwise.core.object.get', {
            'from': {'path': [sound_path]},
            'transform': [{'select': ['children']}],
            'options': {'return': ['id', 'name', 'type']}
        })
        audio_id = result['return'][0]['id']
        print(f'Found AudioFileSource: {audio_id}')

        # 删除
        client.call('ak.wwise.core.object.delete', {'object': audio_id})
        print('Deleted')

        # 重新导入
        language = 'zh_CN'
        file_path = r'D:\nami\b0.6.5\Resource\Wwise\Nami_SoundProject_24.1\Originals\Voices\zh_CN\Voice_Player\1005\100502\FAtk\zh_Montage_100501_FAtk03\Montage_100501_FAtk03_03\zh_Montage_100501_FAtk03_03.wav'
        object_Path = sound_path

        result = file_import(client, language, file_path, object_Path)
        print('Import result:', result)

except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
except Exception as e:
    print(f'Error: {e}')
