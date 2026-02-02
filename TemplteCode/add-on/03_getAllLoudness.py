import sys
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
from collections import deque
import soundfile as sf
import loudness

TARGET_TYPE = "Sound"  # 目标类型

# ============================================================
# Wwise Log 封装：同时输出 CMD + WAAPI Log
# ============================================================
def wwise_log(client, text, level="info"):
    """
    level 可选:
        info    → Message
        warning → Warning
        error   → Error
        fatal   → Fatal Error
    """

    # CMD 颜色
    color = ""
    severity = "Message"

    if level == "info":
        color = "\033[92m"  # green
        severity = "Message"

    elif level == "warning":
        color = "\033[93m"  # yellow
        severity = "Warning"

    elif level == "error":
        color = "\033[91m"  # red
        severity = "Error"

    elif level == "fatal":
        color = "\033[95m"  # magenta
        severity = "Fatal Error"

    # 输出到 CMD
    print(f"{color}{text}\033[0m")

    # 写入 Wwise Log
    try:
        client.call("ak.wwise.core.log.addItem", {
            "severity": severity,
            "message": text
        })
    except Exception as e:
        print(f"\033[91m[ERROR] 写入 Wwise Log 失败: {e}\033[0m")


# ============================================================
# 音频响度判断
# ============================================================
def check_loudness(client, file_path, name):
    try:
        audio, sr = sf.read(file_path, dtype="float32")

        duration_ms = len(audio) / sr * 1000
        min_duration = 400

        if duration_ms < min_duration:
            wwise_log(
                client,
                f"[警告]  {name}: 音频过短 ({duration_ms:.1f}ms < {min_duration}ms)，无法计算响度",
                level="warning"
            )
            return None

        lufs = loudness.integrated_loudness(audio, sr)

        wwise_log(client, f"[正常]  {lufs:.2f} LUFS - {name}", level="info")

        return lufs

    except Exception as e:
        wwise_log(client, f"[错误] 读取音频文件失败 {name}: {e}", level="error")
        return None


# ============================================================
# WAAPI 获取对象
# ============================================================
def get_children(client, object_id):
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {"return": ["id", "name", "type", "originalWavFilePath"]}
    })
    return result.get("return", [])


def get_object_info(client, object_id):
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "options": {"return": ["id", "name", "type", "originalWavFilePath"]}
    })
    arr = result.get("return", [])
    return arr[0] if arr else None


# ============================================================
# BFS 广度优先遍历
# ============================================================
def bfs_collect_objects(client, start_id, target_type):
    queue = deque([start_id])
    collected = []

    while queue:
        current_id = queue.popleft()
        children = get_children(client, current_id)

        for child in children:
            queue.append(child["id"])
            if child["type"] == target_type:
                collected.append(child)

    return collected


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":

    try:
        with WaapiClient() as client:

            raw_string = sys.argv[2].strip()
            wav_ids = raw_string.split()

            print("========== Input Wwise IDs ==========")
            pprint(wav_ids)

            print("=========== BFS Result ===========")
            total_collected = []

            for wid in wav_ids:

                obj = get_object_info(client, wid)
                if not obj:
                    wwise_log(client, f"[警告] 找不到对象 {wid}", level="warning")
                    continue

                # 本身是目标类型
                if obj["type"] == TARGET_TYPE:
                    total_collected.append(obj)
                    continue

                # BFS 子节点
                results = bfs_collect_objects(client, wid, TARGET_TYPE)
                total_collected.extend(results)

            print("\n========== SUMMARY ==========")
            print(f"Total {TARGET_TYPE}: {len(total_collected)}")

            # 检测响度
            for sound in total_collected:
                check_loudness(client, sound['originalWavFilePath'], sound['name'])

            input("按回车键退出...")

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi")
