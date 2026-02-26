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


if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:

            selected = client.call("ak.wwise.ui.getSelectedObjects", options={
                "return": ['id', "type", "name", "childrenCount", "IsVoice"]})

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
                    'return': ['name', 'id', "path", "type", "originalRelativeFilePath", "audioSourceLanguage"]
                }
                descendants = client.call(
                    "ak.wwise.core.object.get", args, options=options)

                print(f"  下级对象数量: {len(descendants['return'])}")
                pprint(descendants['return'])

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
