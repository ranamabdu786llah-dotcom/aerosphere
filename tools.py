"""
tools.py - Sidebar ke "Quick Tools" ke liye utility functions.
Currency converter, profit margin calculator, QR code generator, aur to-do list.
"""

import os
import json
import io
import requests
import qrcode

TODO_FILE = "todos.json"


# ------------------------------------------------------------
# Currency Converter (free, no API key - frankfurter.app use karta hai)
# ------------------------------------------------------------
def convert_currency(amount: float, from_currency: str, to_currency: str):
    try:
        url = f"https://api.frankfurter.app/latest?amount={amount}&from={from_currency}&to={to_currency}"
        response = requests.get(url, timeout=15)
        data = response.json()
        rate_value = data["rates"][to_currency]
        return rate_value, None
    except Exception as e:
        return None, str(e)


def get_currency_list():
    try:
        response = requests.get("https://api.frankfurter.app/currencies", timeout=15)
        return list(response.json().keys())
    except Exception:
        return ["USD", "EUR", "GBP", "PKR", "INR", "AED", "SAR", "CNY", "JPY", "AUD"]


# ------------------------------------------------------------
# Profit Margin Calculator
# ------------------------------------------------------------
def profit_margin(cost: float, selling_price: float):
    if selling_price == 0:
        return None, None
    profit = selling_price - cost
    margin_percent = (profit / selling_price) * 100
    markup_percent = (profit / cost) * 100 if cost != 0 else 0
    return profit, margin_percent, markup_percent


# ------------------------------------------------------------
# QR Code Generator
# ------------------------------------------------------------
def generate_qr(text: str) -> bytes:
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


# ------------------------------------------------------------
# To-Do List (simple local JSON storage)
# ------------------------------------------------------------
def load_todos() -> list:
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_todos(todos: list):
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(text: str):
    todos = load_todos()
    todos.append({"text": text, "done": False})
    save_todos(todos)


def toggle_todo(index: int):
    todos = load_todos()
    if 0 <= index < len(todos):
        todos[index]["done"] = not todos[index]["done"]
        save_todos(todos)


def delete_todo(index: int):
    todos = load_todos()
    if 0 <= index < len(todos):
        todos.pop(index)
        save_todos(todos)