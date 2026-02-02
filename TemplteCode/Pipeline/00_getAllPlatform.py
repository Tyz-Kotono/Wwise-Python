from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

def get_wwise_platforms_languages():
    """
    获取Wwise工程中的平台和语言信息

    Returns:
        tuple: 包含两个数组的元组 (platforms_array, languages_array)
    """
    try:
        with WaapiClient() as client:
            # 获取所有平台
            platforms_result = client.call("ak.wwise.core.object.get", {
                "waql": "from type platform"
            }, options={
                "return": ["id", "name"]
            })
            pprint(platforms_result)
            # 获取所有语言
            languages_result = client.call("ak.wwise.core.object.get", {
                "waql": "from type language"
            }, options={
                "return": ["id", "name"]
            })
            pprint(languages_result)
            # 过滤掉不需要的平台（如WwiseAuthoringPlayback）
            platforms = [platform['name'] for platform in platforms_result['return']
                         if platform['name'] != 'WwiseAuthoringPlayback']

            # 过滤掉不需要的语言（根据您的需求调整）
            languages = [language['name'] for language in languages_result['return']
                         if language['name'] not in ['Mixed', 'External', 'SFX']]

            print("獲取語言完成")
            pprint(platforms)
            pprint(languages)
            return platforms, languages

    except CannotConnectToWaapiException:
        print("无法连接到Wwise，请确保Wwise作者工具正在运行。")
        return [], []
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return [], []


get_wwise_platforms_languages()