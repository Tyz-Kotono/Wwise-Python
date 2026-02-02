
from waapi import WaapiClient

# Connect to Wwise.
client = WaapiClient()

# Find all Sound objects that are set to loop.
args_get = {"waql": '$ from type Sound where IsLoopingEnabled = true'}
objs = client.call("ak.wwise.core.object.get", args_get)

# Go over each object, making sure it is set to be streamed.
for obj in objs["return"]:
  args_set = {"object": obj["id"], "property": "IsStreamingEnabled", "value": True}
  client.call("ak.wwise.core.object.setProperty", args_set)

# Done!
client.disconnect()