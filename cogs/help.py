import discord
from discord.ext import commands
import os
import logging

logger = logging.getLogger(__name__)

REPO_LINK = os.getenv("REPO_LINK", "https://github.com/yourusername/DiscordMusicBot")

class HelpCog(commands.Cog):
    """Provides detailed help information for the bot commands."""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Help cog initialized.")

    @commands.command(name="help")
    async def help_command(self, ctx, topic: str = None):
        """
        Displays help information.
        
        Usage: 
          !help             - Displays general help.
          !help ai          - Displays help for AI conversation commands.
          !help music       - Displays help for music commands.
          !help repo        - Displays help for the repository command.
        """
        if topic is None:
            embed = discord.Embed(
                title="Bot General Help",
                description=(
                    "Use `!help <topic>` for detailed information on a specific topic.\n"
                    "Available topics: `ai`, `music`, `repo`."
                ),
                color=discord.Color.blue()
            )
            embed.add_field(name="AI Commands", value="Use `!help ai` for details on chatting with the AI.", inline=False)
            embed.add_field(name="Music Commands", value="Use `!help music` for details on playing music.", inline=False)
            embed.add_field(name="Repository", value="Use `!help repo` for info on the repo command.", inline=False)
            embed.set_footer(text="For more info, ask the owner!")
            await ctx.send(embed=embed)
            logger.info("General help command invoked by %s", ctx.author)
        else:
            topic = topic.lower()
            if topic == "ai":
                embed = discord.Embed(
                    title="AI Commands Help",
                    description=(
                        "**!chat** or **!ai**: Engage in a conversation with the AI.\n"
                        "Example: `!chat How's it going, you crazy bastard?`\n\n"
                        "**!setmeme <context>**: Change the AI's personality context.\n"
                        "Example: `!setmeme I want you to be extra unhinged and real.`\n\n"
                        "You can also mention the bot (e.g. `@Duck jammie Tell me something wild!`) to start a conversation."
                    ),
                    color=discord.Color.green()
                )
                embed.set_footer(text="Brace yourself—this AI is as unhinged as they come!")
                await ctx.send(embed=embed)
                logger.info("AI help command invoked by %s", ctx.author)
            elif topic == "music":
                embed = discord.Embed(
                    title="Music Commands Help",
                    description=(
                        "**!join**: Make the bot join your voice channel.\n"
                        "**!play <query>**: Play a song from Spotify. Example: `!play Never Gonna Give You Up`.\n"
                        "**!pause** / **!resume**: Pause or resume the current track.\n"
                        "**!skip**: Skip the current track.\n"
                        "**!queue**: Show the current song queue.\n"
                        "**!shuffle**: Shuffle the song queue.\n"
                        "**!nowplaying**: Display the currently playing track."
                    ),
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Rock on!")
                await ctx.send(embed=embed)
                logger.info("Music help command invoked by %s", ctx.author)
            elif topic == "repo":
                embed = discord.Embed(
                    title="Repository Help",
                    description=(
                        "Use the **!repo** command to get the link to the bot's source code.\n"
                        "Example: `!repo`"
                    ),
                    color=discord.Color.orange()
                )
                embed.set_footer(text="Contribute or check out the source code!")
                await ctx.send(embed=embed)
                logger.info("Repo help command invoked by %s", ctx.author)
            else:
                await ctx.send("Sorry, I don't have help information for that topic. Try `ai`, `music`, or `repo`.")
                logger.info("Help command invoked with unknown topic '%s' by %s", topic, ctx.author)

    @commands.command(name="repo")
    async def repo_command(self, ctx):
        """Displays the repository link for this bot."""
        await ctx.send(f"Check out the repository here: {REPO_LINK}")
        logger.info("Repo command invoked by %s", ctx.author)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
