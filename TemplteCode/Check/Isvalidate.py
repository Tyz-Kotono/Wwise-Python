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

        validate = client.call("ak.wwise.core.object.validate", {
            "object": sound_id
        })
        pprint(validate)


