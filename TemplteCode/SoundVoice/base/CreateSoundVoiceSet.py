# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html
# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=ak_wwise_core_object_set_example_importing_a_wav_file_into_a_sound_voice.html

from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
sound_path = r"\Actor-Mixer Hierarchy\Voice_Enemy\601702\GAtk\New Voice1"  # 可以改成你的父对象路径或 ID
audio_file_path = r"D:\WAV\001.wav"
audio_file_path = r"D:\nami\b0.6.5\Resource\Wwise\Nami_SoundProject_24.1\Originals\Voices\zh_CN\Voice_Enemy\601902\601902\Locomotion\zh_Montage_601901_CombatRun01\zh_Montage_601901_CombatRun01_01.wav"

# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html

# \Actor-Mixer Hierarchy\Voice_Enemy\601702\GAtk

# 1. 导入文件并建立音频层级


def file_import(file_path):
    # 定义文件导入参数，imports 中包含了硬盘中的文件路径和目标路径，目标路径中包括对创建对象的类型定义。
    # 对于非语音的 Sound SFX，importLanguage 使用 SFX。importOperation 为 useExisting，这代表了如果已经有所需的容器存在就直接替换，如果没有就创建一个。
    #  replaceExisting useExisting
    args_import = {
        "importOperation": "useExisting",
        "imports": [
            {
                "importLanguage": "zh_CN",
                "audioFile": audio_file_path,
                "objectPath": "\\Actor-Mixer Hierarchy\\Voice_Enemy\\<Work Unit>601703\\<Random Container>Test 0\\<Sound Voice>My SFX 0"

            }
        ]
    }
    # 定义返回结果参数，让其只返回 Windows 平台下的信息，信息中包含 GUID 和新创建的对象名
    opts = {
        "platform": "Windows",
        "return": [
            "id", "name"
        ]
    }

    return client.call("ak.wwise.core.audio.import", args_import, options=opts)


try:
    with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:
        print("✅ 成功连接到 Wwise Waapi!")

        result = file_import(audio_file_path)
        pprint(result)
        print("✅ Sound Voice 创建并导入音频成功!")
        # print("返回结果:", result)

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Waapi")
except Exception as e:
    print(f"❌ 发生错误: {e}")
