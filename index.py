import os
from dotenv import load_dotenv
import json
import asyncio
import discord
import requests
from badge_data_updater import initialize_badge_data

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

BADGE_DATA_FILE = 'badge_data.json'

def fetch_badge_data(badge_id):
    """Fetches fresh badge data from the API, including badge name and game details."""
    url = f'https://badges.roblox.com/v1/badges/{badge_id}'
    response = requests.get(url)

    if response.status_code != 200:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            print(f"[ERROR] Fetch failed for {badge_id}: HTTP {response.status_code} (Retry-After: {retry_after})")
        else:
            print(f"[ERROR] Fetch failed for {badge_id}: HTTP {response.status_code}")
        return None

    badge_info = response.json()

    game_id = badge_info.get("awardingUniverseId", None)
    game_name = "Unknown Game"
    game_url = "https://www.roblox.com"

    if game_id:
        game_data = fetch_game_data(game_id)
        if game_data:
            game_name = game_data["name"]
            game_url = f"https://www.roblox.com/games/{game_id}"

    return {
        "badge_name": badge_info["name"],
        "awarded_count": badge_info["statistics"]["awardedCount"],
        "game_name": game_name,
        "game_url": game_url
    }

def fetch_game_data(game_id):
    """Fetches game data using the Universe ID to get the game name."""
    url = f'https://games.roblox.com/v1/games?universeIds={game_id}'
    response = requests.get(url)

    if response.status_code != 200:
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            print(f"[ERROR] Fetch failed for {game_id}: HTTP {response.status_code} (Retry-After: {retry_after})")
        else:
            print(f"[ERROR] Fetch failed for {game_id}: HTTP {response.status_code}")
        return None

    data = response.json()
    if "data" in data and len(data["data"]) > 0:
        return data["data"][0]
    return None

def load_json_file(filename):
    """Loads a JSON file, returns an empty list if it doesn’t exist or fails."""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] Error decoding {filename}. Returning empty list.")
    return []

def save_json_file(filename, data):
    """Saves data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

async def process_badge_updates():
    """Continuously cycles through all badges, checks API data, and updates badge_data.json correctly."""
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("[ERROR] Invalid channel ID!")
        return

    badge_index = 0

    while True:
        latest_data = load_json_file(BADGE_DATA_FILE)

        if not latest_data:
            print("[ERROR] No badge data found! Re-initializing...")
            await initialize_badge_data()
            await asyncio.sleep(2)
            continue

        if badge_index >= len(latest_data):  # Reset cycle
            badge_index = 0

        latest_badge = latest_data[badge_index]
        badge_id = latest_badge["id"]

        print(f"[DEBUG] Checking Badge {badge_index + 1}/{len(latest_data)}: {latest_badge['name']}")

        # Fetch fresh data from API
        new_data = fetch_badge_data(badge_id)
        if not new_data:
            print(f"[ERROR] Failed to fetch fresh data for {latest_badge['name']}")
            badge_index += 1
            await asyncio.sleep(2)
            continue

        new_awarded = new_data["awarded_count"]
        game_name = new_data["game_name"]
        game_url = new_data["game_url"]

        # Load previous stored data
        previous_data = load_json_file(BADGE_DATA_FILE)

        # Update the correct badge entry in badge_data.json
        for prev_badge in previous_data:
            if prev_badge["id"] == badge_id:
                old_awarded = prev_badge["statistics"]["awardedCount"]

                print(f"[DEBUG] {latest_badge['name']}: {old_awarded} -> {new_awarded}")

                if new_awarded > old_awarded:
                    increase = new_awarded - old_awarded
                    print(f"[INFO] Badge {latest_badge['name']} increased by {increase}!")

                    # Format Discord message
                    message = (
                        f"@badge_tracking Someone just got **{new_data['badge_name']}** from **{game_name}**\n"
                        f"📊 **Previous:** {old_awarded}\n"
                        f"🚀 **New:** {new_awarded} (Increase: {increase})\n"
                        f"🎮 [Play {game_name}]({game_url})"
                    )
                    await channel.send(message)

                # Force update badge_data.json with the correct values
                prev_badge["statistics"]["awardedCount"] = new_awarded
                break  # Stop looping once the badge is found and updated

        # Save updated badge_data.json
        save_json_file(BADGE_DATA_FILE, previous_data)

        badge_index += 1
        await asyncio.sleep(2)

@client.event
async def on_ready():
    """Runs when the bot connects to Discord."""
    print(f"[INFO] Bot is online as {client.user}")

    asyncio.create_task(process_badge_updates())

client.run(DISCORD_TOKEN)