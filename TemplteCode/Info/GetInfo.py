#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint
 
WAAPI_URL = "ws://127.0.0.1:8080/waapi"


def Check(client,path):
    object_get_args = {
        "from": {
            "path": [path]
        },
        "options": {
            "return": ["id", "name", "type"]
        }
    }
    result = client.call("ak.wwise.core.object.get", object_get_args)
    pprint(result)

try:
    # Connecting to Waapi using default URL
    with WaapiClient(WAAPI_URL) as client:
        Check(client,r"\Actor-Mixer Hierarchy\Voice_Player\100501\100501_1P\FAtk\zh_Montage_100501_FAtk03")
       
except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")