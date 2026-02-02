# Raw WAAPI

from waapi import WaapiClient

# New connection.
client = WaapiClient()

# JSON object with data inputs. The parent object is the Default Work Unit in the Actor-Mixer Hierarchy.
parent = "\\Actor-Mixer Hierarchy\\Default Work Unit"
args_new = {"name": "MyCoolSfx", "type": "Sound", "parent": parent, "onNameConflict": "replace"}

# Function call (by name).
obj = client.call("ak.wwise.core.object.create", args_new)

# Set Volume property.
args_volume = {"object": obj["id"], "property": "Volume", "value": -6.0}
client.call("ak.wwise.core.object.setProperty", args_volume)

# Set IsLoopingEnabled property.
args_loop = {"object": obj["id"], "property": "IsLoopingEnabled", "value": True}
client.call("ak.wwise.core.object.setProperty", args_loop)

# Set IsStreamingEnabled property.
args_stream = {"object": obj["id"], "property": "IsStreamingEnabled", "value": True}
client.call("ak.wwise.core.object.setProperty", args_stream)

# Set OutputBus reference.
path_bus = "/Master-Mixer Hierarchy/Default Work Unit/Master Audio Bus/Sfx"  # The bus MUST exist!
args_bus = {"object": obj["id"], "reference": "OutputBus", "value": path_bus}
client.call("ak.wwise.core.object.setReference", args_bus)

# Done!
client.disconnect()