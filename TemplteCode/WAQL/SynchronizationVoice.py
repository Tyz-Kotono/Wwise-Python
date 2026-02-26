from waapi import WaapiClient
import pprint
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
# Connect (default URL)
client = WaapiClient(WAAPI_URL)

# Return all objects under the Containers hierarchy with a name that starts with "My"
args = {
    # 'waql': '$ from type sound'
    'waql': '$ from type sound  where (IsVoice = True) select children'
}

options = {
    'return': ['name', 'id', "path", "originalRelativeFilePath", "audioSourceLanguage"]
}
result = client.call("ak.wwise.core.object.get", args, options=options)
pprint.pprint(result['return'])
print(len(result['return']))

client.disconnect()
