import discord
import json
import asyncio
import os
from discord.ext import tasks
from datetime import datetime

# Load environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Load badge data from the previous file (badge_data.json)
def load_badge_data():
    with open('badge_data.json', 'r') as file:
        return json.load(file)

# Save the updated badge data back to the file
def save_badge_data(data):
    with open('badge_data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Set the cutoff for when tracking should stop
TRACKING_CUTOFF = 1000  # Example cutoff, you can adjust it to your needs

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Track updates for the badge data
def track_badge_updates():
    badge_data = load_badge_data()

    for badge in badge_data:
        # Fetch the new awarded count
        previous_count = badge["statistics"]["awardedCount"]
        current_count = badge["statistics"]["awardedCount"]  # Replace with actual current count if needed

        # Calculate the difference
        awarded_diff = current_count - previous_count

        # If the difference exceeds a certain amount, send a Discord message
        if awarded_diff > 0:
            # Format the message
            message = (
                f"🔥 <@&1353603959691939931> Someone just got something! **{badge['name']}** Updated!\n"
                f"**Previous:** {previous_count}\n"
                f"**New:** {current_count} (Increase: {awarded_diff})\n"
                f"[{badge['name']}]({badge['awardingUniverse']['rootPlaceId']})"
            )

            # Send the message to Discord
            send_to_discord(message)

        # Stop tracking if the cutoff is reached
        if awarded_diff > TRACKING_CUTOFF:
            tracking_message = (
                f"✅ Tracking stopped for {badge['name']} because you get the point. "
                f"It increased by {awarded_diff} since tracking began (from {previous_count} to {current_count})."
            )
            send_to_discord(tracking_message)

            # Mark this badge as stopped tracking
            badge["trackingStopped"] = True

    # Save the updated badge data
    save_badge_data(badge_data)

# Send a message to Discord channel
def send_to_discord(message):
    channel = client.get_channel(int(CHANNEL_ID))
    if channel:
        asyncio.create_task(channel.send(message))

# Task to periodically check and send badge updates
@tasks.loop(seconds=15)  # Every 15 seconds
async def check_badge_updates():
    track_badge_updates()

# On bot startup
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    check_badge_updates.start()  # Start the loop when the bot is ready

# Start the bot
client.run(DISCORD_TOKEN)
