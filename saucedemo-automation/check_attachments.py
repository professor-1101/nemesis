#!/usr/bin/env python3
"""
Check attachments for the latest launch
"""

import requests

def check_attachments():
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

                # Get test items for this launch
                items_url = f"{endpoint}/api/v1/{project}/item"
                params = {
                    "filter.eq.launchId": launch_id,
                    "page.size": 50
                }

                items_response = requests.get(items_url, headers=headers, params=params, verify=False, timeout=10)
                print(f"Items API Status: {items_response.status_code}")

                if items_response.status_code == 200:
                    items_data = items_response.json()
                    items = items_data.get('content', [])

                    print(f"Found {len(items)} test items")

                    for item in items:
                        item_type = item.get('type')
                        name = item.get('name')
                        item_id = item.get('id')

                        print(f"  - {item_type}: {name} (ID: {item_id})")

                        # Check for attachments
                        if item_id:
                            logs_url = f"{endpoint}/api/v1/{project}/log"
                            logs_params = {
                                "filter.eq.item": item_id,
                                "page.size": 50
                            }

                            logs_response = requests.get(logs_url, headers=headers, params=logs_params, verify=False, timeout=10)

                            if logs_response.status_code == 200:
                                logs_data = logs_response.json()
                                logs = logs_data.get('content', [])

                                attachments = []
                                messages = []
                                for log in logs:
                                    if log.get('attachment'):
                                        attachments.append(log['attachment'])
                                    messages.append(f"{log.get('level', 'UNK')}: {log.get('message', '')[:50]}...")

                                if attachments:
                                    print(f"    Attachments: {len(attachments)}")
                                    for att in attachments:
                                        print(f"      - {att.get('name')}")
                                else:
                                    print(f"    No attachments (checked {len(logs)} logs)")

                                if messages:
                                    print(f"    Logs: {len(messages)}")
                                    for msg in messages[:3]:  # Show first 3 logs
                                        print(f"      - {msg}")
                            else:
                                print(f"    Logs API error: {logs_response.status_code}")
                                print(f"    Response: {logs_response.text}")
                else:
                    print("No launch found with name 'User Authentication'")
            else:
                print("Launch not found")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_attachments()
