import re

SWEAR_WORDS = ["Fuck", "shit"]

def censor_text(text):
    """
    Censors strong language by replacing each character (except the first) with asterisks.
    """
    def replace(match):
        word = match.group()
        return word[0] + "*" * (len(word) - 1)
    pattern = re.compile("|".join(re.escape(word) for word in SWEAR_WORDS), re.IGNORECASE)
    return pattern.sub(replace, text)
