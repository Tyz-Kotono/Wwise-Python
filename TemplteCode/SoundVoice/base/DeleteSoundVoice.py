import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
TARGET_TYPE = "Sound"


def CheckAudioSourceLanguageById(Clinet,  Id):
    result = Clinet.call("ak.wwise.core.object.get", {
        "from": {"id": [Id]},
        "transform": [
            {"select": ["children"]},
            # {"where": ["audioSourceLanguage.name:is", "zh_CN"]}
        ],
        "options": {
            "return": ["id", "name", "audioSourceLanguage"]
        }
    })
    return result


def CheckAudioSourceLanguageByPath(Clinet, path):
    result = Clinet.call("ak.wwise.core.object.get", {
        "from": {"path": [path]},
        "transform": [
            {"select": ["children"]},
            # {"where": ["audioSourceLanguage.name:is", "zh_CN"]}
        ],
        "options": {
            "return": ["id", "name", 'path', "audioSourceLanguage"]
        }
    })
    return result


def deleteWwiseObject(client, Id):
    result = client.call("ak.wwise.core.object.delete", {
        "object":  Id,
    })
    return result


def RemoveLanguageSoundVoice(client, Id, language):
    result = CheckAudioSourceLanguageByPath(client, Id)
    for wavInfo in result['return']:
        if wavInfo['audioSourceLanguage']['name'] == language:
            deleteWwiseObject(client, wavInfo['id'])


if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:

            selected = client.call("ak.wwise.ui.getSelectedObjects", options={
                "return": ['id', "type", "name", 'path']})

            pprint(selected)
            sound_obj = selected["objects"][0]

            sound_id = sound_obj["id"]

            result = CheckAudioSourceLanguageByPath(
                client, selected["objects"][0]['path'])
            for wavInfo in result['return']:
                if wavInfo['audioSourceLanguage']['name'] == 'zh_CN':
                    pprint(wavInfo)
                    # deleteWwiseObject(client, wavInfo['id'])
                    deleteWwiseObject(client, wavInfo['path'])

            # pprint(result)
    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
