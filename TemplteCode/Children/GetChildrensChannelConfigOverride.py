from waapi import WaapiClient
from pprint import pprint

with WaapiClient() as client:
    # 获取当前选中的 Sound
    selected = client.call("ak.wwise.ui.getSelectedObjects", {})

    if not selected["objects"]:
        print("没有选中任何对象。")
    else:
        sound_obj = selected["objects"][0]
        sound_id = sound_obj["id"]
        sound_name = sound_obj["name"]

        print(f"选中 Sound:{sound_name} ({sound_id})")

        # 获取子对象(AudioFileSource)
        result = client.call("ak.wwise.core.object.get", {
            "from": {"id": [sound_id]},
            "transform": [{"select": ["children"]}],
            "options": {"return": ["id", "name", "type", "ChannelConfigOverride"]}
        })

        # 筛选出 AudioFileSource
        sources = [obj for obj in result["return"] if obj["type"] == "AudioFileSource"]
        pprint(sources)

        # 获取属性信息 - 修正的部分
        if sources:
            source_id = sources[0]["id"]
            result = client.call("ak.wwise.core.object.getPropertyInfo", {
                "object": source_id,
                "property": "ChannelConfigOverride"
            })
            pprint(result)

            pprint('****************************************')
            pprint('****************************************')
            result = client.call("ak.wwise.core.object.setProperty", {
                "object":source_id,
                "property": "ChannelConfigOverride",
                "value": 49410
            })