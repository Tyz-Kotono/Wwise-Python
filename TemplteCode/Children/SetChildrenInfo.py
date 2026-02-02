from waapi import WaapiClient
from pprint import pprint

with WaapiClient() as client:
    selected = client.call("ak.wwise.ui.getSelectedObjects", {})

    sound_obj = selected["objects"][0]

    print(f"选中 Sound：")
    pprint(selected)
    sound_id = sound_obj["id"]

    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [sound_id]},
        "transform": [{"select": ["children"]}],
        "options": {
            "return": ["id", "name", "type", "ChannelConfigOverride"]
        }
    })

    sources = [obj for obj in result["return"] if obj["type"] == "AudioFileSource"]
    # 获取属性信息 - 修正的部分
    if sources:
        source_id = sources[0]["id"]
        result = client.call("ak.wwise.core.object.getPropertyInfo", {
            "object": source_id,
            "property": "ChannelConfigOverride"
        })
        pprint(result)

        result = client.call("ak.wwise.core.object.setProperty", {
            "object":source_id,
            "property": "ChannelConfigOverride",
            "value": 49410
        })