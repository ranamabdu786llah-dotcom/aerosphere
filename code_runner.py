"""
code_runner.py - Python code ko chala kar output deta hai.
Sirf apna khud ka code chalane ke liye use karo, kisi anjaan source ka code yahan mat chalana.
"""

import subprocess
import sys
import tempfile
import os


def run_python(code: str, timeout: int = 10):
    """Code ko ek temporary file mein likh ke chalata hai. Returns (stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        path = f.name

    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return "", f"Code {timeout} seconds se zyada chal raha tha, isliye rok diya gaya."
    finally:
        os.remove(path)