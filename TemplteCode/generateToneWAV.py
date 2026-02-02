#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
import os

try:
    # 连接到 Wwise Authoring
    with WaapiClient() as client:

        output_path = os.path.abspath("TestTone.wav")

        args = {
            "path": output_path,
            "bitDepth": "int16",
            "sampleRate": 48000,
            "channelConfig": "1.0",
            "waveform": "sine",
            "frequency": 440,
            "sustainTime": 2.0,
            "sustainLevel": 0.0,
            "attackTime": 0.1,
            "releaseTime": 0.2,
        }

        print(f"🎵 生成测试音频: {output_path}")
        result = client.call("ak.wwise.debug.generateToneWAV", args)
        print("✅ 成功生成！")

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Wwise，请确认 Wwise 已开启并启用 Authoring API。")

except Exception as e:
    print(f"⚠️ 生成失败: {e}")
