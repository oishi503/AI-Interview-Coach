import streamlit as st
from modules.interview import load_questions, get_question
from modules.evaluator import get_similarity_score
from modules.feedback import get_feedback
from modules.dashboard import compute_topic_averages, get_strengths_and_weaknesses, plot_topic_scores
from modules.resume_parser import extract_text_from_pdf, extract_skills_and_generate_questions, generate_questions_for_role
from database.db import (init_db, signup_user, login_user,
                          save_session, save_answer,
                          get_user_sessions, get_session_answers, get_user_stats)

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="AI Interview Coach", page_icon="🤖", layout="centered")

# ── Session state init ────────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",
        "role": None,
        "questions": [],
        "q_index": 0,
        "session_results": [],
        "current_feedback": None,
        "resume_data": None,
        "generating_role": None,
        "weak_areas": [],
        "user": None,           
        "session_id": None, 
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def reset_interview_state():
    """Reset only interview data, preserve user session"""
    st.session_state.page = "home"
    st.session_state.role = None
    st.session_state.questions = []
    st.session_state.q_index = 0
    st.session_state.session_results = []
    st.session_state.current_feedback = None
    st.session_state.resume_data = None
    st.session_state.generating_role = None
    st.session_state.session_id = None

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0a0f; color: #e2e8f0; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 900px; }
    h1 {
        background: linear-gradient(135deg, #a855f7, #6366f1, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 0.5rem !important;
    }
    h2, h3 { color: #c4b5fd !important; font-weight: 600 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #9333ea, #6366f1) !important;
        box-shadow: 0 6px 25px rgba(124, 58, 237, 0.5) !important;
        transform: translateY(-2px) !important;
    }
    .stTextArea > div > div > textarea {
        background: #13131f !important;
        border: 1px solid #3b3b5c !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        padding: 1rem !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25) !important;
    }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #13131f, #1a1a2e) !important;
        border: 1px solid #3b3b5c !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
        text-align: center !important;
    }
    [data-testid="metric-container"] label {
        color: #a855f7 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e2e8f0 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #06b6d4) !important;
        border-radius: 10px !important;
    }
    .stProgress > div > div { background: #1a1a2e !important; border-radius: 10px !important; }
    .streamlit-expanderHeader {
        background: #13131f !important;
        border: 1px solid #3b3b5c !important;
        border-radius: 10px !important;
        color: #c4b5fd !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderContent {
        background: #13131f !important;
        border: 1px solid #3b3b5c !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        color: #e2e8f0 !important;
    }
    .stAlert { border-radius: 12px !important; border: none !important; }
    [data-baseweb="notification"] {
        background: #13131f !important;
        border-left: 4px solid #7c3aed !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    .stSuccess {
        background: linear-gradient(135deg, #052e16, #14532d) !important;
        border: 1px solid #16a34a !important;
        border-radius: 10px !important;
        color: #86efac !important;
    }
    .stError {
        background: linear-gradient(135deg, #2d0a0a, #450a0a) !important;
        border: 1px solid #dc2626 !important;
        border-radius: 10px !important;
        color: #fca5a5 !important;
    }
    [data-testid="stFileUploader"] {
        background: #13131f !important;
        border: 2px dashed #3b3b5c !important;
        border-radius: 16px !important;
        padding: 1rem !important;
    }
    .stCaption { color: #6b7280 !important; font-size: 0.85rem !important; }
    hr { border-color: #3b3b5c !important; }
    code {
        background: #1a1a2e !important;
        color: #c4b5fd !important;
        border-radius: 6px !important;
        padding: 0.2rem 0.4rem !important;
    }
    pre {
        background: #13131f !important;
        border: 1px solid #3b3b5c !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    .stSpinner > div { border-top-color: #7c3aed !important; }
    .question-card {
        background: linear-gradient(135deg, #13131f, #1a1a2e);
        border: 1px solid #3b3b5c;
        border-left: 4px solid #7c3aed;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
    }
    div[data-testid="column"] .stButton > button {
        width: 100%;
        padding: 1rem !important;
        font-size: 0.85rem !important;
        border-radius: 12px !important;
    }
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background: linear-gradient(135deg, #9333ea, #6366f1) !important;
    }
    [data-testid="stFileUploader"] section {
        background: #13131f !important;
        border: 2px dashed #7c3aed !important;
        border-radius: 16px !important;
    }
    /* ── Confetti ── */
@keyframes fall {
    0% { transform: translateY(-10px) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}
.confetti-piece {
    position: fixed;
    width: 10px;
    height: 10px;
    top: -10px;
    opacity: 0;
    animation: fall linear forwards;
    z-index: 9999;
    border-radius: 2px;
}
/* ── Metric values brighter ── */
[data-testid="metric-container"] label {
    color: #a855f7 !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}
                
/* ── Form submit buttons ── */
[data-testid="stForm"] button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

[data-testid="stForm"] button:hover {
    background: linear-gradient(135deg, #9333ea, #6366f1) !important;
}

/* ── Form inputs dark theme ── */
[data-testid="stForm"] input {
    background: #13131f !important;
    color: #e2e8f0 !important;
    border: 1px solid #3b3b5c !important;
    border-radius: 10px !important;
}
                
/* ── Fix password eye icon inside input ── */
[data-testid="stTextInput"] div[data-testid="InputInstructions"] {
    display: none !important;
}

[data-testid="stTextInput"] > div > div {
    background: #13131f !important;
    border: 1px solid #3b3b5c !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stTextInput"] > div > div > div {
    background: #13131f !important;
}

[data-testid="stTextInput"] button {
    background: #13131f !important;
    border: none !important;
    border-left: 1px solid #3b3b5c !important;
    color: #a855f7 !important;
    border-radius: 0 !important;
}

[data-testid="stTextInput"] button:hover {
    background: #1a1a2e !important;
}
                
/* ── Password input dark fix ── */
[data-testid="stTextInput"] input {
    background: #13131f !important;
    color: #e2e8f0 !important;
    border: none !important;
}

[data-testid="stTextInput"] > div > div {
    background: #13131f !important;
    border: 1px solid #3b3b5c !important;
    border-radius: 10px !important;
}

[data-testid="stTextInput"] > div > div:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25) !important;
}

[data-testid="stTextInput"] button {
    background: #13131f !important;
    border: none !important;
    color: #a855f7 !important;
}

[data-testid="stTextInput"] button:hover {
    background: #1a1a2e !important;
    color: #c4b5fd !important;
}

/* ── Form container dark ── */
[data-testid="stForm"] {
    background: #13131f !important;
    border: 1px solid #3b3b5c !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
}
                
/* ── Remove white space next to eye icon ── */
[data-testid="stTextInput"] > div {
    background: #13131f !important;
    border-radius: 10px !important;
}

[data-testid="stTextInput"] > div > div > div {
    background: #13131f !important;
    border-radius: 10px !important;
}

[data-testid="stTextInput"] button {
    background: #13131f !important;
    border: none !important;
    border-radius: 0 10px 10px 0 !important;
    color: #a855f7 !important;
    margin: 0 !important;
    padding: 0 0.5rem !important;
}
                
/* ── Remove extra border/line on password input ── */
[data-testid="stTextInput"] > div > div {
    border: none !important;
    box-shadow: none !important;
}

[data-testid="stTextInput"] > div {
    border: 1px solid #3b3b5c !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stTextInput"] > div:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.25) !important;
}

/* ── Remove double border on focus ── */
[data-testid="stTextInput"] > div > div {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stTextInput"] > div > div:focus-within {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}

[data-testid="stTextInput"] input:focus {
    box-shadow: none !important;
    outline: none !important;
}
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()
init_db()

# ── Top nav (shown when logged in) ───────────────────────────
if st.session_state.user:
    col_name, col_profile, col_logout = st.columns([4, 1, 1])
    with col_name:
        st.markdown(f"""
        <p style="color:#94a3b8; font-size:0.85rem; padding-top:0.5rem;">
            Welcome, <span style="color:#a855f7; font-weight:600;">
            {st.session_state.user['name']}</span>
        </p>
        """, unsafe_allow_html=True)
    with col_profile:
        if st.button("👤 Profile"):
            st.session_state.page = "profile"
            st.rerun()
    with col_logout:
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ── LOGIN PAGE ────────────────────────────────────────────────
# ── AUTH GATE ─────────────────────────────────────────────────
if st.session_state.user is None and st.session_state.page not in ["login", "signup", "landing"]:
    st.session_state.page = "landing"
    st.rerun()

if st.session_state.page == "landing":
    st.markdown("""
    <div style="text-align:center; padding: 4rem 0 2rem 0;">
        <div style="display:inline-block; background: linear-gradient(135deg, #7c3aed22, #06b6d422); 
                    border: 1px solid #7c3aed44; border-radius: 50px; padding: 0.4rem 1.2rem; 
                    margin-bottom: 1.5rem;">
            <span style="color:#a855f7; font-size:0.85rem; font-weight:600; letter-spacing:0.1em;">
                🤖 AI POWERED MOCK INTERVIEWS
            </span>
        </div>
        <h1 style="font-size:3.2rem !important; margin-bottom:1rem !important;">
            Ace Your Next Interview
        </h1>
        <p style="color:#94a3b8; font-size:1.1rem; max-width:550px; margin:0 auto 3rem auto; line-height:1.7;">
            Practice with AI-generated questions, get instant feedback,
            and track your progress across multiple domains.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature highlights ──
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-bottom:3rem;">
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #7c3aed;
                    border-radius:14px; padding:1.5rem; text-align:center; min-width:180px; max-width:200px;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">🎯</div>
            <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">Fresh Questions</div>
            <div style="color:#6b7280; font-size:0.78rem; line-height:1.5;">AI generates new questions every session</div>
        </div>
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #06b6d4;
                    border-radius:14px; padding:1.5rem; text-align:center; min-width:180px; max-width:200px;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">⚡</div>
            <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">Instant Feedback</div>
            <div style="color:#6b7280; font-size:0.78rem; line-height:1.5;">Scored on correctness, depth and clarity</div>
        </div>
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #10b981;
                    border-radius:14px; padding:1.5rem; text-align:center; min-width:180px; max-width:200px;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📈</div>
            <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">Track Progress</div>
            <div style="color:#6b7280; font-size:0.78rem; line-height:1.5;">See weak areas and improve over time</div>
        </div>
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #a855f7;
                    border-radius:14px; padding:1.5rem; text-align:center; min-width:180px; max-width:200px;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">📄</div>
            <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">Resume Based</div>
            <div style="color:#6b7280; font-size:0.78rem; line-height:1.5;">Personalized to your skills and projects</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tracks preview ──
    st.markdown("""
    <p style="color:#94a3b8; font-size:0.85rem; font-weight:600; text-transform:uppercase;
              letter-spacing:0.1em; text-align:center; margin-bottom:1rem;">
        Available Interview Tracks
    </p>
    <div style="display:flex; justify-content:center; gap:0.8rem; flex-wrap:wrap; margin-bottom:3rem;">
        <span style="background:#7c3aed22; border:1px solid #7c3aed44; color:#a855f7;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">🤖 AIML Engineer</span>
        <span style="background:#f59e0b22; border:1px solid #f59e0b44; color:#f59e0b;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">☕ Java Developer</span>
        <span style="background:#06b6d422; border:1px solid #06b6d444; color:#06b6d4;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">💻 DSA</span>
        <span style="background:#10b98122; border:1px solid #10b98144; color:#10b981;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">🧩 OOPs</span>
        <span style="background:#ef444422; border:1px solid #ef444444; color:#ef4444;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">🗄️ DBMS</span>
        <span style="background:#a855f722; border:1px solid #a855f744; color:#a855f7;
                     border-radius:20px; padding:0.3rem 1rem; font-size:0.85rem; font-weight:600;">📄 Resume Based</span>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA buttons ──
    st.markdown("""
    <p style="text-align:center; color:#94a3b8; font-size:0.9rem; margin-bottom:1rem;">
        Ready to start practicing?
    </p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Create Account", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True, type="secondary"):
            st.session_state.page = "login"
            st.rerun()

# ── LOGIN PAGE ────────────────────────────────────────────────
elif st.session_state.page == "login":
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div style="text-align:center; padding:2rem 0 1.5rem 0;">
            <h1>Welcome Back</h1>
            <p style="color:#94a3b8;">Sign in to continue your practice</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    result = login_user(email, password)
                    if result["success"]:
                        st.session_state.user = result
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        st.error(result["error"])

        if st.button("← Back", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

        st.markdown("""
        <p style="text-align:center; color:#6b7280; margin-top:1rem; font-size:0.85rem;">
            Don't have an account?
        </p>
        """, unsafe_allow_html=True)

        if st.button("Create Account →", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ── SIGNUP PAGE ───────────────────────────────────────────────
elif st.session_state.page == "signup":
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div style="text-align:center; padding:2rem 0 1.5rem 0;">
            <h1>Create Account</h1>
            <p style="color:#94a3b8;">Start your interview preparation journey</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="Your Name")
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            confirm = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                if not name or not email or not password or not confirm:
                    st.error("Please fill in all fields.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    result = signup_user(name, email, password)
                    if result["success"]:
                        st.session_state.user = result
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        st.error(result["error"])

        if st.button("← Back", use_container_width=True):
            st.session_state.page = "landing"
            st.rerun()

        st.markdown("""
        <p style="text-align:center; color:#6b7280; margin-top:1rem; font-size:0.85rem;">
            Already have an account?
        </p>
        """, unsafe_allow_html=True)

        if st.button("Sign In →", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

# ── HOME PAGE ─────────────────────────────────────────────────
elif st.session_state.page == "home":

    st.markdown("""
    <div style="text-align:center; padding: 3rem 0 1rem 0;">
        <div style="display:inline-block; background: linear-gradient(135deg, #7c3aed22, #06b6d422); 
                    border: 1px solid #7c3aed44; border-radius: 50px; padding: 0.4rem 1.2rem; 
                    margin-bottom: 1rem;">
            <span style="color:#a855f7; font-size:0.85rem; font-weight:600; letter-spacing:0.1em;">
                🤖 AI POWERED MOCK INTERVIEWS
            </span>
        </div>
        <h1 style="font-size:3.2rem !important; margin-bottom:1rem !important;">
            Ace Your Next Interview
        </h1>
        <p style="color:#94a3b8; font-size:1.1rem; max-width:550px; margin:0 auto 0.5rem auto; line-height:1.7;">
            Practice with AI-generated questions, get instant feedback, 
            and track your progress across multiple domains.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:1.5rem 0 2.5rem 0; border-bottom:1px solid #3b3b5c; margin-bottom:2.5rem;">
        <div style="display:flex; justify-content:center; gap:2rem; flex-wrap:wrap;">
            <div style="display:flex; align-items:flex-start; gap:0.8rem; max-width:220px;">
                <div style="background: linear-gradient(135deg, #7c3aed22, #7c3aed44); 
                            border-radius:10px; padding:0.6rem; flex-shrink:0;">
                    <span style="font-size:1.2rem;">🎯</span>
                </div>
                <div>
                    <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.2rem;">
                        Fresh Every Session
                    </div>
                    <div style="color:#6b7280; font-size:0.8rem; line-height:1.5;">
                        AI generates new questions every time — no two interviews are the same
                    </div>
                </div>
            </div>
            <div style="display:flex; align-items:flex-start; gap:0.8rem; max-width:220px;">
                <div style="background: linear-gradient(135deg, #06b6d422, #06b6d444); 
                            border-radius:10px; padding:0.6rem; flex-shrink:0;">
                    <span style="font-size:1.2rem;">⚡</span>
                </div>
                <div>
                    <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.2rem;">
                        Instant AI Feedback
                    </div>
                    <div style="color:#6b7280; font-size:0.8rem; line-height:1.5;">
                        Get scored on correctness, depth and clarity right after answering
                    </div>
                </div>
            </div>
            <div style="display:flex; align-items:flex-start; gap:0.8rem; max-width:220px;">
                <div style="background: linear-gradient(135deg, #10b98122, #10b98144); 
                            border-radius:10px; padding:0.6rem; flex-shrink:0;">
                    <span style="font-size:1.2rem;">📈</span>
                </div>
                <div>
                    <div style="color:#e2e8f0; font-weight:700; font-size:0.95rem; margin-bottom:0.2rem;">
                        Track Weak Areas
                    </div>
                    <div style="color:#6b7280; font-size:0.8rem; line-height:1.5;">
                        See exactly where you struggle and get targeted practice next session
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <p style="color:#94a3b8; font-size:0.9rem; font-weight:600; 
              text-transform:uppercase; letter-spacing:0.1em; 
              text-align:center; margin-bottom:1.2rem;">
        Choose Your Interview Track
    </p>
    """, unsafe_allow_html=True)

    roles = [
        ("🤖", "AIML Engineer", "ML, Deep Learning, NLP, Statistics", "#7c3aed", "AIML Engineer"),
        ("☕", "Java Developer", "Core Java, OOP, Collections, Code snippets", "#f59e0b", "Java Developer"),
        ("💻", "DSA", "Arrays, Trees, DP, Sorting, Graphs", "#06b6d4", "DSA"),
        ("🧩", "OOPs", "Classes, Inheritance, SOLID, Patterns", "#10b981", "OOPs"),
        ("🗄️", "DBMS", "SQL, Normalization, Transactions, Indexing", "#ef4444", "DBMS"),
        ("📄", "Resume Based", "Personalized to your skills & projects", "#a855f7", "resume"),
    ]

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3, col1, col2, col3]

    for i, (icon, title, desc, color, role_key) in enumerate(roles):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #13131f, #1a1a2e);
                        border: 1px solid #3b3b5c;
                        border-top: 3px solid {color};
                        border-radius: 16px;
                        padding: 1.5rem;
                        margin-bottom: 1rem;
                        text-align: center;
                        min-height: 140px;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">{icon}</div>
                <div style="color:#e2e8f0; font-weight:700; font-size:1rem; margin-bottom:0.3rem;">{title}</div>
                <div style="color:#6b7280; font-size:0.78rem; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Start {title}", key=f"btn_{role_key}", use_container_width=True):
                if role_key == "resume":
                    st.session_state.questions = []
                    st.session_state.q_index = 0
                    st.session_state.session_results = []
                    st.session_state.current_feedback = None
                    st.session_state.session_id = None
                    st.session_state.resume_data = None
                    st.session_state.page = "resume_upload"
                else:
                    st.session_state.questions = []
                    st.session_state.q_index = 0
                    st.session_state.session_results = []
                    st.session_state.current_feedback = None
                    st.session_state.session_id = None
                    st.session_state.resume_data = None
                    st.session_state.role = role_key
                    st.session_state.generating_role = role_key
                    st.session_state.page = "generating"
                st.rerun()

    st.markdown("""
    <div style="margin-top:3rem; padding-top:2rem; border-top:1px solid #3b3b5c;">
        <p style="color:#94a3b8; font-size:0.9rem; font-weight:600;
                  text-transform:uppercase; letter-spacing:0.1em;
                  text-align:center; margin-bottom:1.5rem;">
            How It Works
        </p>
        <div style="display:flex; justify-content:center; gap:1rem; flex-wrap:wrap;">
            <div style="background:#13131f; border:1px solid #3b3b5c; border-radius:12px; 
                        padding:1.2rem 1.5rem; text-align:center; flex:1; min-width:150px; max-width:180px;">
                <div style="color:#7c3aed; font-size:1.4rem; font-weight:700; margin-bottom:0.3rem;">01</div>
                <div style="color:#e2e8f0; font-size:0.85rem; font-weight:600;">Pick a Track</div>
                <div style="color:#6b7280; font-size:0.75rem; margin-top:0.3rem;">Choose your domain or upload resume</div>
            </div>
            <div style="color:#3b3b5c; display:flex; align-items:center; font-size:1.5rem;">→</div>
            <div style="background:#13131f; border:1px solid #3b3b5c; border-radius:12px; 
                        padding:1.2rem 1.5rem; text-align:center; flex:1; min-width:150px; max-width:180px;">
                <div style="color:#06b6d4; font-size:1.4rem; font-weight:700; margin-bottom:0.3rem;">02</div>
                <div style="color:#e2e8f0; font-size:0.85rem; font-weight:600;">Answer Questions</div>
                <div style="color:#6b7280; font-size:0.75rem; margin-top:0.3rem;">AI generates fresh questions every session</div>
            </div>
            <div style="color:#3b3b5c; display:flex; align-items:center; font-size:1.5rem;">→</div>
            <div style="background:#13131f; border:1px solid #3b3b5c; border-radius:12px; 
                        padding:1.2rem 1.5rem; text-align:center; flex:1; min-width:150px; max-width:180px;">
                <div style="color:#a855f7; font-size:1.4rem; font-weight:700; margin-bottom:0.3rem;">03</div>
                <div style="color:#e2e8f0; font-size:0.85rem; font-weight:600;">Get Feedback</div>
                <div style="color:#6b7280; font-size:0.75rem; margin-top:0.3rem;">Instant scores and improvement tips</div>
            </div>
            <div style="color:#3b3b5c; display:flex; align-items:center; font-size:1.5rem;">→</div>
            <div style="background:#13131f; border:1px solid #3b3b5c; border-radius:12px; 
                        padding:1.2rem 1.5rem; text-align:center; flex:1; min-width:150px; max-width:180px;">
                <div style="color:#10b981; font-size:1.4rem; font-weight:700; margin-bottom:0.3rem;">04</div>
                <div style="color:#e2e8f0; font-size:0.85rem; font-weight:600;">Track Progress</div>
                <div style="color:#6b7280; font-size:0.75rem; margin-top:0.3rem;">See strengths and weak areas</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── GENERATING PAGE ───────────────────────────────────────────

elif st.session_state.page == "generating":
    # ── Guard: if no role, redirect home ──
    if not st.session_state.get("generating_role"):
        st.session_state.page = "home"
        st.rerun()

    # ── Clear old results when starting fresh ──
    if st.session_state.get("q_index", 0) == 0:
        st.session_state.session_results = []
        st.session_state.current_feedback = None
        st.session_state.session_id = None

    st.title("🎯 AI Interview Coach")
    role = st.session_state.generating_role
    weak_areas = st.session_state.get("weak_areas", [])

    st.info(f"Generating fresh questions for **{role}**... this may take a few seconds.")

    questions = generate_questions_for_role(role, weak_areas=weak_areas)

    if questions:
        st.session_state.questions = questions
        st.session_state.page = "interview"
        st.rerun()
    else:
        st.error("Could not generate questions after 3 attempts. Please try again.")
        if st.button("🔄 Retry"):
            st.rerun()
        if st.button("Go Home"):
            st.session_state.page = "home"
            st.rerun()

# ── INTERVIEW PAGE ────────────────────────────────────────────
elif st.session_state.page == "interview":
    questions = st.session_state.questions
    idx = st.session_state.q_index
    total = min(len(questions), 7)

    if idx >= total:
        st.session_state.page = "dashboard"
        st.rerun()

    q = get_question(questions, idx)

    # ── Top bar: Home button + Role ──
    # ── Top bar: Home button + Role ──
    col_home, col_role = st.columns([1, 5])
    with col_home:
        if st.button("Home"):
            reset_interview_state()
            st.rerun()
    with col_role:
        st.caption(f"Role: {st.session_state.role}")

    # ── Progress bar ──
    st.progress(idx / total)

    # ── Question dots ──
    dots = ""
    for i in range(total):
        if i < idx:
            dots += '<span style="color:#7c3aed; font-size:1.1rem;">●</span> '
        elif i == idx:
            dots += '<span style="color:#06b6d4; font-size:1.3rem;">●</span> '
        else:
            dots += '<span style="color:#3b3b5c; font-size:1.1rem;">○</span> '

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
        {dots}
        <span style="color:#6b7280; font-size:0.8rem; margin-left:0.5rem;">
            Question {idx + 1} of {total}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Difficulty badge + Question card ──
    difficulty = q.get('difficulty', 'Intermediate')
    difficulty_colors = {
        "Basic": ("#16a34a", "#052e16"),
        "Intermediate": ("#d97706", "#1c1007"),
        "Advanced": ("#dc2626", "#2d0a0a"),
    }
    badge_color, badge_bg = difficulty_colors.get(difficulty, ("#a855f7", "#1a0a2e"))

    # Render badge + topic via HTML, question via st.markdown separately
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #13131f, #1a1a2e);
                border: 1px solid #3b3b5c;
                border-left: 4px solid #7c3aed;
                border-radius: 16px;
                padding: 1.5rem 2rem;
                margin: 1rem 0;
                box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.8rem;">
            <span style="background:{badge_bg}; color:{badge_color}; border:1px solid {badge_color};
                    border-radius:20px; padding:0.2rem 0.8rem; font-size:0.75rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:0.05em;">
                {difficulty}
            </span>
            <span style="color:#6b7280; font-size:0.8rem;">{q.get('topic', '')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render question text separately using st.markdown so code blocks render correctly
    st.markdown(f"{q['question']}")

    answer = st.text_area("Your Answer", height=150, placeholder="Type your answer here...")

    is_last = (idx + 1 >= total)
    btn_label = "Submit" if is_last else "Save & Next"

    if st.button(btn_label, use_container_width=True):
        if not answer.strip():
            st.warning("Please type an answer before submitting.")
        else:
            with st.spinner("Evaluating your answer..."):
                sim_score = get_similarity_score(q["ideal_answer"], answer)
                feedback = get_feedback(q["question"], q["ideal_answer"], answer, sim_score)

            if feedback is None:
                st.error("Evaluation failed. Please try again.")
                st.stop()

            st.session_state.current_feedback = feedback
            st.session_state.session_results.append({
                "topic": q["topic"],
                "question": q["question"],
                "your_answer": answer,
                "overall_score": feedback.get("overall_score", 0),
                "feedback": feedback
            })
            st.session_state.page = "feedback"
            st.rerun()

# ── FEEDBACK PAGE ─────────────────────────────────────────────
elif st.session_state.page == "feedback":
    fb = st.session_state.current_feedback
    idx = st.session_state.q_index
    total = min(len(st.session_state.questions), 7)

    if fb is None:
        st.error("Something went wrong. Please go back and try again.")
        if st.button("Go Back"):
            st.session_state.page = "home"
            st.rerun()
        st.stop()

    col_home, col_title = st.columns([1, 5])
    with col_home:
        if st.button("Home"):
            st.session_state.page = "home"
            st.rerun()

    st.title("Answer Feedback")

    # ── Score cards ──
    overall = fb['overall_score']

    if overall >= 7:
        verdict_color = "#10b981"
        verdict_bg = "#052e16"
        verdict_border = "#16a34a"
        verdict_icon = "✅"
        verdict_text = "Accepted"
    elif overall >= 5:
        verdict_color = "#d97706"
        verdict_bg = "#1c1007"
        verdict_border = "#d97706"
        verdict_icon = "⚠️"
        verdict_text = "Needs Improvement"
    else:
        verdict_color = "#dc2626"
        verdict_bg = "#2d0a0a"
        verdict_border = "#dc2626"
        verdict_icon = "❌"
        verdict_text = "Insufficient"

    st.markdown(f"""
    <div style="display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap;">
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #7c3aed;
                    border-radius:14px; padding:1rem 1.5rem; text-align:center; flex:1; min-width:120px;">
            <div style="color:#a855f7; font-size:0.78rem; font-weight:700; text-transform:uppercase; 
                        letter-spacing:0.08em; margin-bottom:0.4rem;">✅ Correctness</div>
            <div style="color:#e2e8f0; font-size:1.8rem; font-weight:700;">{fb['correctness_score']}/10</div>
        </div>
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #06b6d4;
                    border-radius:14px; padding:1rem 1.5rem; text-align:center; flex:1; min-width:120px;">
            <div style="color:#06b6d4; font-size:0.78rem; font-weight:700; text-transform:uppercase; 
                        letter-spacing:0.08em; margin-bottom:0.4rem;">🧠 Depth</div>
            <div style="color:#e2e8f0; font-size:1.8rem; font-weight:700;">{fb['depth_score']}/10</div>
        </div>
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #a855f7;
                    border-radius:14px; padding:1rem 1.5rem; text-align:center; flex:1; min-width:120px;">
            <div style="color:#a855f7; font-size:0.78rem; font-weight:700; text-transform:uppercase; 
                        letter-spacing:0.08em; margin-bottom:0.4rem;">💬 Clarity</div>
            <div style="color:#e2e8f0; font-size:1.8rem; font-weight:700;">{fb['clarity_score']}/10</div>
        </div>
        <div style="background:{verdict_bg}; border:1px solid {verdict_border}; border-top:3px solid {verdict_color};
                    border-radius:14px; padding:1rem 1.5rem; text-align:center; flex:1; min-width:120px;">
            <div style="color:{verdict_color}; font-size:0.78rem; font-weight:700; text-transform:uppercase; 
                        letter-spacing:0.08em; margin-bottom:0.4rem;">{verdict_icon} Overall</div>
            <div style="color:#e2e8f0; font-size:1.8rem; font-weight:700;">{overall}/10</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Verdict banner ──
    extra_msg = "— Good answer! See below to make it even better." if overall >= 8 else ""
    extra_color = "#6b7280" if overall >= 8 else ""

    st.markdown(f"""
    <div style="background:{verdict_bg}; border:1px solid {verdict_border}; border-radius:12px;
                padding:0.8rem 1.2rem; margin-bottom:1.2rem; display:flex; align-items:center; gap:0.8rem;">
        <span style="font-size:1.3rem;">{verdict_icon}</span>
        <div>
            <span style="color:{verdict_color}; font-weight:700; font-size:1rem;">{verdict_text}</span>
            <span style="color:{extra_color}; font-size:0.85rem;"> {extra_msg}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ── Missing points ──
    if fb.get("missing_points"):
        if overall >= 7:
            st.markdown("""
            <p style="color:#94a3b8; font-size:0.85rem; font-weight:600; margin-bottom:0.5rem;">
                💡 To make your answer even stronger:
            </p>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <p style="color:#fca5a5; font-size:0.85rem; font-weight:600; margin-bottom:0.5rem;">
                ❌ Missing Points:
            </p>
            """, unsafe_allow_html=True)

        for point in fb["missing_points"]:
            bullet_color = "#94a3b8" if overall >= 8 else "#fca5a5"
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:0.5rem; margin-bottom:0.4rem;">
                <span style="color:{bullet_color}; margin-top:0.1rem;">•</span>
                <span style="color:{bullet_color}; font-size:0.9rem;">{point}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Suggested answer ──
    with st.expander("💡 Suggested Answer"):
        formatted = fb['suggested_answer'].replace('\\n', '\n').replace('\n', '<br>')
        st.markdown(f"""
        <div style="color:#c4b5fd; font-size:0.95rem; line-height:1.8; padding:0.5rem 0;">
            {formatted}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if idx + 1 >= total:
        if st.button("📊 View Final Report", use_container_width=True):
            st.session_state.q_index += 1
            st.session_state.page = "dashboard"
            st.rerun()
    else:
        if st.button("Next Question", use_container_width=True):
            st.session_state.q_index += 1
            st.session_state.page = "interview"
            st.rerun()

# ── RESUME UPLOAD PAGE ────────────────────────────────────────
elif st.session_state.page == "resume_upload":
    st.title("📄 Resume-Based Interview")
    st.markdown("Upload your resume and get a personalized interview based on your skills and projects.")

    uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type=["pdf"])

    if uploaded_file is not None:
        if st.button("Start My Interview", use_container_width=True):
            with st.spinner("Reading your resume and generating personalized questions..."):
                resume_text = extract_text_from_pdf(uploaded_file)

                if not resume_text:
                    st.error("Could not read the PDF. Please make sure it is not scanned or image-based.")
                else:
                    resume_data = extract_skills_and_generate_questions(resume_text)

                    if resume_data and "questions" in resume_data:
                        st.session_state.resume_data = resume_data
                        st.session_state.role = f"Resume - {resume_data.get('candidate_name', 'Candidate')}"
                        st.session_state.questions = resume_data["questions"]
                        st.session_state.page = "resume_preview"
                        st.rerun()
                    else:
                        st.error("Could not generate questions. Please try again.")

# ── RESUME PREVIEW PAGE ───────────────────────────────────────
elif st.session_state.page == "resume_preview":
    data = st.session_state.resume_data
    st.title("Resume Analyzed!")
    st.markdown(f"### Hello, {data.get('candidate_name', 'Candidate')}!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🛠 Skills Found**")
        for s in data.get("skills", []):
            st.markdown(f"- {s}")
    with col2:
        st.markdown("**💼 Projects Found**")
        for p in data.get("projects", []):
            st.markdown(f"- {p}")
    with col3:
        st.markdown("**🏆 Certifications**")
        certs = data.get("certifications", [])
        if certs:
            for c in certs:
                st.markdown(f"- {c}")
        else:
            st.markdown("- None found")

    st.info("7 personalized questions have been generated based on your resume.")

    if st.button("▶ Begin Interview", use_container_width=True):
        st.session_state.page = "interview"
        st.rerun()

elif st.session_state.page == "profile":
    user = st.session_state.user
    stats = get_user_stats(user["user_id"])
    sessions = get_user_sessions(user["user_id"])

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.page = "home"
            st.rerun()

    st.title("👤 My Profile")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #13131f, #1a1a2e);
                border:1px solid #3b3b5c; border-radius:16px; padding:1.5rem; margin-bottom:2rem;">
        <div style="color:#e2e8f0; font-size:1.2rem; font-weight:700; margin-bottom:0.3rem;">
            {user['name']}
        </div>
        <div style="color:#6b7280; font-size:0.9rem;">{user['email']}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #7c3aed;
                border-radius:14px; padding:1rem; text-align:center; 
                min-height:110px; display:flex; flex-direction:column; justify-content:center;">
            <div style="color:#a855f7; font-size:0.78rem; font-weight:700; 
                    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;">
                Total Sessions
            </div>
            <div style="color:#e2e8f0; font-size:2rem; font-weight:700;">{stats['total_sessions']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #06b6d4;
                border-radius:14px; padding:1rem; text-align:center;
                min-height:110px; display:flex; flex-direction:column; justify-content:center;">
            <div style="color:#06b6d4; font-size:0.78rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;">
                Avg Score
            </div>
            <div style="color:#e2e8f0; font-size:2rem; font-weight:700;">{stats['avg_score']}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background:#13131f; border:1px solid #3b3b5c; border-top:3px solid #10b981;
                border-radius:14px; padding:1rem; text-align:center;
                min-height:110px; display:flex; flex-direction:column; justify-content:center;">
            <div style="color:#10b981; font-size:0.78rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;">
                Favourite Track
            </div>
            <div style="color:#e2e8f0; font-size:1.3rem; font-weight:700; margin-top:0.3rem;">
                {stats['favourite_role']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Interview History")

    if not sessions:
        st.info("No interviews yet. Start your first session!")
    else:
        for s in sessions:
            score_color = "#10b981" if s["overall_score"] >= 70 else "#d97706" if s["overall_score"] >= 50 else "#dc2626"
            with st.expander(f"{s['role']} — {s['created_at'][:10]} — Score: {s['overall_score']}%"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**✅ Questions:** {s['total_questions']}")
                    st.markdown(f"**💪 Strengths:** {s['strengths'] or 'None'}")
                with col2:
                    st.markdown(f"""<span style="color:{score_color}; font-size:1.5rem; font-weight:700;">
                        {s['overall_score']}%</span>""", unsafe_allow_html=True)
                    st.markdown(f"**⚠️ Weak Areas:** {s['weak_areas'] or 'None'}")
# ── DASHBOARD PAGE ────────────────────────────────────────────

elif st.session_state.page == "dashboard":
    # ── Guard: if no results, redirect home ──
    if not st.session_state.get("session_results"):
        st.session_state.page = "home"
        st.rerun()

    results = st.session_state.session_results

    col_home, _ = st.columns([1, 5])
    with col_home:
        if st.button("Home"):
            reset_interview_state()
            st.rerun()

    st.title("📊 Interview Report")

    if not results:
        st.warning("No results to show.")
    else:
        total_score = round(sum(r["overall_score"] for r in results) / len(results) * 10, 1)

        if st.session_state.user and st.session_state.get("session_id") is None:
            topic_avgs = compute_topic_averages(results)
            strengths, weaknesses = get_strengths_and_weaknesses(topic_avgs)

            session_id = save_session(
                user_id=st.session_state.user["user_id"],
                role=st.session_state.role or "Unknown",
                overall_score=total_score,
                total_questions=len(results),
                weak_areas=weaknesses,
                strengths=strengths
            )
            st.session_state.session_id = session_id

            for r in results:
                fb = r.get("feedback", {})
                save_answer(
                    session_id=session_id,
                    topic=r.get("topic", ""),
                    question=r["question"],
                    student_answer=r["your_answer"],
                    correctness=fb.get("correctness_score", 0),
                    depth=fb.get("depth_score", 0),
                    clarity=fb.get("clarity_score", 0),
                    overall=r["overall_score"],
                    missing_points=fb.get("missing_points", [])
                )

        if total_score >= 80:
            confetti_html = ""
            colors = ["#7c3aed", "#06b6d4", "#a855f7", "#10b981", "#f59e0b", "#6366f1"]
            import random
            for i in range(60):
                color = random.choice(colors)
                left = random.randint(0, 100)
                delay = round(random.uniform(0, 2.5), 2)
                duration = round(random.uniform(2, 4), 2)
                size = random.randint(6, 14)
                confetti_html += f'<div class="confetti-piece" style="left:{left}vw; background:{color}; width:{size}px; height:{size}px; animation-duration:{duration}s; animation-delay:{delay}s;"></div>'
            st.markdown(f"""
            <div style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9999;">
                {confetti_html}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; padding:1rem 0;">
                <div style="font-size:2rem;">🎉</div>
                <div style="color:#10b981; font-size:1.1rem; font-weight:700;">Excellent Performance!</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <span style="color:#6b7280; font-size:0.85rem; font-weight:600; 
                         text-transform:uppercase; letter-spacing:0.08em;">🏆 Overall Score</span>
            <div style="color:#e2e8f0; font-size:2.8rem; font-weight:700; line-height:1.2;">
                {total_score}%
            </div>
        </div>
        """, unsafe_allow_html=True)

        topic_avgs = compute_topic_averages(results)
        strengths, weaknesses = get_strengths_and_weaknesses(topic_avgs)
        st.session_state.weak_areas = weaknesses

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 💪 Strengths")
            for s in strengths:
                st.success(s)
        with col2:
            st.markdown("#### ⚠️ Weak Areas")
            if weaknesses:
                for w in weaknesses:
                    st.error(w)
            else:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #0a1628, #0f2444);
                            border: 1px solid #1e40af; border-radius: 12px;
                            padding: 1.5rem; text-align:center;">
                    <div style="font-size:1.8rem; margin-bottom:0.5rem;">🏆</div>
                    <div style="color:#60a5fa; font-weight:700; font-size:0.95rem; margin-bottom:0.3rem;">
                        No Weak Areas!
                    </div>
                    <div style="color:#6b7280; font-size:0.8rem; line-height:1.5;">
                        You scored 8+ on all topics.<br>Try a harder session to challenge yourself.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.plotly_chart(plot_topic_scores(topic_avgs), use_container_width=True)

        if weaknesses:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="border-top:1px solid #3b3b5c; padding-top:1.5rem; margin-bottom:1rem;">
                <p style="color:#e2e8f0; font-weight:700; font-size:1rem; margin-bottom:0.3rem;">
                    🎯 Practice Weak Areas
                </p>
                <p style="color:#6b7280; font-size:0.82rem; margin-bottom:1rem;">
                    Pick a topic to start a focused session
                </p>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(min(len(weaknesses), 3))
            for i, weak_topic in enumerate(weaknesses):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style="background:#13131f; border:1px solid #3b3b5c; 
                                border-top:3px solid #ef4444; border-radius:12px;
                                padding:0.8rem 1rem; text-align:center; margin-bottom:0.5rem;">
                        <div style="color:#fca5a5; font-size:0.75rem; font-weight:600;
                                text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">
                            Weak Area
                        </div>
                        <div style="color:#e2e8f0; font-size:0.9rem; font-weight:600;">
                            {weak_topic}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Practice →", key=f"practice_{i}", use_container_width=True):
                        role = st.session_state.role
                        st.session_state.weak_areas = [weak_topic]
                        st.session_state.generating_role = role if role not in ["resume", None] else "AIML Engineer"
                        st.session_state.role = st.session_state.generating_role
                        st.session_state.questions = []
                        st.session_state.q_index = 0
                        st.session_state.session_results = []
                        st.session_state.current_feedback = None
                        st.session_state.page = "generating"
                        st.rerun()

        with st.expander("📝 Detailed Question Log"):
            for i, r in enumerate(results, 1):
                st.markdown(f"**Q{i}: {r['question']}**")
                st.write(f"Your answer: {r['your_answer']}")
                st.write(f"Score: {r['overall_score']}/10")
                st.divider()

        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_interview_state()
            st.rerun()