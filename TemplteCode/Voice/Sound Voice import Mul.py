import os
from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException


# ================================
# 配置区
# ================================

WAAPI_URL = "ws://127.0.0.1:8080/waapi"

parent_id = "{076D3CA5-38AB-4076-8F36-2C7CF9FB1CAD}"  # 父 Actor-Mixer（ID 或 Path）

json_data = [
    {
        "index": 0,
        "path": "Voice/Character/100901/",
        "name": 100801,
        "dictionary": {
            "ko_KR": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/ko_KR/Voice/Character/100801/VO_100801_Battle_Laugh.wav",
            "ja_JP": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/ja_JP/Voice/Character/100801/VO_100801_Battle_Laugh.wav",
            "zh_CN": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/zh_CN/Voice/Character/100801/VO_100801_Battle_Laugh.wav"
        }
    },
    {
        "index": 1,
        "path": "Voice/Character/101001/",
        "name": 100601,
        "dictionary": {
            "ko_KR": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/ko_KR/Voice/Character/100601/VO_100601_Battle_UAtk.wav",
            "ja_JP": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/ja_JP/Voice/Character/100601/VO_100601_Battle_UAtk.wav",
            "zh_CN": "D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/zh_CN/Voice/Character/100601/VO_100601_Battle_UAtk.wav"
        }
    }
]


# ================================
# 核心函数
# ================================

def create_sound_voice_with_languages(client, parent_id: str, voice_data: dict):
    """
    在 parent_id 下创建 Sound Voice，并一次性导入多语言音频
    """
    lang_dict = voice_data["dictionary"]

    # 1️⃣ Sound Voice 名称（从任意 wav 推导）
    sample_wav = next(iter(lang_dict.values()))
    sound_name = os.path.splitext(os.path.basename(sample_wav))[0]

    # 2️⃣ 组装 import files
    import_files = [
        {
            "audioFile": wav_path,
            "language": language
        }
        for language, wav_path in lang_dict.items()
    ]

    # 3️⃣ object.set + children + import
    result = client.call(
        "ak.wwise.core.object.set",
        {
            "objects": [
                {
                    "object": parent_id,
                    "children": [
                        {
                            "type": "Sound Voice",
                            "name": sound_name,
                            # 如果需要避免重复执行报错，可打开下面一行
                            # "onNameConflict": "replace",
                            "import": {
                                "files": import_files
                            }
                        }
                    ]
                }
            ]
        }
    )

    return result


# ================================
# 主流程
# ================================

def main():
    try:
        with WaapiClient(url=WAAPI_URL) as client:
            print("✅ 成功连接到 Wwise Waapi!")

            for voice_data in json_data:
                result = create_sound_voice_with_languages(
                    client,
                    parent_id,
                    voice_data
                )

                # 调试用（需要可打开）
                pprint(result['objects'][0]['id'])

                sample_wav = next(iter(voice_data["dictionary"].values()))
                sound_name = os.path.splitext(os.path.basename(sample_wav))[0]
                print(f"✅ 创建并导入 Sound Voice: {sound_name}")

    except CannotConnectToWaapiException:
        print("❌ 无法连接到 Waapi")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


# ================================
# 入口
# ================================

if __name__ == "__main__":
    main()
