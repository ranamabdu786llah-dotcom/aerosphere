"""
memory.py - Har user ke liye persistent memory notes.
User khud kuch important baatein save kar sakta hai (jaise preferences, projects),
jo har chat mein AI ko automatically context ke roop mein milti hain.
"""

import os
import json

MEMORY_FILE = "memory_notes.json"


def _load_all() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_all(data: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_notes(username: str) -> list:
    data = _load_all()
    return data.get(username, [])


def add_note(username: str, note: str):
    data = _load_all()
    if username not in data:
        data[username] = []
    data[username].append(note.strip())
    _save_all(data)


def delete_note(username: str, index: int):
    data = _load_all()
    if username in data and 0 <= index < len(data[username]):
        data[username].pop(index)
        _save_all(data)


def notes_as_text(username: str) -> str:
    """Notes ko ek text block mein jodta hai, system prompt mein daalne ke liye."""
    notes = get_notes(username)
    if not notes:
        return ""
    joined = "\n".join(f"- {n}" for n in notes)
    return f"Here are some things the user has asked you to remember about them:\n{joined}"