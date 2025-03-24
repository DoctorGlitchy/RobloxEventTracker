import os
import discord
import asyncio
from discord.ext import commands, tasks
import requests

# Load token from environment variable file
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

CHANNEL_ID =  # Replace with your actual Discord channel ID

# Set up Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# List of games to track
games = [
    {"url": "https://www.roblox.com/games/124180448122765/The-Hunt-Mega-Edition", "badge_name": "Hexanoval Overlay", "start_value": None, "last_value": None, "tracking": True},
    {"url": "https://www.roblox.com/games/124180448122765/The-Hunt-Mega-Edition", "badge_name": "The Hunt: Mega Edition", "start_value": None, "last_value": None, "tracking": True}
]

def get_badge_stats(badge_name):
    # Replace with Roblox badge endpoint API call
    url = f"https://badges.roblox.com/v1/badges/{badge_name}/stats"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["wonEver"]
    else:
        return None

@tasks.loop(seconds=15)
async def update_badge_stats():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Error: Channel not found")
        return

    for game in games:
        if not game["tracking"]:
            continue  # Skip tracking if it's already hit the 1,000 increase

        new_value = get_badge_stats(game["badge_name"])

        if new_value is None:
            continue

        # Set the start_value if this is the first time tracking
        if game["start_value"] is None:
            game["start_value"] = new_value

        old_value = game["last_value"] if game["last_value"] is not None else game["start_value"]

        cumulative_increase = new_value - game["start_value"]

        if cumulative_increase >= 1000:
            game["tracking"] = False  # Stop tracking this game
            await channel.send(f"âœ… **Tracking stopped for {game['badge_name']}** Because you get the point. - It increased by **{cumulative_increase:,}** since tracking began (from {game['start_value']:,} to {new_value:,})")

        else:
            if new_value > old_value:
                increase = new_value - old_value
                await channel.send(f"ðŸ”” <@&1353603959691939931> Someone just got something! **{game['badge_name']}** Updated!\n**Previous:** {old_value:,}\n**New:** {new_value:,} (Increase: {increase:,}) \n[The Hunt: Mega Edition](https://www.roblox.com/games/124180448122765/)")

        game["last_value"] = new_value  # Update last known value

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    update_badge_stats.start()

bot.run(DISCORD_TOKEN)