"""
app.py - Main entry point for the EduForAll Streamlit application.

This file:
- Applies premium CSS styling (color blind safe: blues + oranges)
- Controls page routing: login, signup, profile setup, dashboard
- Connects auth.py, database.py, and model.py together
- Renders the dashboard with 3 tabs: Analytics, Recommendations, Rate
"""

import streamlit as st
import plotly.graph_objects as go
from database import init_db, save_profile, get_profile, save_rating, get_user_ratings
from auth import signup_page, login_page, logout, is_authenticated
from model import recommend
from metrics import (
    LOGIN_COUNTER, SIGNUP_COUNTER, RECOMMENDATIONS_COUNTER,
    RATINGS_COUNTER, ACTIVE_USERS_GAUGE, RECOMMENDATIONS_HISTOGRAM
)

# ── Start Prometheus metrics server ────────────────────────────────────────────
# Runs on port 8000 in a background thread so it doesn't block Streamlit
from prometheus_client import start_http_server
import threading

def _start_metrics():
    try:
        start_http_server(8000)
    except OSError:
        pass  # Already running

threading.Thread(target=_start_metrics, daemon=True).start()

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduForAll",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"  # collapsed by default on mobile
)

init_db()

# ── Global CSS ─────────────────────────────────────────────────────────────────
# Color blind safe palette:
#   --blue        #0077BB  primary actions (deuteranopia/protanopia safe)
#   --blue-dark   #012A4A  headings, sidebar
#   --orange      #EE7733  accents, highlights (clearly distinct from blue)
#   --teal        #009988  success states (safe alternative to green)
#   --grey        #F0F4F8  page background
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Fraunces:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --blue:        #0077BB;
    --blue-dark:   #012A4A;
    --blue-mid:    #0a3d6b;
    --blue-light:  #deeaf6;
    --orange:      #EE7733;
    --orange-light:#fff4ec;
    --teal:        #009988;
    --grey:        #F0F4F8;
    --grey-border: #D8E2EC;
    --text:        #0D1B2A;
    --text-mid:    #3D5166;
    --text-light:  #7A8FA6;
    --white:       #FFFFFF;
    --shadow-sm:   0 1px 4px rgba(0,0,0,0.06);
    --shadow-md:   0 4px 20px rgba(0,0,0,0.09);
    --shadow-lg:   0 8px 40px rgba(0,0,0,0.13);
}

/* ── Reset & Base ── */
html, body, .stApp {
    font-family: 'Sora', sans-serif;
    background-color: var(--grey);
    color: var(--text);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #012A4A 0%, #01395f 60%, #0a5080 100%);
    border-right: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.15);
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--white) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }

/* Main content selectbox — force dark text always */
section.main .stSelectbox div,
section.main .stSelectbox span,
section.main .stSelectbox input,
section.main .stSelectbox svg { color: #0D1B2A !important; }
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
div[role="option"],
div[role="option"] * { color: #0D1B2A !important; background: white !important; }
div[role="option"]:hover,
div[role="option"]:hover * { background: #deeaf6 !important; }

/* sidebar nav items */
.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 4px;
    cursor: pointer;
    transition: background 0.2s;
    font-weight: 500;
    font-size: 0.9rem;
}
.nav-item:hover { background: rgba(255,255,255,0.1); }
.nav-item.active { background: rgba(238,119,51,0.25); border-left: 3px solid var(--orange); }

[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.08);
    color: var(--white) !important;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px;
    font-family: 'Sora', sans-serif;
    font-weight: 500;
    width: 100%;
    margin-bottom: 6px;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.15);
}

/* logout button */
.logout-btn button {
    background: rgba(238,119,51,0.2) !important;
    border-color: rgba(238,119,51,0.4) !important;
}
.logout-btn button:hover {
    background: rgba(238,119,51,0.35) !important;
}

/* ── Auth Page ── */
.auth-split {
    display: flex;
    min-height: 100vh;
}
.auth-left {
    flex: 1;
    background: linear-gradient(145deg, #012A4A 0%, #0077BB 50%, #1A9BE8 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 4rem 3rem;
    position: relative;
    overflow: hidden;
}
.auth-left::before {
    content: '';
    position: absolute;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    top: -150px; right: -150px;
}
.auth-left::after {
    content: '';
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(238,119,51,0.12);
    bottom: -80px; left: -80px;
}
.auth-brand {
    font-family: 'Fraunces', serif;
    font-size: 2.8rem;
    color: white;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 1rem;
    position: relative; z-index: 1;
}
.auth-tagline {
    color: rgba(255,255,255,0.75);
    font-size: 1.05rem;
    line-height: 1.7;
    position: relative; z-index: 1;
    max-width: 340px;
}
.auth-features {
    margin-top: 2.5rem;
    position: relative; z-index: 1;
}
.auth-feature-item {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
    color: rgba(255,255,255,0.85);
    font-size: 0.9rem;
}
.auth-feature-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--orange);
    flex-shrink: 0;
}
.auth-right {
    flex: 1;
    background: var(--white);
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 3rem 4rem;
}

/* ── Form Elements ── */
.stTextInput input, .stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid var(--grey-border) !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1rem !important;
    background: var(--white) !important;
    color: var(--text) !important;
    transition: border 0.2s, box-shadow 0.2s !important;
}
.stTextInput input:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(0,119,187,0.12) !important;
}

label { font-weight: 500 !important; font-size: 0.85rem !important; color: #3D5166 !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0077BB 0%, #005F99 100%);
    color: var(--white) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 14px rgba(0,119,187,0.3) !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #005F99 0%, #004880 100%) !important;
    box-shadow: 0 6px 20px rgba(0,119,187,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Cards ── */
.card {
    background: var(--white);
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid var(--grey-border);
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: var(--shadow-md); }

/* ── Stat Cards ── */
.stat-card {
    background: var(--white);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    border: 1px solid var(--grey-border);
    box-shadow: var(--shadow-sm);
    display: flex;
    align-items: center;
    gap: 1rem;
}
.stat-icon {
    width: 48px; height: 48px;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
}
.stat-icon.blue  { background: var(--blue-light); }
.stat-icon.orange{ background: var(--orange-light); }
.stat-icon.teal  { background: #e0f5f3; }
.stat-value {
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    color: var(--text);
    line-height: 1;
    font-weight: 700;
}
.stat-label {
    font-size: 0.78rem;
    color: var(--text-light);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 2px;
}

/* ── Recommendation Cards ── */
.rec-card {
    background: var(--white);
    border-radius: 14px;
    padding: 1.3rem 1.5rem;
    border: 1px solid var(--grey-border);
    border-left: 4px solid var(--orange);
    box-shadow: var(--shadow-sm);
    margin-bottom: 0.9rem;
    transition: transform 0.15s, box-shadow 0.15s;
    position: relative;
}
.rec-card:hover {
    transform: translateX(5px);
    box-shadow: var(--shadow-md);
}
.rec-number {
    display: inline-block;
    background: var(--orange-light);
    color: var(--orange);
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.rec-text {
    color: var(--text);
    line-height: 1.65;
    font-size: 0.9rem;
}

/* ── Section Headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid var(--grey-border);
}
.section-title {
    font-family: 'Fraunces', serif;
    font-size: 1.3rem;
    color: var(--text);
    font-weight: 700;
}
.section-badge {
    background: var(--blue-light);
    color: var(--blue);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
}

/* ── Dashboard Header ── */
.dash-header {
    background: linear-gradient(120deg, #012A4A 0%, #0077BB 55%, #1E9ED6 100%);
    padding: 2rem 2.5rem;
    position: relative;
    overflow: hidden;
}
.dash-header::after {
    content: '🎓';
    position: absolute;
    right: 2.5rem; top: 50%;
    transform: translateY(-50%);
    font-size: 6rem;
    opacity: 0.08;
}
.dash-header-title {
    font-family: 'Fraunces', serif;
    font-size: 1.8rem;
    color: white;
    font-weight: 700;
    margin: 0;
}
.dash-header-sub {
    color: rgba(255,255,255,0.7);
    font-size: 0.9rem;
    margin-top: 0.3rem;
}
.dash-header-pill {
    display: inline-block;
    background: rgba(238,119,51,0.25);
    color: #FFB680;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 0.6rem;
    letter-spacing: 0.05em;
    border: 1px solid rgba(238,119,51,0.3);
}

/* ── Profile Badge ── */
.profile-badge {
    background: linear-gradient(135deg, var(--blue-light) 0%, #f0f7ff 100%);
    border: 1px solid #c0d8f0;
    border-radius: 14px;
    padding: 1.4rem;
}
.profile-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(0,0,0,0.05);
    font-size: 0.88rem;
}
.profile-row:last-child { border-bottom: none; }
.profile-key { color: var(--text-light); font-weight: 500; }
.profile-val {
    color: var(--text);
    font-weight: 600;
    background: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    border: 1px solid var(--grey-border);
}

/* ── Rating History ── */
.rating-row {
    background: var(--white);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid var(--grey-border);
    margin-bottom: 0.7rem;
    box-shadow: var(--shadow-sm);
}
.rating-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
}
.rating-date { font-size: 0.75rem; color: var(--text-light); }
.rating-stars { color: var(--orange); font-size: 0.85rem; }
.rating-helpful-yes { color: var(--teal); font-size: 0.78rem; font-weight: 600; }
.rating-helpful-no  { color: #CC3311; font-size: 0.78rem; font-weight: 600; }
.rating-text { font-size: 0.85rem; color: var(--text-mid); line-height: 1.5; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--white) !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid var(--grey-border) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--text-mid) !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0077BB, #005F99) !important;
    color: white !important;
    box-shadow: 0 2px 10px rgba(0,119,187,0.3) !important;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: var(--grey-border);
    margin: 1.5rem 0;
}

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: var(--text-light);
}
.empty-state-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-state-text { font-size: 0.9rem; line-height: 1.6; }

/* ── Content padding wrapper ── */
.content-wrap { padding: 2rem 2.5rem; }

/* ── Profile form card ── */
.form-card {
    background: var(--white);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    border: 1px solid var(--grey-border);
    box-shadow: var(--shadow-md);
    margin-top: 1.5rem;
}
/* ── Mobile Responsive ────────────────────────────────────────────────────── */
/* Applies when screen width is 768px or less (phones and small tablets) */

@media (max-width: 768px) {

    /* Reduce content padding on small screens */
    .content-wrap { padding: 1rem 1rem !important; }

    /* Stack stat cards vertically */
    .stat-card {
        flex-direction: column;
        text-align: center;
        padding: 1rem;
    }

    /* Smaller dashboard header text */
    .dash-header { padding: 1.2rem 1rem !important; }
    .dash-header-title { font-size: 1.3rem !important; }
    .dash-header-sub   { font-size: 0.8rem !important; }

    /* Smaller section titles */
    .section-title { font-size: 1.1rem !important; }

    /* Recommendation cards — remove hover slide on mobile */
    .rec-card:hover { transform: none !important; }
    .rec-card { padding: 1rem !important; }

    /* Tabs — smaller text and padding */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.75rem !important;
        padding: 6px 10px !important;
    }

    /* Buttons — full width on mobile */
    .stButton > button { width: 100% !important; }

    /* Profile badge — smaller text */
    .profile-row { font-size: 0.78rem !important; }
    .profile-val { font-size: 0.72rem !important; }

    /* Auth page — hide left brand panel on mobile, show only form */
    .auth-left-panel { display: none !important; }
    .auth-right-panel {
        padding: 1.5rem 1rem !important;
        min-height: 100vh;
    }

    /* Rating history cards */
    .rating-row { padding: 0.8rem !important; }
    .rating-text { font-size: 0.78rem !important; }

    /* Empty state — smaller icon */
    .empty-state { padding: 2rem 0.5rem !important; }
    .empty-state-icon { font-size: 2rem !important; }

    /* Reduce font size globally on mobile */
    html, body, .stApp { font-size: 14px !important; }
}

/* Medium screens (tablets) */
@media (max-width: 1024px) and (min-width: 769px) {
    .content-wrap { padding: 1.5rem 1.5rem !important; }
    .dash-header-title { font-size: 1.5rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUTH — Premium split-screen design
# ══════════════════════════════════════════════════════════════════════════════

def auth_page():
    """
    Premium split-screen auth page.
    Left panel: brand story and features.
    Right panel: login or signup form.
    After signup, auto-switches to login with a success banner.
    """

    # Left panel — brand story
    left, right = st.columns([1, 1])

    with left:
        st.markdown("""
        <div style='background:linear-gradient(145deg,#012A4A 0%,#0077BB 55%,#1A9BE8 100%);
                    min-height:92vh; padding:4rem 3rem; display:flex;
                    flex-direction:column; justify-content:center;
                    border-radius:0 24px 24px 0; position:relative; overflow:hidden;'>
            <div style='position:absolute;width:400px;height:400px;border-radius:50%;
                        background:rgba(255,255,255,0.04);top:-120px;right:-120px;'></div>
            <div style='position:absolute;width:250px;height:250px;border-radius:50%;
                        background:rgba(238,119,51,0.1);bottom:-60px;left:-60px;'></div>
            <div style='position:relative;z-index:1;'>
                <div style='font-size:2.8rem;margin-bottom:0.5rem;'>🎓</div>
                <div style='font-family:Fraunces,serif;font-size:2.6rem;color:white;
                            font-weight:700;line-height:1.1;margin-bottom:1rem;'>
                    EduForAll
                </div>
                <div style='color:rgba(255,255,255,0.75);font-size:1rem;
                            line-height:1.75;max-width:320px;margin-bottom:2.5rem;'>
                    Personalized study strategies powered by AI — designed for students
                    with learning disabilities.
                </div>
                <div style='display:flex;flex-direction:column;gap:14px;'>
                    <div style='display:flex;align-items:center;gap:12px;
                                color:rgba(255,255,255,0.85);font-size:0.88rem;'>
                        <div style='width:8px;height:8px;border-radius:50%;
                                    background:#EE7733;flex-shrink:0;'></div>
                        AI-powered personalized recommendations
                    </div>
                    <div style='display:flex;align-items:center;gap:12px;
                                color:rgba(255,255,255,0.85);font-size:0.88rem;'>
                        <div style='width:8px;height:8px;border-radius:50%;
                                    background:#EE7733;flex-shrink:0;'></div>
                        Designed for all types of learning disabilities
                    </div>
                    <div style='display:flex;align-items:center;gap:12px;
                                color:rgba(255,255,255,0.85);font-size:0.88rem;'>
                        <div style='width:8px;height:8px;border-radius:50%;
                                    background:#EE7733;flex-shrink:0;'></div>
                        Track your progress and rate strategies
                    </div>
                    <div style='display:flex;align-items:center;gap:12px;
                                color:rgba(255,255,255,0.85);font-size:0.88rem;'>
                        <div style='width:8px;height:8px;border-radius:50%;
                                    background:#EE7733;flex-shrink:0;'></div>
                        Color blind safe — accessible for everyone
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Right panel — form
    with right:
        st.markdown("<div style='padding:3rem 2rem;'>", unsafe_allow_html=True)

        # After signup → show login with success banner
        if st.session_state.get("just_signed_up", False):
            st.session_state["just_signed_up"] = False
            st.markdown("""
            <div style='background:#e0f5f3;border:1px solid #009988;border-radius:10px;
                        padding:12px 16px;margin-bottom:1.5rem;display:flex;
                        align-items:center;gap:10px;'>
                <span style='font-size:1.2rem;'>✅</span>
                <span style='color:#006655;font-weight:600;font-size:0.9rem;'>
                    Account created! Please log in below.
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style='font-family:Fraunces,serif;font-size:1.8rem;
                        color:#012A4A;font-weight:700;margin-bottom:0.3rem;'>
                Welcome back
            </div>
            <div style='color:#7A8FA6;font-size:0.88rem;margin-bottom:1.8rem;'>
                Sign in to continue your learning journey
            </div>
            """, unsafe_allow_html=True)
            login_page()

        else:
            # Tab switcher
            tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

            with tab_login:
                st.markdown("""
                <div style='font-family:Fraunces,serif;font-size:1.8rem;
                            color:#012A4A;font-weight:700;margin-bottom:0.3rem;
                            margin-top:1rem;'>
                    Welcome back
                </div>
                <div style='color:#7A8FA6;font-size:0.88rem;margin-bottom:1.8rem;'>
                    Sign in to continue your learning journey
                </div>
                """, unsafe_allow_html=True)
                login_page()

            with tab_signup:
                st.markdown("""
                <div style='font-family:Fraunces,serif;font-size:1.8rem;
                            color:#012A4A;font-weight:700;margin-bottom:0.3rem;
                            margin-top:1rem;'>
                    Get started
                </div>
                <div style='color:#7A8FA6;font-size:0.88rem;margin-bottom:1.8rem;'>
                    Create your account — it only takes a minute
                </div>
                """, unsafe_allow_html=True)
                signup_page(on_success=lambda: st.session_state.update({"just_signed_up": True}))

        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PROFILE SETUP
# ══════════════════════════════════════════════════════════════════════════════

def profile_page():
    """
    Profile setup page using only native Streamlit widgets.
    No custom CSS on form elements — avoids the white text bug entirely.
    Pre-fills existing values if the student is editing their profile.
    """
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='dash-header'>
        <div class='dash-header-pill'>PROFILE SETUP</div>
        <div class='dash-header-title'>🎓 Your Learning Profile</div>
        <div class='dash-header-sub'>
            Tell us about your learning needs so we can personalize your strategies.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")  # spacer

    user_id  = st.session_state.get("user_id")
    existing = get_profile(user_id)

    # Helper: get index of saved value in options list
    def idx(options, key):
        val = existing.get(key) if existing else None
        return options.index(val) if val in options else 0

    # ── Options ───────────────────────────────────────────────────────────────
    disability_options = [
        "Visual Impairment", "Hearing Impairment", "ADHD",
        "Dyslexia", "Autism Spectrum", "Physical Disability", "Other"
    ]
    challenge_options = [
        "Complete Blindness", "Low Vision", "Color Blindness",
        "Partial Hearing Loss", "Complete Deafness",
        "Attention Difficulties", "Reading Difficulties",
        "Memory Challenges", "Motor Difficulties", "Social Challenges"
    ]
    severity_options = ["Mild", "Moderate", "Severe"]
    age_options      = ["Child", "Teenager", "Adult"]
    env_options      = [
        "Home", "Online", "Library", "In Classes",
        "Home, Online", "Home, Library", "Online, Library",
        "Online, In Classes", "Library, In Classes"
    ]

    # ── Layout: narrow centered column ────────────────────────────────────────
    # Using columns to center the form on the page
    _, center, _ = st.columns([1, 3, 1])

    with center:
        st.subheader("Step 1 — About Your Disability")
        col1, col2 = st.columns(2)
        with col1:
            disability_type = st.selectbox(
                "Disability Type", disability_options,
                index=idx(disability_options, "disability_type")
            )
        with col2:
            specific_challenge = st.selectbox(
                "Specific Challenge", challenge_options,
                index=idx(challenge_options, "specific_challenge")
            )

        st.write("")
        st.subheader("Step 2 — Your Learning Context")
        col3, col4, col5 = st.columns(3)
        with col3:
            severity_level = st.selectbox(
                "Severity Level", severity_options,
                index=idx(severity_options, "severity_level")
            )
        with col4:
            age_group = st.selectbox(
                "Age Group", age_options,
                index=idx(age_options, "age_group")
            )
        with col5:
            study_environment = st.selectbox(
                "Study Environment", env_options,
                index=idx(env_options, "study_environment")
            )

        st.write("")
        # Show a summary before saving
        st.info(
            f"**Summary:** {disability_type} · {specific_challenge} · "
            f"{severity_level} · {age_group} · {study_environment}"
        )

        if st.button("💾 Save Profile & Go to Dashboard", use_container_width=True):
            save_profile(
                user_id, disability_type, specific_challenge,
                severity_level, age_group, study_environment
            )
            st.session_state["profile_complete"] = True
            st.session_state["editing_profile"]  = False
            st.success("Profile saved!")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB: Analytics
# ══════════════════════════════════════════════════════════════════════════════

def analytics_tab(profile, ratings):
    """
    Analytics tab — premium stat cards, profile badge, and rating chart.
    Uses color blind safe blue for chart bars.
    """
    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)

    # ── Stat Cards ────────────────────────────────────────────────────────────
    total_ratings = len(ratings)
    avg_stars     = round(sum(r["stars"] for r in ratings) / total_ratings, 1) if ratings else 0
    helpful_count = sum(1 for r in ratings if r["helpful"] == 1)

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon blue'>📋</div>
            <div>
                <div class='stat-value'>{total_ratings}</div>
                <div class='stat-label'>Strategies Rated</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon orange'>⭐</div>
            <div>
                <div class='stat-value'>{avg_stars}</div>
                <div class='stat-label'>Avg. Star Rating</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon teal'>✅</div>
            <div>
                <div class='stat-value'>{helpful_count}</div>
                <div class='stat-label'>Marked Helpful</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Profile + Chart row ───────────────────────────────────────────────────
    col_a, col_b = st.columns([1, 1.4], gap="large")

    with col_a:
        st.markdown("""
        <div class='section-header'>
            <span class='section-title'>Your Profile</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class='profile-badge'>
            <div class='profile-row'>
                <span class='profile-key'>Disability Type</span>
                <span class='profile-val'>{profile.get('disability_type','N/A')}</span>
            </div>
            <div class='profile-row'>
                <span class='profile-key'>Specific Challenge</span>
                <span class='profile-val'>{profile.get('specific_challenge','N/A')}</span>
            </div>
            <div class='profile-row'>
                <span class='profile-key'>Severity Level</span>
                <span class='profile-val'>{profile.get('severity_level','N/A')}</span>
            </div>
            <div class='profile-row'>
                <span class='profile-key'>Age Group</span>
                <span class='profile-val'>{profile.get('age_group','N/A')}</span>
            </div>
            <div class='profile-row'>
                <span class='profile-key'>Study Environment</span>
                <span class='profile-val'>{profile.get('study_environment','N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("""
        <div class='section-header'>
            <span class='section-title'>Rating Distribution</span>
        </div>
        """, unsafe_allow_html=True)
        if ratings:
            star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for r in ratings:
                star_counts[r["stars"]] += 1

            fig = go.Figure(go.Bar(
                x=["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"],
                y=list(star_counts.values()),
                marker=dict(
                    color=list(star_counts.values()),
                    colorscale=[[0, "#B8D9F0"], [1, "#0077BB"]],  # blue gradient, color blind safe
                    showscale=False
                ),
                text=list(star_counts.values()),
                textposition="outside",
            ))
            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Sora", color="#3D5166", size=12),
                margin=dict(l=10, r=10, t=20, b=10),
                height=280,
                showlegend=False,
                xaxis=dict(showgrid=False, tickfont=dict(size=11)),
                yaxis=dict(showgrid=True, gridcolor="#F0F4F8", tickfont=dict(size=11))
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div class='empty-state'>
                <div class='empty-state-icon'>📊</div>
                <div class='empty-state-text'>
                    Rate some strategies to see your<br>distribution chart here.
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB: Recommendations
# ══════════════════════════════════════════════════════════════════════════════

def recommendations_tab(profile):
    """
    Recommendations tab — displays all ML-generated strategies as
    premium orange-accented cards with strategy numbers.
    """
    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='section-header'>
        <span class='section-title'>Your Study Strategies</span>
        <span class='section-badge'>{profile.get('disability_type','').upper()}</span>
    </div>
    <div style='color:#7A8FA6;font-size:0.85rem;margin-bottom:1.5rem;'>
        Personalized for · <strong>{profile.get('specific_challenge')}</strong>
        · <strong>{profile.get('severity_level')} severity</strong>
        · <strong>{profile.get('study_environment')}</strong>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading your personalized strategies..."):
        try:
            recs = recommend(profile)
            # ── Prometheus: track recommendation generation ─────────────────────
            RECOMMENDATIONS_COUNTER.inc()          # +1 recommendation request
            RECOMMENDATIONS_HISTOGRAM.observe(len(recs))  # track how many returned
        except Exception as e:
            st.error(f"Could not load recommendations: {e}")
            st.markdown("</div>", unsafe_allow_html=True)
            return

    if not recs:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-state-icon'>🔍</div>
            <div class='empty-state-text'>
                No strategies found for your current profile.<br>
                Try updating your profile with different options.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for i, rec in enumerate(recs, start=1):
        st.markdown(f"""
        <div class='rec-card'>
            <span class='rec-number'>Strategy {i}</span>
            <div class='rec-text'>{rec}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB: Rate Recommendations
# ══════════════════════════════════════════════════════════════════════════════

def rate_tab(profile, user_id):
    """
    Rate tab — clean rating form with star slider and helpful toggle,
    followed by a premium history of past ratings.
    """
    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)

    st.markdown("""
    <div class='section-header'>
        <span class='section-title'>Rate a Strategy</span>
    </div>
    <div style='color:#7A8FA6;font-size:0.85rem;margin-bottom:1.5rem;'>
        Your feedback helps us improve recommendations for everyone.
    </div>
    """, unsafe_allow_html=True)

    try:
        recs = recommend(profile)
    except Exception as e:
        st.error(f"Could not load recommendations: {e}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not recs:
        st.warning("No strategies available to rate.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ── Rating Form ──────────────────────────────────────────────────────────
    with st.form("rating_form"):
        selected_rec = st.selectbox(
            "Select a strategy",
            recs,
            format_func=lambda x: x[:90] + "..." if len(x) > 90 else x
        )
        col1, col2 = st.columns([2, 1], gap="large")
        with col1:
            stars = st.slider("Star Rating", min_value=1, max_value=5, value=3,
                              help="1 = Not helpful, 5 = Extremely helpful")
        with col2:
            helpful = st.radio("Was it helpful?", ["Yes", "No"], horizontal=True)

        submitted = st.form_submit_button("Submit Feedback →", use_container_width=True)
        if submitted:
            save_rating(user_id, selected_rec, stars, 1 if helpful == "Yes" else 0)
            # ── Prometheus: track rating submission ─────────────────────────────
            RATINGS_COUNTER.inc()  # +1 rating submitted
            st.success("Feedback submitted — thank you!")
            st.rerun()

    # ── Past Ratings ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style='height:1.5rem'></div>
    <div class='section-header'>
        <span class='section-title'>Your Rating History</span>
    </div>
    """, unsafe_allow_html=True)

    past = get_user_ratings(user_id)
    if past:
        for r in past:
            short = r["recommendation_text"][:110] + "..." \
                if len(r["recommendation_text"]) > 110 else r["recommendation_text"]
            helpful_cls   = "rating-helpful-yes" if r["helpful"] == 1 else "rating-helpful-no"
            helpful_label = "✅ Helpful" if r["helpful"] == 1 else "❌ Not Helpful"
            stars_html    = "⭐" * r["stars"]
            st.markdown(f"""
            <div class='rating-row'>
                <div class='rating-meta'>
                    <span class='rating-date'>{r['timestamp'][:10]}</span>
                    <span>
                        <span class='rating-stars'>{stars_html}</span>
                        &nbsp;·&nbsp;
                        <span class='{helpful_cls}'>{helpful_label}</span>
                    </span>
                </div>
                <div class='rating-text'>{short}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-state-icon'>⭐</div>
            <div class='empty-state-text'>
                No ratings yet.<br>Rate a strategy above to get started!
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB: Live Metrics (Prometheus)
# ══════════════════════════════════════════════════════════════════════════════

def metrics_tab():
    """
    Live Metrics tab — reads directly from Prometheus counters and gauges
    and displays them as clean readable cards and charts.
    No raw text — just the numbers that matter.
    """
    import requests

    st.markdown("<div class='content-wrap'>", unsafe_allow_html=True)

    st.markdown("""
    <div class='section-header'>
        <span class='section-title'>Live App Metrics</span>
        <span class='section-badge'>PROMETHEUS</span>
    </div>
    <div style='color:#7A8FA6;font-size:0.85rem;margin-bottom:1.5rem;'>
        Real-time monitoring data collected by Prometheus.
        Refresh the page to see updated counts.
    </div>
    """, unsafe_allow_html=True)

    # ── Fetch metrics from Prometheus endpoint ────────────────────────────────
    # We read the raw text and parse only our custom eduforall_ metrics
    try:
        response = requests.get("http://localhost:8000/metrics", timeout=3)
        raw = response.text
    except Exception:
        st.warning("⚠️ Metrics server not reachable. Make sure the app is running normally.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # ── Parse metric values from raw Prometheus text ──────────────────────────
    def parse_metric(text, metric_name):
        """Extracts the numeric value of a metric from raw Prometheus text."""
        for line in text.split("\n"):
            if line.startswith(metric_name + " "):
                try:
                    return float(line.split(" ")[1])
                except Exception:
                    return 0.0
        return 0.0

    # Read each metric value
    logins          = int(parse_metric(raw, "eduforall_logins_total"))
    signups         = int(parse_metric(raw, "eduforall_signups_total"))
    recommendations = int(parse_metric(raw, "eduforall_recommendations_total"))
    ratings         = int(parse_metric(raw, "eduforall_ratings_total"))
    active_users    = int(parse_metric(raw, "eduforall_active_users"))
    rec_sum         = parse_metric(raw, "eduforall_recommendations_count_sum")
    rec_count       = parse_metric(raw, "eduforall_recommendations_count_count")
    avg_recs        = round(rec_sum / rec_count, 1) if rec_count > 0 else 0

    # ── Stat Cards Row 1 ──────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon blue'>🔐</div>
            <div>
                <div class='stat-value'>{logins}</div>
                <div class='stat-label'>Total Logins</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon orange'>✍️</div>
            <div>
                <div class='stat-value'>{signups}</div>
                <div class='stat-label'>Total Signups</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon teal'>👥</div>
            <div>
                <div class='stat-value'>{active_users}</div>
                <div class='stat-label'>Active Users</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Stat Cards Row 2 ──────────────────────────────────────────────────────
    c4, c5, c6 = st.columns(3, gap="medium")
    with c4:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon blue'>🎯</div>
            <div>
                <div class='stat-value'>{recommendations}</div>
                <div class='stat-label'>Recommendations Loaded</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon orange'>⭐</div>
            <div>
                <div class='stat-value'>{ratings}</div>
                <div class='stat-label'>Ratings Submitted</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-icon teal'>📈</div>
            <div>
                <div class='stat-value'>{avg_recs}</div>
                <div class='stat-label'>Avg. Recommendations</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Bar Chart of all metrics ───────────────────────────────────────────────
    st.markdown("""
    <div class='section-header'>
        <span class='section-title'>Metrics Overview</span>
    </div>
    """, unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        x=["Logins", "Signups", "Recommendations", "Ratings", "Active Users"],
        y=[logins, signups, recommendations, ratings, active_users],
        marker=dict(
            color=["#0077BB", "#EE7733", "#0077BB", "#EE7733", "#009988"],
        ),
        text=[logins, signups, recommendations, ratings, active_users],
        textposition="outside",
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Sora", color="#3D5166", size=12),
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#F0F4F8")
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Refresh button ────────────────────────────────────────────────────────
    if st.button("🔄 Refresh Metrics", use_container_width=False):
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def dashboard_page():
    """
    Main dashboard — premium sidebar with user info and nav,
    dashboard header banner, and 3 content tabs.
    """
    user_id  = st.session_state.get("user_id")
    username = st.session_state.get("username", "Student")
    profile  = get_profile(user_id)
    ratings  = get_user_ratings(user_id)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:1.5rem 0 1rem 0;'>
            <div style='font-size:2rem;margin-bottom:0.5rem;'>🎓</div>
            <div style='font-family:Fraunces,serif;font-size:1.4rem;
                        color:white;font-weight:700;line-height:1.1;'>
                EduForAll
            </div>
            <div style='color:rgba(255,255,255,0.55);font-size:0.78rem;margin-top:4px;'>
                Adaptive Learning Platform
            </div>
        </div>
        <hr>
        <div style='margin-bottom:0.5rem;'>
            <div style='font-size:0.7rem;color:rgba(255,255,255,0.4);
                        text-transform:uppercase;letter-spacing:0.1em;
                        margin-bottom:8px;font-weight:600;'>
                Account
            </div>
            <div style='display:flex;align-items:center;gap:10px;
                        background:rgba(255,255,255,0.08);border-radius:10px;
                        padding:10px 12px;margin-bottom:1rem;'>
                <div style='width:36px;height:36px;border-radius:50%;
                            background:linear-gradient(135deg,#EE7733,#cc5500);
                            display:flex;align-items:center;justify-content:center;
                            font-size:1rem;font-weight:700;color:white;flex-shrink:0;'>
                    {username[0].upper()}
                </div>
                <div>
                    <div style='color:white;font-weight:600;font-size:0.88rem;'>{username}</div>
                    <div style='color:rgba(255,255,255,0.5);font-size:0.72rem;'>Student</div>
                </div>
            </div>
        </div>
        <div style='font-size:0.7rem;color:rgba(255,255,255,0.4);
                    text-transform:uppercase;letter-spacing:0.1em;
                    margin-bottom:8px;font-weight:600;'>
            Navigation
        </div>
        """, unsafe_allow_html=True)

        if st.button("✏️  Edit Profile", use_container_width=True):
            st.session_state["profile_complete"] = False
            st.session_state["editing_profile"] = True  # override DB check
            st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("🚪  Log Out", use_container_width=True):
            logout()
        st.markdown("</div>", unsafe_allow_html=True)

        # Profile summary in sidebar
        if profile:
            st.markdown(f"""
            <hr>
            <div style='font-size:0.7rem;color:rgba(255,255,255,0.4);
                        text-transform:uppercase;letter-spacing:0.1em;
                        margin-bottom:10px;font-weight:600;'>
                Profile Summary
            </div>
            <div style='font-size:0.78rem;color:rgba(255,255,255,0.7);
                        line-height:2;'>
                <b style='color:rgba(255,255,255,0.45);'>Type</b><br>
                {profile.get('disability_type','N/A')}<br>
                <b style='color:rgba(255,255,255,0.45);'>Severity</b><br>
                {profile.get('severity_level','N/A')}<br>
                <b style='color:rgba(255,255,255,0.45);'>Environment</b><br>
                {profile.get('study_environment','N/A')}
            </div>
            """, unsafe_allow_html=True)

    # ── Header Banner ─────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class='dash-header'>
        <div class='dash-header-pill'>DASHBOARD</div>
        <div class='dash-header-title'>Hello, {username}! 👋</div>
        <div class='dash-header-sub'>
            Here are your personalized learning insights and study strategies.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    st.markdown("<div style='padding:1.2rem 2.5rem 0 2.5rem;'>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊  Analytics", "🎯  Recommendations",
        "⭐  Rate Strategies", "📡  Live Metrics"
    ])
    st.markdown("</div>", unsafe_allow_html=True)

    with tab1:
        analytics_tab(profile, ratings)
    with tab2:
        recommendations_tab(profile)
    with tab3:
        rate_tab(profile, user_id)
    with tab4:
        metrics_tab()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Routes to the correct page based on authentication and profile state:
        Not logged in         → auth_page
        Logged in, no profile → profile_page
        Logged in + profile   → dashboard_page
    """
    if not is_authenticated():
        auth_page()
    elif st.session_state.get("editing_profile", False):
        # User clicked "Edit Profile" — go straight to profile page
        profile_page()
    elif not st.session_state.get("profile_complete", False):
        user_id = st.session_state.get("user_id")
        if get_profile(user_id):
            st.session_state["profile_complete"] = True
            dashboard_page()
        else:
            profile_page()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()