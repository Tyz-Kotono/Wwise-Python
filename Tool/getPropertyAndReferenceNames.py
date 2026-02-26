#!/usr/bin/env python3
from waapi import WaapiClient, CannotConnectToWaapiException
from pprint import pprint

WAAPI_URL = "ws://127.0.0.1:8080/waapi"
try:
    with WaapiClient(WAAPI_URL) as client:
        # 先拿一个 AudioFileSource 的 GUID

        # 取第一个来查它的 Property 和 Reference 名称
        first_guid = '{2A3CC489-073B-41D9-AFF4-A53AF9A26A2E}'

        result = client.call(
            "ak.wwise.core.object.getPropertyAndReferenceNames", {
                'object': first_guid,
            })
        pprint(result)
except CannotConnectToWaapiException:
    print("Could not connect to Waapi: Is Wwise running and Wwise Authoring API enabled?")
