#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

def get_type(client: WaapiClient, guid):
    args = {
        'from': {'id': [guid]}
    }
    options = {'return': ['id', 'name', 'type']}
    result = client.call("ak.wwise.core.object.get", args, options=options)
    return result['return'][0]['type']

def get_Property_by_classID(client: WaapiClient, class_id):
    args = {
        'classId': class_id,
    }
    result = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", args)
    return result['return']


try:
    with WaapiClient() as client:
        result =  client.call('ak.wwise.core.object.getTypes')

        pprint(result)
        pprint('=========================================')
        pprint('                 getTypes                ')
        pprint('=========================================')

        result = get_Property_by_classID(client,16)
        pprint(result)
        pprint('=========================================')
        pprint('    getPropertyAndReferenceNames         ')
        pprint('=========================================')

        result = get_type(client, '{B4FB56ED-9B08-4037-BC73-A43C9163CF62}')
        pprint(result)
        pprint('=========================================')
        pprint('                getType                  ')
        pprint('=========================================')

except CannotConnectToWaapiException:
    print(
        "Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?"
    )