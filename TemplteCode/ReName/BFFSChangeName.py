import re
import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
from pprint import pprint

TARGET_TYPE = "Sound"


# =============================
# 命名规则系统
# =============================

class RenameRule:
    """命名规则基类：对名字做一次处理"""
    def apply(self, name: str) -> str:
        return name


class RegexReplaceRule(RenameRule):
    """使用正则表达式替换名称内容"""
    def __init__(self, pattern: str, replacement: str):
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, name: str) -> str:
        return re.sub(self.pattern, self.replacement, name)


class PrefixRule(RenameRule):
    """给名称添加前缀"""
    def __init__(self, prefix: str, skip_if_exists=True):
        self.prefix = prefix
        self.skip_if_exists = skip_if_exists

    def apply(self, name: str) -> str:
        if self.skip_if_exists and name.startswith(self.prefix):
            return name
        return f"{self.prefix}{name}"


class SuffixRule(RenameRule):
    """给名称添加后缀"""
    def __init__(self, suffix: str, skip_if_exists=True):
        self.suffix = suffix
        self.skip_if_exists = skip_if_exists

    def apply(self, name: str) -> str:
        if self.skip_if_exists and name.endswith(self.suffix):
            return name
        return f"{name}{self.suffix}"


class RenameEngine:
    """按顺序执行多条命名规则"""
    def __init__(self, rules):
        self.rules = rules

    def rename(self, name: str) -> str:
        new_name = name
        for rule in self.rules:
            new_name = rule.apply(new_name)
        return new_name


# =============================
# Wwise 工具函数
# =============================

def wwise_log(client, text, level="info"):
    """同时输出到控制台和 Wwise Log"""
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
    """根据 ID 获取 Wwise 对象基础信息"""
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "options": {"return": ["id", "name", "type", "originalWavFilePath"]}
    })
    arr = result.get("return", [])
    return arr[0] if arr else None


def get_children(client, object_id):
    """获取对象的直接子节点 ID"""
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id"]}
    })
    return result.get("return", [])


def bfs_collect_with_prune(client, start_id, stop_type):
    """BFS 遍历对象树，遇到指定类型后不再向下遍历"""
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


def process_collected_data(client, objects, rename_engine):
    """生成重命名预览（不实际修改 Wwise）"""

    sounds = [o for o in objects if o["type"] == TARGET_TYPE]

    wwise_log(client, f"Collected Objects: {len(objects)}")
    wwise_log(client, f"Collected Sounds: {len(sounds)}")

    print("========== RENAME PREVIEW ==========")

    for sound_obj in sounds:
        old_name = sound_obj["name"]
        new_name = rename_engine.rename(old_name)

        pprint({
            "id": sound_obj["id"],
            "old_name": old_name,
            "new_name": new_name,
        })


# =============================
# 主入口
# =============================

if __name__ == "__main__":
    try:
        with WaapiClient() as client:

            # 命名规则定义（集中管理）
            rename_engine = RenameEngine([
                RegexReplaceRule(r"\s+", "_"),
                RegexReplaceRule(r"_\d+$", ""),
                PrefixRule("SFX_"),
            ])

            selected = client.call("ak.wwise.ui.getSelectedObjects", {})
            sound_objs = selected["objects"]

            input_ids = []

            print("选中对象：")
            pprint(selected)

            print("========== Input IDs ==========")
            for sound_obj in sound_objs:
                input_ids.append(sound_obj["id"])
                pprint(sound_obj["id"])
                pprint(sound_obj["name"])

            all_objects = []
            for obj_id in input_ids:
                objects = bfs_collect_with_prune(client, obj_id, TARGET_TYPE)
                all_objects.extend(objects)

            print("========== SUMMARY ==========")
            process_collected_data(client, all_objects, rename_engine)

            input("按回车键退出...")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
