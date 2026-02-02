#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint


try:
    with WaapiClient() as client:
        result = client.call(
            "ak.wwise.ui.getSelectedObjects",
            options ={"return": ['id',"type", "name","originalWavFilePath"]}
        )
        pprint(result["objects"])

        id = result["objects"][0]['id']
        pprint('=========================================')
        pprint('=========================================')
        pprint(id)
except CannotConnectToWaapiException:
    print(
        "Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?"
    )