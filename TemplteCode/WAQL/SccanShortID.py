from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

short_id = 2745116205  # 你的 ShortID

query = {
    "waql": f"$ where shortId = {short_id}",
    "options": {
        "return": [
            "id",
            "name",
            "type",
            "path",
            "shortId",
            "parent",
            "children"
        ]
    }
}

try:
    with WaapiClient() as client:
        result = client.call("ak.wwise.core.object.get", query)
        if result['return']:
            pprint(result['return'])
        else:
            print(f"[ShortID={short_id}] 未找到任何对象")
except CannotConnectToWaapiException:
    print("无法连接到 Wwise，请确保 Wwise 作者工具正在运行。")
except Exception as e:
    print(f"查询失败: {e}")
