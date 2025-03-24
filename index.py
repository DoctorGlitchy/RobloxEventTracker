import os
from dotenv import load_dotenv
import json
import requests
import asyncio
import discord

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Set up Discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# File paths
BADGE_DATA_FILE = 'badge_data.json'
TRACKING_FILE = 'tracking_stopped.json'

def load_json_file(filename):
    """Loads a JSON file, returns an empty list if it doesn’t exist or fails."""
    print(f"Loading JSON file: {filename}")  # Log
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                print(f"Successfully loaded data from {filename}: {data}")  # Log
                return data
        except json.JSONDecodeError:
            print(f"Error decoding {filename}, returning empty list.")  # Log
    return []

def save_json_file(filename, data):
    """Saves data to a JSON file."""
    print(f"Saving data to {filename}: {data}")  # Log
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def ensure_tracking_file():
    """Ensures tracking_stopped.json exists with default values."""
    tracking_data = load_json_file(TRACKING_FILE)
    if not tracking_data:
        print(f"{TRACKING_FILE} does not exist or is empty, creating default tracking data.")  # Log
        tracking_data = [{"id": badge["id"], "name": badge["name"], "tracking": "online"} for badge in load_json_file(BADGE_DATA_FILE)]
        save_json_file(TRACKING_FILE, tracking_data)
    return tracking_data

async def fetch_badge_data(badge, tracking_entry, channel, tracking_data, previous_data):
    """Fetches updated badge data from the Roblox API."""
    badge_id = badge["id"]
    print(f"Fetching badge data for badge ID: {badge_id}")  # Log
    url = f'https://badges.roblox.com/v1/badges/{badge_id}'
    response = requests.get(url)

    if response.status_code == 200:
        processed_data = response.json()
        print(f"API Response for {badge_id}: {processed_data}")  # Log

        awarded_count = processed_data.get("statistics", {}).get("awardedCount", 0)

        if awarded_count > badge["statistics"].get("awardedCount", 0):  
            increase = awarded_count - badge["statistics"]["awardedCount"]
            message = (
                f"<@&1353603959691939931> Someone just got **{badge['name']}** from **{badge['awardingUniverse']['name']}**\n"
                f"**Previous:** {badge['statistics']['awardedCount']}\n"
                f"**New:** {awarded_count} (Increase: {increase})\n"
                f"[Play {badge['awardingUniverse']['name']}](https://www.roblox.com/games/{badge['awardingUniverse']['rootPlaceId']}/)"
            )
            await channel.send(message)

            if awarded_count > 200:
                await channel.send(f"Tracking stopped for **{badge['name']}**. It increased by {increase} since tracking began.")
                tracking_entry["tracking"] = "stopped"
                save_json_file(TRACKING_FILE, tracking_data)
                print(f"Tracking for badge ID {badge_id} stopped.")  # Log

            for b in previous_data:
                if b["id"] == badge_id:
                    b["statistics"]["awardedCount"] = awarded_count
            save_json_file(BADGE_DATA_FILE, previous_data)
            print(f"Updated awarded count for badge ID {badge_id}.")  # Log

async def update_badge_data():
    """Continuously checks for badge award increases and updates tracking."""
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("Invalid channel ID!")  # Log
        return

    while True:
        previous_data = load_json_file(BADGE_DATA_FILE)
        tracking_data = ensure_tracking_file()

        for badge in previous_data:
            badge_id = badge["id"]
            tracking_entry = next((t for t in tracking_data if t["id"] == badge_id), None)

            if tracking_entry and tracking_entry["tracking"] == "stopped":
                print(f"Skipping badge ID {badge_id} as tracking is stopped.")  # Log
                continue

            await fetch_badge_data(badge, tracking_entry, channel, tracking_data, previous_data)
        
        print("Sleeping for 15 seconds before the next check...")  # Log
        await asyncio.sleep(15)  # Wait before checking again

@client.event
async def on_ready():
    """Runs when the bot connects to Discord."""
    print(f"Bot is online as {client.user}")  # Log
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Bot is now online and monitoring badge data!")

    asyncio.create_task(update_badge_data())

client.run(DISCORD_TOKEN)
