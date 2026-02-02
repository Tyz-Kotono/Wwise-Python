from waapi import WaapiClient
from pprint import pprint

with WaapiClient() as client:

    selected = client.call("ak.wwise.ui.getSelectedObjects", options ={"return": ['id',"type", "name","originalWavFilePath"]})

    sound_obj = selected["objects"][0]

    print(f"选中 Sound：{sound_obj}")
    pprint(selected)
    sound_id = sound_obj["id"]

    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [sound_id]},
        "transform": [{"select": ["children"]}],
        "options": {
            "return": ["id", "name", "type","ChannelConfigOverride"]
        }
    })

    sources = [obj for obj in result["return"] if obj["type"] == "AudioFileSource"]

    pprint(result)
