#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

WAAPI_URL = "ws://127.0.0.1:8080/waapi"


def Check(client, id_or_path, is_path=False):
    """
    Check Wwise object by ID or path.

    Args:
        client: WaapiClient instance
        id_or_path: Object ID (GUID or Short ID) or path
        is_path: If True, treat as path; otherwise as ID
    """
    if is_path:
        object_get_args = {
            "from": {
                "path": [id_or_path]
            }
        }
    else:
        object_get_args = {
            "from": {
                "id": [id_or_path]
            }
        }

    object_get_args["options"] = {
        "return": ["id", "name", "type", "parent.id", "IsVoice", "audioSourceLanguage"
                   ]
    }

    result = client.call("ak.wwise.core.object.get", object_get_args)
    pprint(result)


try:
    # Connecting to Waapi using default URL
    with WaapiClient(WAAPI_URL) as client:
        Check(client, '{30EAE2D4-212F-475D-B124-66543FB14C93}')

except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
