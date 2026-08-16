"""
themes.py - AeroSphere ke liye 150+ premium themes.

Hum har theme haath se nahi likhte - iski jagah "families" (base look) aur
"accents" (highlight color) ko combine karke themes generate karte hain.
6 families x 25 accents = 150 themes, sab categorized.

Agar user apna khud ka color chahta hai, to CUSTOM theme option bhi hai
jahan wo apne hex colors daal sakta hai (import jaisa).
"""

# Har family ek "category" hai - background/surface/text ka base look
FAMILIES = {
    "Midnight":   {"category": "Dark",    "bg": "#0A0A0F", "surface": "#15151C", "text": "#EDEDF2", "muted": "#8A8A96"},
    "Obsidian":   {"category": "Dark",    "bg": "#0D0D0D", "surface": "#1A1A1A", "text": "#F2F2F2", "muted": "#8F8F8F"},
    "Deep Ocean": {"category": "Dark",    "bg": "#071019", "surface": "#0E1E2B", "text": "#E4F0F6", "muted": "#7E97A6"},
    "Snowfield":  {"category": "Light",   "bg": "#FAFAF9", "surface": "#FFFFFF", "text": "#1A1A1A", "muted": "#6B6B6B"},
    "Ivory":      {"category": "Light",   "bg": "#F7F4EE", "surface": "#FFFDF9", "text": "#211D15", "muted": "#7A7364"},
    "Slate Day":  {"category": "Light",   "bg": "#F1F3F6", "surface": "#FFFFFF", "text": "#1D2430", "muted": "#69707D"},
}

# Har accent ek highlight color hai - buttons, links, active states ke liye
ACCENTS = {
    "Crimson": "#E0304F", "Rose": "#F5417B", "Ember": "#FF6B3D", "Amber": "#FFB020",
    "Gold": "#D4A24C", "Lime": "#8FD14F", "Emerald": "#22C55E", "Jade": "#0FBF8F",
    "Teal": "#14B8B8", "Cyan": "#22D3EE", "Sky": "#38BDF8", "Azure": "#3B82F6",
    "Indigo": "#6366F1", "Violet": "#7A63FF", "Purple": "#A855F7", "Orchid": "#D946EF",
    "Magenta": "#EC4899", "Coral": "#FF7A6B", "Sunset": "#FF8C42", "Mint": "#4ADE80",
    "Ocean": "#0EA5E9", "Steel": "#64748B", "Graphite": "#94A3B8", "Copper": "#C4784A",
    "Ruby": "#DC2653",
}

CATEGORIES = ["Dark", "Light"]


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-")


def build_all_themes() -> dict:
    """150 themes = 6 families x 25 accents, har ek ek unique naam ke sath."""
    themes = {}
    for fam_name, fam in FAMILIES.items():
        for acc_name, acc_hex in ACCENTS.items():
            theme_name = f"{fam_name} {acc_name}"
            themes[theme_name] = {
                "category": fam["category"],
                "bg": fam["bg"],
                "surface": fam["surface"],
                "text": fam["text"],
                "muted": fam["muted"],
                "accent": acc_hex,
            }
    return themes


ALL_THEMES = build_all_themes()  # 150 themes total


def get_categories() -> list:
    return CATEGORIES


def get_themes_by_category(category: str) -> dict:
    return {name: t for name, t in ALL_THEMES.items() if t["category"] == category}


def custom_theme(bg: str, surface: str, text: str, muted: str, accent: str) -> dict:
    """User apna khud ka theme bana sake - hex colors se (import jaisa)."""
    return {"category": "Custom", "bg": bg, "surface": surface, "text": text, "muted": muted, "accent": accent}


def css_for_theme(t: dict) -> str:
    """Theme dictionary ko actual CSS mein convert karta hai."""
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');

    .stApp {{
        background-color: {t['bg']};
        color: {t['text']};
        font-family: 'Inter', sans-serif;
    }}

    #MainMenu, footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; box-shadow: none; }}

    section[data-testid="stSidebar"] {{
        background-color: {t['surface']};
        border-right: 1px solid {t['accent']}22;
    }}

    h1, h2, h3 {{
        font-family: 'Poppins', sans-serif !important;
        color: {t['text']} !important;
    }}

    .stChatMessage {{
        background-color: {t['surface']};
        border: 1px solid {t['accent']}22;
        border-radius: 12px;
    }}

    .stButton > button {{
        background-color: {t['accent']};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.15s ease, opacity 0.15s ease;
    }}
    .stButton > button:hover {{ opacity: 0.88; transform: translateY(-1px); }}

    input, textarea, .stTextInput input, .stSelectbox > div {{
        background-color: {t['surface']} !important;
        color: {t['text']} !important;
        border-radius: 8px !important;
        border: 1px solid {t['accent']}33 !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        background-color: {t['surface']};
        padding: 6px;
        border-radius: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        color: {t['muted']};
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {t['accent']};
        color: #FFFFFF !important;
    }}

    ::-webkit-scrollbar {{ width: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: {t['accent']}55; border-radius: 8px; }}

    /* Chat input ko hamesha screen ke bottom pe fix rakhta hai */
    [data-testid="stBottomBlockContainer"] {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0;
        right: 0;
        background: {t['bg']} !important;
        z-index: 999;
        padding: 12px 24px !important;
        border-top: 1px solid {t['accent']}22;
    }}
    [data-testid="stChatInput"] {{
        background: {t['surface']} !important;
    }}
    .stMainBlockContainer {{
        padding-bottom: 110px !important;
    }}

    /* Premium logo badge */
    .aero-logo-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 54px;
        height: 54px;
        border-radius: 16px;
        background: linear-gradient(135deg, {t['accent']}, {t['accent']}99);
        font-size: 26px;
        box-shadow: 0 4px 16px {t['accent']}55;
        flex-shrink: 0;
        animation: aeroLogoFloat 5s ease-in-out infinite;
    }}
    .aero-logo-badge.glow {{
        animation: aeroLogoFloat 5s ease-in-out infinite, aeroGlowPulse 2.4s ease-in-out infinite;
    }}
    @keyframes aeroLogoFloat {{
        0%, 70% {{ transform: translateY(0) rotate(0deg); }}
        85% {{ transform: translateY(-8px) rotate(-4deg); }}
        100% {{ transform: translateY(0) rotate(0deg); }}
    }}
    @keyframes aeroGlowPulse {{
        0%, 100% {{ box-shadow: 0 0 14px {t['accent']}66, 0 4px 16px {t['accent']}55; }}
        50% {{ box-shadow: 0 0 32px {t['accent']}cc, 0 4px 24px {t['accent']}99; }}
    }}

    /* Chat area - sirf ye scroll ho, baaki sab fix rahe */
    [data-testid="stVerticalBlockBorderWrapper"]:has(.stChatMessage) {{
        border-radius: 12px;
    }}

    /* Poora app fade + slide in hoke khulta hai */
    .stApp {{
        animation: aeroFadeIn 0.6s ease-out;
    }}
    @keyframes aeroFadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Background mein halka sa moving glow - premium depth ke liye */
    .stApp::before {{
        content: "";
        position: fixed;
        top: -20%;
        left: -10%;
        width: 60%;
        height: 60%;
        background: radial-gradient(circle, {t['accent']}22, transparent 70%);
        filter: blur(60px);
        pointer-events: none;
        z-index: 0;
        animation: aeroDrift 18s ease-in-out infinite;
    }}
    @keyframes aeroDrift {{
        0%, 100% {{ transform: translate(0, 0); }}
        50% {{ transform: translate(6%, 8%); }}
    }}

    /* Har naya chat message halke se slide+fade karke aata hai */
    .stChatMessage {{
        animation: aeroMsgIn 0.35s ease-out;
    }}
    @keyframes aeroMsgIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Tabs smooth feel */
    .stTabs [data-baseweb="tab"] {{
        transition: all 0.25s ease;
    }}
    .stTabs [aria-selected="true"] {{
        transform: translateY(-1px);
    }}

    /* Sidebar expanders smoothly highlight hote hain */
    [data-testid="stExpander"] {{
        transition: all 0.25s ease;
    }}
    [data-testid="stExpander"]:hover {{
        border-color: {t['accent']}55 !important;
    }}

    /* Inputs pe focus glow */
    input:focus, textarea:focus {{
        box-shadow: 0 0 0 3px {t['accent']}33 !important;
        transition: box-shadow 0.2s ease;
    }}

    /* Images halke se fade hoke render hote hain */
    .stImage img {{
        animation: aeroFadeIn 0.5s ease-out;
        transition: transform 0.3s ease;
    }}
    .stImage img:hover {{
        transform: scale(1.01);
    }}
    </style>
    """