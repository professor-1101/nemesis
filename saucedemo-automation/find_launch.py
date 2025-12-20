#!/usr/bin/env python3
"""
Find ReportPortal launch by name
"""

import requests
import json
import sys

def find_launch_by_name(endpoint: str, project: str, api_key: str, launch_name: str):
    """Find launch by name"""

    try:
        # Prepare API endpoint
        endpoint = endpoint.rstrip("/")
        if not endpoint.endswith("/api/v1"):
            if endpoint.endswith("/api"):
                endpoint = endpoint[:-4]
            endpoint = f"{endpoint}/api/v1"

        url = f"{endpoint}/{project}/launch"

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Parameters to find launch by name
        params = {
            "filter.eq.name": launch_name,
            "page.size": 1
        }

        print(f"Searching for launch: {launch_name}")
        print(f"URL: {url}")

        # Make the API call
        response = requests.get(
            url,
            headers=headers,
            params=params,
            verify=False,
            timeout=10
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            launches = data.get('content', [])

            if launches:
                launch = launches[0]
                launch_id = launch.get('id')
                status = launch.get('status')

                print("Launch found!")
                print(f"Launch ID: {launch_id}")
                print(f"Status: {status}")
                print(f"Name: {launch.get('name')}")
                print(f"Start Time: {launch.get('startTime')}")

                return launch_id, status
            else:
                print("Launch not found")
                return None, None
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None

    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    # Configuration from reportportal.yaml
    config = {
        "endpoint": "http://192.168.10.191:9080",
        "project": "saucedemo",
        "api_key": "saucedemo_JL_9PyVyTK-W_KNUP6tXPK7vdCC4ChEHBunBbBGA_8BnpnmHPLKBeB"
    }

    launch_name = "Nemesis Test Execution - 2025-12-19_14-56-26_a286f5dd"

    launch_id, status = find_launch_by_name(
        config["endpoint"],
        config["project"],
        config["api_key"],
        launch_name
    )

    if launch_id:
        print(f"\nTo finish this launch, run:")
        print(f"python finish_launch.py {launch_id}")
    else:
        print("\nLaunch not found in ReportPortal")
