from pprint import pprint
from waapi import WaapiClient, CannotConnectToWaapiException

audio_file_path = r"D:\nami\b0.6.5\Resource\Wwise\Nami_SoundProject_24.1\Originals\Voices\zh_CN\Voice_Enemy\601701_1\Temp_\AC\Locomotion\zh_Montage_601701_EnterCombat01\zh_Montage_601701_EnterCombat01_01.wav"


def file_import(client, file_path):
    args_import = {
        "importOperation": "createNew",
        "imports": [
            {
                "importLanguage": "zh_CN",
                "audioFile": audio_file_path,
                "objectPath": file_path
            }
        ]
    }
    opts = {
        "platform": "Windows",
        "return": ["id", "name"]
    }

    try:
        result = client.call("ak.wwise.core.audio.import",
                             args_import, options=opts)
        print(f"✅ 成功: {file_path.split('\\')[-1]}")
        return result
    except Exception as e:
        print(f"❌ 失败: {file_path}")
        print(f"   错误详情: {e}\n")
        return None


try:
    with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:
        print("✅ 成功连接到 Wwise Waapi!\n")

        # 测试 1: Random Container 直接包含 Sound - ✅ 应该成功
        file_import(client, r"\Actor-Mixer Hierarchy\<Physical Folder>Voice_Temp\<Work Unit>Temp_Wrok\<Random Container>Test 0\<Random Container>My_Random_Container\<Sound Voice>My SFX 0")

        # 测试 2: Switch Container 直接包含 Sound - ❌ 应该失败
        file_import(client, r"\Actor-Mixer Hierarchy\<Physical Folder>Voice_Temp\<Work Unit>Temp_Wrok\<SwitchContainer>My_Switch_Container\<Sound>My SFX 0")

        # 测试 3: Virtual Folder -> Random Container -> Sound - ✅ 应该成功!
        file_import(client, r"\Actor-Mixer Hierarchy\<Physical Folder>Voice_Temp\<Work Unit>Temp_Wrok\<Random Container>Test 0\<Virtual Folder>My_Folder\<Random Container>My_Random_Container-2\<Sound Voice>My SFX 0")

        # 测试 4: Actor Mixer -> Actor Mixer -> Random Container -> Sound - ✅ 应该成功!
        file_import(client, r"\Actor-Mixer Hierarchy\<Physical Folder>Voice_Temp\<Work Unit>Temp_Wrok2\<ActorMixer>Test 1\<ActorMixer>My_Mixer\<Random Container>My_Random_Container-3\<Sound Voice>My SFX 0")

    print("\n✅ 所有有效操作完成!")

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Waapi")
except Exception as e:
    print(f"❌ 发生错误: {e}")
