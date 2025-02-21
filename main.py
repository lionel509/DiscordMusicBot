import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("main")

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = "!"

# New environment variables
OWNER_ID = os.getenv("OWNER_ID")
MODEL = os.getenv("MODEL")

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

# Create the bot instance.
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# List of extensions to load.
extensions = ['cogs.music', 'cogs.ai']

async def load_extensions():
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"Loaded extension '{ext}'")
        except Exception as e:
            logger.exception(f"Failed to load extension {ext}: {e}")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    # Notify the owner via DM that the bot has started.
    if OWNER_ID:
        owner = await bot.fetch_user(int(OWNER_ID))
        if owner:
            try:
                await owner.send(f"Hey, your bot **{bot.user.name}** has started using model **{MODEL}**!")
                logger.info(f"Sent startup notification DM to owner (ID: {OWNER_ID}).")
            except Exception as e:
                logger.exception(f"Failed to send DM to owner: {e}")
        else:
            logger.warning("Owner not found.")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot is shutting down due to KeyboardInterrupt.")
