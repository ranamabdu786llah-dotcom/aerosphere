"""
AeroSphere - Premium AI Assistant
-------------------------------------------------------------
Chalane ke liye terminal mein likho:
    python -m streamlit run app.py

Features: Chat (with memory/sessions + web search + voice reply),
Document Q&A, Image Generator, Code Runner.
"""

import os
import time
import base64
from datetime import datetime
import streamlit as st
import requests
import urllib.parse
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder

import themes
import i18n
import sessions
import docs
import search
import voice
import code_runner
import tools
import web_reader
import users
import memory

load_dotenv()

# .env se key milti hai (local pe chalate waqt), ya st.secrets se (online deploy hone pe)
API_KEY = os.getenv("GEMINI_API_KEY", "")
if not API_KEY:
    try:
        API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        API_KEY = ""

# Public/online deploy hone pe Code Runner disable karne ke liye (security ke liye)
try:
    ENABLE_CODE_RUNNER = st.secrets.get("ENABLE_CODE_RUNNER", "true").lower() == "true"
except Exception:
    ENABLE_CODE_RUNNER = os.getenv("ENABLE_CODE_RUNNER", "true").lower() == "true"

st.set_page_config(page_title="AeroSphere", page_icon="\U0001F310", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# LOGIN / SIGNUP - har user ka apna account, usage limit account ke saath judi
# ------------------------------------------------------------
try:
    SIGNUP_CODE = st.secrets.get("SIGNUP_CODE", "")
except Exception:
    SIGNUP_CODE = os.getenv("SIGNUP_CODE", "")

if "username" not in st.session_state:
    st.session_state.username = None

if not st.session_state.username:
    st.markdown(
        """
        <div style="text-align:center; padding-top:60px; padding-bottom:20px;">
            <h1>\U0001F310 AeroSphere</h1>
            <p style="opacity:0.7;">Login or create an account to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        login_tab, signup_tab = st.tabs(["Login", "Sign up"])

        with login_tab:
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            if st.button("Log in", use_container_width=True, key="login_btn"):
                if users.verify_user(login_username, login_password):
                    st.session_state.username = login_username.strip().lower()
                    usage = users.get_usage(st.session_state.username)
                    st.session_state.usage_count = usage["usage_count"]
                    st.session_state.image_count = usage["image_count"]
                    st.session_state.usage_window_start = usage["usage_window_start"]
                    st.rerun()
                else:
                    st.error("Wrong username or password.")

        with signup_tab:
            signup_username = st.text_input("Choose a username", key="signup_username")
            signup_password = st.text_input("Choose a password", type="password", key="signup_password")
            if SIGNUP_CODE:
                signup_code_entered = st.text_input("Invite code", type="password", key="signup_code")
            else:
                signup_code_entered = ""
            if st.button("Create account", use_container_width=True, key="signup_btn"):
                if SIGNUP_CODE and signup_code_entered != SIGNUP_CODE:
                    st.error("Invalid invite code.")
                else:
                    success, message = users.create_user(signup_username, signup_password)
                    if success:
                        st.success(message + " You can now log in.")
                    else:
                        st.error(message)
    st.stop()

# AeroSphere ki apni identity - is se AI ko pata rahega ke usay kisne banaya
SYSTEM_INFO = (
    "You are AeroSphere, an AI assistant created and founded by Abdullah VSP. "
    "If the user asks who made you, who your founder or creator is, or similar questions, "
    "answer clearly that you were created by Abdullah VSP. "
    "Reply in the same language/style the user writes in (Hinglish, Urdu, English, etc)."
)

# ------------------------------------------------------------
# Session defaults
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = sessions.new_session_id()
if "language" not in st.session_state:
    st.session_state.language = "English"
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []
if "glow_enabled" not in st.session_state:
    st.session_state.glow_enabled = True
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "image_count" not in st.session_state:
    st.session_state.image_count = 0
if "usage_window_start" not in st.session_state:
    st.session_state.usage_window_start = time.time()

# Ek session ke liye limits - taake API quota safe rahe jab sab log bina apni key ke use karein
try:
    MAX_MESSAGES_PER_SESSION = int(st.secrets.get("MAX_MESSAGES_PER_SESSION", "90"))
    MAX_IMAGES_PER_SESSION = int(st.secrets.get("MAX_IMAGES_PER_SESSION", "8"))
    COOLDOWN_HOURS = float(st.secrets.get("COOLDOWN_HOURS", "3"))
except Exception:
    MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "90"))
    MAX_IMAGES_PER_SESSION = int(os.getenv("MAX_IMAGES_PER_SESSION", "8"))
    COOLDOWN_HOURS = float(os.getenv("COOLDOWN_HOURS", "3"))


def check_and_reset_usage_window():
    """Agar cooldown time guzar chuka hai, to limit reset kar do (chat/history waisi hi rehti hai)."""
    elapsed_hours = (time.time() - st.session_state.usage_window_start) / 3600
    if elapsed_hours >= COOLDOWN_HOURS:
        st.session_state.usage_count = 0
        st.session_state.image_count = 0
        st.session_state.usage_window_start = time.time()
        if st.session_state.username:
            users.update_usage(
                st.session_state.username,
                usage_count=0, image_count=0, usage_window_start=st.session_state.usage_window_start,
            )


check_and_reset_usage_window()

lang = st.session_state.language


def call_gemini(contents):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.5-flash-lite:generateContent?key={API_KEY}"
    )
    memory_text = memory.notes_as_text(st.session_state.username) if st.session_state.username else ""
    full_system = SYSTEM_INFO + ("\n\n" + memory_text if memory_text else "")
    body = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": full_system}]},
    }
    response = requests.post(url, json=body, timeout=45)
    data = response.json()
    if "candidates" in data:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    return "Error: " + data.get("error", {}).get("message", "Unknown error")


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.button("Log out", use_container_width=True):
        st.session_state.username = None
        st.session_state.messages = []
        st.session_state.doc_messages = []
        st.rerun()

    st.markdown("---")
    st.markdown(f"### {i18n.t(lang, 'settings')}")

    st.session_state.language = st.selectbox(
        i18n.t(lang, "language"), i18n.get_language_names(),
        index=i18n.get_language_names().index(st.session_state.language),
    )
    lang = st.session_state.language

    st.markdown("---")
    st.markdown(f"**{i18n.t(lang, 'theme')}**")
    category = st.radio("Category", themes.get_categories(), horizontal=True, label_visibility="collapsed")
    themes_in_cat = themes.get_themes_by_category(category)
    theme_choice = st.selectbox("Pick a theme", list(themes_in_cat.keys()), label_visibility="collapsed")

    with st.expander("Custom theme (import your own colors)"):
        c1, c2 = st.columns(2)
        with c1:
            bg = st.color_picker("Background", "#0A0A0F")
            surface = st.color_picker("Surface", "#15151C")
            accent = st.color_picker("Accent", "#7A63FF")
        with c2:
            text = st.color_picker("Text", "#EDEDF2")
            muted = st.color_picker("Muted text", "#8A8A96")
        use_custom = st.checkbox("Use custom theme")

    active_theme = themes.custom_theme(bg, surface, text, muted, accent) if use_custom else themes_in_cat[theme_choice]

    st.markdown("---")
    st.checkbox("Glow effect", key="glow_enabled")

    st.markdown("---")
    st.markdown(f"**{i18n.t(lang, 'quick_tools')}**")

    with st.expander(i18n.t(lang, "currency_converter")):
        curr_list = tools.get_currency_list()
        amt = st.number_input(i18n.t(lang, "amount"), min_value=0.0, value=100.0, step=1.0, key="curr_amt")
        c1, c2 = st.columns(2)
        with c1:
            from_curr = st.selectbox(i18n.t(lang, "from_label"), curr_list, index=curr_list.index("USD") if "USD" in curr_list else 0)
        with c2:
            to_curr = st.selectbox(i18n.t(lang, "to_label"), curr_list, index=curr_list.index("PKR") if "PKR" in curr_list else 0)
        if st.button(i18n.t(lang, "convert"), key="curr_btn"):
            result, err = tools.convert_currency(amt, from_curr, to_curr)
            if err:
                st.error(f"Error: {err}")
            else:
                st.success(f"{amt} {from_curr} = {result:.2f} {to_curr}")

    with st.expander(i18n.t(lang, "profit_margin_calc")):
        cost = st.number_input(i18n.t(lang, "cost_price"), min_value=0.0, value=0.0, key="pm_cost")
        sell = st.number_input(i18n.t(lang, "selling_price"), min_value=0.0, value=0.0, key="pm_sell")
        if st.button(i18n.t(lang, "calculate"), key="pm_btn"):
            result = tools.profit_margin(cost, sell)
            if result[0] is None:
                st.error("Selling price cannot be 0.")
            else:
                profit, margin_pct, markup_pct = result
                st.write(f"{i18n.t(lang, 'profit_label')}: {profit:.2f}")
                st.write(f"{i18n.t(lang, 'margin_label')}: {margin_pct:.1f}%")
                st.write(f"{i18n.t(lang, 'markup_label')}: {markup_pct:.1f}%")

    with st.expander(i18n.t(lang, "qr_generator")):
        qr_text = st.text_input(i18n.t(lang, "qr_placeholder"), key="qr_text")
        if st.button(i18n.t(lang, "generate_qr"), key="qr_btn"):
            if qr_text.strip():
                qr_bytes = tools.generate_qr(qr_text)
                st.image(qr_bytes, width=180)
                st.download_button(i18n.t(lang, "download_qr"), qr_bytes, file_name="qrcode.png", mime="image/png")
            else:
                st.error(i18n.t(lang, "qr_error"))

    with st.expander(i18n.t(lang, "email_writer")):
        email_topic = st.text_area(i18n.t(lang, "email_topic_label"), key="email_topic", height=80)
        email_tone = st.selectbox(i18n.t(lang, "tone_label"), ["Professional", "Friendly", "Formal", "Persuasive"], key="email_tone")
        if st.button(i18n.t(lang, "write_it"), key="email_btn"):
            if email_topic.strip() and API_KEY:
                with st.spinner(i18n.t(lang, "writing")):
                    prompt = f"Write a {email_tone.lower()} email/message about: {email_topic}. Keep it clear and well structured."
                    result = call_gemini([{"role": "user", "parts": [{"text": prompt}]}])
                st.text_area("Draft", result, height=200, key="email_result")
            else:
                st.error(i18n.t(lang, "email_error"))

    with st.expander(i18n.t(lang, "summarizer")):
        summ_text = st.text_area(i18n.t(lang, "paste_text"), key="summ_text", height=100)
        if st.button(i18n.t(lang, "summarize"), key="summ_btn"):
            if summ_text.strip() and API_KEY:
                with st.spinner(i18n.t(lang, "summarizing")):
                    prompt = f"Summarize this text in a few clear bullet points:\n\n{summ_text}"
                    result = call_gemini([{"role": "user", "parts": [{"text": prompt}]}])
                st.write(result)
            else:
                st.error(i18n.t(lang, "summarize_error"))

    with st.expander(i18n.t(lang, "translator")):
        trans_text = st.text_area(i18n.t(lang, "translate_text_label"), key="trans_text", height=80)
        trans_lang = st.text_input(i18n.t(lang, "target_lang_label"), value="English", key="trans_lang")
        if st.button(i18n.t(lang, "translate"), key="trans_btn"):
            if trans_text.strip() and API_KEY:
                with st.spinner(i18n.t(lang, "translating")):
                    prompt = f"Translate this text into {trans_lang}, keep the tone natural:\n\n{trans_text}"
                    result = call_gemini([{"role": "user", "parts": [{"text": prompt}]}])
                st.write(result)
            else:
                st.error(i18n.t(lang, "translate_error"))

    with st.expander(i18n.t(lang, "todo_list")):
        new_todo = st.text_input(i18n.t(lang, "new_task"), key="new_todo")
        if st.button(i18n.t(lang, "add_task"), key="add_todo_btn"):
            if new_todo.strip():
                tools.add_todo(new_todo.strip())
                st.rerun()
        for idx, item in enumerate(tools.load_todos()):
            c1, c2, c3 = st.columns([1, 5, 1])
            with c1:
                checked = st.checkbox("", value=item["done"], key=f"todo_chk_{idx}")
                if checked != item["done"]:
                    tools.toggle_todo(idx)
                    st.rerun()
            with c2:
                if item["done"]:
                    st.markdown(f"~~{item['text']}~~")
                else:
                    st.markdown(item["text"])
            with c3:
                if st.button("x", key=f"todo_del_{idx}"):
                    tools.delete_todo(idx)
                    st.rerun()

    with st.expander(i18n.t(lang, "meeting_summarizer")):
        meeting_text = st.text_area(i18n.t(lang, "meeting_placeholder"), key="meeting_text", height=100)
        if st.button(i18n.t(lang, "summarize_meeting"), key="meeting_btn"):
            if meeting_text.strip() and API_KEY:
                with st.spinner(i18n.t(lang, "summarizing")):
                    prompt = (
                        f"Summarize this meeting into: 1) Key discussion points 2) Decisions made "
                        f"3) Action items with owners if mentioned.\n\n{meeting_text}"
                    )
                    result = call_gemini([{"role": "user", "parts": [{"text": prompt}]}])
                st.write(result)
            else:
                st.error(i18n.t(lang, "meeting_error"))

    with st.expander("Memory Notes"):
        st.caption("Save things you want AeroSphere to always remember about you.")
        new_note = st.text_input("New memory", key="new_memory_note", placeholder="e.g. I run a YouTube channel called Art Mylo")
        if st.button("Save memory", key="add_memory_btn"):
            if new_note.strip():
                memory.add_note(st.session_state.username, new_note.strip())
                st.rerun()
        for idx, note in enumerate(memory.get_notes(st.session_state.username)):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"- {note}")
            with c2:
                if st.button("x", key=f"mem_del_{idx}"):
                    memory.delete_note(st.session_state.username, idx)
                    st.rerun()

    if not API_KEY:
        st.markdown("---")
        st.warning("Gemini API key nahi mili.")
        API_KEY = st.text_input("Gemini API Key (free)", type="password",
                                 help="https://aistudio.google.com/apikey se free key lo")

    st.markdown("---")
    st.markdown(f"**{i18n.t(lang, 'your_chats')}**")
    if st.button(i18n.t(lang, "new_chat"), use_container_width=True):
        st.session_state.session_id = sessions.new_session_id()
        st.session_state.messages = []
        st.rerun()

    for s in sessions.list_sessions():
        c1, c2 = st.columns([4, 1])
        with c1:
            if st.button(s["title"] or "New chat", key=f"open_{s['id']}", use_container_width=True):
                st.session_state.session_id = s["id"]
                st.session_state.messages = sessions.load_session(s["id"])
                st.rerun()
        with c2:
            if st.button("x", key=f"del_{s['id']}"):
                sessions.delete_session(s["id"])
                st.rerun()

st.markdown(themes.css_for_theme(active_theme), unsafe_allow_html=True)

# ------------------------------------------------------------
# WARNING BANNER - jab 90% limit use ho jaye
# ------------------------------------------------------------
usage_percent = (st.session_state.usage_count / MAX_MESSAGES_PER_SESSION) * 100 if MAX_MESSAGES_PER_SESSION else 0
if usage_percent >= 90:
    reset_time = datetime.fromtimestamp(st.session_state.usage_window_start + COOLDOWN_HOURS * 3600)
    reset_time_str = reset_time.strftime("%I:%M %p")
    messages_left = max(MAX_MESSAGES_PER_SESSION - st.session_state.usage_count, 0)
    st.markdown(
        f"""
        <div class="aero-warning-banner">
            \u26A0\uFE0F Session limit almost reached ({messages_left} messages left).
            Chat will pause and automatically continue at <strong>{reset_time_str}</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
glow_class = " glow" if st.session_state.glow_enabled else ""
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:16px; padding: 8px 0 18px 0;">
        <span class="aero-logo-badge{glow_class}">\U0001F310</span>
        <div>
            <h1 style="margin-bottom:0;">AeroSphere</h1>
            <p style="color:{active_theme['muted']}; margin-top:2px;">{i18n.t(lang, 'app_subtitle')}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_labels = [i18n.t(lang, "chat_tab"), i18n.t(lang, "documents_tab"), i18n.t(lang, "image_tab")]
if ENABLE_CODE_RUNNER:
    tab_labels.append(i18n.t(lang, "code_tab"))

_tabs = st.tabs(tab_labels)
tab_chat, tab_docs, tab_image = _tabs[0], _tabs[1], _tabs[2]
tab_code = _tabs[3] if ENABLE_CODE_RUNNER else None

# ==============================================================
# TAB 1: CHAT
# ==============================================================
with tab_chat:
    col_a, col_b, col_c = st.columns([1, 1, 1.4])
    with col_a:
        use_search = st.checkbox(i18n.t(lang, "web_search_toggle"))
    with col_b:
        use_voice = st.checkbox(i18n.t(lang, "voice_reply_toggle"))
    with col_c:
        uploaded_image = st.file_uploader("Attach an image", type=["png", "jpg", "jpeg"],
                                           key="chat_image_upload", label_visibility="collapsed")

    st.caption("Or record a voice message:")
    recorded_audio = audio_recorder(text="", icon_size="1x", key="chat_audio_recorder")

    # Sirf ye box scroll hota hai - header, tabs, checkboxes, input sab apni jagah fix rahenge
    chat_box = st.container(height=430)
    with chat_box:
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and st.session_state.get("last_audio_idx") == i:
                    st.audio(st.session_state.get("last_audio_bytes"), format="audio/mp3")

    remaining = MAX_MESSAGES_PER_SESSION - st.session_state.usage_count
    if remaining <= 3:
        st.caption(f"{max(remaining, 0)} messages left in this session.")

    user_input = st.chat_input(i18n.t(lang, "chat_placeholder"))

    # Voice message bhi ek chat turn ki tarah treat hota hai
    new_voice_message = False
    if recorded_audio and recorded_audio != st.session_state.get("last_recorded_audio"):
        st.session_state.last_recorded_audio = recorded_audio
        new_voice_message = True
        user_input = "(voice message)"

    if user_input:
        if not API_KEY:
            st.error(i18n.t(lang, "no_prompt_error"))
        elif st.session_state.usage_count >= MAX_MESSAGES_PER_SESSION:
            elapsed_hours = (time.time() - st.session_state.usage_window_start) / 3600
            hours_left = max(COOLDOWN_HOURS - elapsed_hours, 0)
            st.error(f"Session limit reached. Please wait about {hours_left:.1f} more hour(s) and your chat will continue right here, or add your own API key in the sidebar for unlimited use.")
        else:
            st.session_state.usage_count += 1
            if st.session_state.username:
                users.update_usage(st.session_state.username, usage_count=st.session_state.usage_count)
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner(i18n.t(lang, "thinking")):
                try:
                    final_prompt = user_input
                    extra_parts = []

                    if new_voice_message:
                        extra_parts.append({
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": base64.b64encode(recorded_audio).decode("utf-8"),
                            }
                        })
                        final_prompt = "The user sent a voice message. Listen to it and respond naturally to what they said."
                    elif uploaded_image is not None:
                        image_bytes = uploaded_image.getvalue()
                        mime = "image/png" if uploaded_image.type == "image/png" else "image/jpeg"
                        extra_parts.append({
                            "inline_data": {
                                "mime_type": mime,
                                "data": base64.b64encode(image_bytes).decode("utf-8"),
                            }
                        })
                    else:
                        # Agar message mein koi link hai, us website ko khud padh lo
                        found_url = web_reader.find_url(user_input)
                        if found_url:
                            page_text = web_reader.fetch_page_text(found_url)
                            final_prompt = (
                                f"The user shared this link: {found_url}\n"
                                f"Page content:\n{page_text}\n\n"
                                f"User's message: {user_input}\n\n"
                                "Use the page content above to respond to the user."
                            )
                        elif use_search:
                            results = search.web_search(user_input)
                            final_prompt = (
                                f"Web search results:\n{results}\n\n"
                                f"User question: {user_input}\n\n"
                                "Use the search results above to answer, and mention sources briefly."
                            )

                    contents = []
                    for m in st.session_state.messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        contents.append({"role": role, "parts": [{"text": m["content"]}]})

                    last_parts = [{"text": final_prompt}] + extra_parts
                    contents.append({"role": "user", "parts": last_parts})

                    reply = call_gemini(contents)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    sessions.save_session(st.session_state.session_id, st.session_state.messages)

                    if use_voice:
                        try:
                            audio_bytes = voice.text_to_speech(reply)
                            st.session_state.last_audio_idx = len(st.session_state.messages) - 1
                            st.session_state.last_audio_bytes = audio_bytes
                        except Exception as ve:
                            st.session_state.last_audio_idx = None
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

            st.rerun()

    if st.session_state.messages:
        if st.button(i18n.t(lang, "clear_chat")):
            st.session_state.messages = []
            st.session_state.last_audio_idx = None
            sessions.save_session(st.session_state.session_id, [])
            st.rerun()

# ==============================================================
# TAB 2: DOCUMENTS (Q&A)
# ==============================================================
with tab_docs:
    uploaded = st.file_uploader(i18n.t(lang, "upload_doc"), type=["pdf", "txt", "md"])

    if uploaded:
        if st.session_state.doc_text == "" or st.button("Reload document"):
            with st.spinner("Reading document..."):
                st.session_state.doc_text = docs.extract_text(uploaded)
            st.success(f"Loaded {len(st.session_state.doc_text)} characters from {uploaded.name}")

    doc_box = st.container(height=350)
    with doc_box:
        for msg in st.session_state.doc_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    doc_question = st.chat_input(i18n.t(lang, "ask_about_doc"))

    if doc_question:
        if not st.session_state.doc_text:
            st.error(i18n.t(lang, "no_doc_error"))
        elif not API_KEY:
            st.error("Gemini API key chahiye.")
        else:
            st.session_state.doc_messages.append({"role": "user", "content": doc_question})
            with st.spinner(i18n.t(lang, "thinking")):
                prompt = (
                    f"Document content:\n{st.session_state.doc_text[:12000]}\n\n"
                    f"Question: {doc_question}\n\n"
                    "Answer only using the document content above."
                )
                reply = call_gemini([{"role": "user", "parts": [{"text": prompt}]}])
                st.session_state.doc_messages.append({"role": "assistant", "content": reply})
            st.rerun()

# ==============================================================
# TAB 3: IMAGE GENERATOR
# ==============================================================
with tab_image:
    col1, col2 = st.columns([3, 1])
    with col1:
        image_prompt = st.text_input(i18n.t(lang, "image_prompt_label"),
                                      placeholder=i18n.t(lang, "image_placeholder"))
    with col2:
        size_labels = [i18n.t(lang, "square"), i18n.t(lang, "portrait"), i18n.t(lang, "landscape")]
        aspect = st.selectbox(i18n.t(lang, "size"), size_labels)

    size_map = {
        size_labels[0]: (1024, 1024),
        size_labels[1]: (720, 1280),
        size_labels[2]: (1280, 720),
    }

    if st.button(i18n.t(lang, "generate_image"), type="primary"):
        if not image_prompt:
            st.error(i18n.t(lang, "no_prompt_error"))
        elif st.session_state.image_count >= MAX_IMAGES_PER_SESSION:
            elapsed_hours = (time.time() - st.session_state.usage_window_start) / 3600
            hours_left = max(COOLDOWN_HOURS - elapsed_hours, 0)
            st.error(f"Session limit reached. Please wait about {hours_left:.1f} more hour(s) to generate more images.")
        else:
            st.session_state.image_count += 1
            if st.session_state.username:
                users.update_usage(st.session_state.username, image_count=st.session_state.image_count)
            with st.spinner(i18n.t(lang, "generating")):
                try:
                    width, height = size_map[aspect]
                    encoded_prompt = urllib.parse.quote(image_prompt)
                    image_url = (
                        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                        f"?width={width}&height={height}&nologo=true"
                    )
                    st.image(image_url, caption=image_prompt, use_container_width=True)
                    st.markdown(f"[Direct link]({image_url})")
                except Exception as e:
                    st.error(f"Error: {e}")

# ==============================================================
# TAB 4: CODE RUNNER (sirf tab_code available ho tab dikhega)
# ==============================================================
if ENABLE_CODE_RUNNER and tab_code is not None:
    with tab_code:
        code_input = st.text_area(i18n.t(lang, "code_placeholder"), height=220,
                                   placeholder="print('Hello AeroSphere')")

        if st.button(i18n.t(lang, "run_code"), type="primary"):
            if not code_input.strip():
                st.error(i18n.t(lang, "no_code_error"))
            else:
                with st.spinner("Running..."):
                    stdout, stderr = code_runner.run_python(code_input)
                st.markdown(f"**{i18n.t(lang, 'output_label')}**")
                if stdout:
                    st.code(stdout, language="text")
                if stderr:
                    st.error(stderr)
                if not stdout and not stderr:
                    st.caption("No output.")

st.markdown("---")
st.caption(f"AeroSphere | {len(themes.ALL_THEMES)}+ themes | {len(i18n.LANGUAGES)} languages")