"""
web_reader.py - Chat mein agar koi URL/link mile, uska content padh kar deta hai.
Isse AeroSphere kisi bhi website ke baare mein baat kar sakta hai jo user share kare.
"""

import re
import requests

URL_PATTERN = re.compile(r"https?://[^\s]+")


def find_url(text: str):
    """Text mein pehla URL dhoondta hai, agar ho to."""
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


def fetch_page_text(url: str, max_chars: int = 8000) -> str:
    """URL ka content fetch karke plain text nikalta hai (basic HTML cleanup ke saath)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (AeroSphere)"}
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text

        # Script/style tags hata do
        html = re.sub(r"<script.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        # Baaki saare HTML tags hata do
        text = re.sub(r"<[^>]+>", " ", html)
        # Extra whitespace saaf karo
        text = re.sub(r"\s+", " ", text).strip()

        return text[:max_chars]
    except Exception as e:
        return f"Could not read this page: {e}"