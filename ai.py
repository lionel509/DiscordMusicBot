# ai.py
import os
import re
import requests
import logging

class AIChat:
    """Handles AI-powered conversations using Ollama's Qwen:0.5b model."""
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_API_URL")
        self.memory = []  # List of recent conversation messages (tuples of (role, message))
        self.memory_limit = int(os.getenv("AI_MEMORY_LIMIT", "10"))
        self.system_prompt = (
            "You are Grok, a direct, irreverent, humorous, and sarcastic AI. "
            "Answer succinctly and with a touch of dry wit. Do not use strong language; "
            "if needed, replace swear words with asterisks."
        )

    def update_memory(self, role: str, message: str):
        """Stores a message in the conversation memory and maintains its size."""
        self.memory.append((role, message))
        if len(self.memory) > self.memory_limit:
            self.memory.pop(0)

    def self_censor(self, text: str) -> str:
        """Replaces strong language with asterisks."""
        # Example: simple censorship of a few words (expand as needed)
        censored = re.sub(r'\b(fuck|shit|damn)\b', lambda m: '*' * len(m.group()), text, flags=re.IGNORECASE)
        return censored

    def format_conversation(self):
        """Formats the conversation memory to send to the AI API."""
        conversation = [{"role": "system", "content": self.system_prompt}]
        for role, message in self.memory:
            conversation.append({"role": role, "content": message})
        return conversation

    def chat(self, prompt: str) -> str:
        """Sends a conversation prompt to Ollama and returns the AI's response."""
        # Update memory with the user prompt
        self.update_memory("user", prompt)
        conversation = self.format_conversation()
        payload = {"messages": conversation}

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            ai_response = data.get("response", "")
            # Censor the AI response before returning
            ai_response = self.self_censor(ai_response)
            self.update_memory("assistant", ai_response)
            return ai_response
        except Exception as e:
            logging.error(f"Ollama API error: {e}")
            return "Sorry, I'm having trouble processing that right now."

    def set_meme_context(self, new_context: str):
        """Allows the user to change the AI's meme context (personality prompt)."""
        self.system_prompt = new_context
        # Reset memory if needed
        self.memory.clear()
