from waapi import WaapiClient
from pprint import pprint

with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:

    selected = client.call("ak.wwise.ui.getSelectedObjects", options={
        "return": ['id', "type", "name", "originalWavFilePath", "childrenCount"]
    })

    # 检查是否有选中对象
    if not selected.get("objects"):
        print("没有选中任何对象")
        exit()

    sound_obj = selected["objects"][0]
    sound_id = sound_obj["id"]

    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [sound_id]},
        "transform": [
            {"select": ["descendants"]},
            {"where": ["type:isIn", ["Sound"]]}  # 修正语法
        ],
        "options": {
            "return": ["id", "name", "type", "ChannelConfigOverride"]
        }
    })
    pprint(result)
    print(len(result['return']))
