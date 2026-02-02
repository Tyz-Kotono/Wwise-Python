import sys
import os
from pprint import pprint

# ==============================
# 环境设置（必须在所有 import 前执行）
# ==============================
def setup_environment():
    venv_path = r"D:\Code\env313"
    site_packages = os.path.join(venv_path, "Lib", "site-packages")
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)
        return True
    return False

setup_environment()

import soundfile as sf
import loudness
from waapi import WaapiClient


# ==============================
# 响度计算
# ==============================
def check_loudness(file_path):
    name = os.path.basename(file_path)

    try:
        audio, sr = sf.read(file_path, dtype="float32")

        duration_ms = len(audio) / sr * 1000
        min_duration = 400

        if duration_ms < min_duration:
            return f"[警告] {name}: 过短 ({duration_ms:.1f} ms)，无法计算 LUFS"

        lufs = loudness.integrated_loudness(audio, sr)
        return f"{lufs:.2f} LUFS - {name} ({duration_ms:.1f} ms)"

    except Exception as e:
        return f"[错误] {name}: 读取失败 -> {e}"


# ==============================
# 主流程
# ==============================
def main():
    # 解析传入参数
    if len(sys.argv) < 3:
        print("No audio path provided.")
        return

    # sys.argv[2] 是一个包含多个 path 的长字符串
    raw_path_string = sys.argv[2].strip()

    # 按空格分割成多个 wav 文件路径
    wav_paths = raw_path_string.split()

    # 打印调试信息
    pprint(wav_paths)

    # 建立 waapi 连接
    client = WaapiClient()

    def log_to_wwise(msg, severity="Message"):
        """向 Wwise Log 输出消息"""
        client.call("ak.wwise.core.log.addItem", {
            "message": msg,
            "severity": severity,
            "channel": "general"
        })

    # 逐个处理 wav 文件
    for path in wav_paths:
        result = check_loudness(path)
        log_to_wwise(result)
        pprint(result)
    client.disconnect()


if __name__ == "__main__":
    main()
    input("按回车键退出...") # 等待用户输入