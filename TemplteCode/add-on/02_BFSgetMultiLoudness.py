import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from collections import deque

TARGET_TYPE = "Sound"  # 你想筛选的类型，可修改为 "Sound", "ActorMixer", "WorkUnit" 等

def get_children(client, object_id):
    """查询某个对象的直接子对象（非递归）"""
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id", "name", "type"]}
    })

    return result.get("return", [])


def bfs_collect_objects(client, start_id, target_type):
    """广度优先查找所有指定类型的子物体"""
    queue = deque([start_id])
    collected = []

    while queue:
        current_id = queue.popleft()
        children = get_children(client, current_id)

        for child in children:
            # 入队用于继续 BFS
            queue.append(child["id"])

            # 筛选目标类型
            if child["type"] == target_type:
                collected.append(child)

    return collected


if __name__ == "__main__":

    try:
        with WaapiClient() as client:

            # sys.argv[2] 是一个包含多个 ID 的字符串
            raw_string = sys.argv[2].strip()

            # ID 列表
            wav_ids = raw_string.split()

            pprint("========== Input Wwise IDs ==========")
            pprint(wav_ids)

            print("=========== BFS Result ===========")
            total_collected = []

            for wid in wav_ids:
                results = bfs_collect_objects(client, wid, TARGET_TYPE)
                total_collected.extend(results)

            print("\n========== SUMMARY ==========")
            print(f"Total {TARGET_TYPE}: {len(total_collected)}")
            pprint(total_collected)

            input("按回车键退出...")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
