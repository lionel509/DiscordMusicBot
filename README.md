# Discord Music & AI Bot

This bot integrates music playback (via Spotify and FFMPEG) with AI-powered conversations using Ollama’s Qwen:0.5b model.

## Features

### Music Bot Features
- **Play music from Spotify:** Search for tracks, playlists, or albums.
- **Queue system:** Commands for play, pause, resume, skip, stop, loop, clear, shuffle, and show queue.
- **Volume control & Now Playing:** Display current track information.
- **Voice channel management:** Join and leave voice channels.
- **Additional features:** You can extend with commands like lyrics, search by artist, etc.

### AI Conversation Features
- **AI Chat:** Engage in natural language conversation using Ollama’s Qwen:0.5b model.
- **Memory management:** Maintains recent conversation history (configurable via `AI_MEMORY_LIMIT`).
- **Command integration:** AI can be instructed to perform music bot functions (e.g., “play some music”).
- **Grok-like personality:** The AI is direct, irreverent, humorous, and sarcastic.
- **Self-censorship:** Swear words are replaced with asterisks.
- **Meme context:** Change the AI’s personality with the `!setcontext` command.

## Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/discord_music_bot.git
cd discord_music_bot
```

2. **Create a virtual environment and install dependencies:**
```bash
python -m venv venv
# For Linux/macOS:
source venv/bin/activate 
# For Windows:
venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure Environment Variables:**

Copy .env.example to .env and fill in your credentials:
```bash
cp .env.example .env
```

4. **Set Up Ollama & Qwen:0.5b Model:**

Follow Ollama’s documentation to download and host the Qwen:0.5b model.
Ensure the OLLAMA_API_URL in your .env file points to your Ollama endpoint.

5. **Run the Bot:**
```bash
python main.py
```

6. **Docker Setup:**

- Build the Docker image:
```bash
docker build -t discord-music-ai-bot .
```
- Run the container:
```bash
docker run -d --env-file .env discord-music-ai-bot
```

7. **Changing the AI Meme Context**

Use the command !setcontext <new context prompt> in Discord.
This will update the AI’s personality prompt on the fly.

8. **Handling Rate Limits and Conversation History**

- Rate Limits: The code uses basic error handling. For production use, consider adding retries and back-off strategies.
- Conversation Memory: The AI stores the last few messages (default 10). Adjust the AI_MEMORY_LIMIT in the .env file to suit your needs.

9. **Additional Music Bot Features to Consider**
- Lyrics lookup.
- Playlist management.
- User-specific queues.
- Music recommendations.
- Integration with other music APIs.
- Customizable command prefixes.
