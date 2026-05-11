"""
DonorBridge prototype — reports, Hospitals / Patients CRUD, and Assistant (chatbot).
Run from this directory: streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import sys

import streamlit as st
import pandas as pd

import db

_CHATBOT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Chatbot"))
if os.path.isdir(_CHATBOT_ROOT) and _CHATBOT_ROOT not in sys.path:
    sys.path.insert(0, _CHATBOT_ROOT)

try:
    import chatbot_backend as chatbot_backend  # type: ignore

    _HAS_CHATBOT = True
except ImportError:
    chatbot_backend = None  # type: ignore[assignment]
    _HAS_CHATBOT = False


st.set_page_config(page_title="DonorBridge prototype", layout="wide")


@st.cache_resource
def _assistant_pg_connection():
    if not chatbot_backend:
        raise RuntimeError(
            "Chatbot backend is not importable (missing Chatbot/ folder?)."
        )
    return chatbot_backend.get_connection()

_LARGER_TYPE = """
<style>
/* Global readable typography (tables + prose + sidebar) */
html {
    font-size: 124%;
}
[data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] label {
    font-size: inherit !important;
}
[data-testid="stSidebarContent"] p,
[data-testid="stSidebarContent"] div,
[data-testid="stSidebarContent"] span,
[data-testid="stSidebarNav"] span {
    font-size: inherit !important;
}
[data-testid="stHeadingWithActionElements"] span,
[data-testid="stHeadingWithActionElements"] h1 {
    font-size: 1.85rem !important;
}

/* DonorBridge command-centre theme */
.stApp {
    background:
        radial-gradient(circle at 18% 8%, rgba(45, 212, 191, 0.18), transparent 28%),
        radial-gradient(circle at 88% 18%, rgba(56, 189, 248, 0.14), transparent 30%),
        linear-gradient(135deg, #eefdfa 0%, #f1f5f9 42%, #e8f4fb 100%) !important;
}
.main .block-container {
    max-width: 1180px;
    padding-top: 2rem;
}
[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 10% 10%, rgba(94, 234, 212, 0.2), transparent 28%),
        linear-gradient(180deg, #062925 0%, #073b36 52%, #0f172a 100%) !important;
}
[data-testid="stSidebarContent"] {
    color: rgba(255, 255, 255, 0.84) !important;
}
[data-testid="stSidebarContent"] h1,
[data-testid="stSidebarContent"] h2,
[data-testid="stSidebarContent"] h3,
[data-testid="stSidebarContent"] p,
[data-testid="stSidebarContent"] span,
[data-testid="stSidebarContent"] label {
    color: rgba(255, 255, 255, 0.86) !important;
}
[data-testid="stSidebarContent"] code {
    color: #99f6e4 !important;
    background: rgba(255, 255, 255, 0.1) !important;
}
[data-testid="stSidebarContent"] div[data-testid="stAlert"] {
    border-color: rgba(94, 234, 212, 0.32) !important;
    background: rgba(16, 185, 129, 0.16) !important;
}
[data-testid="stSidebarContent"] .stButton button,
[data-testid="stSidebarContent"] .stButton button *,
[data-testid="stSidebarContent"] div[data-testid="stButton"] button,
[data-testid="stSidebarContent"] div[data-testid="stButton"] button * {
    color: #063b35 !important;
}
.app-hero {
    position: relative;
    overflow: hidden;
    margin-bottom: 1.35rem;
    padding: 1.5rem 1.7rem;
    border: 1px solid rgba(13, 148, 136, 0.2);
    border-radius: 28px;
    color: #ffffff;
    background:
        radial-gradient(circle at 12% 18%, rgba(94, 234, 212, 0.36), transparent 30%),
        radial-gradient(circle at 92% 8%, rgba(56, 189, 248, 0.25), transparent 32%),
        linear-gradient(135deg, #062925 0%, #073b36 48%, #0f172a 100%);
    box-shadow: 0 28px 80px rgba(15, 23, 42, 0.2);
}
.app-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    opacity: 0.18;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.12) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.12) 1px, transparent 1px);
    background-size: 44px 44px;
}
.app-hero > * {
    position: relative;
    z-index: 1;
}
.app-hero h1 {
    margin: 0;
    color: #ffffff;
    font-size: 2.1rem;
    letter-spacing: -0.05em;
}
.app-hero p {
    max-width: 760px;
    margin: 0.45rem 0 0;
    color: rgba(255, 255, 255, 0.78);
    line-height: 1.55;
}
.app-hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1rem;
}
.app-hero-pills span {
    padding: 0.4rem 0.7rem;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 999px;
    color: rgba(255, 255, 255, 0.84);
    background: rgba(255, 255, 255, 0.1);
    font-size: 0.78rem;
    font-weight: 800;
}
[data-testid="stTabs"] [role="tab"] {
    font-size: 1.12rem !important;
    padding-top: 0.45rem !important;
    padding-bottom: 0.45rem !important;
}
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] button,
.stButton button {
    font-size: 1.06rem !important;
    padding: 0.5rem 0.95rem !important;
}
[data-testid="stExpander"] summary {
    font-size: 1.08rem !important;
}
.block-container div[data-testid="stDataFrame"] {
    zoom: 1.08 !important;
}
.main .block-container {
    font-size: 1.04rem !important;
}

/* Care Clarity — tabs & expanders (teal accent) */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0.25rem;
    padding: 0.35rem;
    border: 1px solid rgba(13, 148, 136, 0.16);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.7);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 999px;
    color: #0f172a !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-bottom-color: transparent !important;
    background: linear-gradient(135deg, #0d9488, #0284c7) !important;
    box-shadow: 0 12px 28px rgba(13, 148, 136, 0.24);
}
[data-testid="stExpander"] details {
    overflow: hidden;
    border: 1px solid rgba(13, 148, 136, 0.18) !important;
    border-radius: 18px !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.96)) !important;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.07) !important;
}
[data-testid="stExpander"] summary {
    color: #0f172a !important;
    background: linear-gradient(90deg, rgba(13, 148, 136, 0.1), rgba(56, 189, 248, 0.08));
    border-radius: 16px !important;
    font-weight: 800 !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid rgba(13, 148, 136, 0.16);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}
[data-testid="stAlert"] {
    border-radius: 16px !important;
}
.stButton button {
    border: 1px solid rgba(13, 148, 136, 0.28) !important;
    border-radius: 999px !important;
    color: #0f766e !important;
    background: linear-gradient(135deg, #ffffff, #ecfeff) !important;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07) !important;
    font-weight: 800 !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton button:hover {
    border-color: #0d9488 !important;
    color: #063b35 !important;
    transform: translateY(-1px);
    box-shadow: 0 14px 34px rgba(13, 148, 136, 0.18) !important;
}
.risk-legend {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.7rem;
    margin: 0.85rem 0 1rem;
}
.risk-chip {
    padding: 0.75rem 0.85rem;
    border-radius: 16px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}
.risk-chip strong {
    display: block;
    margin-bottom: 0.2rem;
    color: #0f172a;
}
.risk-chip span {
    color: #334155;
    font-size: 0.78rem;
    font-weight: 700;
}
.risk-low {
    background: linear-gradient(135deg, #dcfce7, #bbf7d0);
}
.risk-moderate {
    background: linear-gradient(135deg, #fef9c3, #fde68a);
}
.risk-high {
    background: linear-gradient(135deg, #ffedd5, #fed7aa);
}
.risk-critical {
    background: linear-gradient(135deg, #fee2e2, #fecaca);
}
@media (max-width: 760px) {
    .risk-legend {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

/* Form widgets — visible outlines on light backgrounds */
[data-testid="stTextInput"] input[type="text"],
[data-testid="stTextInput"] input:not([type]) {
    border: 1px solid #94a3b8 !important;
    border-radius: 10px !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
    padding: 0.45rem 0.65rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #0d9488 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.2) !important;
}
[data-testid="stNumberInput"] input {
    border: 1px solid #94a3b8 !important;
    border-radius: 10px !important;
    background-color: #f8fafc !important;
    color: #0f172a !important;
}
[data-testid="stNumberInput"] input:focus {
    border-color: #0d9488 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.2) !important;
}
[data-testid="stNumberInput"] button {
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background: #f1f5f9 !important;
}
/* Select boxes (Base Web + newer builds) */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border-color: #94a3b8 !important;
    border-radius: 10px !important;
    background-color: #f8fafc !important;
}
[data-testid="stSelectbox"]:focus-within div[data-baseweb="select"] > div {
    border-color: #0d9488 !important;
    box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.15) !important;
}

/* Assistant — chat (light clinical, matches Chatbot/static) */
[data-testid="stChatMessage"] {
    background: rgba(13, 148, 136, 0.08) !important;
    border: 1px solid rgba(13, 148, 136, 0.22) !important;
    border-radius: 16px !important;
    padding: 0.55rem 0.65rem !important;
    margin-bottom: 0.6rem !important;
    box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    line-height: 1.55;
    color: #0f172a;
}
[data-testid="stChatInput"] textarea {
    border-radius: 14px !important;
    border: 1px solid #cbd5e1 !important;
    background: #ffffff !important;
    color: #0f172a !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #0d9488 !important;
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2) !important;
}
.stChatInputToolbar {
    padding-bottom: 0.35rem !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: #0d9488 !important;
    border: none !important;
    color: #ffffff !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    background: #0f766e !important;
}

/* DonorBridge landing screen */
.donorbridge-landing {
    position: relative;
    min-height: auto;
    overflow: hidden;
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
    gap: 1.6rem 2.4rem;
    align-items: start;
    padding: clamp(1.6rem, 4vw, 3rem);
    border-radius: 34px;
    color: #ffffff;
    background:
        radial-gradient(circle at 18% 18%, rgba(45, 212, 191, 0.34), transparent 28%),
        radial-gradient(circle at 85% 12%, rgba(56, 189, 248, 0.26), transparent 30%),
        linear-gradient(135deg, #062925 0%, #073b36 42%, #0f172a 100%);
    box-shadow: 0 36px 100px rgba(15, 23, 42, 0.28);
}
.donorbridge-landing::before {
    content: "";
    position: absolute;
    inset: 18px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 26px;
    pointer-events: none;
}
.donorbridge-landing::after {
    content: "";
    position: absolute;
    inset: 0;
    opacity: 0.22;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
    background-size: 58px 58px;
    mask-image: radial-gradient(circle at center, #000 0%, transparent 72%);
}
.landing-copy,
.landing-preview {
    position: relative;
    z-index: 1;
}
.landing-preview {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.85rem;
}
.landing-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    margin-bottom: 1.2rem;
    padding: 0.45rem 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 999px;
    color: rgba(255, 255, 255, 0.78);
    background: rgba(255, 255, 255, 0.08);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.landing-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background: #5eead4;
    box-shadow: 0 0 20px rgba(94, 234, 212, 0.9);
}
.landing-copy h1 {
    margin: 0;
    color: #ffffff;
    font-size: clamp(3rem, 7vw, 6.4rem);
    line-height: 0.9;
    letter-spacing: -0.08em;
}
.landing-copy p {
    max-width: 620px;
    margin: 1rem 0 0;
    color: rgba(255, 255, 255, 0.76);
    font-size: clamp(1rem, 2vw, 1.25rem) !important;
    line-height: 1.6;
}
.landing-preview-card {
    width: min(390px, 100%);
    margin-left: auto;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.12);
    box-shadow: 0 28px 80px rgba(0, 0, 0, 0.26);
    backdrop-filter: blur(22px);
}
.landing-preview-title {
    color: rgba(255, 255, 255, 0.74);
    font-size: 0.76rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.landing-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    margin: 1rem 0;
}
.landing-stat {
    padding: 1rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.12);
}
.landing-stat strong {
    display: block;
    color: #ffffff;
    font-size: 2rem;
    line-height: 1;
}
.landing-stat span {
    display: block;
    margin-top: 0.45rem;
    color: rgba(255, 255, 255, 0.66);
    font-size: 0.75rem;
}
.landing-bar {
    height: 0.75rem;
    margin-top: 0.62rem;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.16);
}
.landing-bar span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #5eead4, #38bdf8);
}
.landing-feature-grid {
    position: relative;
    z-index: 1;
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 0;
}
.landing-feature-card {
    min-height: 116px;
    padding: 0.85rem;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(18px);
}
.landing-feature-card strong {
    display: block;
    margin-bottom: 0.45rem;
    color: #ffffff;
    font-size: 0.95rem;
}
.landing-feature-card span {
    display: block;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.78rem;
    line-height: 1.5;
}
.landing-cta div[data-testid="stButton"] button {
    min-height: 3.2rem;
    padding: 0 1.5rem !important;
    border: none !important;
    border-radius: 999px !important;
    color: #063b35 !important;
    background: linear-gradient(135deg, #ffffff, #99f6e4) !important;
    box-shadow: 0 22px 55px rgba(20, 184, 166, 0.32) !important;
    font-weight: 900 !important;
}
.landing-cta div[data-testid="stButton"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 28px 65px rgba(20, 184, 166, 0.42) !important;
}
@media (max-width: 900px) {
    .donorbridge-landing {
        grid-template-columns: 1fr;
        padding: 2rem;
    }
    .landing-preview-card {
        margin-left: 0;
    }
    .landing-feature-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (max-width: 620px) {
    .landing-feature-grid {
        grid-template-columns: 1fr;
    }
}

</style>
"""
st.markdown(_LARGER_TYPE, unsafe_allow_html=True)


def landing_page():
    if st.session_state.get("entered_donorbridge", False):
        return

    st.markdown(
        """
        <div class="donorbridge-landing">
            <div class="landing-copy">
                <div class="landing-eyebrow">
                    <span class="landing-dot"></span>
                    Healthcare resource intelligence
                </div>
                <h1>DonorBridge</h1>
                <p>
                    A smarter command center for blood inventory, donors,
                    transplant requests, and hospital risk signals.
                </p>
            </div>
            <div class="landing-preview">
                <div class="landing-preview-card">
                    <div class="landing-preview-title">App capabilities</div>
                    <div class="landing-stats">
                        <div class="landing-stat">
                            <strong>Reports</strong>
                            <span>Live database views</span>
                        </div>
                        <div class="landing-stat">
                            <strong>Q&A</strong>
                            <span>Guided assistant</span>
                        </div>
                    </div>
                    <div class="landing-bar"><span style="width: 82%"></span></div>
                    <div class="landing-bar"><span style="width: 64%"></span></div>
                    <div class="landing-bar"><span style="width: 46%"></span></div>
                </div>
            </div>
            <div class="landing-feature-grid">
                <div class="landing-feature-card">
                    <strong>Operational reports</strong>
                    <span>
                        Review request load, blood availability, supply gaps,
                        organ offers, and transplant progress from one centre.
                    </span>
                </div>
                <div class="landing-feature-card">
                    <strong>Hospital coordination</strong>
                    <span>
                        Manage hospital records and keep each site aligned with
                        current resource and contact information.
                    </span>
                </div>
                <div class="landing-feature-card">
                    <strong>Patient oversight</strong>
                    <span>
                        Track patient records, risk scores, blood groups, and
                        hospital assignment for faster follow-up.
                    </span>
                </div>
                <div class="landing-feature-card">
                    <strong>Assistant support</strong>
                    <span>
                        Ask natural-language questions about donors, inventory,
                        requests, matches, and audit-backed insights.
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-cta">', unsafe_allow_html=True)
    if st.button("Open DonorBridge", type="primary"):
        st.session_state.entered_donorbridge = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


landing_page()

st.markdown(
    """
    <div class="app-hero">
        <h1>DonorBridge Command Centre</h1>
        <p>
            Monitor healthcare resource flows, manage hospital and patient
            records, and ask the assistant database-backed operational questions.
        </p>
        <div class="app-hero-pills">
            <span>Reports</span>
            <span>Hospitals</span>
            <span>Patients</span>
            <span>Assistant</span>
            <span>Audit-ready insights</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

REPORT_VIEWS = (
    ("Open requests by hospital", "SELECT * FROM report_open_requests_by_hospital"),
    ("Available blood units by site", "SELECT * FROM report_available_blood_units_by_site"),
    ("Blood need vs supply", "SELECT * FROM report_blood_need_vs_supply"),
    ("Organ offer pipeline", "SELECT * FROM report_organ_offer_pipeline"),
    ("Match / transplant status", "SELECT * FROM report_match_and_transplant_status"),
    ("Assistant audit trail", "SELECT * FROM report_assistant_audit_trail"),
)

SAMPLE_QUESTIONS = (
    "What is the inventory for O- blood?",
    "Is there any O blood group available?",
    "Is there any shortage or low stock?",
    "Who are the high-risk patients?",
    "List all patients.",
    "Who should get the next kidney transplant?",
    "Show me the eligible donors.",
    "Show me recent blood donations.",
    "List the pending requests.",
    "Show me the match candidates.",
    "Which blood units are expiring soon?",
    "Show me the transplant history.",
    "List all hospitals.",
    "Why is Hospital 1 at risk?",
)

RISK_BANDS = (
    ("Low", 0, 49.99, "#dcfce7"),
    ("Moderate", 50, 69.99, "#fef9c3"),
    ("High", 70, 84.99, "#ffedd5"),
    ("Critical", 85, 100, "#fee2e2"),
)


def risk_category(score):
    value = float(score or 0)
    if value >= 85:
        return "Critical"
    if value >= 70:
        return "High"
    if value >= 50:
        return "Moderate"
    return "Low"


def risk_row_style(row):
    colors = {
        "Low": "background-color: rgba(34, 197, 94, 0.14)",
        "Moderate": "background-color: rgba(234, 179, 8, 0.18)",
        "High": "background-color: rgba(249, 115, 22, 0.18)",
        "Critical": "background-color: rgba(239, 68, 68, 0.18)",
    }
    return [colors.get(row.get("risk_category"), "") for _ in row]


def patient_dataframe(rows):
    df = pd.DataFrame(rows)
    if df.empty or "risk_score" not in df:
        return df
    df["risk_category"] = df["risk_score"].apply(risk_category)
    return df.style.apply(risk_row_style, axis=1).format({"risk_score": "{:.2f}"})


def render_risk_legend():
    st.markdown(
        """
        <div class="risk-legend">
            <div class="risk-chip risk-low">
                <strong>Low</strong><span>0-49.99</span>
            </div>
            <div class="risk-chip risk-moderate">
                <strong>Moderate</strong><span>50-69.99</span>
            </div>
            <div class="risk-chip risk-high">
                <strong>High</strong><span>70-84.99</span>
            </div>
            <div class="risk-chip risk-critical">
                <strong>Critical</strong><span>85-100</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_connection():
    if st.sidebar.button("Show opening page"):
        st.session_state.entered_donorbridge = False
        st.rerun()

    st.sidebar.divider()
    st.sidebar.header("Database")
    st.sidebar.markdown(
        "Set **`DATABASE_URL`** before launch (see [README.md](README.md))."
    )
    if st.sidebar.button("Test connection"):
        try:
            db.test_connection()
            st.sidebar.success("Connection OK")
        except Exception as exc:
            st.sidebar.error(str(exc))


sidebar_connection()

tab_reports, tab_hospitals, tab_patients, tab_assistant = st.tabs(
    ["Reports", "Hospitals", "Patients", "Assistant"],
)

with tab_reports:
    st.subheader("Business reports (PostgreSQL views)")
    st.markdown(
        "Ensure you have executed **`database/queries_reports.sql`** once "
        "(creates/replaces `report_*` views)."
    )
    for title, sql in REPORT_VIEWS:
        try:
            rows = db.fetch_all(sql)
        except Exception as exc:
            st.error(f"**{title}** — `{exc}`")
            continue
        with st.expander(title, expanded=False):
            if not rows:
                st.caption("(no rows)")
            else:
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tab_hospitals:
    st.subheader("Hospitals — retrieval and manipulation")

    try:
        hospitals = db.fetch_all(
            "SELECT hospital_id, name, location, contact FROM hospital ORDER BY hospital_id"
        )
        st.dataframe(pd.DataFrame(hospitals), use_container_width=True)
    except Exception as exc:
        st.error(str(exc))
        hospitals = []

    add = st.expander("Add hospital", expanded=False)
    with add:
        name = st.text_input("Name", key="h_add_name")
        location = st.text_input("Location", key="h_add_loc")
        contact = st.text_input("Contact", key="h_add_contact")
        if st.button("Insert hospital"):
            try:
                db.execute(
                    "INSERT INTO hospital (name, location, contact) VALUES (%s,%s,%s)",
                    (name.strip(), location.strip(), contact.strip()),
                )
                st.success("Inserted.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    upd = st.expander("Update hospital", expanded=False)
    with upd:
        ids = [h["hospital_id"] for h in hospitals]
        if not ids:
            st.info("No hospitals loaded.")
        else:
            hid = st.selectbox("Hospital ID", options=ids, key="h_upd_pick")
            sel = next((x for x in hospitals if x["hospital_id"] == hid), {})
            name_u = st.text_input("Name", value=sel.get("name", ""), key="h_upd_name")
            loc_u = st.text_input(
                "Location",
                value=sel.get("location", ""),
                key="h_upd_loc",
            )
            ct_u = st.text_input(
                "Contact",
                value=sel.get("contact", ""),
                key="h_upd_ct",
            )
            if st.button("Save changes", key="h_upd_btn"):
                try:
                    db.execute(
                        "UPDATE hospital SET name=%s, location=%s, contact=%s "
                        "WHERE hospital_id=%s",
                        (
                            name_u.strip(),
                            loc_u.strip(),
                            ct_u.strip(),
                            hid,
                        ),
                    )
                    st.success("Updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    dele = st.expander("Delete hospital (blocked if dependents exist)", expanded=False)
    with dele:
        ids = [h["hospital_id"] for h in hospitals]
        if not ids:
            st.info("No hospitals to delete.")
        else:
            hid_d = st.selectbox(
                "Hospital ID to delete",
                options=ids,
                key="h_del_pick",
            )
            confirm = st.checkbox(
                "I understand this deletes the row (only if FKs allow).",
                key="h_del_ck",
            )
            if st.button("Delete hospital", key="h_del_btn"):
                if not confirm:
                    st.warning("Confirm before deleting.")
                else:
                    try:
                        n = db.execute(
                            "DELETE FROM hospital WHERE hospital_id=%s",
                            (hid_d,),
                        )
                        st.success(f"Deleted {n} row(s).") if n else st.info(
                            "Nothing deleted."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

with tab_patients:
    st.subheader("Patients — retrieval, add, update, delete")
    st.caption("Patient risk scores use a 0-100 scale.")
    render_risk_legend()

    try:
        patients = db.fetch_all(
            """
            SELECT p.patient_id, p.hospital_id, p.full_name, p.age,
                   p.gender, p.blood_group, p.contact_info, p.risk_score,
                   p.created_at, h.name AS hospital_name
            FROM patient p
            JOIN hospital h ON h.hospital_id = p.hospital_id
            ORDER BY p.patient_id
            """
        )
        st.dataframe(patient_dataframe(patients), use_container_width=True)
        hosp_opts = db.fetch_all(
            "SELECT hospital_id, name FROM hospital ORDER BY hospital_id"
        )
    except Exception as exc:
        st.error(str(exc))
        patients = []
        hosp_opts = []

    pa = st.expander("Add patient", expanded=False)
    with pa:
        if not hosp_opts:
            st.info("Load hospitals before adding patients.")
        else:
            labels = {
                f'{r["name"]} (#{r["hospital_id"]})': r["hospital_id"] for r in hosp_opts
            }
            choice = st.selectbox(
                "Hospital",
                options=list(labels.keys()),
                key="p_add_hosp_lab",
            )
            hosp_id = labels[choice]
            full_name = st.text_input("Full name", key="p_add_fn")
            age = st.number_input("Age", min_value=0, max_value=150, value=40, key="p_add_age")
            gender = st.text_input("Gender (e.g. M / F)", value="M", key="p_add_g")
            blood_group = st.text_input(
                "Blood group (e.g. O+)", value="O+", key="p_add_bg"
            )
            contact_info = st.text_input("Contact info", key="p_add_ci")
            risk_score = st.number_input(
                "Risk score (0-100)",
                min_value=0.0,
                max_value=100.0,
                value=55.55,
                step=0.01,
                key="p_add_rs",
            )
            if st.button("Insert patient", key="p_add_btn"):
                try:
                    db.execute(
                        """
                        INSERT INTO patient (
                            hospital_id, full_name, age, gender,
                            blood_group, contact_info, risk_score
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            hosp_id,
                            full_name.strip(),
                            int(age),
                            gender.strip(),
                            blood_group.strip(),
                            contact_info.strip(),
                            float(risk_score),
                        ),
                    )
                    st.success("Inserted.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    pu = st.expander("Update patient", expanded=False)
    with pu:
        pids = [p["patient_id"] for p in patients] if patients else []
        if not pids:
            st.info("No patients.")
        else:
            pid = st.selectbox("Patient ID", options=pids, key="p_upd_pick")
            cur = next((x for x in patients if x["patient_id"] == pid), {})
            nh = cur.get("hospital_id")
            hosp_labels = [
                (f'{r["name"]} (#{r["hospital_id"]})', r["hospital_id"])
                for r in hosp_opts
            ]
            hosp_default_idx = next(
                (i for i, (_, hid) in enumerate(hosp_labels) if hid == nh),
                0,
            )
            hchoice = st.selectbox(
                "Hospital",
                options=[x[0] for x in hosp_labels],
                index=hosp_default_idx,
                key="p_upd_hosp_lab",
            )
            new_hospital_id = dict(hosp_labels)[hchoice] if hosp_labels else nh
            fn = st.text_input(
                "Full name",
                value=str(cur.get("full_name", "")),
                key="p_upd_fn",
            )
            ag = st.number_input(
                "Age",
                min_value=0,
                max_value=150,
                value=int(cur.get("age", 0)),
                key="p_upd_ag",
            )
            gd = st.text_input(
                "Gender",
                value=str(cur.get("gender", "")),
                key="p_upd_ge",
            )
            bg = st.text_input(
                "Blood group",
                value=str(cur.get("blood_group", "")),
                key="p_upd_bg",
            )
            ci = st.text_input(
                "Contact info",
                value=str(cur.get("contact_info", "")),
                key="p_upd_ci",
            )
            rs = st.number_input(
                "Risk score (0-100)",
                min_value=0.0,
                max_value=100.0,
                value=min(max(float(cur.get("risk_score", 0)), 0.0), 100.0),
                step=0.01,
                key="p_upd_rs",
            )
            if st.button("Save patient", key="p_upd_btn"):
                try:
                    db.execute(
                        """
                        UPDATE patient SET
                            hospital_id=%s, full_name=%s, age=%s,
                            gender=%s, blood_group=%s,
                            contact_info=%s, risk_score=%s
                        WHERE patient_id=%s
                        """,
                        (
                            new_hospital_id,
                            fn.strip(),
                            ag,
                            gd.strip(),
                            bg.strip(),
                            ci.strip(),
                            float(rs),
                            pid,
                        ),
                    )
                    st.success("Updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    pdel = st.expander("Delete patient (cascade medical_record per schema)", expanded=False)
    with pdel:
        pids = [p["patient_id"] for p in patients] if patients else []
        if not pids:
            st.info("No patients.")
        else:
            dp = st.selectbox("Patient ID to delete", options=pids, key="p_del_pick")
            c2 = st.checkbox("Confirm patient delete", key="p_del_ck")
            if st.button("Delete patient", key="p_del_btn"):
                if not c2:
                    st.warning("Confirm first.")
                else:
                    try:
                        n = db.execute(
                            "DELETE FROM patient WHERE patient_id=%s", (dp,)
                        )
                        st.success(f"Deleted {n} row(s).") if n else st.info(
                            "Nothing deleted."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


with tab_assistant:
    st.subheader("Natural-language assistant")
    st.caption(
        "Rule-based Q&A on the same PostgreSQL data (inventory, patients, "
        "requests, transplants). Run **`database/chatbot_sql_template_seed.sql`** "
        "so chat audit (`sql_template`) is populated."
    )

    if not _HAS_CHATBOT or chatbot_backend is None:
        st.warning(
            "The **Chatbot** package was not found. Expected folder "
            "`DonorBridge/Chatbot` next to this `prototype` directory."
        )
        st.stop()

    try:
        conn_asst = _assistant_pg_connection()
    except Exception as exc:
        st.error(f"Assistant could not connect (check DATABASE_URL): {exc}")
        st.stop()

    try:
        hospital_rows_asst = db.fetch_all(
            "SELECT hospital_id, name FROM hospital ORDER BY hospital_id"
        )
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if not hospital_rows_asst:
        st.info("No hospitals in the database — load seed data first.")
        st.stop()

    hid_opts = [(r["hospital_id"], r["name"]) for r in hospital_rows_asst]

    assistant_hospital_id = st.selectbox(
        "Scope answers to hospital",
        options=[x[0] for x in hid_opts],
        format_func=lambda i: next(n for hid, n in hid_opts if hid == i),
        key="asst_hospital_id",
    )
    assistant_role = st.selectbox(
        "Recorded role (audit)",
        ["Doctor", "Nurse", "Coordinator", "Admin"],
        index=0,
        key="asst_user_role",
    )

    if st.button("New assistant conversation", key="asst_reset"):
        st.session_state.assistant_session_id = None
        st.session_state.assistant_messages = []
        st.rerun()

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []
    if "assistant_session_id" not in st.session_state:
        st.session_state.assistant_session_id = None

    if st.session_state.assistant_session_id is None:
        st.caption(
            f"No audit session yet — **send a question** to start one "
            f"(hospital #{assistant_hospital_id} scope)."
        )
    else:
        st.caption(
            f"Session #{st.session_state.assistant_session_id} · "
            f"hospital #{assistant_hospital_id} context."
        )

    sample_prompt = None
    with st.expander("Sample questions you can ask", expanded=True):
        st.caption("Click a question to send it to the assistant.")
        sample_cols = st.columns(2)
        for idx, question in enumerate(SAMPLE_QUESTIONS):
            if sample_cols[idx % 2].button(
                question,
                key=f"sample_question_{idx}",
                use_container_width=True,
            ):
                sample_prompt = question

    for msg in st.session_state.assistant_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    chat_prompt = st.chat_input("Ask about donors, inventory, requests…")
    prompt = sample_prompt or chat_prompt
    if prompt:
        if st.session_state.assistant_session_id is None:
            st.session_state.assistant_session_id = chatbot_backend.start_chat_session(
                conn_asst,
                assistant_hospital_id or chatbot_backend.DEFAULT_HOSPITAL_ID,
                assistant_role,
            )
        st.session_state.assistant_messages.append(
            {"role": "user", "content": prompt}
        )
        reply = chatbot_backend.process_user_query(
            conn_asst,
            prompt,
            assistant_hospital_id or chatbot_backend.DEFAULT_HOSPITAL_ID,
            st.session_state.assistant_session_id,
        )
        st.session_state.assistant_messages.append(
            {"role": "assistant", "content": reply}
        )
        st.rerun()
