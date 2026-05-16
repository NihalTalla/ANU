import streamlit as st
import datetime
import random
import os
import math
import psutil
import pyjokes
import smtplib
import ssl
import io
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from supabase import create_client, Client

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ANU - Personal AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Supabase Init ────────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        st.error("⚠️ Supabase credentials not configured. Check secrets.toml or environment variables.")
        st.stop()
    return create_client(url, key)

supabase: Client = init_supabase()

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif !important;}

.auth-card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #e94560;border-radius:20px;padding:40px;max-width:480px;margin:60px auto;box-shadow:0 0 60px rgba(233,69,96,0.2);}
.auth-title{font-size:2.2rem;font-weight:700;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:4px;}
.auth-sub{text-align:center;color:#8892b0;font-size:0.95rem;margin-bottom:28px;}

.step-card{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:28px;margin:12px 0;}
.step-num{background:#e94560;color:white;border-radius:50%;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;margin-right:10px;}
.step-title{color:#e6f1ff;font-size:1.15rem;font-weight:600;vertical-align:middle;}
.progress-bar{background:#2a2a4a;border-radius:99px;height:6px;margin:16px 0;}
.progress-fill{background:linear-gradient(90deg,#e94560,#533483);border-radius:99px;height:6px;transition:width 0.5s;}

.anu-header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);border-radius:16px;padding:22px 28px;margin-bottom:20px;border:1px solid #e94560;box-shadow:0 0 30px rgba(233,69,96,0.15);}
.anu-title{font-size:2.2rem;font-weight:700;background:linear-gradient(90deg,#e94560,#0f3460,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;}
.status-dot{display:inline-block;width:10px;height:10px;background:#00ff88;border-radius:50%;margin-right:8px;animation:pulse 2s infinite;box-shadow:0 0 6px #00ff88;}
@keyframes pulse{0%{opacity:1}50%{opacity:0.4}100%{opacity:1}}
.metric-card{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:12px;padding:16px;text-align:center;}
.metric-value{font-size:2rem;font-weight:700;color:#e94560;}
.metric-label{font-size:0.78rem;color:#8892b0;text-transform:uppercase;letter-spacing:1px;}
.chat-user{background:linear-gradient(135deg,#0f3460,#1a1a4e);border-radius:16px 16px 4px 16px;padding:12px 16px;margin:8px 0;border-left:3px solid #0f3460;color:#ccd6f6;}
.chat-anu{background:linear-gradient(135deg,#1a1a2e,#2a1a3e);border-radius:16px 16px 16px 4px;padding:12px 16px;margin:8px 0;border-left:3px solid #e94560;color:#e6f1ff;}
.voice-box{background:linear-gradient(135deg,#0a1628,#1a0a28);border:2px solid #533483;border-radius:16px;padding:20px;text-align:center;margin:12px 0;}
.call-box{background:#1a1a0a;border:2px dashed #ffaa00;border-radius:12px;padding:24px;text-align:center;color:#ffaa00;}
.user-badge{background:#1a1a2e;border:1px solid #e94560;border-radius:99px;padding:6px 14px;color:#e94560;font-size:0.85rem;font-weight:600;display:inline-block;}

.stTextInput>div>div>input{background-color:#1a1a2e !important;color:#ccd6f6 !important;border-color:#2a2a4a !important;border-radius:10px !important;}
.stTextArea>div>div>textarea{background-color:#1a1a2e !important;color:#ccd6f6 !important;border-color:#2a2a4a !important;}
.stButton>button{background:linear-gradient(135deg,#e94560,#c62a47) !important;color:white !important;border:none !important;border-radius:10px !important;font-weight:600 !important;}
[data-testid="stSidebar"]{background-color:#0a0a15 !important;border-right:1px solid #2a2a4a !important;}
.stSelectbox>div>div{background-color:#1a1a2e !important;color:#ccd6f6 !important;border-color:#2a2a4a !important;}
.stNumberInput>div>div>input{background-color:#1a1a2e !important;color:#ccd6f6 !important;}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
defaults = {
    "auth_page": "login",
    "user": None,
    "cfg": {},
    "messages": [],
    "notes": [],
    "active_tab": "Chat",
    "calc_history": [],
    "joke_list": [],
    "voice_text": "",
    "contacts": [],
    "onboard_step": 1,
    "custom_links": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Supabase Helpers ─────────────────────────────────────────────────────────
def signup_user(email: str, password: str, full_name: str):
    try:
        res = supabase.auth.sign_up({
            "email": email.strip().lower(),
            "password": password,
            "options": {"data": {"full_name": full_name.strip()}},
        })
        if res.user:
            supabase.table("user_profiles").insert({
                "user_id": res.user.id,
                "email": email.strip().lower(),
                "full_name": full_name.strip(),
                "onboarding_done": False,
            }).execute()
            return True, "Account created! Please check your email to confirm."
        return False, "Signup failed. Try again."
    except Exception as e:
        err = str(e)
        if "already registered" in err.lower() or "duplicate" in err.lower():
            return False, "Email already registered."
        return False, err

def login_user(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password,
        })
        if res.user:
            return {
                "id": res.user.id,
                "email": res.user.email,
                "full_name": res.user.user_metadata.get("full_name", ""),
            }
        return None
    except Exception:
        return None

def get_profile(user_id: str):
    try:
        res = supabase.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return None

def get_config(user_id: str):
    try:
        res = supabase.table("user_config").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        return {}
    except Exception:
        return {}

def save_config(user_id: str, **kwargs):
    try:
        payload = {"user_id": user_id}
        payload.update(kwargs)
        supabase.table("user_config").upsert(payload, on_conflict="user_id").execute()
    except Exception as e:
        st.error(f"Failed to save config: {e}")

def get_notes(user_id: str):
    try:
        res = supabase.table("notes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def save_note(user_id: str, title: str, content: str, tags: list):
    try:
        supabase.table("notes").insert({
            "user_id": user_id,
            "title": title,
            "content": content,
            "tags": tags,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save note: {e}")
        return False

def update_note(note_id: int, title: str, content: str, tags: list):
    try:
        supabase.table("notes").update({
            "title": title,
            "content": content,
            "tags": tags,
        }).eq("id", note_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to update note: {e}")
        return False

def delete_note(note_id: int):
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete note: {e}")
        return False

def load_user_session(user: dict):
    st.session_state.user = user
    st.session_state.cfg = get_config(user["id"])
    profile = get_profile(user["id"])
    st.session_state.notes = get_notes(user["id"])

    if profile and profile.get("onboarding_done"):
        st.session_state.auth_page = "app"
        if profile.get("custom_links"):
            st.session_state.custom_links = profile["custom_links"]
    else:
        st.session_state.auth_page = "onboarding"

def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k in ["user", "cfg", "messages", "notes", "active_tab", "calc_history",
              "joke_list", "voice_text", "contacts", "custom_links"]:
        st.session_state[k] = [] if isinstance(defaults.get(k), list) else ({} if k == "cfg" else (None if k == "user" else ""))
    st.session_state.active_tab = "Chat"
    st.session_state.custom_links = []
    st.session_state.auth_page = "login"

# ─── App Helpers ──────────────────────────────────────────────────────────────
def cfg(key, fallback=""):
    return st.session_state.cfg.get(key) or fallback

def get_gemini(prompt, history):
    key = cfg("gemini_key")
    if not key:
        return "⚠️ Gemini API key not set. Go to ⚙️ Settings to add it."
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                f"You are ANU, a smart personal AI assistant. "
                f"Be helpful, friendly, witty. "
                f"The user's name is {st.session_state.user.get('full_name', 'there')}. "
                f"Keep answers concise."
            ),
        )
        hist = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in history[-10:]
        ]
        chat = model.start_chat(history=hist[:-1] if len(hist) > 1 else [])
        return chat.send_message(prompt).text
    except Exception as e:
        return f"❌ Gemini error: {e}"

def send_email_fn(to, subject, body):
    se = cfg("smtp_email")
    sp = cfg("smtp_password")
    if not se or not sp:
        return False, "Email credentials not configured. Go to ⚙️ Settings."
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = se
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        ctx = ssl.create_default_context()
        host = cfg("smtp_host", "smtp.gmail.com")
        port = int(cfg("smtp_port", 587) or 587)
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(se, sp)
            s.sendmail(se, to, msg.as_string())
        return True, "✅ Email sent!"
    except Exception as e:
        return False, f"❌ {e}"

def get_weather(city):
    key = cfg("weather_api_key")
    if not key:
        return None, "Weather API key not set. Go to ⚙️ Settings."
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric",
            timeout=5,
        )
        d = r.json()
        if r.status_code == 200:
            return {
                "city": d["name"],
                "temp": d["main"]["temp"],
                "feels": d["main"]["feels_like"],
                "desc": d["weather"][0]["description"].title(),
                "humidity": d["main"]["humidity"],
                "wind": d["wind"]["speed"],
            }, None
        return None, d.get("message", "City not found")
    except Exception as e:
        return None, str(e)

def safe_calc(expr):
    try:
        c = expr.lower()
        replacements = [
            ("x", "*"), ("÷", "/"), ("^", "**"), ("plus", "+"), ("minus", "-"),
            ("times", "*"), ("divided by", "/"), ("sqrt", "math.sqrt"), ("pi", str(math.pi)),
        ]
        for o, n in replacements:
            c = c.replace(o, n)
        return round(eval(c, {"__builtins__": {}, "math": math}), 6)
    except Exception:
        return None

def pct_color(p):
    return "#ff4444" if p > 80 else "#ffaa00" if p > 50 else "#00ff88"

def get_sys():
    c = psutil.cpu_percent(0.5)
    m = psutil.virtual_memory()
    d = psutil.disk_usage('/')
    b = psutil.sensors_battery()
    return {
        "cpu": c,
        "mp": m.percent,
        "mu": round(m.used / 1024**3, 1),
        "mt": round(m.total / 1024**3, 1),
        "dp": d.percent,
        "du": round(d.used / 1024**3, 1),
        "dt": round(d.total / 1024**3, 1),
        "bat": b.percent if b else None,
        "plug": b.power_plugged if b else None,
        "procs": len(list(psutil.process_iter())),
    }

def get_joke():
    try:
        return pyjokes.get_joke()
    except Exception:
        return "Why do programmers prefer dark mode? Light attracts bugs! 🐛"

CODE_TEMPLATES = {
    "Python - Hello World": ("python", 'print("Hello, World!")'),
    "Python - Function": ("python", 'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("ANU"))'),
    "Python - API Request": ("python", 'import requests\nr = requests.get("https://api.example.com/data")\nif r.status_code == 200:\n    print(r.json())'),
    "JavaScript - Fetch": ("javascript", 'async function getData(url) {\n    const res = await fetch(url);\n    return await res.json();\n}\ngetData("https://api.example.com").then(console.log);'),
    "HTML - Basic Page": ("html", '<!DOCTYPE html>\n<html lang="en">\n<head><meta charset="UTF-8"><title>Page</title></head>\n<body><h1>Hello ANU!</h1></body>\n</html>'),
    "SQL - Query": ("sql", 'SELECT u.name, COUNT(o.id) AS orders\nFROM users u\nJOIN orders o ON u.id = o.user_id\nGROUP BY u.name ORDER BY orders DESC LIMIT 10;'),
}

now = datetime.datetime.now()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown("""
    <div style="text-align:center;margin-top:40px;">
        <div style="font-size:4rem;">🤖</div>
        <h1 style="font-size:3rem;font-weight:800;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;">ANU</h1>
        <p style="color:#8892b0;font-size:1.1rem;">Your Personal AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Welcome Back</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Sign in to your ANU account</div>', unsafe_allow_html=True)

        email = st.text_input("📧 Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("🔒 Password", type="password", placeholder="Your password", key="login_pw")

        if st.button("Sign In →", use_container_width=True):
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                user = login_user(email, password)
                if user:
                    load_user_session(user)
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#8892b0;font-size:0.9rem;">Don\'t have an account?</div>', unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True):
            st.session_state.auth_page = "signup"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SIGNUP
# ══════════════════════════════════════════════════════════════════════════════
def page_signup():
    st.markdown("""
    <div style="text-align:center;margin-top:40px;">
        <div style="font-size:4rem;">🤖</div>
        <h1 style="font-size:3rem;font-weight:800;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;">ANU</h1>
        <p style="color:#8892b0;font-size:1.1rem;">Create your personal AI assistant</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.2, 1])[1]
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Set up your own ANU in seconds</div>', unsafe_allow_html=True)

        full_name = st.text_input("👤 Full Name", placeholder="Your Name", key="su_name")
        email = st.text_input("📧 Email", placeholder="you@example.com", key="su_email")
        password = st.text_input("🔒 Password", type="password", placeholder="Min 6 characters", key="su_pw")
        confirm = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password", key="su_cpw")

        if st.button("Create My ANU →", use_container_width=True):
            if not all([full_name, email, password, confirm]):
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords don't match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                ok, msg = signup_user(email, password, full_name)
                if ok:
                    st.success(msg)
                    st.info("Please confirm your email, then sign in.")
                else:
                    st.error(f"❌ {msg}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#8892b0;font-size:0.9rem;">Already have an account?</div>', unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ONBOARDING WIZARD
# ══════════════════════════════════════════════════════════════════════════════
def page_onboarding():
    user = st.session_state.user
    step = st.session_state.onboard_step
    total = 4

    st.markdown(f"""
    <div style="text-align:center;margin:30px 0 10px;">
        <div style="font-size:2.5rem;">🤖</div>
        <h2 style="color:#e6f1ff;">Welcome, {user.get('full_name', 'there')}! Let's set up your ANU.</h2>
        <p style="color:#8892b0;">This takes 2 minutes. You can always change these in Settings later.</p>
    </div>
    <div class="progress-bar">
        <div class="progress-fill" style="width:{int((step / total) * 100)}%;"></div>
    </div>
    <div style="text-align:right;color:#8892b0;font-size:0.85rem;margin-bottom:24px;">Step {step} of {total}</div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:

        if step == 1:
            st.markdown("""
            <div class="step-card">
                <span class="step-num">1</span><span class="step-title">Gemini API Key (Required)</span>
                <p style="color:#8892b0;margin-top:12px;">
                    ANU uses Google Gemini AI for chat, code generation, email drafting, and more.
                    Your key is stored securely and never shared.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Get your free key at:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)")
            gemini_key = st.text_input("Paste your Gemini API key", type="password", placeholder="AIza...", key="ob_gemini")

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Skip for now →", use_container_width=True):
                    st.session_state.onboard_step = 2
                    st.rerun()
            with c2:
                if st.button("Save & Continue →", use_container_width=True):
                    if gemini_key.strip():
                        save_config(user["id"], gemini_key=gemini_key.strip())
                        st.session_state.cfg["gemini_key"] = gemini_key.strip()
                    st.session_state.onboard_step = 2
                    st.rerun()

        elif step == 2:
            st.markdown("""
            <div class="step-card">
                <span class="step-num">2</span><span class="step-title">Email Setup (Optional)</span>
                <p style="color:#8892b0;margin-top:12px;">
                    Let ANU send emails on your behalf using your Gmail.
                    You need a Gmail <b>App Password</b> (not your regular password).
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Get App Password:** [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)")
            smtp_email = st.text_input("Your Gmail address", placeholder="you@gmail.com", key="ob_email")
            smtp_pw = st.text_input("Gmail App Password", type="password", placeholder="xxxx xxxx xxxx xxxx", key="ob_smtp_pw")

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboard_step = 1
                    st.rerun()
            with c2:
                if st.button("Save & Continue →", use_container_width=True):
                    if smtp_email.strip() and smtp_pw.strip():
                        save_config(user["id"], smtp_email=smtp_email.strip(), smtp_password=smtp_pw.strip())
                        st.session_state.cfg.update({"smtp_email": smtp_email.strip(), "smtp_password": smtp_pw.strip()})
                    st.session_state.onboard_step = 3
                    st.rerun()

        elif step == 3:
            st.markdown("""
            <div class="step-card">
                <span class="step-num">3</span><span class="step-title">Your Personal Links (Optional)</span>
                <p style="color:#8892b0;margin-top:12px;">
                    Add your social profiles and favourite links. ANU will show them as quick-open buttons on your dashboard.
                </p>
            </div>
            """, unsafe_allow_html=True)

            insta = st.text_input("📸 Instagram URL", placeholder="https://instagram.com/yourhandle", key="ob_insta")
            li = st.text_input("💼 LinkedIn URL", placeholder="https://linkedin.com/in/yourprofile", key="ob_li")
            github = st.text_input("🐱 GitHub URL", placeholder="https://github.com/yourprofile", key="ob_gh")
            yt = st.text_input("🎥 YouTube URL", placeholder="https://youtube.com/@yourchannel", key="ob_yt")
            tw = st.text_input("🐦 Twitter/X URL", placeholder="https://twitter.com/yourhandle", key="ob_tw")

            st.markdown("---")
            st.markdown("**Custom Links** (add as many as you want)")

            custom_links = st.session_state.get("custom_links", [])
            if not custom_links:
                custom_links = [{"label": "", "url": ""}]

            for idx, link in enumerate(custom_links):
                c1, c2, c3 = st.columns([2, 3, 0.5])
                with c1:
                    link["label"] = st.text_input("Label", value=link["label"], key=f"cl_label_{idx}", label_visibility="collapsed")
                with c2:
                    link["url"] = st.text_input("URL", value=link["url"], key=f"cl_url_{idx}", label_visibility="collapsed")
                with c3:
                    if len(custom_links) > 1 and st.button("❌", key=f"cl_del_{idx}"):
                        custom_links.pop(idx)
                        st.session_state.custom_links = custom_links
                        st.rerun()

            if st.button("➕ Add Another Link", key="add_custom_link"):
                custom_links.append({"label": "", "url": ""})
                st.session_state.custom_links = custom_links
                st.rerun()

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboard_step = 2
                    st.rerun()
            with c2:
                if st.button("Save & Continue →", use_container_width=True):
                    save_config(user["id"],
                        link_instagram=insta.strip(),
                        link_linkedin=li.strip(),
                        link_github=github.strip(),
                        link_youtube=yt.strip(),
                        link_twitter=tw.strip(),
                    )
                    st.session_state.cfg.update({
                        "link_instagram": insta,
                        "link_linkedin": li,
                        "link_github": github,
                        "link_youtube": yt,
                        "link_twitter": tw,
                    })
                    st.session_state.custom_links = custom_links
                    st.session_state.onboard_step = 4
                    st.rerun()

        elif step == 4:
            st.markdown("""
            <div style="text-align:center;padding:40px 20px;">
                <div style="font-size:4rem;margin-bottom:16px;">🎉</div>
                <h2 style="color:#e6f1ff;">ANU is ready for you!</h2>
                <p style="color:#8892b0;font-size:1rem;max-width:380px;margin:0 auto;">
                    Your personal AI assistant is fully configured. You can update any settings
                    later from the Settings page inside the app.
                </p>
            </div>
            """, unsafe_allow_html=True)

            also_weather = st.text_input(
                "🌤️ OpenWeatherMap API Key (optional — free at openweathermap.org)",
                type="password",
                placeholder="Paste key...",
                key="ob_weather",
            )

            if st.button("🚀 Launch My ANU!", use_container_width=True):
                updates = {"onboarding_done": True}
                if also_weather.strip():
                    updates["weather_api_key"] = also_weather.strip()
                save_config(user["id"], **updates)

                profile_updates = {"onboarding_done": True}
                if st.session_state.custom_links:
                    profile_updates["custom_links"] = st.session_state.custom_links
                supabase.table("user_profiles").update(profile_updates).eq("user_id", user["id"]).execute()

                st.session_state.cfg["onboarding_done"] = True
                st.session_state.auth_page = "app"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def page_app():
    user = st.session_state.user
    full_name = user.get("full_name", "User")

    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:16px 0 8px;">
            <div style="font-size:2.8rem;">🤖</div>
            <div style="font-size:1.3rem;font-weight:700;color:#e94560;">ANU</div>
            <div class="user-badge" style="margin-top:8px;">👤 {full_name}</div>
            <div style="margin-top:8px;"><span class="status-dot"></span><span style="color:#00ff88;font-size:0.85rem;">Online</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        nav_items = [
            ("💬", "Chat"), ("🎤", "Voice"), ("📊", "System Monitor"),
            ("📝", "Notes"), ("🧮", "Calculator"), ("💻", "Code Generator"),
            ("😂", "Jokes"), ("📧", "Email"), ("🌤️", "Weather"),
            ("📞", "Calls"), ("🔗", "My Links"), ("⚙️", "Settings"), ("ℹ️", "About"),
        ]
        for icon, label in nav_items:
            if st.button(f"{icon} {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.active_tab = label

        st.markdown("---")
        st.markdown(f"""
        <div style="background:#1a1a2e;border-radius:10px;padding:12px;border:1px solid #2a2a4a;">
            <div style="color:#8892b0;font-size:0.75rem;">DATE & TIME</div>
            <div style="color:#e6f1ff;font-size:1.1rem;font-weight:600;">{now.strftime("%I:%M %p")}</div>
            <div style="color:#8892b0;font-size:0.85rem;">{now.strftime("%A, %B %d, %Y")}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            logout_user()
            st.rerun()

    st.markdown(f"""
    <div class="anu-header">
        <h1 class="anu-title">🤖 ANU — {full_name}'s Dashboard</h1>
        <div style="color:#8892b0;font-size:0.9rem;">Powered by Google Gemini · Your personal AI, your keys, your data</div>
    </div>
    """, unsafe_allow_html=True)

    tab = st.session_state.active_tab

    if tab == "Chat":
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### 💬 Chat with ANU")
            if not st.session_state.messages:
                st.markdown(f'<div class="chat-anu"><b>ANU 🤖</b><br>Hello {full_name}! I\'m ANU, your personal AI. Ask me anything! 😊</div>', unsafe_allow_html=True)
            for m in st.session_state.messages:
                cls = "chat-user" if m["role"] == "user" else "chat-anu"
                who = f'{full_name} 👤' if m["role"] == "user" else "ANU 🤖"
                st.markdown(f'<div class="{cls}"><b>{who}</b><br>{m["content"]}</div>', unsafe_allow_html=True)
            with st.form("chat_f", clear_on_submit=True):
                inp = st.text_input("Message", placeholder="Ask ANU anything...", label_visibility="collapsed")
                _, c2 = st.columns([4, 1])
                with c2:
                    sub = st.form_submit_button("Send 🚀", use_container_width=True)
            if sub and inp.strip():
                st.session_state.messages.append({"role": "user", "content": inp})
                with st.spinner("ANU is thinking..."):
                    r = get_gemini(inp, st.session_state.messages[:-1])
                st.session_state.messages.append({"role": "assistant", "content": r})
                st.rerun()
            if st.session_state.messages and st.button("🗑️ Clear"):
                st.session_state.messages = []
                st.rerun()
        with col2:
            st.markdown("### ⚡ Quick Actions")
            if st.button("🕐 Current time?", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "What time is it?"})
                st.session_state.messages.append({"role": "assistant", "content": f"It's **{now.strftime('%I:%M %p')}** on {now.strftime('%A, %B %d, %Y')}."})
                st.rerun()
            if st.button("😂 Tell me a joke", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": "Tell me a joke"})
                st.session_state.messages.append({"role": "assistant", "content": get_joke()})
                st.rerun()
            for label in ["💡 Motivate me", "🧠 Fun AI fact"]:
                if st.button(label, use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": label})
                    with st.spinner("..."):
                        r = get_gemini(label, [])
                    st.session_state.messages.append({"role": "assistant", "content": r})
                    st.rerun()

    elif tab == "Voice":
        st.markdown("### 🎤 Voice Input")
        col1, col2 = st.columns([1, 1])
        with col1:
            try:
                from streamlit_mic_recorder import mic_recorder
                st.markdown('<div class="voice-box"><b style="color:#ccd6f6;">🎤 Browser Microphone</b><br><span style="color:#8892b0;font-size:0.9rem;">Click record → speak → stop → send</span></div>', unsafe_allow_html=True)
                audio = mic_recorder(start_prompt="🎤 Start", stop_prompt="⏹ Stop", just_once=True, use_container_width=True, key="mic")
                if audio and audio.get("bytes"):
                    with st.spinner("🧠 Transcribing..."):
                        try:
                            import speech_recognition as sr
                            rec = sr.Recognizer()
                            af = io.BytesIO(audio["bytes"])
                            with sr.AudioFile(af) as src:
                                ad = rec.record(src)
                            text = rec.recognize_google(ad)
                            st.success(f"🎙️ **{text}**")
                            st.session_state.voice_text = text
                        except sr.UnknownValueError:
                            st.warning("Couldn't understand audio. Try again.")
                        except Exception as e:
                            st.error(f"Error: {e}")
            except ImportError:
                st.warning("Install `streamlit-mic-recorder` for voice.")
            if st.session_state.voice_text:
                st.markdown(f'<div style="background:#1a1a2e;border:1px solid #533483;border-radius:12px;padding:14px;margin-top:12px;"><div style="color:#8892b0;font-size:0.8rem;">Recognized:</div><div style="color:#e6f1ff;">"{st.session_state.voice_text}"</div></div>', unsafe_allow_html=True)
                if st.button("📨 Send to ANU", use_container_width=True):
                    p = st.session_state.voice_text
                    st.session_state.messages.append({"role": "user", "content": f"🎤 {p}"})
                    with st.spinner("..."):
                        r = get_gemini(p, st.session_state.messages[:-1])
                    st.session_state.messages.append({"role": "assistant", "content": r})
                    st.session_state.voice_text = ""
                    st.rerun()
        with col2:
            st.markdown("#### 💬 Last Response")
            last = next((m for m in reversed(st.session_state.messages) if m["role"] == "assistant"), None)
            if last:
                st.markdown(f'<div class="chat-anu"><b>ANU 🤖</b><br>{last["content"]}</div>', unsafe_allow_html=True)
            else:
                st.info("Responses will appear here.")

    elif tab == "System Monitor":
        st.markdown("### 📊 System Monitor")
        if st.button("🔄 Refresh"):
            st.rerun()
        s = get_sys()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-card"><div style="font-size:2rem;">🖥️</div><div class="metric-value" style="color:{pct_color(s["cpu"])};">{s["cpu"]:.1f}%</div><div class="metric-label">CPU</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div style="font-size:2rem;">💾</div><div class="metric-value" style="color:{pct_color(s["mp"])};">{s["mp"]:.1f}%</div><div class="metric-label">Memory</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div style="font-size:2rem;">💿</div><div class="metric-value" style="color:{pct_color(s["dp"])};">{s["dp"]:.1f}%</div><div class="metric-label">Disk</div></div>', unsafe_allow_html=True)
        with c4:
            if s["bat"] is not None:
                icon = "🔌" if s["plug"] else "🔋"
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem;">{icon}</div><div class="metric-value" style="color:{pct_color(100 - s["bat"])};">{s["bat"]:.0f}%</div><div class="metric-label">Battery</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem;">⚙️</div><div class="metric-value">{s["procs"]}</div><div class="metric-label">Processes</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns(2)
        with cl:
            st.markdown("**CPU"); st.progress(min(s["cpu"] / 100, 1.0))
            st.markdown("**Memory**"); st.progress(min(s["mp"] / 100, 1.0))
        with cr:
            st.markdown("**Disk**"); st.progress(min(s["dp"] / 100, 1.0))
            if s["bat"]:
                st.markdown("**Battery**"); st.progress(min(s["bat"] / 100, 1.0))
        st.markdown("---")
        st.markdown("### 🔧 Top Processes")
        import pandas as pd
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except Exception:
                pass
        procs.sort(key=lambda x: x.get('cpu_percent') or 0, reverse=True)
        if procs:
            df = pd.DataFrame(procs[:8])
            df.columns = ["PID", "Process", "CPU%", "Mem%"]
            df["CPU%"] = df["CPU%"].round(2)
            df["Mem%"] = df["Mem%"].round(2)
            st.dataframe(df, use_container_width=True, hide_index=True)

    elif tab == "Notes":
        st.markdown("### 📝 ANU Notes")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### ✏️ New Note")
            with st.form("note_f", clear_on_submit=True):
                title = st.text_input("Title", placeholder="Note title...")
                content = st.text_area("Content", height=150)
                tags = st.text_input("Tags", placeholder="work, ideas...")
                saved = st.form_submit_button("💾 Save")
            if saved and content.strip():
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                ok = save_note(user["id"], title or f"Note {len(st.session_state.notes) + 1}", content.strip(), tag_list)
                if ok:
                    st.session_state.notes = get_notes(user["id"])
                    st.success("✅ Saved!")
                    st.rerun()
        with col2:
            st.markdown(f"#### 📋 Notes ({len(st.session_state.notes)})")
            if not st.session_state.notes:
                st.info("No notes yet.")
            else:
                notes_text = "\n\n".join([f"# {n['title']}\n{n['created_at']}\n\n{n['content']}" for n in st.session_state.notes])
                st.download_button("📥 Export", notes_text, "anu_notes.txt", use_container_width=True)
                for i, note in enumerate(st.session_state.notes):
                    with st.expander(f"📌 {note['title']} — {note['created_at']}"):
                        st.write(note["content"])
                        if note.get("tags"):
                            st.markdown(" ".join([f"`{t}`" for t in note["tags"]]))
                        if st.button("🗑️ Delete", key=f"del_{note['id']}"):
                            delete_note(note["id"])
                            st.session_state.notes = get_notes(user["id"])
                            st.rerun()

    elif tab == "Calculator":
        st.markdown("### 🧮 Smart Calculator")
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.form("calc_f", clear_on_submit=True):
                expr = st.text_input("Expression", placeholder="2+3*4, sqrt(144)...", label_visibility="collapsed")
                calc = st.form_submit_button("= Calculate", use_container_width=True)
            if calc and expr.strip():
                res = safe_calc(expr)
                if res is not None:
                    st.success(f"**{expr} = {res}**")
                    st.session_state.calc_history.insert(0, {"expr": expr, "result": res})
                else:
                    with st.spinner("Asking ANU..."):
                        r = get_gemini(f"Calculate, give only a short answer: {expr}", [])
                    st.info(f"**ANU:** {r}")
                    st.session_state.calc_history.insert(0, {"expr": expr, "result": r})
        with col2:
            st.markdown("#### 📜 History")
            for e in st.session_state.calc_history[:15]:
                st.markdown(f'<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:8px;padding:10px;margin:4px 0;"><span style="color:#8892b0;">{e["expr"]}</span><span style="color:#e94560;float:right;">= {e["result"]}</span></div>', unsafe_allow_html=True)
            if st.session_state.calc_history and st.button("🗑️ Clear"):
                st.session_state.calc_history = []
                st.rerun()

    elif tab == "Code Generator":
        st.markdown("### 💻 Code Generator")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 🤖 AI Generate")
            with st.form("code_f", clear_on_submit=True):
                prompt = st.text_area("What to build?", height=100)
                lang = st.selectbox("Language", ["Python", "JavaScript", "HTML/CSS", "SQL", "Java", "C++", "Any"])
                gen = st.form_submit_button("⚡ Generate")
            if gen and prompt.strip():
                with st.spinner("✨ Generating..."):
                    r = get_gemini(f"Write clean {lang} code for: {prompt}\nAdd brief comments.", [])
                st.code(r, language=lang.lower().replace("html/css", "html").replace("c++", "cpp"))
        with col2:
            st.markdown("#### 📚 Templates")
            tmpl = st.selectbox("Choose template", list(CODE_TEMPLATES.keys()))
            if tmpl:
                lh, code = CODE_TEMPLATES[tmpl]
                st.code(code, language=lh)
                ext = {"python": "py", "javascript": "js", "html": "html", "sql": "sql"}.get(lh, "txt")
                st.download_button("📥 Download", code, f"anu_{tmpl.lower().replace(' ', '_')}.{ext}", use_container_width=True)

    elif tab == "Jokes":
        st.markdown("### 😂 Joke Machine")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🎲 Random Joke", use_container_width=True):
                st.session_state.joke_list.insert(0, get_joke())
                st.rerun()
            if st.button("🤖 AI Joke", use_container_width=True):
                with st.spinner("..."):
                    j = get_gemini("Tell me one original clever joke. Just the joke.", [])
                st.session_state.joke_list.insert(0, j)
                st.rerun()
        with col2:
            if st.session_state.joke_list:
                st.markdown(f'<div style="background:linear-gradient(135deg,#1a1a2e,#2a1a3e);border:2px solid #e94560;border-radius:16px;padding:24px;text-align:center;font-size:1.1rem;color:#e6f1ff;line-height:1.6;">😄 {st.session_state.joke_list[0]}</div>', unsafe_allow_html=True)
        for j in st.session_state.joke_list[1:4]:
            st.markdown(f'<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:12px;margin:6px 0;color:#ccd6f6;">😂 {j}</div>', unsafe_allow_html=True)

    elif tab == "Email":
        st.markdown("### 📧 Send Email")
        se = cfg("smtp_email")
        if not se:
            st.warning("⚙️ Email not configured. Go to **Settings** → Email Setup.")
        else:
            st.success(f"✅ Sending from: **{se}**")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### ✍️ Compose")
            with st.form("email_f", clear_on_submit=True):
                to = st.text_input("To")
                subject = st.text_input("Subject")
                body = st.text_area("Message", height=180)
                send = st.form_submit_button("📨 Send Email")
            if send:
                if not to or not subject or not body:
                    st.error("Fill all fields.")
                else:
                    ok, msg = send_email_fn(to, subject, body)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
        with col2:
            st.markdown("#### 🤖 AI Draft")
            with st.form("draft_f", clear_on_submit=True):
                desc = st.text_area("Describe the email", height=100)
                tone = st.selectbox("Tone", ["Professional", "Friendly", "Formal", "Casual"])
                dbtn = st.form_submit_button("✨ Draft with AI")
            if dbtn and desc.strip():
                with st.spinner("Writing..."):
                    drafted = get_gemini(f"Write a {tone.lower()} email for: {desc}\nSubject line first, then body.", [])
                st.text_area("Copy this:", drafted, height=250, key="draft_out")

    elif tab == "Weather":
        st.markdown("### 🌤️ Weather")
        if not cfg("weather_api_key"):
            st.warning("⚙️ Go to **Settings** → Weather API Key. Free at openweathermap.org")
        with st.form("weather_f"):
            city = st.text_input("City", placeholder="e.g. Hyderabad")
            check = st.form_submit_button("🔍 Get Weather")
        if check and city.strip():
            with st.spinner("Fetching..."):
                data, err = get_weather(city)
            if err:
                st.error(f"❌ {err}")
            elif data:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1a1a2e,#0f2a3e);border:1px solid #2a2a4a;border-radius:16px;padding:24px;">
                    <h2 style="color:#e6f1ff;margin:0;">🌍 {data['city']}</h2>
                    <div style="font-size:3rem;color:#e94560;margin:12px 0;">{data['temp']:.1f}°C</div>
                    <div style="color:#8892b0;">Feels like {data['feels']:.1f}°C · {data['desc']}</div>
                    <div style="display:flex;gap:24px;margin-top:16px;color:#ccd6f6;">
                        <div>💧 Humidity: {data['humidity']}%</div><div>💨 Wind: {data['wind']} m/s</div>
                    </div>
                </div>""", unsafe_allow_html=True)

    elif tab == "Calls":
        st.markdown("### 📞 Calls")
        st.markdown("""<div class="call-box">
            <div style="font-size:3rem;">📞</div>
            <h3 style="margin:12px 0;">Calls require the Desktop Version</h3>
            <p style="color:#ccd6f6;max-width:480px;margin:0 auto;">
                Phone calling needs access to your local system dialer. This works fully in the
                <b>ANU Desktop App</b>.<br><br>
                <span style="color:#ffaa00;">Want web calls?</span> Integrate
                <a href="https://twilio.com" target="_blank" style="color:#ffaa00;">Twilio API</a> —
                add your credentials in Settings.
            </p>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### 📋 Contact Book")
        with st.form("contact_f", clear_on_submit=True):
            cn = st.text_input("Name")
            cp = st.text_input("Phone")
            ca = st.form_submit_button("➕ Save")
        if ca and cn and cp:
            st.session_state.contacts.append({"name": cn, "phone": cp})
            st.success(f"Saved {cn}")
            st.rerun()
        for c in st.session_state.contacts:
            st.markdown(f'<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:8px;padding:10px;margin:4px 0;color:#ccd6f6;">👤 <b>{c["name"]}</b> — 📞 {c["phone"]}</div>', unsafe_allow_html=True)

    elif tab == "My Links":
        st.markdown("### 🔗 My Quick Links")
        all_links = [
            ("📸 Instagram", cfg("link_instagram"), "#e1306c"),
            ("💼 LinkedIn", cfg("link_linkedin"), "#0077b5"),
            ("🐱 GitHub", cfg("link_github"), "#6e5494"),
            ("🎥 YouTube", cfg("link_youtube"), "#ff0000"),
            ("🐦 Twitter/X", cfg("link_twitter"), "#1da1f2"),
        ]
        custom_links = st.session_state.get("custom_links", [])
        if custom_links:
            for cl in custom_links:
                if cl.get("label") and cl.get("url"):
                    all_links.append((f"🌐 {cl['label']}", cl["url"], "#533483"))
        active_links = [(l, u, c) for l, u, c in all_links if u]
        if not active_links:
            st.info("No links configured yet. Go to ⚙️ Settings → Personal Links to add them.")
        else:
            cols = st.columns(2)
            for i, (label, url, color) in enumerate(active_links):
                with cols[i % 2]:
                    st.markdown(f'<a href="{url}" target="_blank" style="display:block;background:#1a1a2e;border:2px solid {color};border-radius:12px;padding:14px 18px;color:#e6f1ff;text-decoration:none;margin:6px 0;font-weight:600;">{label}</a>', unsafe_allow_html=True)

    elif tab == "Settings":
        st.markdown("### ⚙️ Settings")
        st.info("All your data is stored securely in Supabase. Changes take effect immediately.")

        with st.expander("🤖 Gemini AI", expanded=True):
            new_key = st.text_input("Gemini API Key", value=cfg("gemini_key"), type="password")
            if st.button("Save Gemini Key"):
                save_config(user["id"], gemini_key=new_key)
                st.session_state.cfg["gemini_key"] = new_key
                st.success("✅ Saved!")

        with st.expander("📧 Email / SMTP"):
            se2 = st.text_input("Gmail address", value=cfg("smtp_email"))
            sp2 = st.text_input("App Password", value=cfg("smtp_password"), type="password")
            sh2 = st.text_input("SMTP Host", value=cfg("smtp_host", "smtp.gmail.com"))
            spo = st.number_input("SMTP Port", value=int(cfg("smtp_port", 587) or 587), step=1)
            if st.button("Save Email Settings"):
                save_config(user["id"], smtp_email=se2, smtp_password=sp2, smtp_host=sh2, smtp_port=int(spo))
                st.session_state.cfg.update({"smtp_email": se2, "smtp_password": sp2, "smtp_host": sh2, "smtp_port": spo})
                st.success("✅ Saved!")

        with st.expander("🌤️ Weather API"):
            wk = st.text_input("OpenWeatherMap API Key", value=cfg("weather_api_key"), type="password")
            st.markdown("Free key: [openweathermap.org/api](https://openweathermap.org/api)")
            if st.button("Save Weather Key"):
                save_config(user["id"], weather_api_key=wk)
                st.session_state.cfg["weather_api_key"] = wk
                st.success("✅ Saved!")

        with st.expander("🔗 Personal Links"):
            li_insta = st.text_input("📸 Instagram", value=cfg("link_instagram"))
            li_lin = st.text_input("💼 LinkedIn", value=cfg("link_linkedin"))
            li_gh = st.text_input("🐱 GitHub", value=cfg("link_github"))
            li_yt = st.text_input("🎥 YouTube", value=cfg("link_youtube"))
            li_tw = st.text_input("🐦 Twitter/X", value=cfg("link_twitter"))

            st.markdown("---")
            st.markdown("**Custom Links**")
            custom_links = st.session_state.get("custom_links", [])
            if not custom_links:
                custom_links = [{"label": "", "url": ""}]

            for idx, link in enumerate(custom_links):
                c1, c2, c3 = st.columns([2, 3, 0.5])
                with c1:
                    link["label"] = st.text_input("Label", value=link["label"], key=f"set_cl_label_{idx}", label_visibility="collapsed")
                with c2:
                    link["url"] = st.text_input("URL", value=link["url"], key=f"set_cl_url_{idx}", label_visibility="collapsed")
                with c3:
                    if len(custom_links) > 1 and st.button("❌", key=f"set_cl_del_{idx}"):
                        custom_links.pop(idx)
                        st.session_state.custom_links = custom_links
                        st.rerun()

            if st.button("➕ Add Another Link", key="set_add_link"):
                custom_links.append({"label": "", "url": ""})
                st.session_state.custom_links = custom_links
                st.rerun()

            if st.button("Save All Links"):
                save_config(user["id"],
                    link_instagram=li_insta, link_linkedin=li_lin,
                    link_github=li_gh, link_youtube=li_yt, link_twitter=li_tw,
                )
                st.session_state.cfg.update({
                    "link_instagram": li_insta, "link_linkedin": li_lin,
                    "link_github": li_gh, "link_youtube": li_yt, "link_twitter": li_tw,
                })
                supabase.table("user_profiles").update({"custom_links": custom_links}).eq("user_id", user["id"]).execute()
                st.session_state.custom_links = custom_links
                st.success("✅ Saved!")

    elif tab == "About":
        st.markdown("### ℹ️ About ANU")
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:24px;">
                <h3 style="color:#e94560;">🤖 ANU — AI Nucleus Unit</h3>
                <p style="color:#8892b0;">A multi-user personal AI assistant platform. Everyone uses their own API keys — privacy first.</p>
                <h4 style="color:#ccd6f6;">✨ Features</h4>
                <ul style="color:#8892b0;">
                    <li>💬 Gemini AI Chat</li><li>🎤 Voice Input</li>
                    <li>📊 System Monitor</li><li>📝 Notes</li>
                    <li>🧮 Calculator</li><li>💻 Code Generator</li>
                    <li>📧 Email + AI Draft</li><li>🌤️ Weather</li>
                    <li>🔗 Personal Links</li><li>👤 Multi-user Auth</li>
                </ul>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""<div style="background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:24px;">
                <h3 style="color:#e94560;">👨‍💻 Developer</h3>
                <p style="color:#ccd6f6;font-size:1.1rem;font-weight:600;">Nihal Talla</p>
                <h4 style="color:#ccd6f6;">🛠️ Tech Stack</h4>
                <ul style="color:#8892b0;">
                    <li><b>AI:</b> Google Gemini 1.5 Flash</li>
                    <li><b>Web UI:</b> Streamlit</li>
                    <li><b>Auth/DB:</b> Supabase (PostgreSQL)</li>
                    <li><b>Voice:</b> Browser Mic + SpeechRecognition</li>
                    <li><b>Email:</b> smtplib</li>
                    <li><b>System:</b> psutil</li>
                </ul>
                <a href="https://github.com/NihalTalla/ANU" target="_blank"
                   style="display:inline-block;background:#e94560;color:white;padding:10px 20px;border-radius:10px;text-decoration:none;font-weight:600;margin-top:12px;">📂 GitHub</a>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;padding:20px;color:#8892b0;font-size:0.8rem;border-top:1px solid #2a2a4a;margin-top:40px;">ANU · Built by Nihal Talla · Powered by Google Gemini</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state.auth_page
if page == "login":
    page_login()
elif page == "signup":
    page_signup()
elif page == "onboarding":
    page_onboarding()
elif page == "app":
    page_app()
