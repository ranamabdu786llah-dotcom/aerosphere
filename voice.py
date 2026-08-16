"""
voice.py - Text ko awaaz (audio) mein badalta hai, gTTS se (bilkul free hai).
"""

import io
from gtts import gTTS


def text_to_speech(text: str, lang: str = "en") -> bytes:
    """Text ko mp3 audio bytes mein convert karta hai."""
    clean_text = text[:800]  # bohot lamba text na ho, isliye limit rakhi hai
    tts = gTTS(text=clean_text, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()