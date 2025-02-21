import discord
from discord.ext import commands
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord import FFmpegPCMAudio
import logging
from cogs.utils import censor_text

logger = logging.getLogger(__name__)

# Load Spotify credentials from environment variables.
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Initialize the Spotify client using client credentials flow.
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

class Music(commands.Cog):
    """Music playback and queue commands using Spotify and FFmpeg for audio streaming."""
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.queue = asyncio.Queue()
        self.play_next_song = asyncio.Event()
        self.current_track = None
        self.loop = False
        logger.info("Music cog initialized.")
        # Start the player loop as a background task.
        self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        logger.info("Player loop started.")
        while True:
            self.play_next_song.clear()
            self.current_track = await self.queue.get()
            logger.info(f"Track dequeued: {self.current_track['title']}")
            if self.voice_client is not None:
                source = FFmpegPCMAudio(self.current_track['url'])
                self.voice_client.play(source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next_song.set))
                channel = self.current_track.get('channel')
                if channel:
                    await channel.send(f"Now playing: **{self.current_track['title']}**")
                logger.info(f"Playing track: {self.current_track['title']}")
                await self.play_next_song.wait()
                if self.loop:
                    logger.info("Loop enabled, re-queuing track.")
                    await self.queue.put(self.current_track)
            else:
                logger.warning("Voice client not connected, skipping track.")

    @commands.command(name="join")
    async def join(self, ctx):
        """Joins the voice channel of the command invoker."""
        logger.info(f"Join command invoked by {ctx.author}.")
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_client = await channel.connect()
            await ctx.send(f"Joined **{channel.name}**.")
            logger.info(f"Connected to voice channel: {channel.name}")
        else:
            await ctx.send("You need to be in a voice channel to summon me.")
            logger.warning("Join command: user not in voice channel.")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Leaves the voice channel."""
        logger.info(f"Leave command invoked by {ctx.author}.")
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await ctx.send("Left the voice channel.")
            logger.info("Disconnected from voice channel.")
        else:
            await ctx.send("I'm not in a voice channel.")
            logger.warning("Leave command: not in voice channel.")

    @commands.command(name="play")
    async def play(self, ctx, *, query: str):
        """
        Play a song from Spotify.
        Example: !play song name or Spotify URL.
        Note: This uses Spotify search; a real stream URL may require additional integration.
        """
        logger.info(f"Play command invoked by {ctx.author} with query: {query}")
        try:
            results = sp.search(q=query, type='track', limit=1)
            tracks = results.get('tracks', {}).get('items', [])
            if not tracks:
                await ctx.send("No track found on Spotify.")
                logger.info("No track found for query: " + query)
                return
            track = tracks[0]
            track_title = f"{track['name']} - {track['artists'][0]['name']}"
            playable_url = track['external_urls']['spotify']  # Placeholder URL
            track_info = {
                'title': censor_text(track_title),
                'url': playable_url,
                'channel': ctx.channel
            }
            await self.queue.put(track_info)
            await ctx.send(f"Queued: **{track_info['title']}**")
            logger.info("Queued track: " + track_info['title'])
        except Exception as e:
            await ctx.send("An error occurred while retrieving the track.")
            logger.exception("Error in play command: " + str(e))

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pauses the current track."""
        logger.info(f"Pause command invoked by {ctx.author}.")
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("Paused the track.")
            logger.info("Track paused.")
        else:
            await ctx.send("No track is playing.")
            logger.warning("Pause command: no track is playing.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resumes the paused track."""
        logger.info(f"Resume command invoked by {ctx.author}.")
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("Resumed the track.")
            logger.info("Track resumed.")
        else:
            await ctx.send("The track is not paused.")
            logger.warning("Resume command: track not paused.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skips the current track."""
        logger.info(f"Skip command invoked by {ctx.author}.")
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send("Skipped the track.")
            logger.info("Track skipped.")
        else:
            await ctx.send("No track is playing.")
            logger.warning("Skip command: no track playing.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops playback and clears the queue."""
        logger.info(f"Stop command invoked by {ctx.author}.")
        if self.voice_client:
            self.queue = asyncio.Queue()
            self.voice_client.stop()
            await ctx.send("Stopped playback and cleared the queue.")
            logger.info("Playback stopped and queue cleared.")
        else:
            await ctx.send("I'm not in a voice channel.")
            logger.warning("Stop command: not in voice channel.")

    @commands.command(name="loop")
    async def loop_command(self, ctx):
        """Toggles looping of the current track."""
        self.loop = not self.loop
        status = "enabled" if self.loop else "disabled"
        await ctx.send(f"Looping is now {status}.")
        logger.info(f"Loop toggled to: {status} by {ctx.author}.")

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """Displays the current music queue."""
        logger.info(f"Queue command invoked by {ctx.author}.")
        if self.queue.empty():
            await ctx.send("The queue is empty.")
            logger.info("Queue is empty.")
        else:
            queue_list = list(self.queue._queue)
            message = "Upcoming tracks:\n"
            for idx, track in enumerate(queue_list, 1):
                message += f"{idx}. {track['title']}\n"
            await ctx.send(message)
            logger.info("Displayed music queue.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        """Shuffles the current queue."""
        logger.info(f"Shuffle command invoked by {ctx.author}.")
        import random
        queue_list = list(self.queue._queue)
        random.shuffle(queue_list)
        self.queue = asyncio.Queue()
        for item in queue_list:
            await self.queue.put(item)
        await ctx.send("Shuffled the queue.")
        logger.info("Queue shuffled.")

    @commands.command(name="volume")
    async def volume(self, ctx, vol: int):
        """
        Sets the volume.
        Example: !volume 50 sets volume to 50%.
        (Note: Volume control is a placeholder.)
        """
        logger.info(f"Volume command invoked by {ctx.author} with volume {vol}.")
        if 0 <= vol <= 100:
            await ctx.send(f"Volume set to {vol}% (placeholder).")
            logger.info("Volume set to " + str(vol))
        else:
            await ctx.send("Volume must be between 0 and 100.")
            logger.warning("Invalid volume: " + str(vol))

    @commands.command(name="nowplaying")
    async def now_playing(self, ctx):
        """Displays the currently playing track."""
        logger.info(f"NowPlaying command invoked by {ctx.author}.")
        if self.current_track:
            await ctx.send(f"Now playing: **{self.current_track['title']}**")
            logger.info("Now playing: " + self.current_track['title'])
        else:
            await ctx.send("No track is playing.")
            logger.info("NowPlaying command: no track playing.")

    @commands.command(name="eq")
    async def eq(self, ctx, *, settings: str):
        """
        Adjusts the equalizer settings.
        Example: !eq bass+5 treble-3.
        (Placeholder for equalizer functionality.)
        """
        logger.info(f"EQ command invoked by {ctx.author} with settings: {settings}")
        await ctx.send(f"Equalizer settings updated: {settings}")
        logger.info("EQ settings updated.")

async def setup(bot):
    await bot.add_cog(Music(bot))
