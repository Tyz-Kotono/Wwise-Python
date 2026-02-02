import soundfile as sf
import loudness
import os
import re
import threading
import sys
import traceback
from queue import Queue
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint


# 添加详细的错误处理
def main():
    try:
        print("程序启动...")

        with WaapiClient() as client:
            print("成功连接到 Wwise WAAPI")
            result = client.call(
                "ak.wwise.ui.getSelectedObjects",
                options={"return": ['id', "type", "name"]}
            )
            print("获取到选中的对象:")
            pprint(result["objects"])
            print('========================================')

            for obj in result["objects"]:
                my_id = obj['id']
                sounds = process_single_id(my_id, client)

                for sound in sounds:
                    file_exists, processed_path = check_file_exists(sound['wav_path'])
                    # print(f"检查文件: {sound['name']} -> {processed_path}")
                    if file_exists:
                        check_loudness(processed_path, sound['name'])
                    else:
                        print(f"[错误] 文件不存在: {sound['wav_path']}")

        print("程序执行完成")
        input("按回车键退出...")

    except CannotConnectToWaapiException:
        print("无法连接到 WAAPI: 请确保 Wwise 正在运行且启用了 Wwise Authoring API")
        input("按回车键退出...")
    except Exception as e:
        print(f"程序执行出错: {e}")
        traceback.print_exc()
        input("按回车键退出...")


# 你的其他函数保持不变...
lock = threading.Lock()


def process_single_id(start_id, client):
    """
    从单个Wwise ID开始，收集所有Sound类型对象及其源文件路径
    """
    collected_sounds = []

    queue = Queue()
    queue.put(start_id)

    def worker():
        while not queue.empty():
            wwise_id = queue.get()
            try:
                result = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [wwise_id]},
                    "transform": [{"select": ["children"]}],
                    "options": {"return": ["id", "name", "type", "originalWavFilePath", "childrenCount"]}
                })

                children = result.get("return", [])

                for child in children:
                    c_type = child.get("type")
                    c_id = child.get("id")
                    c_name = child.get("name")
                    wav_path = child.get("originalWavFilePath")
                    children_count = child.get("childrenCount", 0)

                    # 只收集Sound类型的对象
                    if c_type == "Sound":
                        with lock:
                            collected_sounds.append({
                                "id": c_id,
                                "name": c_name,
                                "wav_path": wav_path
                            })
                    # 如果有子对象，继续遍历（排除Sound类型，因为Sound的子对象是AudioFileSource）
                    elif children_count > 0 and c_type != "Sound":
                        queue.put(c_id)

            except Exception as e:
                print(f"[错误] 遍历 {wwise_id} 失败: {e}")
            finally:
                queue.task_done()

    # 创建线程
    threads = []
    for _ in range(min(8, queue.qsize())):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    queue.join()

    print(f"共收集到 {len(collected_sounds)} 个 Sound 对象:")
    # pprint(collected_sounds)

    return collected_sounds


def process_windows_path(file_path):
    """
    处理Windows文件路径，统一格式
    """
    if not file_path:
        return None
    return file_path.replace('\\', '/')


def check_file_exists(file_path):
    """
    检查文件是否存在
    """
    if not file_path:
        return False, "路径为空"

    normalized_path = file_path.replace('\\', '/')

    if os.path.exists(normalized_path):
        return True, normalized_path
    else:
        return False, f"文件不存在: {normalized_path}"


def check_loudness(file_path, name):
    """
    检查音频文件响度，处理短音频文件
    """
    try:
        audio, sr = sf.read(file_path, dtype="float32")

        # 计算音频时长（毫秒）
        duration_ms = len(audio) / sr * 1000
        min_duration = 400  # 最小需要400ms

        if duration_ms < min_duration:
            print(f"[警告] {name}: 音频过短 ({duration_ms:.1f}ms < {min_duration}ms)，无法计算响度")
            return None

        lufs = loudness.integrated_loudness(audio, sr)
        print(f"{lufs:.2f} LUFS - {name} ({duration_ms:.1f}ms)")
        return lufs

    except Exception as e:
        print(f"[错误] 读取音频文件失败 {name}: {e}")
        return None


if __name__ == "__main__":
    main()