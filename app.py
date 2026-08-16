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
import streamlit as st
import requests
import urllib.parse
from dotenv import load_dotenv

import themes
import i18n
import sessions
import docs
import search
import voice
import code_runner
import tools

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
# LOGIN - agar APP_PASSWORD set hai, to password ke bina app nahi khulegi
# ------------------------------------------------------------
try:
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "")
except Exception:
    APP_PASSWORD = os.getenv("APP_PASSWORD", "")

if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown(
            """
            <div style="text-align:center; padding-top:80px;">
                <h1>\U0001F310 AeroSphere</h1>
                <p style="opacity:0.7;">Enter password to continue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            entered = st.text_input("Password", type="password", key="login_password")
            if st.button("Enter", use_container_width=True):
                if entered == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong password.")
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

lang = st.session_state.language


def call_gemini(contents):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.5-flash-lite:generateContent?key={API_KEY}"
    )
    body = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": SYSTEM_INFO}]},
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
    col_a, col_b = st.columns(2)
    with col_a:
        use_search = st.checkbox(i18n.t(lang, "web_search_toggle"))
    with col_b:
        use_voice = st.checkbox(i18n.t(lang, "voice_reply_toggle"))

    # Sirf ye box scroll hota hai - header, tabs, checkboxes, input sab apni jagah fix rahenge
    chat_box = st.container(height=430)
    with chat_box:
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and st.session_state.get("last_audio_idx") == i:
                    st.audio(st.session_state.get("last_audio_bytes"), format="audio/mp3")

    user_input = st.chat_input(i18n.t(lang, "chat_placeholder"))

    if user_input:
        if not API_KEY:
            st.error(i18n.t(lang, "no_prompt_error"))
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner(i18n.t(lang, "thinking")):
                try:
                    final_prompt = user_input
                    if use_search:
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
                    contents.append({"role": "user", "parts": [{"text": final_prompt}]})

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
        else:
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
