from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

# Python 的异常处理 try…except…else… 语句
try:
    client = WaapiClient()

except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")

else:
    # 建立 on_name_changed() 准备在订阅中作为回调函数，用来接收字典形式的返回参数
    def on_name_changed(*args, **kwargs):
        # 获取对象类型
        obj_type = kwargs.get("object", {}).get("type")
        # 获取之前的名字
        old_name = kwargs.get("oldName")
        # 获取新名字
        new_name = kwargs.get("newName")

        # 使用 format 格式化函数进行输出信息（其中的{}代表 format() 函数中的对应变量），告知用户XXX类型的对象从 A 改名到了 B
        print("Object '{}' (of type '{}') was renamed to '{}'\n".format(old_name, obj_type, new_name))
        # 执行完成后断开 WAMP 连接，当然，要是想一直监控信息也可以不断开
        client.disconnect()

    # 订阅所需主题，传入回调函数，使用选项 type 以让名称修改时传回的字典里直接有被修改的对象类型
    handler = client.subscribe("ak.wwise.core.object.nameChanged", on_name_changed, {"return": ["type"]})

    # 打印信息，提醒用户已经订阅了 ak.wwise.core.object.nameChanged 并建议用户执行重命名操作以验证脚本功能
    print("Subscribed 'ak.wwise.core.object.nameChanged', rename an object in Wwise")

