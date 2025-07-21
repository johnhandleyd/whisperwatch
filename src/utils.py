import re
import os

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove markdown artifacts and brackets
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)  # markdown links
    text = re.sub(r"[`\*\[\]\(\)]", "", text)   # loose markdown
    text = re.sub(r"\n+", "\n", text)

    # Remove Reddit-specific patterns
    text = re.sub(r"r\/\w+", "", text)
    text = re.sub(r"u\/\w+", "", text)
    text = re.sub(r"&amp;#x200B;", "", text)

    # Remove extra whitespace and short leftovers
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()

    return text

def ensure_all_dirs():
    for var, val in globals().items():
        # Regex: variable name ends with "DIR" (case insensitive)
        if re.search(r'DIR$', var, re.IGNORECASE):
            if isinstance(val, str):  # Only handle string paths
                os.makedirs(val, exist_ok=True)