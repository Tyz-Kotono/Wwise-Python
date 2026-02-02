from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint


def dfs_collect_children(client, object_id, target_type=None):
    """
    深度优先（DFS）递归遍历 Wwise 子对象
    - object_id: 起始对象 ID
    - target_type: 如果指定，只返回该类型对象；None = 所有子对象
    """
    result = []

    # 1. 获取当前对象的子对象（transform children）
    response = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id", "name", "type", "path", "childrenCount"]}
    })

    children = response.get("return", [])

    # 2. 遍历子对象
    for child in children:
        child_id = child["id"]
        child_type = child["type"]

        # 类型过滤
        if target_type is None or child_type == target_type:
            result.append(child)

        # 如果仍有子对象，则继续递归
        if child.get("childrenCount", 0) > 0:
            sub_children = dfs_collect_children(client, child_id, target_type)
            result.extend(sub_children)

    return result


try:
    with WaapiClient() as client:
        # 获取选中的对象
        result = client.call(
            "ak.wwise.ui.getSelectedObjects",
            options={"return": ['id', "type", "name"]}
        )
        pprint(result["objects"])

        object_id = result["objects"][0]['id']
        pprint("=========== Selected ===========")

        # 递归获取 Sound 类型
        sounds = dfs_collect_children(client, object_id, target_type="Sound")

        pprint("=========== DFS Result (Sound Only) ===========")
        pprint(len(sounds))
        for s in sounds:
            pprint(s)

except CannotConnectToWaapiException:
    print("Could not connect to Waapi")

