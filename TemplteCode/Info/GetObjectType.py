#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

WAAPI_URL = "ws://127.0.0.1:8080/waapi"


try:
    # Connecting to Waapi using default URL
    with WaapiClient(WAAPI_URL) as client:
        result = client.call("ak.wwise.core.object.getTypes")
        pprint(result)
except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
