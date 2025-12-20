#!/usr/bin/env python3
"""
Check logs for the latest launch
"""

import requests

def check_logs():
    endpoint = "http://192.168.10.191:9080"
    project = "saucedemo"
    api_key = "saucedemo_JL_9PyVyTK-W_KNUP6tX0mGYHL51XcPK7vdCC4ChEHBunBbBGA_8BnpnmHPLKBeB"

    # Get latest launch
    url = f"{endpoint}/api/v1/{project}/launch"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            launches = data.get('content', [])

            # Find latest launch
            latest_launch = None
            for launch in launches:
                if launch.get('name') == 'User Authentication':
                    if not latest_launch or launch.get('id') > latest_launch.get('id'):
                        latest_launch = launch

            if latest_launch:
                launch_id = latest_launch.get('id')
                print(f"Found launch: {latest_launch.get('name')} (ID: {launch_id})")

                # Get all logs for this launch
                logs_url = f"{endpoint}/api/v1/{project}/log"
                logs_params = {
                    "filter.eq.launchId": launch_id,
                    "page.size": 100,
                    "page.page": 1
                }

                logs_response = requests.get(logs_url, headers=headers, params=logs_params, verify=False, timeout=10)
                print(f"Logs API Status: {logs_response.status_code}")

                if logs_response.status_code == 200:
                    logs_data = logs_response.json()
                    logs = logs_data.get('content', [])

                    print(f"Found {len(logs)} logs total")

                    # Show recent logs
                    for log in logs[-10:]:  # Show last 10 logs
                        level = log.get('level')
                        message = log.get('message', '')[:100]
                        time = log.get('time')
                        item_id = log.get('itemId')
                        attachment = log.get('attachment')

                        print(f"  Log: {level} - {message}... (item: {item_id})")
                        if attachment:
                            print(f"    Attachment: {attachment.get('name')}")

                else:
                    print(f"Logs API error: {logs_response.status_code}")
                    print(f"Response: {logs_response.text}")
            else:
                print("Launch not found")
        else:
            print(f"Launch API error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_logs()
