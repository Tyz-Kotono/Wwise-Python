from pprint import pprint

from waapi import WaapiClient, CannotConnectToWaapiException

parent_id = "{076D3CA5-38AB-4076-8F36-2C7CF9FB1CAD}"  # 可以改成你的父对象路径或 ID
audio_file_path = "D:/Temp/ja_JP/Voice/Character/100901/VO_100801_Battle_Cheer.wav"
# https://www.audiokinetic.com/en/public-library/2025.1.4_9062/?source=SDK&id=wobjects_index.html


try:
    with WaapiClient(url='ws://127.0.0.1:8080/waapi') as client:
        print("✅ 成功连接到 Wwise Waapi!")


        result = client.call(
            "ak.wwise.core.object.set",
            {
                "objects": [
                    {
                        "object": parent_id,
                        "children": [
                            {
                                "type": "Sound Voice",
                                "name": "New Voice",
                                "import": {
                                    "files":         #files
                                        [
                                        {
                                            "audioFile": audio_file_path,
                                            "language": "en_US"
                                        },
                                        {
                                            "audioFile": audio_file_path,
                                            "language": "zh_CN"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        )



    print("✅ Sound Voice 创建并导入音频成功!")
    # print("返回结果:", result)

except CannotConnectToWaapiException:
    print("❌ 无法连接到 Waapi")
except Exception as e:
    print(f"❌ 发生错误: {e}")
