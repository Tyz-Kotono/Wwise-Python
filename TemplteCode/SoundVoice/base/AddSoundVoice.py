# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html
# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=ak_wwise_core_object_set_example_importing_a_wav_file_into_a_sound_voice.html

from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
sound_path = "\Actor-Mixer Hierarchy\Voice_Enemy\<Work Unit>601703\<Random Container>Test \<Sound Voice>My SFX 0"  # 可以改成你的父对象路径或 ID
audio_file_path = r"D:\WAV\001.wav"
# audio_file_path = r"D:/nami/b0.6.5/Resource/Wwise/Nami_SoundProject_24.1/Originals/Voices/zh_CN/Voice_Enemy/601702/Hurt/zh_Montage_601701_LandKnock01/zh_Montage_601701_LandKnock01_01.wav"

# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html

# \Actor-Mixer Hierarchy\Voice_Enemy\601702\GAtk

# 1. 导入文件并建立音频层级


def file_import(client, Language, file_path, objectPath):
    args_import = {
        "importOperation": "useExisting",
        "default": {
            # "importLanguage": "zh_CN"
        },
        "imports": [
            {
                'importLanguage': Language,
                "audioFile": file_path,
                "objectPath": objectPath
            }
        ]
    }
    opts = {
        "platform": "Windows",
        "return": [
            "path", "id", "name",
        ]
    }

    return client.call("ak.wwise.core.audio.import", args_import, options=opts)


try:
    with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:
        print("✅ 成功连接到 Wwise Waapi!")

        result = file_import(client, "zh_CN", audio_file_path, sound_path)
        pprint(result)
        print("✅ Sound Voice 创建并导入音频成功!")
        # print("返回结果:", result)

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Waapi")
except Exception as e:
    print(f"❌ 发生错误: {e}")
