from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint


def decode_channel_mask(mask: int):
    CHANNEL_MASKS = {
        0x1: "Front Left",
        0x2: "Front Right",
        0x4: "Front Center",
        0x8: "LFE (Low Frequency)",
        0x10: "Back Left",
        0x20: "Back Right",
        0x40: "Front Left of Center",
        0x80: "Front Right of Center",
        0x100: "Back Center",
        0x200: "Side Left",
        0x400: "Side Right",
        0x800: "Top Center",
        0x1000: "Top Front Left",
        0x2000: "Top Front Center",
        0x4000: "Top Front Right",
        0x8000: "Top Back Left",
        0x10000: "Top Back Center",
        0x20000: "Top Back Right",
    }
    channels = [name for bit, name in CHANNEL_MASKS.items() if mask & bit]
    return channels if channels else ["Unknown or Mono (no mask info)"]


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

            print(f"🎵 {name}")
            print(f"  配置: {config}")
            print(f"  掩码: {mask:#x}")
            print(f"  声道列表: {decoded_channels}")
            print(f"  含有 Center: {'✅' if 0x4 & mask else '❌'}")
            print(f"  含有 LFE: {'✅' if 0x8 & mask else '❌'}")
            print("===================================")

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Wwise（请确认 Wwise 正在运行且启用了 Authoring API）")
