# commands.py
import discord
from discord.ext import commands
from music import MusicPlayer
from ai import AIChat
import asyncio

# Dictionary to keep track of MusicPlayer instances per guild
music_players = {}

class MusicCommands(commands.Cog):
    """Commands for music playback."""
    def __init__(self, bot):
        self.bot = bot

    def get_player(self, ctx):
        """Gets or creates a MusicPlayer instance for the guild."""
        guild_id = ctx.guild.id
        if guild_id not in music_players:
            if ctx.author.voice and ctx.author.voice.channel:
                music_players[guild_id] = MusicPlayer(self.bot, ctx.author.voice.channel)
            else:
                return None
        return music_players[guild_id]

    @commands.command(name="join")
    async def join(self, ctx):
        """Joins the voice channel."""
        player = self.get_player(ctx)
        if not player:
            await ctx.send("You must be in a voice channel first!")
            return
        await player.join()
        await ctx.send(f"Joined {player.voice_channel.name}")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Leaves the voice channel."""
        player = self.get_player(ctx)
        if player:
            await player.leave()
            await ctx.send("Left the voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        """Plays a song from Spotify. (For demo purposes, uses preview URL if available.)"""
        player = self.get_player(ctx)
        if not player:
            await ctx.send("You must be in a voice channel first!")
            return

        # Search Spotify for the track preview URL
        url = player.search_spotify(query, search_type='track')
        if not url:
            await ctx.send("Could not find the track or no preview available.")
            return
        # Add to queue and start playing if not already
        player.add_to_queue(url)
        if not player.voice_client or not player.voice_client.is_playing():
            await player._play_next()
        await ctx.send(f"Queued track: {query}")

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pauses the current track."""
        player = self.get_player(ctx)
        if player:
            player.pause()
            await ctx.send("Paused playback.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resumes playback."""
        player = self.get_player(ctx)
        if player:
            player.resume()
            await ctx.send("Resumed playback.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skips the current track."""
        player = self.get_player(ctx)
        if player:
            player.skip()
            await ctx.send("Skipped track.")

    @commands.command(name="queue")
    async def queue(self, ctx):
        """Displays the current music queue."""
        player = self.get_player(ctx)
        if player:
            q = player.get_queue()
            if q:
                await ctx.send("Queue:\n" + "\n".join(q))
            else:
                await ctx.send("The queue is empty.")

    @commands.command(name="nowplaying")
    async def nowplaying(self, ctx):
        """Displays the currently playing track."""
        player = self.get_player(ctx)
        if player and player.now_playing():
            await ctx.send(f"Now playing: {player.now_playing()}")
        else:
            await ctx.send("Nothing is playing currently.")

    @commands.command(name="loop")
    async def loop(self, ctx):
        """Toggles loop mode."""
        player = self.get_player(ctx)
        if player:
            status = player.toggle_loop()
            await ctx.send(f"Loop mode is now {'enabled' if status else 'disabled'}.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Shuffles the current queue."""
        player = self.get_player(ctx)
        if player:
            player.shuffle_queue()
            await ctx.send("Queue shuffled.")

class AICommands(commands.Cog):
    """Commands for AI-powered conversations."""
    def __init__(self, bot):
        self.bot = bot
        self.ai_chat = AIChat()

    @commands.command(name="chat")
    async def chat(self, ctx, *, message: str):
        """
        Engage in conversation with the AI.
        Usage: !chat How's it going?
        """
        await ctx.send("Thinking...")
        response = await self.bot.loop.run_in_executor(None, self.ai_chat.chat, message)
        await ctx.send(response)

    @commands.command(name="setcontext")
    async def set_context(self, ctx, *, new_context: str):
        """
        Changes the AI's meme context (personality prompt).
        Usage: !setcontext [new context prompt]
        """
        self.ai_chat.set_meme_context(new_context)
        await ctx.send("AI context updated.")
