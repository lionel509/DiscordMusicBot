# main.py
import os
import logging
from discord.ext import commands
from dotenv import load_dotenv
from commands import MusicCommands, AICommands

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

logging.basicConfig(level=logging.INFO)

# Initialize the bot with the chosen prefix
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=commands.Intents.all())

# Register cogs
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logging.info("------")

bot.add_cog(MusicCommands(bot))
bot.add_cog(AICommands(bot))

# Start the bot
bot.run(DISCORD_TOKEN)
