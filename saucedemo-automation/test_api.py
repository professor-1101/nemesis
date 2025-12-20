#!/usr/bin/env python3
"""
Test ReportPortal API connectivity
"""

import requests

def test_api():
    endpoint = "http://192.168.10.191:9080"
    project = "saucedemo"
    api_key = "saucedemo_JL_9PyVyTK-W_KNUP6tX0mGYHL51XcPK7vdCC4ChEHBunBbBGA_8BnpnmHPLKBeB"

    url = f"{endpoint}/api/v1/{project}/launch"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Testing API: {url}")

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            launches = data.get('content', [])
            print(f"Found {len(launches)} launches")

        # Show all launches
        for launch in launches:
            name = launch.get('name')
            status = launch.get('status')
            start_time = launch.get('startTime')
            launch_id = launch.get('id')
            print(f"  - ID: {launch_id}, Name: {name}, Status: {status}, Time: {start_time}")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api()
