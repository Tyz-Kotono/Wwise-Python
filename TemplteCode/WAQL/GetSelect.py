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
                "return": ['id', "type", "name", "childrenCount", "IsVoice"]})

            pprint(selected)
            for obj in selected["objects"]:
                guid = obj["id"]
                print(f"选中: {obj['name']} ({guid})")

                # 2. 查询所有后代
                waql = f'$ "{guid}" select descendants , this'
                descendants = client.call("ak.wwise.core.object.get",
                                          {"waql": waql},
                                          {"return": ["id", "name", "type"]})

                print(f"  下级对象数量: {len(descendants['return'])}")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
