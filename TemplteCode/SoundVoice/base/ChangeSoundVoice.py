import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
TARGET_TYPE = "Sound"


def CheckAudioSourceLanguageByPath(Clinet, objectPath):
    result = Clinet.call("ak.wwise.core.object.get", {
        "from": {"path": [objectPath]},
        "transform": [
            {"select": ["children"]}
        ],
        "options": {
            "return": ["id", "name", "audioSourceLanguage"]
        }
    })
    return result


def deleteWwiseObject(client, Id):
    result = client.call("ak.wwise.core.object.delete", {
        "object":  Id,
    })
    return result


def RemoveLanguageSoundVoice(client, path, language):
    result = CheckAudioSourceLanguageByPath(client, path)
    for wavInfo in result['return']:
        if wavInfo['audioSourceLanguage']['name'] == language:
            deleteWwiseObject(client, wavInfo['id'])


def file_import(client, language, file_path, objectPath):
    args_import = {
        "importOperation": "useExisting",
        "imports": [
            {
                'importLanguage': language,
                "audioFile": file_path,
                "objectPath": objectPath
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


def ReplaceSoundVoice(client, language, file_path, objectPath):
    RemoveLanguageSoundVoice(client, objectPath, language)
    file_import(client, language, file_path, objectPath)
