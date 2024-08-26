import requests
import json

def send_embed_via_webhook(webhook_url):
    # Create the embed structure
    embed = {
        "title": "Example Embed",
        "description": "This is an example of an embed sent via a webhook.",
        "color": 9283822,  # Hex color code in decimal
        "fields": [
            {
                "name": "Field 1",
                "value": "This is the value for field 1",
                "inline": False
            },
            {
                "name": "Field 2",
                "value": "This is the value for field 2",
                "inline": True
            },
            {
                "name": "Field 3",
                "value": "This is the value for field 3",
                "inline": True
            }
        ],
        "thumbnail": {
            "url": "https://example.com/image.png"
        },
        "footer": {
            "text": "This is a footer text"
        }
    }

    # Create the payload with the embed
    data = {
        "embeds": [embed]
    }

    # Send the POST request to the webhook URL
    response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    if response.status_code == 204:
        print("Embed sent successfully!")
    else:
        print(f"Failed to send embed. Status code: {response.status_code}, Response: {response.text}")

# Replace 'YOUR_WEBHOOK_URL' with your actual Discord webhook URL
send_embed_via_webhook("https://discord.com/api/webhooks/1275490424420696124/O48oPQSk6-zMUFHRSIiTUo1xBwkGMn2GtQG4rTbpttfl-Zq3m0Iy7U1ASVID7z7hmC91")









import requests
import json

def send_embed_with_link(webhook_url):
    # Create the embed structure
    embed = {
        "title": "Example Embed",
        "description": "This is an example of an embed with a clickable link.",
        "color": 3447003,  # Hex color code in decimal
        "fields": [
            {
                "name": "Clickable Link",
                "value": "[Click here to visit OpenAI](https://www.openai.com)",
                "inline": False
            }
        ],
        "footer": {
            "text": "This is a footer text"
        }
    }

    # Create the payload with the embed
    data = {
        "embeds": [embed]
    }

    # Send the POST request to the webhook URL
    response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    if response.status_code == 204:
        print("Embed sent successfully!")
    else:
        print(f"Failed to send embed. Status code: {response.status_code}, Response: {response.text}")

# Replace 'YOUR_WEBHOOK_URL' with your actual Discord webhook URL
send_embed_with_link('https://discord.com/api/webhooks/1275490424420696124/O48oPQSk6-zMUFHRSIiTUo1xBwkGMn2GtQG4rTbpttfl-Zq3m0Iy7U1ASVID7z7hmC91')

# Replace 'YOUR_WEBHOOK_URL' with your actual Discord webhook URL
# send_embed_via_webhook("https://discord.com/api/webhooks/1275490424420696124/O48oPQSk6-zMUFHRSIiTUo1xBwkGMn2GtQG4rTbpttfl-Zq3m0Iy7U1ASVID7z7hmC91")
