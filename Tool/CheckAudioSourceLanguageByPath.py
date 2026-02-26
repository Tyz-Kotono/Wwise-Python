import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
TARGET_TYPE = "Sound"


def deleteWwiseObject(client, Id):
    result = client.call("ak.wwise.core.object.delete", {
        "object":  Id,
    })
    return result


def file_import(client, language, file_path, object_Path):
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


if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:
            language = 'zh_CN'
            language = 'ko_KR'
            wwise_path = r'\Actor-Mixer Hierarchy\<Physical Folder>Voice_Player\<Work Unit>1005\<ActorMixer>100502\<ActorMixer>FAtk\<Random Container>zh_Montage_100501_FAtk03\<Sound Voice>Montage_100501_FAtk03_03'
            file_path = r'D:\nami\b0.6.5\Resource\Wwise\Nami_SoundProject_24.1\Originals\Voices\zh_CN\Voice_Player\1005\100502\FAtk\zh_Montage_100501_FAtk03\zh_Montage_100501_FAtk03_03.wav'
            object_Path = r'\Actor-Mixer Hierarchy\Voice_Player\1005\100502\FAtk\zh_Montage_100501_FAtk03\Montage_100501_FAtk03_03'
            soundVoice_id = r'{A124E5DA-4255-4D47-AAB7-06E7DB86A18C}'
            # result = file_import(client, language, file_path, object_Path)
            result = file_Set(client, soundVoice_id, language, file_path)
            print(result)
    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
