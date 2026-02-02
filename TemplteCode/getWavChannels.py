from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException
import struct
import os

# 声道对应位定义
CHANNEL_MASKS = {
    0: "Front Left",
    1: "Front Right",
    2: "Front Center",
    3: "LFE (Low Frequency)",
    4: "Back Left",
    5: "Back Right",
    6: "Front Left of Center",
    7: "Front Right of Center",
    8: "Back Center",
    9: "Side Left",
    10: "Side Right",
    11: "Top Center",
    12: "Top Front Left",
    13: "Top Front Center",
    14: "Top Front Right",
    15: "Top Back Left",
    16: "Top Back Center",
    17: "Top Back Right",
}

# PCM 默认映射（用于非 WAVEFORMATEXTENSIBLE）
PCM_DEFAULT_MAPPING = {
    1: ["Center"],
    2: ["Front Left", "Front Right"],
    3: ["Front Left", "Front Right", "Front Center"],
    4: ["Front Left", "Front Right", "Back Left", "Back Right"],
    6: ["Front Left", "Front Right", "Front Center", "LFE (Low Frequency)", "Back Left", "Back Right"],
    8: ["Front Left", "Front Right", "Front Center", "LFE (Low Frequency)", "Back Left", "Back Right", "Side Left",
        "Side Right"]
}


def decode_channel_mask(mask: int):
    """返回置位的声道名称列表"""
    channels = [name for bit, name in CHANNEL_MASKS.items() if mask & (1 << bit)]
    return channels if channels else ["Unknown or Mono (no mask info)"]


def read_wav_channel_mask(wav_path: str):
    """读取 WAV 文件声道数和 32 位通道掩码"""
    if not os.path.isfile(wav_path):
        return None, None, None
    with open(wav_path, "rb") as f:
        f.read(12)  # RIFF header
        while True:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                return None, None, None
            chunk_id, chunk_size = struct.unpack('<4sI', chunk_header)
            if chunk_id == b"fmt ":
                fmt_data = f.read(chunk_size)
                break
            else:
                f.read(chunk_size)
        wFormatTag, nChannels = struct.unpack('<HH', fmt_data[:4])
        channel_mask = None
        is_pcm = False
        if wFormatTag == 0xFFFE and len(fmt_data) >= 24:  # WAVE_FORMAT_EXTENSIBLE
            channel_mask = struct.unpack('<I', fmt_data[20:24])[0]
        elif wFormatTag == 1:  # 普通 PCM
            is_pcm = True
        return nChannels, channel_mask, is_pcm


def print_channel_mask(mask: int):
    """可视化显示每个位对应声道状态"""
    binary_str = f"{mask:032b}"
    print(f"二进制表示: {binary_str}")
    for i, bit_val in enumerate(binary_str[::-1]):  # 从低位到高位
        channel_name = CHANNEL_MASKS.get(i, f"Bit {i} (未定义)")
        status = "✅" if bit_val == "1" else "❌"
        print(f"  位{i}: {status} -> {channel_name}")


def get_selected_sound_channels():
    """获取当前 WAAPI 选中对象的实际 WAV 声道信息"""
    try:
        with WaapiClient() as client:
            result = client.call(
                "ak.wwise.ui.getSelectedObjects",
                options={
                    "return": ["id", "name", "originalWavFilePath"]
                }
            )
            objects = result.get("objects", [])
            if not objects:
                print("❌ 当前没有选中 Sound 对象")
                return

            for obj in objects:
                name = obj["name"]
                wav_path = obj.get("originalWavFilePath")
                print("===================================")
                print(f"🎵 {name}")
                print(f"源文件路径: {wav_path}")

                if not wav_path or not os.path.isfile(wav_path):
                    print(f"未找到源文件: {wav_path}")
                    continue

                n_channels, mask, is_pcm = read_wav_channel_mask(wav_path)
                print(f"WAV 声道数: {n_channels}")

                if is_pcm:
                    print("⚠️ 普通 PCM WAV，没有扩展通道掩码，使用默认映射")
                    channels = PCM_DEFAULT_MAPPING.get(n_channels, ["未知映射"])
                    print(f"推测声道列表: {channels}")
                elif mask is not None:
                    print(f"32位通道掩码: {mask:#010x}")
                    channels = decode_channel_mask(mask)
                    print(f"实际声道列表: {channels}")
                    print_channel_mask(mask)
                else:
                    print("⚠️ 未检测到 WAVEFORMATEXTENSIBLE 掩码信息，也不是 PCM？")
                print("===================================\n")

    except CannotConnectToWaapiException:
        print("❌ 无法连接到 Wwise（请确认 Wwise 正在运行且启用了 Authoring API）")


# 执行查询
if __name__ == "__main__":
    get_selected_sound_channels()
