#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

WAAPI_URL = "ws://127.0.0.1:8080/waapi"


def deleteWwiseObject(client, identifier, is_path=False):
    """
    Delete a Wwise object by ID or path.

    Args:
        client: WaapiClient instance
        identifier: Object ID (GUID or Short ID) or path
        is_path: If True, treat identifier as path; otherwise as ID
    """
    if is_path:
        delete_args = {
            "from": {
                "path": [identifier]
            }
        }
    else:
        delete_args = {
            "from": {
                "object": [identifier]
            }
        }

    result = client.call("ak.wwise.core.object.delete", delete_args)
    return result


def main():
    try:
        with WaapiClient(WAAPI_URL) as client:
            # Example 1: Delete by path
            path = r"/Actor-Mixer Hierarchy/Voice_Player/TestObject"
            print(f"Deleting by path: {path}")
            result = deleteWwiseObject(client, path, is_path=True)
            pprint(result)

            # Example 2: Delete by GUID
            # guid = "{BE28AB39-72CC-4A9E-8C8C-F2B9197969FB}"
            # print(f"Deleting by ID: {guid}")
            # result = deleteWwiseObject(client, guid, is_path=False)
            # pprint(result)

            # Example 3: Delete by Short ID
            # short_id = 12345678
            # print(f"Deleting by Short ID: {short_id}")
            # result = deleteWwiseObject(client, short_id, is_path=False)
            # pprint(result)

    except CannotConnectToWaapiException:
        print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
