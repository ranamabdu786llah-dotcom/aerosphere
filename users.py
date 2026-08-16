"""
users.py - AeroSphere ka advanced login system.
Har user ka apna username/password hota hai, passwords hash karke store hote hain
(kabhi bhi plain text mein save nahi hote). Usage limits bhi har user ke account
ke saath judi hoti hain, sirf browser session ke saath nahi.
"""

import os
import json
import time
import hashlib
import secrets as secrets_module

USERS_FILE = "users.json"


def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str, salt: str) -> str:
    """Password ko salt ke saath hash karta hai - plain text kabhi save nahi hota."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()


def create_user(username: str, password: str) -> tuple:
    """Naya user banata hai. Returns (success: bool, message: str)."""
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password required."
    if len(password) < 4:
        return False, "Password should be at least 4 characters."

    users = _load_users()
    if username in users:
        return False, "This username is already taken."

    salt = secrets_module.token_hex(16)
    users[username] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
        "created_at": time.time(),
        "usage_count": 0,
        "image_count": 0,
        "usage_window_start": time.time(),
    }
    _save_users(users)
    return True, "Account created."


def verify_user(username: str, password: str) -> bool:
    """Login check karta hai."""
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return False
    user = users[username]
    return _hash_password(password, user["salt"]) == user["password_hash"]


def get_usage(username: str) -> dict:
    users = _load_users()
    username = username.strip().lower()
    if username not in users:
        return {"usage_count": 0, "image_count": 0, "usage_window_start": time.time()}
    return {
        "usage_count": users[username].get("usage_count", 0),
        "image_count": users[username].get("image_count", 0),
        "usage_window_start": users[username].get("usage_window_start", time.time()),
    }


def update_usage(username: str, usage_count: int = None, image_count: int = None, usage_window_start: float = None):
    users = _load_users()
    username = username.strip().lower()
    if username not in users:
        return
    if usage_count is not None:
        users[username]["usage_count"] = usage_count
    if image_count is not None:
        users[username]["image_count"] = image_count
    if usage_window_start is not None:
        users[username]["usage_window_start"] = usage_window_start
    _save_users(users)