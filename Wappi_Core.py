from waapi import WaapiClient
from pprint import pprint


def set_channel_config(client: WaapiClient, guid, channel_config):
    result = client.call("ak.wwise.core.object.setProperty", {
        "object": guid,
        "property": "ChannelConfigOverride",
        "value": channel_config
    })
    return result