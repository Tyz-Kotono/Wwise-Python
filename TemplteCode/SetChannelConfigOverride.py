from waapi import WaapiClient
from pprint import pprint

def get_type(client: WaapiClient, guid):
    args = {
        'from': {'id': [guid]}
    }
    options = {'return': ['id', 'name', 'type']}
    result = client.call("ak.wwise.core.object.get", args, options=options)
    return result['return'][0]['type']

def set_channel_config(client: WaapiClient, guid, channel_config):
    result = client.call("ak.wwise.core.object.setProperty", {
        "object": guid,
        "property": "ChannelConfigOverride",
        "value": channel_config
    })
    return result

with (WaapiClient() as client):
    source_id = '{3B288C07-B4E2-4419-A133-9A77A9015C82}'
    fileSource_id = source_id;
    result = get_type(client,source_id)
    pprint(result)


    if(result == 'Sound'):
        result = client.call("ak.wwise.core.object.get", {
            "from": {"id": [source_id]},
            "transform": [{"select": ["children"]}],
            "options": {
                "return": ["id", "name", "type", "ChannelConfigOverride"]
            }
        })
        source_id = result['return'][0]['id']
        pprint(result)

        result =set_channel_config(client,source_id,49410)

    pprint(result)