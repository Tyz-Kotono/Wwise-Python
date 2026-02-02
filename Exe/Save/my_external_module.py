import os
import json
import threading
from queue import Queue
from waapi import WaapiClient
from pprint import pprint
OUTPUT_JSON = "CollectedSounds.json"
lock = threading.Lock()

def process_single_id(id_list):
    """
    遍历 Wwise ID，收集所有 Sound 类型，写入 CollectedSounds.json
    """
    collected_sounds = []

    queue = Queue()
    for wid in id_list:
        queue.put(wid)

    # WaapiClient 只在主线程使用
    with WaapiClient() as client:

        def worker():
            while not queue.empty():
                wwise_id = queue.get()
                try:
                    result = client.call("ak.wwise.core.object.get", {
                        "from": {"id": [wwise_id]},
                        "transform": [{"select": ["children"]}],
                        "options": {"return": ["id", "name", "type"]}
                    })

                    for child in result.get("return", []):
                        c_type = child.get("type")
                        c_id = child.get("id")
                        c_name = child.get("name")

                        if c_type == "Sound":
                            with lock:
                                collected_sounds.append({"id": c_id, "name": c_name})
                        elif c_type in ["Folder", "Event", "Actor-Mixer", "SwitchContainer", "StateGroup"]:
                            queue.put(c_id)
                except Exception as e:
                    print(f"[错误] 遍历 {wwise_id} 失败: {e}")
                finally:
                    queue.task_done()

        threads = []
        for _ in range(min(8, len(id_list))):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        queue.join()

    # 先清空 JSON
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            f.write('{"sounds": []}')

    # 写入收集结果
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"sounds": collected_sounds}, f, indent=4, ensure_ascii=False)

    print(f"完成收集，共 {len(collected_sounds)} 个 Sound 写入 {OUTPUT_JSON}")
    return len(collected_sounds)


def channel_C_LFE():
    """
    读取 CollectedSounds.json 并打印所有 Sound ID
    """
    try:
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[错误] 文件 {OUTPUT_JSON} 不存在")
        return
    except json.JSONDecodeError:
        print(f"[错误] 文件 {OUTPUT_JSON} 不是有效 JSON")
        return

    sounds = data.get("sounds", [])
    if not sounds:
        print("没有收集到任何 Sound")
        return

    print(f"共 {len(sounds)} 个 Sound ID：")
    for s in sounds:
        setChannel(s["id"])
        # print(s["id"])

def setChannel(sound_id):
    with WaapiClient() as client:

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
            # pprint(result)


            result = client.call("ak.wwise.core.object.setProperty", {
                "object": source_id,
                "property": "ChannelConfigOverride",
                "value": 49410
            })