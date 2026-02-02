import sys
import os
from waapi import WaapiClient, CannotConnectToWaapiException
from collections import deque
import soundfile as sf
import subprocess
import re
from datetime import datetime
import traceback

TARGET_TYPE = "Sound"
WAAPI_URL = "ws://127.0.0.1:8080/waapi"

# ============================================================
# 获取 ffmpeg 路径（当前 EXE/脚本同级目录）
# ============================================================
def get_ffmpeg_path():
    """
    获取 ffmpeg 路径：
    打包前：当前 py 同级目录
    打包后：EXE 同级目录
    """
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, "ffmpeg", "ffmpeg.exe")


FFMPEG_PATH = get_ffmpeg_path()

# ============================================================
# 检查 ffmpeg
# ============================================================
if not os.path.exists(FFMPEG_PATH):
    print(f"[ERROR] ffmpeg 不存在: {FFMPEG_PATH}")
    input("按回车键退出...")
    sys.exit(1)
else:
    print(f"[INFO] Using ffmpeg path: {FFMPEG_PATH}")

# ============================================================
# Wwise Log
# ============================================================
def wwise_log(client, text, level="info"):
    color = ""
    severity = "Message"

    if level == "info":
        color = "\033[92m"
        severity = "Message"
    elif level == "warning":
        color = "\033[93m"
        severity = "Warning"
    elif level == "error":
        color = "\033[91m"
        severity = "Error"
    elif level == "fatal":
        color = "\033[95m"
        severity = "Fatal Error"

    print(f"{color}{text}\033[0m")

    try:
        client.call("ak.wwise.core.log.addItem", {
            "severity": severity,
            "message": text
        })
    except Exception:
        pass

# ============================================================
# Loudness 计算
# ============================================================
def momentary_max(file_path: str) -> float | None:
    """使用 ffmpeg 计算 Momentary Max 响度"""
    if not os.path.exists(file_path):
        return None

    cmd = [
        FFMPEG_PATH,
        "-loglevel", "info",
        "-nostats",
        "-i", file_path,
        "-filter_complex", "ebur128",
        "-f", "null",
        "-"
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        values = []
        pattern = re.compile(r"\bM:\s*(-?\d+(?:\.\d+)?)")

        for line in proc.stderr:
            match = pattern.search(line)
            if match:
                values.append(float(match.group(1)))

        proc.wait()
        return max(values) if values else None

    except Exception:
        return None

def check_loudness(file_path):
    if not os.path.exists(file_path):
        return None, f"文件不存在: {file_path}"

    try:
        audio, sr = sf.read(file_path, dtype="float32")
        duration_ms = len(audio) / sr * 1000
    except Exception as e:
        return None, f"读取音频失败: {e}"

    if duration_ms < 400:
        return None, f"音频过短 ({duration_ms:.1f} ms)"

    lufs = momentary_max(file_path)
    if lufs is None:
        return None, "无法计算 Momentary Max 响度 (ffmpeg或文件问题)"

    return lufs, None

# ============================================================
# WAAPI helpers
# ============================================================
def get_selected_objects(client):
    result = client.call("ak.wwise.ui.getSelectedObjects", {
        "options": {
            "return": ["id", "name", "type", "originalWavFilePath", "notes"]
        }
    })
    return result.get("objects", [])

def get_children(client, object_id):
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "transform": [{"select": ["children"]}],
        "options": {
            "return": ["id", "name", "type", "originalWavFilePath", "notes"]
        }
    })
    return result.get("return", [])

def get_object_info(client, object_id):
    result = client.call("ak.wwise.core.object.get", {
        "from": {"id": [object_id]},
        "options": {
            "return": ["id", "name", "type", "originalWavFilePath", "notes"]
        }
    })
    arr = result.get("return", [])
    return arr[0] if arr else None

def set_notes(client, object_id, new_notes):
    client.call("ak.wwise.core.object.set", {
        "object": object_id,
        "notes": new_notes
    })

# ============================================================
# BFS
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
# Main
# ============================================================
if __name__ == "__main__":
    try:
        try:
            with WaapiClient(url=WAAPI_URL) as client:
                selected = get_selected_objects(client)

                if not selected:
                    wwise_log(client, "当前未选择任何 Wwise 对象", "error")
                    input("按回车键退出...")
                    sys.exit(1)

                wav_ids = [obj["id"] for obj in selected]
                total_sounds = []

                for wid in wav_ids:
                    obj = get_object_info(client, wid)
                    if not obj:
                        continue

                    if obj["type"] == TARGET_TYPE:
                        total_sounds.append(obj)
                    else:
                        total_sounds.extend(
                            bfs_collect_objects(client, wid, TARGET_TYPE)
                        )

                wwise_log(client, f"Total Sound found: {len(total_sounds)}")

                for sound in total_sounds:
                    wav_path = sound.get("originalWavFilePath")
                    if not wav_path or not os.path.exists(wav_path):
                        wwise_log(client, f"{sound['name']} 没有原始 WAV 文件或路径无效", "warning")
                        continue

                    lufs, error = check_loudness(wav_path)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if error:
                        note_line = f"[Loudness Check {timestamp}] FAILED: {error}"
                        wwise_log(client, f"{sound['name']} - {error}", "warning")
                    else:
                        note_line = (
                            f"[Loudness Check {timestamp}]\n"
                            f"Momentary Max: {lufs:.2f} LUFS\n"
                            f"Source: {wav_path}\n"
                        )
                        wwise_log(client, f"{sound['name']} Momentary Max: {lufs:.2f} LUFS", "info")

        except CannotConnectToWaapiException:
            print("无法连接 WAAPI")

    except Exception as e:
        print("发生未捕获异常:", e)
        traceback.print_exc()

    finally:
        input("按回车键退出...")
