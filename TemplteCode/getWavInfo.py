from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

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
    # 后续位可根据需要添加
}

def decode_channel_mask(mask: int):
    """返回所有置位的声道名称"""
    channels = [name for bit, name in CHANNEL_MASKS.items() if mask & (1 << bit)]
    return channels if channels else ["Unknown or Mono (no mask info)"]

def mask_to_binary(mask: int, bits=32):
    """将掩码转为指定位数的二进制字符串"""
    return f"{mask:0{bits}b}"

try:
    with WaapiClient() as client:
        result = client.call(
            "ak.wwise.ui.getSelectedObjects",
            options={
                "return": [
                    "id", "type", "name",
                    "originalTotalChannelCount",
                    "originalChannelConfig",
                    "originalChannelMask"
                ]
            }
        )

        for obj in result["objects"]:
            name = obj["name"]
            mask = obj.get("originalChannelMask", 0)
            config = obj.get("originalChannelConfig", "Unknown")

            decoded_channels = decode_channel_mask(mask)
            binary_str = mask_to_binary(mask)

            print(f"🎵 {name}")
            print(f"  配置: {config}")
            print(f"  掩码: {mask:#x}")
            print(f"  32位二进制: {binary_str}")
            print(f"  声道列表: {decoded_channels}")
            print(f"  含有 Center: {'✅' if mask & (1 << 2) else '❌'}")
            print(f"  含有 LFE: {'✅' if mask & (1 << 3) else '❌'}")
            print("  位对应说明:")
            for i, bit_val in enumerate(binary_str[::-1]):  # 从右到左显示每个位
                channel_name = CHANNEL_MASKS.get(i, f"Bit {i} (未定义)")
                print(f"    位{i}: {bit_val} -> {channel_name}")
            print("===================================")

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Wwise（请确认 Wwise 正在运行且启用了 Authoring API）")
