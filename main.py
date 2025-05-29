import time
import json
import requests
import os
import re

# Set your Discord webhook URL here.
WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_url_here"
PING_USER_ID = "123456789012345678"

# The API endpoint for tournament information.
API_URL = "https://fortnitecontent-website-prod07.ol.epicgames.com/content/api/pages/fortnite-game/tournamentinformation"

# Local file to store previous tournaments.
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

    # Prepare descriptions with fixed links.
    flavor_description = fix_links(info.get("flavor_description", "No information provided."))
    details_description = fix_links(info.get("details_description", "No details provided."))

    # Determine main title using title_line_1 as primary, falling back if needed.
    main_title = info.get("title_line_1") or info.get("short_format_title") or info.get("title_line_2") or "No Title Provided"
    
    # Build embed fields starting with the main title.
    fields = [
        {
            "name": "Main Title",
            "value": main_title,
            "inline": False
        }
    ]
    
    # For each extra title field not used as the main title, add a separate field.
    for field_key in ["short_format_title", "title_line_2"]:
        field_value = info.get(field_key)
        if field_value and field_value != main_title:
            # Format field name, e.g., "title_line_2" becomes "Title Line 2"
            formatted_field_name = field_key.replace("_", " ").title()
            fields.append({
                "name": formatted_field_name,
                "value": field_value,
                "inline": False
            })

    # Add the description fields.
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

    # Build the embed payload.
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
        "content": f"<@{PING_USER_ID}>",
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

    # Iterate over the top-level keys that have tournament information.
    for key, value in data.items():
        if isinstance(value, dict) and value.get("tournament_info"):
            new_data[key] = value

    # Find new tournaments by comparing keys.
    new_tournaments = []
    for key, tournament in new_data.items():
        if key not in old_data:
            new_tournaments.append(tournament)

    if new_tournaments:
        print(f"Detected {len(new_tournaments)} new tournament(s).")
        for tourney in new_tournaments:
            embed = build_embed(tourney)
            send_webhook(embed)
            # Delay 2 seconds between webhook sends to avoid rate limits so adjust if needed
            time.sleep(2)
    else:
        print("No new tournaments detected.")

    # Save the new data for future comparisons.
    save_data(new_data)

def main():
    print("Starting tournament tracker...")
    while True:
        check_for_new_tournaments()
        # Wait 60 seconds between fetches.
        time.sleep(60)

if __name__ == "__main__":
    main()