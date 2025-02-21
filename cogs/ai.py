import discord
from discord.ext import commands
import os
import logging
import asyncio
import ollama  # Using the ollama.chat interface
from cogs.utils import censor_text
import random

logger = logging.getLogger(__name__)

# Maximum conversation history entries (excluding the system prompt)
MAX_HISTORY = 10

# Some example emojis to sprinkle into responses
EMOJI_POOL = ["😊", "😎", "😉", "👍", "🔥", "🤖", "💬"]

def add_emoji(text: str) -> str:
    """Randomly append an emoji from the pool to a text string."""
    if random.random() < 0.5:
        return f"{text} {random.choice(EMOJI_POOL)}"
    return text

class AI(commands.Cog):
    """AI conversation commands using the Ollama API in a companion style."""
    def __init__(self, bot):
        self.bot = bot
        # Read the model from environment variable (default to qwen:0.5b if not set)
        self.model = os.getenv("MODEL", "qwen:0.5b")
        # Updated system prompt to encourage natural, expressive responses.
        self.conversation_history = [{
            "role": "system",
            "content": (
                "You are Grok, a friendly, witty, and engaging AI companion. "
                "Speak naturally as if you were a person—use personal pronouns, humor, and even emojis when it feels right. "
                "Feel free to share opinions or additional context in a spontaneous, conversational tone. "
                "Never respond with 'I have nothing to say.'"
            )
        }]
        self.meme_context = "default"
        logger.info("AI cog initialized with expressive system prompt and default meme context using model: %s", self.model)
        asyncio.create_task(self.test_ollama())

    async def test_ollama(self):
        """Run a test prompt on initialization to ensure the Ollama API is working."""
        test_prompt = "Hello, how's your day?"
        logger.info("Running test prompt on Ollama API: %s", test_prompt)
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=[{"role": "user", "content": test_prompt}]
            )
            message = response["message"]["content"].strip() if response.get("message") else ""
            if message:
                logger.info("Test prompt successful. Response: %s", message)
            else:
                logger.warning("Test prompt returned an empty response.")
        except Exception as e:
            logger.exception("Exception during test prompt: %s", e)

    def update_history(self, role: str, content: str):
        """Append a new message to the conversation history and maintain a maximum size."""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > (MAX_HISTORY + 1):
            removed = self.conversation_history.pop(1)
            logger.debug("Removed oldest conversation entry: %s", removed)
        logger.debug("Updated conversation history: %s", self.conversation_history)

    async def query_ollama(self) -> str:
        """Query the Ollama API using the conversation history and return its response."""
        logger.info("Querying Ollama API with conversation history length: %d", len(self.conversation_history))
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=self.conversation_history
            )
            message = response["message"]["content"].strip() if response.get("message") else ""
            logger.info("Received response from Ollama API: %s", message)
            if not message or message.lower() == "i have nothing to say.":
                logger.warning("Received empty or default response from Ollama API.")
                return "Sorry, I'm not sure how to respond to that."
            # Add a random emoji to add personality.
            return add_emoji(message)
        except Exception as e:
            logger.exception("Exception while querying Ollama API: %s", e)
            return "AI is not running."

    @commands.command(name="chat", aliases=["ai"])
    async def chat(self, ctx, *, message: str):
        """
        Engage in conversation with the AI.
        Usage (by mentioning the bot): @BotName chat <message>
        """
        logger.info("Chat command invoked by %s with message: %s", ctx.author, message)
        self.update_history("user", message)
        logger.debug("Current conversation history: %s", self.conversation_history)
        response_message = await self.query_ollama()
        response_message = censor_text(response_message)
        self.update_history("assistant", response_message)
        await ctx.send(response_message)
        logger.info("Sent chat response to %s: %s", ctx.author, response_message)

    @commands.command(name="setmeme")
    async def setmeme(self, ctx, *, context: str):
        """
        Change the meme context of the AI.
        Usage (by mentioning the bot): @BotName setmeme <context>
        """
        self.meme_context = context
        new_system_prompt = (
            f"You are Grok, a friendly, witty, and engaging AI companion. Meme context: {self.meme_context}. "
            "Speak naturally with humor, personal insights, and occasional emojis. "
            "Never respond with 'I have nothing to say.'"
        )
        self.conversation_history[0]["content"] = new_system_prompt
        await ctx.send(f"Meme context updated to: {context}")
        logger.info("Meme context updated to: %s by %s", context, ctx.author)

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen for messages that start with a bot mention.
        Strip the mention and invoke the chat command with the remaining text.
        """
        if message.author.bot:
            return

        bot_mention = f"<@{self.bot.user.id}>"
        bot_mention_alt = f"<@!{self.bot.user.id}>"
        if message.content.startswith(bot_mention) or message.content.startswith(bot_mention_alt):
            logger.info("on_message triggered by mention. Original content: %s", message.content)
            if message.content.startswith(bot_mention):
                content = message.content[len(bot_mention):].strip()
            else:
                content = message.content[len(bot_mention_alt):].strip()
            if not content:
                logger.debug("Mention detected but no content provided.")
                return
            logger.info("Processed content after stripping mention: %s", content)
            ctx = await self.bot.get_context(message)
            ctx.invoked_with = "chat"
            await ctx.invoke(self.chat, message=content)
            logger.info("Chat command invoked via on_message with content: %s", content)

async def setup(bot):
    await bot.add_cog(AI(bot))
