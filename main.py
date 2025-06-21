import time
import json
import requests
import os
import re

WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_url_here"
PING_USER_ID = "123456789012345678"

API_URL = "https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game/tournamentinformation"
DATA_FILE = "old_tournaments.json"

def load_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def fix_links(text):
    """
    Finds any occurrence of a URL starting with 'www.' and prepends 'https://' if missing.
    """
    if not text:
        return text
    fixed_text = re.sub(r'(?<!http://)(?<!https://)(www\.[^\s]+)', r'https://\1', text)
    return fixed_text

def build_embed(tourney):
    info = tourney.get("tournament_info", {})

    flavor_description = fix_links(info.get("flavor_description", "No information provided."))
    details_description = fix_links(info.get("details_description", "No details provided."))
    main_title = info.get("title_line_1") or info.get("short_format_title") or info.get("title_line_2") or "No Title Provided"
    
    fields = [
        {
            "name": "Main Title",
            "value": main_title,
            "inline": False
        }
    ]
    
    for field_key in ["short_format_title", "title_line_2"]:
        field_value = info.get(field_key)
        if field_value and field_value != main_title:
            formatted_field_name = field_key.replace("_", " ").title()
            fields.append({
                "name": formatted_field_name,
                "value": field_value,
                "inline": False
            })

    fields.append({
        "name": "Informations",
        "value": flavor_description,
        "inline": False
    })
    fields.append({
        "name": "Details",
        "value": details_description,
        "inline": False
    })

    embed = {
        "title": "New Tournament Detected",
        "fields": fields,
        "thumbnail": {
            "url": info.get("poster_front_image", "")
        },
        "image": {
            "url": info.get("loading_screen_image", "")
        }
    }
    return embed

def send_webhook(embed):
    payload = {
        "content": f"<@&{PING_USER_ID}>",
        "embeds": [embed]
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Webhook sent successfully.")
    except requests.RequestException as e:
        print("Error sending webhook:", e)

def check_for_new_tournaments():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print("Error fetching API:", e)
        return

    old_data = load_old_data()
    new_data = {}

    for key, value in data.items():
        if isinstance(value, dict) and value.get("tournament_info"):
            new_data[key] = value

    new_tournaments = []
    for key, tournament in new_data.items():
        if key not in old_data:
            new_tournaments.append(tournament)

    if new_tournaments:
        print(f"Detected {len(new_tournaments)} new tournament(s).")
        for tourney in new_tournaments:
            embed = build_embed(tourney)
            send_webhook(embed)
            time.sleep(2)
    else:
        print("No new tournaments detected.")

    save_data(new_data)

def main():
    print("Starting tournament tracker...")
    while True:
        check_for_new_tournaments()
        time.sleep(60)

if __name__ == "__main__":
    main()