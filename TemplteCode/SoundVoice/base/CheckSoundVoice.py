import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
TARGET_TYPE = "Sound"


if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:

            selected = client.call("ak.wwise.ui.getSelectedObjects", options={
                "return": ['id', "type", "name", "originalWavFilePath", "childrenCount"]})

            # pprint(selected)
            sound_obj = selected["objects"][0]

            sound_id = sound_obj["id"]

            result = client.call("ak.wwise.core.object.get", {
                "from": {"id": [sound_id]},
                "transform": [
                    {"select": ["descendants"]},
                    # {"where": ["audioSourceLanguage.name:is", "zh_CN"]}
                ],
                "options": {
                    "return": ["id", "name", "audioSourceLanguage"]
                }
            })
            for wavInfo in result['return']:
                if wavInfo['audioSourceLanguage']['name'] == 'zh_CN':
                    pprint(wavInfo)

            # pprint(result)
    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
