# utils.py
import re

def censor_text(text: str) -> str:
    """
    Replaces strong language with asterisks.
    Extend the list of words as needed.
    """
    censored = re.sub(r'\b(fuck|shit|damn)\b', lambda m: '*' * len(m.group()), text, flags=re.IGNORECASE)
    return censored
