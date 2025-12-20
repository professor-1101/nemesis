#!/usr/bin/env python3
"""
Direct ReportPortal API test to verify launch finish functionality
"""

import time
from reportportal_client import RPClient
from reportportal_client.helpers import timestamp

def test_rp_direct():
    endpoint = "http://192.168.10.191:9080"
    project = "saucedemo"
    api_key = "saucedemo_JL_9PyVyTK-W_KNUP6tX0mGYHL51XcPK7vdCC4ChEHBunBbBGA_8BnpnmHPLKBeB"

    print("Creating RP Client...")
    client = RPClient(endpoint=endpoint, project=project, api_key=api_key)

    print("Starting client...")
    client.start()

    print("Starting launch...")
    launch = client.start_launch(name="Direct API Test",
                                 start_time=timestamp(),
                                 description="Testing direct API calls")

    print(f"Launch started with ID: {launch}")

    print("Starting test item...")
    item_id = client.start_test_item(name="Test Step",
                                     description="A test step",
                                     start_time=timestamp(),
                                     item_type="STEP")

    print(f"Test item started with ID: {item_id}")

    print("Adding a log message...")
    client.log(time=timestamp(),
               message="This is a test log message",
               level="INFO")

    print("Finishing test item...")
    client.finish_test_item(item_id=item_id, end_time=timestamp(), status="PASSED")

    print("Finishing launch...")
    client.finish_launch(end_time=timestamp())

    print("Terminating client (this should flush all data)...")
    client.terminate()

    print("✅ Test completed successfully!")
    print("Check ReportPortal UI to verify launch was created and finished.")

if __name__ == "__main__":
    test_rp_direct()
