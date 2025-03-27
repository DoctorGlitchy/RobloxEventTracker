import os
from dotenv import load_dotenv
import json
import asyncio
import discord
import requests

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

BADGE_DATA_FILE = 'badge_data.json'
BADGE_IDS = [
    "3553892029567363", "2006476404603013", "1402784206109874", "3424760970808412", "2687091214209505",
    "1950752823568522", "896410761526962", "908937030154893", "2249586838099610", "1789955136120943",
    "4026905963190467", "2088247848572439", "2959776838245141", "883863394508649", "3815451850757776",
    "1240956973916309", "1791141774909664", "2402082359357547", "6370627825209", "2182296430347036",
    "834356972037822", "2556479517722", "781374720195142", "4403583257735708", "2596793674187054",
    "78030905354225", "2872283437821216", "4298563535274734", "360931317065964", "429115567812460",
    "2226554901955480", "916880090339227", "2235601077342708", "3970864651194034", "1965756060754704",
    "855420657457185", "1196300524030672", "3565476006116598", "4450899674437231", "3718537393101638",
    "2067625720901930", "1699067754363164", "2498589519167042", "2181382568588484", "2706414659294960",
    "3872635867525597", "4084897593762512", "204451714859034", "1409598089011069", "881664195164545"
]

stopped_tracking = set()  # Track badges that reached the limit
badge_increases = {}  # Track cumulative increases

def fetch_badge_data(badge_id):
    """Fetches fresh badge data from the API."""
    url = f'https://badges.roblox.com/v1/badges/{badge_id}'
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[ERROR] Fetch failed for {badge_id}: HTTP {response.status_code}")
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

# Reset badge_data.json on startup
print("[INFO] Resetting badge_data.json...")
save_json_file(BADGE_DATA_FILE, [])

async def initialize_badge_data():
    """Fetches all badge data and initializes badge_data.json."""
    print("[INFO] Initializing badge data...")
    badge_list = []
    
    for badge_id in BADGE_IDS:
        data = fetch_badge_data(badge_id)
        if data:
            badge_list.append({
                "id": data["id"],
                "name": data["name"],
                "statistics": {
                    "pastDayAwardedCount": data["statistics"]["pastDayAwardedCount"],
                    "awardedCount": data["statistics"]["awardedCount"],
                    "winRatePercentage": data["statistics"]["winRatePercentage"]
                },
                "awardingUniverse": {
                    "id": data["awardingUniverse"]["id"],
                    "name": data["awardingUniverse"]["name"],
                    "rootPlaceId": data["awardingUniverse"]["rootPlaceId"]
                }
            })
            badge_increases[str(data["id"])] = 0  # Initialize tracking with string key
            print(f"[INFO] Fetched badge: {data['name']}")
        else:
            print(f"[ERROR] Failed to fetch badge: {badge_id}")
    
    save_json_file(BADGE_DATA_FILE, badge_list)
    print("[INFO] Badge data initialized successfully.")

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

        # Check if all badges are skipped
        if all(str(badge["id"]) in stopped_tracking for badge in latest_data):
            print("[DEBUG] Entering sleep mode")
            await channel.send("Looks like I need updated. Entering sleep mode 🌙")
            await asyncio.sleep(float("inf"))  # Sleep indefinitely
            return  # Stop further execution

        latest_badge = latest_data[badge_index]
        badge_id = str(latest_badge["id"])  # Ensure badge_id is a string

        if badge_id in stopped_tracking:
            print(f"[DEBUG] Skipping {latest_badge['name']} (No longer tracking)")
            badge_index += 1
            await asyncio.sleep(0.1)
            continue

        print(f"[DEBUG] Checking Badge {badge_index + 1}/{len(latest_data)}: {latest_badge['name']}")

        new_data = fetch_badge_data(badge_id)
        if not new_data:
            print(f"[ERROR] Failed to fetch fresh data for {latest_badge['name']}")
            badge_index += 1
            await asyncio.sleep(2)
            continue

        new_awarded = new_data["statistics"].get("awardedCount", 0)

        previous_data = load_json_file(BADGE_DATA_FILE)

        for prev_badge in previous_data:
            if str(prev_badge["id"]) == badge_id:
                old_awarded = prev_badge["statistics"].get("awardedCount", 0)
                increase = new_awarded - old_awarded
                
                if increase > 0:
                    if badge_id not in badge_increases:
                        badge_increases[badge_id] = 0  # Ensure key exists
                    
                    badge_increases[badge_id] += increase
                    print(f"[INFO] {latest_badge['name']} cumulative increase: {badge_increases[badge_id]}")
                    
                    if badge_increases[badge_id] >= 15:
                        stopped_tracking.add(badge_id)
                        print(f"[INFO] Badge {latest_badge['name']} reached a cumulative increase of 15. No longer tracking.")
                        await channel.send(f"🚨 Badge **{latest_badge['name']}** has reached an increase of 15 and will no longer be tracked. Nobody GAF!")
                        badge_index += 1
                        await asyncio.sleep(0.1)
                        continue

                    game_name = prev_badge["awardingUniverse"]["name"]
                    game_link = f"https://www.roblox.com/games/{prev_badge['awardingUniverse']['rootPlaceId']}"

                    message = (
                        f"<@&1353603959691939931>\n"
                        f"🔔 Someone just got something!\n"
                        f"Badge: {latest_badge['name']} in **{game_name}**\n"
                        f"Previous: **{old_awarded}** → New: **{new_awarded}**\n(📈 Increase: **{increase})**\n"
                        f"Badge ID: {badge_id}\n"
                        f"[{game_name}]({game_link})\n"
                    )
                    await channel.send(message)

                prev_badge["statistics"]["awardedCount"] = new_awarded
                break

        save_json_file(BADGE_DATA_FILE, previous_data)

        badge_index += 1
        await asyncio.sleep(0.5)

@client.event
async def on_ready():
    """Runs when the bot connects to Discord."""
    print(f"[INFO] Bot is online as {client.user}")
    asyncio.create_task(process_badge_updates())

client.run(DISCORD_TOKEN)
