from pprint import pprint

from waapi import WaapiClient, CannotConnectToWaapiException

parent_id = "{076D3CA5-38AB-4076-8F36-2C7CF9FB1CAD}"  # 可以改成你的父对象路径或 ID
audio_file_path = "D:/Temp/ja_JP/Voice/Character/100901/VO_100801_Battle_Cheer.wav"
# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html
# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=waapi_example_index.html


def Creact_WwiseObject(client, type, name, parent):
    # 对一个 Sound SFX 对象创建 Event 并定义其播放行为为播放
    args_new_event = {
        # 上半部分属性中分别为 Event 创建后存放的路径、类型、名称、遇到名字冲突时的处理方法
        "parent": parent,
        "type": type,
        "name": name,
        "onNameConflict": "merge",

    }

    return client.call("ak.wwise.core.object.create", args_new_event)


try:
    with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:
        print("✅ 成功连接到 Wwise Waapi!")
        Creact_WwiseObject(client, "Physical Folder",
                           "Voice Temp", '\Actor-Mixer Hierarchy')
        Creact_WwiseObject(client, "Work Unit", "Voice Temp_Temp",
                           '\Actor-Mixer Hierarchy\Voice Temp')
        # PropertyContainer
        Creact_WwiseObject(client, "Property Container", "My_Property",
                           '\Actor-Mixer Hierarchy\Voice Temp\Voice Temp_Temp')
        # 示例2：创建随机容器
        Creact_WwiseObject(client, "Random Container", "My_Random_Container",
                           '\Actor-Mixer Hierarchy\Voice Temp\Voice Temp_Temp')

        # 示例3：创建切换容器
        Creact_WwiseObject(client, "Switch Container", "My_Switch_Container",
                           '\Actor-Mixer Hierarchy\Voice Temp\Voice Temp_Temp')

        # 示例4：创建虚拟文件夹（不是PropertyContainer）
        Creact_WwiseObject(client, "Folder", "My_Folder",
                           '\Actor-Mixer Hierarchy\Voice Temp\Voice Temp_Temp')

        Creact_WwiseObject(client, "ActorMixer", "My_Mixer",
                           '\Actor-Mixer Hierarchy\Voice Temp\Voice Temp_Temp')

    print("✅ Sound Voice 创建并导入音频成功!")
    # print("返回结果:", result)

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Waapi")
except Exception as e:
    print(f"❌ 发生错误: {e}")
