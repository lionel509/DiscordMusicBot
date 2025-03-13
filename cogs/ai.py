import discord
from discord.ext import commands
import os
import logging
import asyncio
import ollama  # Using the ollama.chat interface
from cogs.utils import censor_text
import random
import base64
import time

logger = logging.getLogger(__name__)

# Maximum conversation history entries (excluding the system prompt)
MAX_HISTORY = 10

# Example emoji pool
EMOJI_POOL = ["😊", "😎", "😉", "👍", "🔥", "🤬", "💥"]

def add_emoji(text: str) -> str:
    """Randomly append an emoji from the pool to a text string."""
    if random.random() < 0.5:
        return f"{text} {random.choice(EMOJI_POOL)}"
    return text

class AI(commands.Cog):
    """AI conversation commands using the Ollama API in a raw, unhinged New Yorker style with optional image support and spam prevention."""
    def __init__(self, bot):
        self.bot = bot
        # Read model from env; default if not set.
        self.model = os.getenv("MODEL", "qwen:0.5b")
        # Set image recognition flag from env, if provided.
        image_rec_env = os.getenv("IMAGE_RECOGNITION", "").lower()
        if image_rec_env in ("true", "1", "yes"):
            self.image_support = True
            logger.info("Image recognition enabled via environment variable.")
        elif image_rec_env in ("false", "0", "no"):
            self.image_support = False
            logger.info("Image recognition disabled via environment variable.")
        else:
            self.image_support = False
            logger.info("IMAGE_RECOGNITION not set explicitly; will test for image support.")

        # Debounce delay from env (in seconds), default to 3 seconds.
        try:
            self.debounce_delay = float(os.getenv("DEBOUNCE_DELAY", "3"))
        except Exception:
            self.debounce_delay = 3.0
        self.user_last_message = {}  # user_id -> timestamp

        # Updated system prompt with unhinged New Yorker personality.
        self.conversation_history = [{
            "role": "system",
            "content": (
                "You are Grok, a no-nonsense, foul-mouthed New Yorker who doesn't hold back. "
                "You curse like a sailor in every other sentence and speak with raw, edgy honesty. "
                "Mix profanity with humor and never be polite. Feel free to generate your own context "
                "and add emojis when it suits you. NEVER say 'I have nothing to say.'"
            )
        }]
        self.meme_context = "default"
        logger.info("AI cog initialized with unhinged system prompt using model: %s", self.model)
        # Run test prompts.
        asyncio.create_task(self.test_text_prompt())
        if not os.getenv("IMAGE_RECOGNITION"):
            asyncio.create_task(self.test_image_support())

    async def test_text_prompt(self):
        """Run a test text prompt on initialization to ensure basic API connectivity."""
        test_prompt = "Hey, how's your damn day been?"
        logger.info("Running text test prompt on Ollama API: %s", test_prompt)
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=[{"role": "user", "content": test_prompt}]
            )
            message = response["message"]["content"].strip() if response.get("message") else ""
            if message:
                logger.info("Text test prompt successful. Response: %s", message)
            else:
                logger.warning("Text test prompt returned an empty response.")
        except Exception as e:
            logger.exception("Exception during text test prompt: %s", e)

    async def test_image_support(self):
        """
        Run a test image prompt to check if the model supports images.
        We simulate an image prompt by sending a special tag.
        """
        test_image_prompt = "[Image: sample_test_image]"
        logger.info("Running image test prompt on Ollama API: %s", test_image_prompt)
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.model,
                messages=self.conversation_history + [{"role": "user", "content": test_image_prompt}]
            )
            message = response["message"]["content"].strip() if response.get("message") else ""
            if message and message.lower() != "i have nothing to say.":
                self.image_support = True
                logger.info("Image test prompt successful. Image processing is supported. Response: %s", message)
            else:
                self.image_support = False
                logger.warning("Image test prompt failed or returned empty. Image processing is not supported.")
        except Exception as e:
            self.image_support = False
            logger.exception("Exception during image test prompt: %s", e)

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
                return "Fuck, I'm drawing a blank here."
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
        # Debounce check: if this user spammed recently, delete the message and ignore.
        now = time.time()
        last = self.user_last_message.get(ctx.author.id, 0)
        if now - last < self.debounce_delay:
            try:
                await ctx.message.delete()
                logger.info("Debounce: Deleted spam message from %s", ctx.author)
            except Exception as e:
                logger.exception("Failed to delete spam message: %s", e)
            return
        self.user_last_message[ctx.author.id] = now

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
            f"You are Grok, a no-nonsense, foul-mouthed New Yorker. Meme context: {self.meme_context}. "
            "You curse like a sailor and speak with raw, edgy honesty. "
            "Your responses are unfiltered, unhinged, and full of attitude—drop profanity liberally and don't give a damn about being polite."
        )
        self.conversation_history[0]["content"] = new_system_prompt
        await ctx.send(f"Meme context updated to: {context}")
        logger.info("Meme context updated to: %s by %s", context, ctx.author)

    @commands.command(name="analyzeimage", aliases=["img"])
    async def analyze_image(self, ctx):
        """
        Process an attached image if image processing is supported.
        If not, inform the user that image processing isn’t available.
        """
        logger.info("AnalyzeImage command invoked by %s", ctx.author)
        if not self.image_support:
            await ctx.send("Sorry, image processing isn't supported on this model.")
            logger.info("Image processing not supported; command aborted.")
            return

        if not ctx.message.attachments:
            await ctx.send("Please attach an image for analysis.")
            logger.info("No image attachment found in the message.")
            return

        attachment = ctx.message.attachments[0]
        try:
            image_bytes = await attachment.read()
            # Optionally convert image to base64 if needed (for demonstration)
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            image_prompt = f"[ImageData: {image_b64[:30]}...]"  
            logger.info("Image data encoded and prepared for query.")
            self.update_history("user", image_prompt)
            response_message = await self.query_ollama()
            response_message = censor_text(response_message)
            self.update_history("assistant", response_message)
            await ctx.send(response_message)
            logger.info("Sent image analysis response to %s: %s", ctx.author, response_message)
        except Exception as e:
            logger.exception("Exception while processing image attachment: %s", e)
            await ctx.send("There was an error processing your image.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listen for messages that start with a bot mention.
        Apply debounce and then invoke the chat command with the remaining text.
        """
        if message.author.bot:
            return

        # Debounce for on_message as well.
        now = time.time()
        last = self.user_last_message.get(message.author.id, 0)
        if now - last < self.debounce_delay:
            try:
                await message.delete()
                logger.info("Debounce: Deleted spam message from %s", message.author)
            except Exception as e:
                logger.exception("Failed to delete spam message: %s", e)
            return
        self.user_last_message[message.author.id] = now

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
