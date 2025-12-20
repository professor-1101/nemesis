#!/usr/bin/env python3
"""
Manual launch finisher for ReportPortal
Use this to manually finish stuck launches
"""

import requests
import json
import sys
from datetime import datetime

def finish_launch_manually(endpoint: str, project: str, api_key: str, launch_id: str):
    """Manually finish a ReportPortal launch using direct API call"""

    try:
        # Prepare API endpoint
        endpoint = endpoint.rstrip("/")
        if not endpoint.endswith("/api/v1"):
            if endpoint.endswith("/api"):
                endpoint = endpoint[:-4]
            endpoint = f"{endpoint}/api/v1"

        url = f"{endpoint}/{project}/launch/{launch_id}/finish"

        # Prepare request data - ReportPortal API for finish launch
        end_time = str(int(datetime.now().timestamp() * 1000))
        data = {
            "endTime": end_time,
            "status": "STOPPED"  # Explicitly set status to STOPPED
        }

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        print(f"Making direct API call to finish launch: {launch_id}")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")

        # Make the API call
        response = requests.put(
            url,
            json=data,
            headers=headers,
            verify=False,  # Since config has verify_ssl: false
            timeout=10
        )

        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("Launch finished successfully!")
            return True
        else:
            print(f"Failed to finish launch. Status: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error finishing launch: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python finish_launch.py <launch_id>")
        print("Example: python finish_launch.py 2025-12-19_14-56-26_a286f5dd")
        sys.exit(1)

    launch_id = sys.argv[1]

    # Configuration from reportportal.yaml
    config = {
        "endpoint": "http://192.168.10.191:9080",
        "project": "saucedemo",
        "api_key": "saucedemo_JL_9PyVyTK-W_KNUP6tX0mGYHL51XcPK7vdCC4ChEHBunBbBGA_8BnpnmHPLKBeB"
    }

    print(f"Finishing launch: {launch_id}")
    success = finish_launch_manually(
        config["endpoint"],
        config["project"],
        config["api_key"],
        launch_id
    )

    sys.exit(0 if success else 1)
