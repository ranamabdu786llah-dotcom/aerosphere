"""
sessions.py - Multiple chat sessions ko save/load karta hai (jaise ChatGPT mein "New Chat").
Har session ek alag JSON file mein save hoti hai "chats" folder ke andar.
"""

import os
import json
import time

CHATS_DIR = "chats"


def _ensure_dir():
    os.makedirs(CHATS_DIR, exist_ok=True)


def list_sessions() -> list:
    """Saare saved sessions ki list deta hai, sabse naya sabse pehle."""
    _ensure_dir()
    files = [f for f in os.listdir(CHATS_DIR) if f.endswith(".json")]
    sessions = []
    for f in files:
        path = os.path.join(CHATS_DIR, f)
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            sessions.append({
                "id": f[:-5],
                "title": data.get("title", "Untitled"),
                "updated": data.get("updated", 0),
            })
        except Exception:
            continue
    sessions.sort(key=lambda s: s["updated"], reverse=True)
    return sessions


def load_session(session_id: str) -> list:
    _ensure_dir()
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("messages", [])


def save_session(session_id: str, messages: list):
    _ensure_dir()
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    title = "New chat"
    for m in messages:
        if m["role"] == "user":
            title = m["content"][:40]
            break
    data = {"title": title, "updated": time.time(), "messages": messages}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def new_session_id() -> str:
    return str(int(time.time() * 1000))


def delete_session(session_id: str):
    path = os.path.join(CHATS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)