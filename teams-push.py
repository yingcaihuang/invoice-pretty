import urllib.request
import json
import os
import sys
from datetime import datetime

def send_teams_notification():
    # Get Webhook URL from environment variable
    # Workflow URL 需要从 Environment secrets 中去取 变量名为 TEAMS_URL
    teams_url = os.getenv('TEAMS_URL')
    if not teams_url:
        print("Error: TEAMS_URL environment variable is not set.")
        # 在本地测试时如果没有设置环境变量，可以打印警告但不退出，或者直接退出
        # 为了在 GitHub Actions 中安全，如果没有 URL 则报错
        sys.exit(1)

    # Get GitHub Actions context
    github_server_url = os.getenv('GITHUB_SERVER_URL', 'https://github.com')
    github_repository = os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
    github_run_id = os.getenv('GITHUB_RUN_ID', '')
    github_workflow = os.getenv('GITHUB_WORKFLOW', 'Unknown Workflow')
    github_actor = os.getenv('GITHUB_ACTOR', 'Unknown Actor')
    github_ref = os.getenv('GITHUB_REF', 'unknown ref')
    github_sha = os.getenv('GITHUB_SHA', 'unknown sha')[:7]
    
    # Construct Workflow Run URL
    workflow_run_url = f"{github_server_url}/{github_repository}/actions/runs/{github_run_id}"

    # Get custom status/version if provided via env vars
    # 可以在 workflow step 中设置: env: WORKFLOW_STATUS: 'Success'
    status = os.getenv('WORKFLOW_STATUS', 'In Progress')
    # 如果是 Release，通常会有 tag
    version = os.getenv('RELEASE_VERSION', github_ref)
    
    # Determine color and icon based on status
    status_color = "Accent"
    status_icon = "🚀"
    if status.lower() == 'success':
        status_color = "Good"
        status_icon = "✅"
    elif status.lower() == 'failure':
        status_color = "Attention"
        status_icon = "❌"
    elif status.lower() == 'cancelled':
        status_color = "Warning"
        status_icon = "⚠️"

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Adaptive Card
    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "msteams": {
                        "width": "Full"
                    },
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"{status_icon} {github_workflow}",
                            "weight": "Bolder",
                            "size": "Large",
                            "color": status_color
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Repository: {github_repository}",
                            "isSubtle": True,
                            "spacing": "None",
                            "size": "Small"
                        },
                        {
                            "type": "Container",
                            "style": "emphasis",
                            "items": [
                                {
                                    "type": "FactSet",
                                    "facts": [
                                        {
                                            "title": "Status",
                                            "value": status
                                        },
                                        {
                                            "title": "Version/Ref",
                                            "value": version
                                        },
                                        {
                                            "title": "Triggered By",
                                            "value": github_actor
                                        },
                                        {
                                            "title": "Commit",
                                            "value": github_sha
                                        },
                                        {
                                            "title": "Time",
                                            "value": current_time
                                        }
                                    ]
                                }
                            ],
                            "spacing": "Medium"
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Workflow Run",
                            "url": workflow_run_url
                        }
                    ]
                }
            }
        ]
    }

    json_data = json.dumps(card).encode('utf-8')
    req = urllib.request.Request(teams_url, data=json_data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            print(f"Notification sent successfully! Status: {response.getcode()}")
            print(f"Response: {response_body}")
    except urllib.error.HTTPError as e:
        print(f"Request failed: HTTP {e.code}")
        print(e.read().decode('utf-8'))
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_teams_notification()
