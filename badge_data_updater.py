import os
import json
import requests
import asyncio

def fetch_badge_data(badge_id):
    url = f'https://badges.roblox.com/v1/badges/{badge_id}'
    response = requests.get(url)
    print(f"HTTP Status Code for badge {badge_id}: {response.status_code}")
    print(f"Raw Response for badge {badge_id}: {response.text[:500]}")
    
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print(f"Error: Failed to decode JSON for badge ID {badge_id}. Response text: {response.text}")
            return None
    else:
        print(f"Error fetching badge data for ID {badge_id}: HTTP {response.status_code} - {response.text}")
        return None

def store_badge_data(badge_data):
    try:
        if os.path.exists('badge_data.json'):
            with open('badge_data.json', 'r') as f:
                try:
                    all_badges = json.load(f)
                except json.JSONDecodeError:
                    print("Error decoding JSON from file, starting with empty list.")
                    all_badges = []
        else:
            all_badges = []

        all_badges.append(badge_data)
        with open('badge_data.json', 'w') as f:
            json.dump(all_badges, f, indent=4)
        print("Badge data updated in 'badge_data.json'.")
    
    except Exception as e:
        print(f"Error storing badge data: {e}")

def process_badge_data(badge_data):
    processed_data = {
        "id": badge_data.get("id"),
        "name": badge_data.get("name"),
        "displayName": badge_data.get("displayName"),
        "enabled": badge_data.get("enabled"),
        "iconImageId": badge_data.get("iconImageId"),
        "created": badge_data.get("created"),
        "updated": badge_data.get("updated"),
        "statistics": badge_data.get("statistics", {}),
        "awardingUniverse": {
            "id": badge_data["awardingUniverse"].get("id"),
            "name": badge_data["awardingUniverse"].get("name"),
            "rootPlaceId": badge_data["awardingUniverse"].get("rootPlaceId")
        }
    }
    return processed_data

badge_ids = [
    "1937835649007198",
    "1632252210831820"
]

async def update_badge_data():
    while True:
        for badge_id in badge_ids:
            print(f"Fetching badge data for ID: {badge_id}")
            
            badge_data = fetch_badge_data(badge_id)
            if badge_data:
                processed_data = process_badge_data(badge_data)
                store_badge_data(processed_data)
            else:
                print(f"Skipping badge ID {badge_id} due to errors.")
        
        await asyncio.sleep(15)  

asyncio.run(update_badge_data())
