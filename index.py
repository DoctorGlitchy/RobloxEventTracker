import os
import discord
import asyncio
from discord.ext import commands, tasks
import requests

# Constants
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1353603012630937650 
BADGE_IDS = [123456789, 987654321]  

# Set up Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_badge_stats(badge_id: int) -> int:
    """Get badge stats from Roblox API"""
    url = f"https://badges.roblox.com/v1/badges/{badge_id}/stats"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4xx or 5xx status codes
        data = response.json()
        return data["wonEver"]
    except requests.RequestException as e:
        print(f"Error getting badge stats: {e}")
        return None

async def get_badge_name(badge_id: int) -> str:
    """Get badge name from Roblox API"""
    url = f"https://badges.roblox.com/v1/badges/{badge_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for 4xx or 5xx status codes
        data = response.json()
        return data["name"]
    except requests.RequestException as e:
        print(f"Error getting badge name: {e}")
        return None

@tasks.loop(seconds=15)
async def update_badge_stats():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Error: Channel not found")
        return

    for badge_id in BADGE_IDS:
        new_value = await get_badge_stats(badge_id)

        if new_value is None:
            continue

        badge_name = await get_badge_name(badge_id)

        if badge_id not in bot.badge_stats:
            bot.badge_stats[badge_id] = {"start_value": new_value, "last_value": new_value, "tracking": True}

        badge_stats = bot.badge_stats[badge_id]

        cumulative_increase = new_value - badge_stats["start_value"]

        if cumulative_increase >= 1000:
            badge_stats["tracking"] = False  # Stop tracking this badge
            await channel.send(f"âœ… **Tracking stopped for {badge_name}** Because you get the point. - It increased by **{cumulative_increase:,}** since tracking began (from {badge_stats['start_value']:,} to {new_value:,})")

        else:
            if new_value > badge_stats["last_value"]:
                increase = new_value - badge_stats["last_value"]
                await channel.send(f"ðŸ”” <@&1353603959691939931> Someone just got something! **{badge_name}** Updated!\n**Previous:** {badge_stats['last_value']:,}\n**New:** {new_value:,} (Increase: {increase:,}) \n[The Hunt: Mega Edition](https://www.roblox.com/games/124180448122765/)")

        badge_stats["last_value"] = new_value  # Update last known value

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.badge_stats = {}  # Initialize badge stats
    update_badge_stats.start()

bot.run(DISCORD_TOKEN)