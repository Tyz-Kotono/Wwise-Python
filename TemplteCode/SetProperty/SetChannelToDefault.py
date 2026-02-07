import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint

TARGET_TYPE = "Sound"
WAAPI_URL = "ws://127.0.0.1:8080/waapi"

def wwise_log(client, text, level="info"):
    """向 CMD 和 Wwise Log 同时输出信息"""
    severity_map = {
        "info": ("Message", "\033[92m"),
        "warning": ("Warning", "\033[93m"),
        "error": ("Error", "\033[91m"),
        "fatal": ("Fatal Error", "\033[95m"),
    }
    severity, color = severity_map.get(level, ("Message", ""))
    print(f"{color}{text}\033[0m")
    try:
        client.call("ak.wwise.core.log.addItem", {
            "severity": severity,
            "message": text
        })
    except Exception:
        pass


def get_object(client, object_id):
    """获取单个 Wwise 对象信息"""
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "options": {"return": ["id", "name", "type", "originalWavFilePath"]}
    })
    arr = result.get("return", [])
    return arr[0] if arr else None


def get_children(client, object_id):
    """获取对象的直接子节点"""
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id"]}
    })
    return result.get("return", [])


def bfs_collect_with_prune(client, start_id, stop_type):
    """BFS 遍历对象树，遇到 stop_type 即停止向下查找"""
    queue = deque([start_id])
    collected = []

    while queue:
        current_id = queue.popleft()
        obj = get_object(client, current_id)
        if not obj:
            continue

        collected.append(obj)

        if obj["type"] == stop_type:
            continue

        for child in get_children(client, current_id):
            queue.append(child["id"])

    return collected



def set_channel_config(client: WaapiClient, guid, channel_config):
    result = client.call("ak.wwise.core.object.setProperty", {
        "object": guid,
        "property": "ChannelConfigOverride",
        "value": channel_config
    })
    return result

def process_collected_data(client, objects):
    """处理收集到的对象数据"""
    sounds = [o for o in objects if o["type"] == TARGET_TYPE]
    pprint(f"{len(sounds)} Sounds")
    for o in sounds:
        result = client.call("ak.wwise.core.object.get", {
            "from": {"id": [o['id']]},
            "transform": [{"select": ["children"]}],
            "options": {
                "return": ["id", "name", "type", "ChannelConfigOverride"]
            }
        })
        source_id = result['return'][0]['id']
        pprint(f"{source_id} - {o['name']}")
        set_channel_config(client, source_id, 0)

if __name__ == "__main__":
    try:
        with WaapiClient(WAAPI_URL) as client:

            selected = client.call("ak.wwise.ui.getSelectedObjects", {})

            sound_objs = selected["objects"]

            input_ids= []
            input_names = []
            print(f"选中 Sound：")
            pprint(selected)

            print("========== Input IDs ==========")
            for sound_obj in sound_objs:
                input_ids.append(sound_obj["id"])
                input_names.append(sound_obj["name"])
                pprint(sound_obj["id"])
                pprint(sound_obj["name"])




            all_objects = []

            for obj_id in input_ids:
                objects = bfs_collect_with_prune(client, obj_id, TARGET_TYPE)
                all_objects.extend(objects)

            print("========== SUMMARY ==========")
            process_collected_data(client, all_objects)

            # input("按回车键退出...")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
