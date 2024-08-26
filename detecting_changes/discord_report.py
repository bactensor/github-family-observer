# discord_report.py
import requests
import config
import json

def post_to_discord(embed, webhook_url):
    data = {
        "embeds": [embed]
    }

    response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    return response.status_code, response.text