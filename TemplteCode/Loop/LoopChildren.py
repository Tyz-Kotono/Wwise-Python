from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

try:
    with WaapiClient() as client:
        result = client.call(
            "ak.wwise.ui.getSelectedObjects",
            options={"return": ['id', "type", "name"]}
        )
        pprint(result["objects"])

        object_id = result["objects"][0]['id']
        pprint("=========== Selected ===========")
        pprint(object_id)

        children = client.call("ak.wwise.core.object.get", {
            "from": {"id": [object_id]},
            "transform": [{"select": ["children"]}],
            "options": {"return": ["id", "name", "type"]}
        })



        pprint("=========== Recursive Result ===========")
        pprint(len(children['return']))
        # pprint(children)

except CannotConnectToWaapiException:
    print("Could not connect to Waapi")
