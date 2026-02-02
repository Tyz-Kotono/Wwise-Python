from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from collections import deque

TARGET_TYPE = "Sound"  # 你想筛选的类型，可自行修改


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


try:
    with WaapiClient() as client:
        # 获取当前选中的对象
        result = client.call(
            "ak.wwise.ui.getSelectedObjects",
            options={"return": ['id', "type", "name"]}
        )

        root_object = result["objects"][0]
        root_id = root_object["id"]
        pprint("=========== Selected ===========")
        pprint(len(result["objects"]))

        print("=========== BFS Result ===========")
        bfs_result = []
        for obj in  result["objects"]:
            bfs_result.append(bfs_collect_objects(client, obj["id"], TARGET_TYPE))

        pprint(f"Total {TARGET_TYPE}: {len(bfs_result)}")
        pprint(bfs_result)


except CannotConnectToWaapiException:
    print("Could not connect to Waapi")
