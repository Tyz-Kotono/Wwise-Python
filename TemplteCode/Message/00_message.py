# Raw WAAPI

from waapi import WaapiClient

# First, we need to connect to Wwise.
client = WaapiClient()

# Next, we need to build a JSON object with our data inputs.
args = {"message": "Hello, Wwise!", "severity": "Message", "channel": "general"}

# Then, we can call the function (by name), using our JSON object.
client.call("ak.wwise.core.log.addItem", args)

# Finally, we can disconnect.
client.disconnect()


