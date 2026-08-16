"""
docs.py - PDF aur text files se content nikalta hai (NotebookLM jaisa feature).
"""

import io
from pypdf import PdfReader


def extract_text(uploaded_file) -> str:
    """Streamlit ke uploaded_file object se text nikalta hai."""
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text.strip()

    if name.endswith(".txt") or name.endswith(".md"):
        return data.decode("utf-8", errors="ignore")

    return ""