# music.py
import asyncio
import discord
import logging
import random
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import os

FFMPEG_OPTIONS = {
    'options': '-vn'
}

class MusicPlayer:
    """Handles music playback and queue management."""
    def __init__(self, bot: discord.Client, voice_channel: discord.VoiceChannel):
        self.bot = bot
        self.voice_channel = voice_channel
        self.voice_client: discord.VoiceClient = None
        self.queue = []
        self.current = None
        self.loop = False

        # Spotify setup
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        ))

    async def join(self):
        """Joins the voice channel."""
        if self.voice_channel and not self.voice_client:
            self.voice_client = await self.voice_channel.connect()
            logging.info(f"Joined {self.voice_channel}")

    async def leave(self):
        """Leaves the voice channel."""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            logging.info(f"Left {self.voice_channel}")

    async def play(self, source_url: str):
        """Plays an audio source from a given URL using FFMPEG."""
        if not self.voice_client:
            await self.join()
        def after_play(error):
            if error:
                logging.error(f"Error playing track: {error}")
            else:
                asyncio.run_coroutine_threadsafe(self._play_next(), self.bot.loop)
        audio_source = discord.FFmpegPCMAudio(source_url, **FFMPEG_OPTIONS)
        self.current = source_url
        self.voice_client.play(audio_source, after=after_play)
        logging.info(f"Now playing: {source_url}")

    async def _play_next(self):
        """Plays the next track in the queue."""
        if self.loop and self.current:
            self.queue.insert(0, self.current)
        if self.queue:
            next_url = self.queue.pop(0)
            await self.play(next_url)
        else:
            logging.info("Queue is empty.")

    def add_to_queue(self, source_url: str):
        """Adds a track to the queue."""
        self.queue.append(source_url)
        logging.info(f"Added to queue: {source_url}")

    def pause(self):
        """Pauses the current track."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()

    def resume(self):
        """Resumes playback."""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()

    def stop(self):
        """Stops playback and clears the queue."""
        if self.voice_client:
            self.voice_client.stop()
        self.queue.clear()

    def skip(self):
        """Skips the current track."""
        if self.voice_client:
            self.voice_client.stop()

    def toggle_loop(self):
        """Toggles loop mode."""
        self.loop = not self.loop
        return self.loop

    def shuffle_queue(self):
        """Shuffles the current queue."""
        random.shuffle(self.queue)

    def get_queue(self):
        """Returns a list of tracks in the queue."""
        return self.queue

    def now_playing(self):
        """Returns the current playing track."""
        return self.current

    def search_spotify(self, query: str, search_type='track'):
        """Searches Spotify for a track, album, or playlist."""
        try:
            results = self.spotify.search(q=query, type=search_type)
            items = results.get(f'{search_type}s', {}).get('items', [])
            if items:
                # For simplicity, return the preview_url if available
                track = items[0]
                preview_url = track.get('preview_url')
                if preview_url:
                    return preview_url
                # If no preview URL, you might want to use another method to stream the track
                return None
            return None
        except Exception as e:
            logging.error(f"Spotify search error: {e}")
            return None
