from __future__ import annotations

import ast
import datetime as dt
import html
import io
import json
import math
import os
import random
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import psutil
import pyjokes
import requests
import streamlit as st

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - deployment dependency issue
    genai = None

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional voice support
    sr = None

try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:  # pragma: no cover - optional voice support
    mic_recorder = None

try:
    from twilio.rest import Client as TwilioClient
except ImportError:  # pragma: no cover - optional call support
    TwilioClient = None


APP_NAME = "ANU - Personal AI Assistant"
REPO_URL = "https://github.com/NihalTalla/ANU"
DEFAULT_NOTES_DIR = Path(os.getenv("ANU_DATA_DIR", "data"))
NOTES_FILE = DEFAULT_NOTES_DIR / "notes.json"
CONTACTS_FILE = DEFAULT_NOTES_DIR / "contacts.json"

ALLOWED_MATH_FUNCS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": math.factorial,
}

CONSTANTS = {"pi": math.pi, "e": math.e}

CODE_TEMPLATES = {
    "Python - Hello World": ("python", 'print("Hello, World!")'),
    "Python - Function": (
        "python",
        'def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("ANU"))',
    ),
    "Python - Class": (
        "python",
        'class Assistant:\n    def __init__(self, name):\n        self.name = name\n\n    def greet(self):\n        return f"Hi! I am {self.name}"\n\nanu = Assistant("ANU")\nprint(anu.greet())',
    ),
    "Python - API Request": (
        "python",
        'import requests\n\nr = requests.get("https://api.example.com/data", timeout=10)\nif r.status_code == 200:\n    print(r.json())',
    ),
    "JavaScript - Fetch": (
        "javascript",
        'async function getData(url) {\n    const res = await fetch(url);\n    return await res.json();\n}\n\ngetData("https://api.example.com").then(console.log);',
    ),
    "HTML - Basic Page": (
        "html",
        '<!DOCTYPE html>\n<html lang="en">\n<head><meta charset="UTF-8"><title>Page</title></head>\n<body><h1>Hello ANU!</h1></body>\n</html>',
    ),
    "SQL - Query": (
        "sql",
        'SELECT u.name, COUNT(o.id) AS orders\nFROM users u\nJOIN orders o ON u.id = o.user_id\nGROUP BY u.name\nORDER BY orders DESC\nLIMIT 10;',
    ),
}

NAV_ITEMS = [
    ("💬 Chat", "Chat"),
    ("🎤 Voice", "Voice"),
    ("📊 System Monitor", "System Monitor"),
    ("📝 Notes", "Notes"),
    ("🧮 Calculator", "Calculator"),
    ("💻 Code Generator", "Code Generator"),
    ("😂 Jokes", "Jokes"),
    ("📧 Email", "Email"),
    ("🌤️ Weather", "Weather"),
    ("📞 Calls", "Calls"),
    ("🔗 My Links", "My Links"),
    ("ℹ️ About", "About"),
]


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
:root {
    --bg: #070b16;
    --panel: #10192b;
    --panel-2: #121f35;
    --border: #23314f;
    --accent: #e94560;
    --accent-2: #7c5cff;
    --text: #e6f1ff;
    --muted: #8b97b8;
    --ok: #00d18f;
    --warn: #ffb020;
}
.stApp { background: radial-gradient(circle at top, #0d1630 0%, #070b16 40%, #05070e 100%); color: var(--text); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #07101f 0%, #050912 100%); border-right: 1px solid var(--border); }
.anu-header {
    background: linear-gradient(135deg, rgba(233,69,96,0.18), rgba(124,92,255,0.14));
    border: 1px solid rgba(233,69,96,0.3);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 22px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.24);
}
.anu-title {
    margin: 0;
    font-size: 2.35rem;
    line-height: 1.1;
    font-weight: 800;
    background: linear-gradient(90deg, #f25f74, #7c5cff, #00d18f);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.status-dot { display:inline-block; width:10px; height:10px; border-radius:50%; background: var(--ok); margin-right:8px; box-shadow: 0 0 12px rgba(0, 209, 143, 0.9); animation: pulse 2s infinite; }
@keyframes pulse { 0%{transform:scale(1);opacity:1} 50%{transform:scale(.72);opacity:.45} 100%{transform:scale(1);opacity:1} }
.metric-card, .info-card {
    background: linear-gradient(180deg, rgba(16,25,43,0.96), rgba(12,18,31,0.96));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,.2);
}
.metric-value { font-size: 1.9rem; font-weight: 800; }
.metric-label { color: var(--muted); font-size: 0.76rem; text-transform: uppercase; letter-spacing: 1px; margin-top: 6px; }
.chat-user, .chat-anu {
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid var(--border);
    margin: 10px 0;
    line-height: 1.55;
}
.chat-user {
    background: linear-gradient(135deg, rgba(17,52,96,0.9), rgba(22,30,62,0.92));
    border-left: 4px solid #2f89fc;
}
.chat-anu {
    background: linear-gradient(135deg, rgba(19,26,45,0.96), rgba(38,23,54,0.96));
    border-left: 4px solid var(--accent);
}
.voice-box, .call-box {
    background: linear-gradient(135deg, rgba(12,18,31,0.96), rgba(19,26,45,0.92));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
}
.small-muted { color: var(--muted); font-size: 0.88rem; }
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #c52f49) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.55rem 1rem !important;
}
.stDownloadButton > button, .stFormSubmitButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
}
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {
    background-color: #0e1728 !important;
    color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
}
code { background: rgba(255,255,255,0.08) !important; }
hr { border-color: rgba(255,255,255,0.12) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, default)


def ensure_storage() -> None:
    DEFAULT_NOTES_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def init_state() -> None:
    defaults = {
        "messages": [],
        "notes": load_json(NOTES_FILE, []),
        "contacts": load_json(CONTACTS_FILE, []),
        "calc_history": [],
        "joke_list": [],
        "voice_text": "",
        "active_tab": "Chat",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource

def gemini_model() -> Any:
    api_key = secret("GEMINI_API_KEY")
    if not api_key:
        return None
    if genai is None:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=(
            "You are ANU, a smart personal AI assistant created by Nihal Talla. "
            "Be helpful, concise, friendly, and a little witty when appropriate."
        ),
    )


def get_gemini_response(prompt: str, history: list[dict[str, str]]) -> str:
    model = gemini_model()
    if model is None:
        if genai is None:
            return "⚠️ google-generativeai is not installed."
        return (
            "⚠️ GEMINI_API_KEY is not set. Add it in Streamlit secrets or as an environment variable."
        )
    try:
        payload = [
            {
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            }
            for msg in history[-10:]
        ]
        chat = model.start_chat(history=payload[:-1] if len(payload) > 1 else [])
        result = chat.send_message(prompt)
        return getattr(result, "text", str(result))
    except Exception as exc:
        return f"❌ Gemini error: {exc}"


def send_email(to: str, subject: str, body: str) -> tuple[bool, str]:
    smtp_email = secret("SMTP_EMAIL")
    smtp_password = secret("SMTP_PASSWORD")
    if not smtp_email or not smtp_password:
        return False, "SMTP_EMAIL / SMTP_PASSWORD are not configured."

    host = secret("SMTP_HOST", "smtp.gmail.com")
    port = int(secret("SMTP_PORT", "587"))
    use_tls = secret("SMTP_USE_TLS", "true").lower() != "false"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = smtp_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [to], msg.as_string())
        return True, "✅ Email sent successfully."
    except Exception as exc:
        return False, f"❌ Failed to send email: {exc}"


def get_weather(city: str) -> tuple[dict[str, Any] | None, str | None]:
    api_key = secret("WEATHER_API_KEY")
    if not api_key:
        return None, "WEATHER_API_KEY is not configured."
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=12,
        )
        payload = response.json()
        if response.status_code != 200:
            return None, payload.get("message", "Weather lookup failed")

        return (
            {
                "city": payload["name"],
                "temp": payload["main"]["temp"],
                "feels": payload["main"]["feels_like"],
                "desc": payload["weather"][0]["description"].title(),
                "humidity": payload["main"]["humidity"],
                "wind": payload["wind"]["speed"],
            },
            None,
        )
    except Exception as exc:
        return None, str(exc)


def get_joke() -> str:
    try:
        return pyjokes.get_joke()
    except Exception:
        return random.choice(
            [
                "Why do programmers prefer dark mode? Because light attracts bugs. 🐛",
                "How many programmers does it take to change a bulb? None — it's a hardware problem. 💡",
                "I told my computer I needed a break, and it said: 'No problem, I'll go to sleep.' 😄",
            ]
        )


def percentile_color(value: float) -> str:
    if value >= 80:
        return "#ff5a7a"
    if value >= 50:
        return "#ffbf47"
    return "#00d18f"


class SafeMathEvaluator(ast.NodeVisitor):
    def visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            raise ValueError(f"Unsupported expression: {node.__class__.__name__}")
        return visitor(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")

    def visit_Num(self, node: ast.Num) -> Any:  # pragma: no cover - Py<3.8 compat
        return node.n

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise ValueError(f"Unknown name: {node.id}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_map = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a**b,
        }
        for op_type, func in op_map.items():
            if isinstance(node.op, op_type):
                return func(left, right)
        raise ValueError("Unsupported operator")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("Unsupported unary operator")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are supported")
        func_name = node.func.id
        if func_name not in ALLOWED_MATH_FUNCS:
            raise ValueError(f"Unsupported function: {func_name}")
        args = [self.visit(arg) for arg in node.args]
        return ALLOWED_MATH_FUNCS[func_name](*args)


def safe_calc(expr: str) -> float | int | None:
    try:
        cleaned = (
            expr.replace("×", "*")
            .replace("÷", "/")
            .replace("^", "**")
            .replace("pi", str(math.pi))
            .replace("π", str(math.pi))
        )
        tree = ast.parse(cleaned, mode="eval")
        return SafeMathEvaluator().visit(tree)
    except Exception:
        return None


def get_sys() -> dict[str, Any]:
    cpu = psutil.cpu_percent(interval=0.4)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    battery = None
    plug = None
    if hasattr(psutil, "sensors_battery"):
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None
    return {
        "cpu": cpu,
        "mem_percent": mem.percent,
        "mem_used": round(mem.used / 1024**3, 1),
        "mem_total": round(mem.total / 1024**3, 1),
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / 1024**3, 1),
        "disk_total": round(disk.total / 1024**3, 1),
        "battery_percent": battery.percent if battery else None,
        "plugged": battery.power_plugged if battery else None,
        "processes": len(list(psutil.process_iter())),
    }


def top_processes(limit: int = 8) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            rows.append(proc.info)
        except Exception:
            continue
    rows.sort(key=lambda row: row.get("cpu_percent") or 0, reverse=True)
    df = pd.DataFrame(rows[:limit])
    if not df.empty:
        df.columns = ["PID", "Process", "CPU%", "Mem%"]
        df["CPU%"] = df["CPU%"].fillna(0).round(2)
        df["Mem%"] = df["Mem%"].fillna(0).round(2)
    return df


def load_voice_transcription() -> None:
    if mic_recorder is None:
        st.warning("Install `streamlit-mic-recorder` to enable browser microphone capture.")
        return

    st.markdown(
        '<div class="voice-box"><b>🎤 Browser microphone</b><br><span class="small-muted">Record in the browser, transcribe locally, then send to Gemini.</span></div>',
        unsafe_allow_html=True,
    )
    audio = mic_recorder(
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=True,
        use_container_width=True,
        key="anu_mic",
    )

    if audio and audio.get("bytes") and sr is not None:
        with st.spinner("Transcribing audio..."):
            recognizer = sr.Recognizer()
            try:
                audio_file = io.BytesIO(audio["bytes"])
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)
                recognized = recognizer.recognize_google(audio_data)
                st.session_state.voice_text = recognized
                st.success(f"🎙️ You said: {recognized}")
            except sr.UnknownValueError:
                st.warning("Couldn’t understand that audio. Please try again.")
            except Exception as exc:
                st.error(f"Transcription error: {exc}")
    elif audio and audio.get("bytes") and sr is None:
        st.warning("SpeechRecognition is not installed, so transcription is unavailable.")


def render_header() -> None:
    now = dt.datetime.now()
    st.markdown(
        f"""
<div class="anu-header">
    <h1 class="anu-title">🤖 ANU Dashboard</h1>
    <div style="color: #8b97b8; font-size: 0.98rem; margin-top: 8px;">Your intelligent personal AI assistant — ready for the web.</div>
    <div style="margin-top: 12px;"><span class="status-dot"></span><span style="color: #00d18f; font-size: 0.9rem; font-weight: 600;">Online</span></div>
    <div style="color: #8b97b8; font-size: 0.87rem; margin-top: 8px;">{now.strftime('%A, %B %d, %Y · %I:%M %p')}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def sidebar_nav() -> None:
    now = dt.datetime.now()
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center;padding:18px 0 10px;">
                <div style="font-size:3rem;">🤖</div>
                <div style="font-size:1.35rem;font-weight:800;color:#e94560;">ANU</div>
                <div style="font-size:0.83rem;color:#8b97b8;">Personal AI Assistant</div>
                <div style="margin-top:8px;"><span class="status-dot"></span><span style="color:#00d18f;font-size:0.85rem;">Online</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.active_tab = st.radio(
            "Navigate",
            [label for _, label in NAV_ITEMS],
            index=[label for _, label in NAV_ITEMS].index(st.session_state.active_tab)
            if st.session_state.active_tab in [label for _, label in NAV_ITEMS]
            else 0,
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            f"""
            <div class="info-card">
                <div class="small-muted">DATE & TIME</div>
                <div style="font-size:1.08rem;font-weight:700;margin-top:4px;">{now.strftime('%I:%M %p')}</div>
                <div class="small-muted">{now.strftime('%A, %B %d, %Y')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="info-card" style="margin-top:12px;">
                <div class="small-muted">DEPLOYMENT</div>
                <div style="font-size:0.9rem;margin-top:6px;line-height:1.5;">
                    Web app ready for Streamlit Cloud.<br>
                    <a href="{REPO_URL}" target="_blank">GitHub repo</a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------

def render_chat() -> None:
    st.markdown("### 💬 Chat with ANU")
    col1, col2 = st.columns([2, 1])

    with col1:
        if not st.session_state.messages:
            st.markdown(
                '<div class="chat-anu"><b>ANU 🤖</b><br>Hello! I’m ANU. Ask me anything — code, emails, notes, weather, jokes, or general questions. 😊</div>',
                unsafe_allow_html=True,
            )

        for msg in st.session_state.messages:
            cls = "chat-user" if msg["role"] == "user" else "chat-anu"
            who = "You 👤" if msg["role"] == "user" else "ANU 🤖"
            st.markdown(
                f'<div class="{cls}"><b>{who}</b><br>{html.escape(msg["content"]).replace("\n", "<br>")}</div>',
                unsafe_allow_html=True,
            )

        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_input("Message", placeholder="Ask ANU anything...", label_visibility="collapsed")
            submit = st.form_submit_button("Send 🚀", use_container_width=True)

        if submit and prompt.strip():
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("ANU is thinking..."):
                response = get_gemini_response(prompt, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

        if st.session_state.messages and st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    with col2:
        st.markdown("### ⚡ Quick Actions")
        now = dt.datetime.now()
        actions = [
            ("🕐 What time is it?", f"It’s **{now.strftime('%I:%M %p')}** on {now.strftime('%A, %B %d, %Y')}."),
            ("😂 Tell me a joke", get_joke()),
        ]
        for label, answer in actions:
            if st.button(label, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()

        for label in ["💡 Motivate me", "🧠 Fun AI fact"]:
            if st.button(label, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": label})
                with st.spinner("ANU is thinking..."):
                    response = get_gemini_response(label, [])
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

        st.markdown(
            '<div class="info-card" style="margin-top:14px;"><div class="small-muted">Tip</div><div style="margin-top:6px;line-height:1.5;">Use the Notes tab for personal memory, the Weather tab for live data, and the Code Generator for fast scaffolds.</div></div>',
            unsafe_allow_html=True,
        )


def render_voice() -> None:
    st.markdown("### 🎤 Voice Input")
    st.info("This browser-based version can capture microphone audio in the page and transcribe it if the optional voice packages are installed.")
    col1, col2 = st.columns([1, 1])

    with col1:
        load_voice_transcription()
        if st.session_state.voice_text:
            st.markdown(
                f'<div class="info-card" style="margin-top:12px;"><div class="small-muted">Recognized text</div><div style="font-size:1.02rem;margin-top:6px;">“{html.escape(st.session_state.voice_text)}”</div></div>',
                unsafe_allow_html=True,
            )
            if st.button("📨 Send to ANU", use_container_width=True):
                prompt = st.session_state.voice_text
                st.session_state.messages.append({"role": "user", "content": f"🎤 {prompt}"})
                with st.spinner("ANU is thinking..."):
                    response = get_gemini_response(prompt, st.session_state.messages[:-1])
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.voice_text = ""
                st.rerun()

    with col2:
        st.markdown("#### 💬 Last Response")
        last = next((msg for msg in reversed(st.session_state.messages) if msg["role"] == "assistant"), None)
        if last:
            st.markdown(
                f'<div class="chat-anu"><b>ANU 🤖</b><br>{html.escape(last["content"]).replace("\n", "<br>")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Responses appear here after you send voice input.")

        st.markdown(
            """
            <div class="info-card" style="margin-top:16px;">
                <div class="small-muted">How it works</div>
                <ol style="margin-top:8px;color:#e6f1ff;line-height:1.7;">
                    <li>Click Start Recording</li>
                    <li>Allow microphone access</li>
                    <li>Speak clearly</li>
                    <li>Stop Recording</li>
                    <li>Send to ANU</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_system_monitor() -> None:
    st.markdown("### 📊 System Monitor")
    if st.button("🔄 Refresh"):
        st.rerun()

    stats = get_sys()
    c1, c2, c3, c4 = st.columns(4)

    cards = [
        (c1, "🖥️", stats["cpu"], "CPU"),
        (c2, "💾", stats["mem_percent"], f"Memory ({stats['mem_used']}GB/{stats['mem_total']}GB)"),
        (c3, "💿", stats["disk_percent"], f"Disk ({stats['disk_used']}GB/{stats['disk_total']}GB)"),
    ]
    for col, icon, value, label in cards:
        with col:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:2rem;">{icon}</div><div class="metric-value" style="color:{percentile_color(value)};">{value:.1f}%</div><div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    with c4:
        if stats["battery_percent"] is not None:
            icon = "🔌" if stats["plugged"] else "🔋"
            st.markdown(
                f'<div class="metric-card"><div style="font-size:2rem;">{icon}</div><div class="metric-value" style="color:{percentile_color(100 - stats["battery_percent"])};">{stats["battery_percent"]:.0f}%</div><div class="metric-label">Battery</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:2rem;">⚙️</div><div class="metric-value">{stats["processes"]}</div><div class="metric-label">Processes</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown("**CPU**")
        st.progress(stats["cpu"] / 100)
        st.markdown("**Memory**")
        st.progress(stats["mem_percent"] / 100)
    with right:
        st.markdown("**Disk**")
        st.progress(stats["disk_percent"] / 100)
        if stats["battery_percent"] is not None:
            st.markdown("**Battery**")
            st.progress(stats["battery_percent"] / 100)

    st.markdown("---")
    st.markdown("### 🔧 Top Processes")
    df = top_processes()
    if df.empty:
        st.info("No process data available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_notes() -> None:
    st.markdown("### 📝 ANU Notes")
    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### ✏️ New Note")
        with st.form("note_form", clear_on_submit=True):
            title = st.text_input("Title", placeholder="Note title...")
            content = st.text_area("Content", height=160, placeholder="Write your note...")
            tags = st.text_input("Tags", placeholder="work, ideas, hackathon")
            save_note = st.form_submit_button("💾 Save Note")

        if save_note and content.strip():
            note = {
                "id": len(st.session_state.notes) + 1,
                "title": title.strip() or f"Note {len(st.session_state.notes) + 1}",
                "content": content.strip(),
                "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.notes.insert(0, note)
            save_json(NOTES_FILE, st.session_state.notes)
            st.success("✅ Saved!")
            st.rerun()

    with right:
        st.markdown(f"#### 📋 Notes ({len(st.session_state.notes)})")
        if not st.session_state.notes:
            st.info("No notes yet.")
        else:
            notes_text = "\n\n".join(
                [
                    f"# {note['title']}\n{note['created']}\nTags: {', '.join(note['tags'])}\n\n{note['content']}"
                    for note in st.session_state.notes
                ]
            )
            st.download_button("📥 Export All", notes_text, "anu_notes.txt", use_container_width=True)
            for idx, note in enumerate(st.session_state.notes):
                with st.expander(f"📌 {note['title']} — {note['created']}"):
                    st.write(note["content"])
                    if note["tags"]:
                        st.markdown(" ".join([f"`{tag}`" for tag in note["tags"]]))
                    if st.button("🗑️ Delete", key=f"delete_note_{note['id']}_{idx}"):
                        st.session_state.notes.pop(idx)
                        save_json(NOTES_FILE, st.session_state.notes)
                        st.rerun()


def render_calculator() -> None:
    st.markdown("### 🧮 Smart Calculator")
    left, right = st.columns([1, 1])

    with left:
        with st.form("calc_form", clear_on_submit=True):
            expr = st.text_input("Expression", placeholder="2+3*4, sqrt(144), sin(pi/2)...", label_visibility="collapsed")
            submit = st.form_submit_button("= Calculate", use_container_width=True)

        if submit and expr.strip():
            result = safe_calc(expr)
            if result is not None:
                st.success(f"**{expr} = {result}**")
                st.session_state.calc_history.insert(0, {"expr": expr, "result": result})
            else:
                with st.spinner("Asking ANU..."):
                    response = get_gemini_response(
                        f"Calculate this and give only a short answer: {expr}",
                        [],
                    )
                st.info(f"**ANU:** {response}")
                st.session_state.calc_history.insert(0, {"expr": expr, "result": response})

        for sample in ["2 ** 10", "sqrt(256)", "15 * 24 + 8", "(100-25)/3"]:
            if st.button(sample, key=f"sample_{sample}"):
                st.success(f"**{sample} = {safe_calc(sample)}**")

    with right:
        st.markdown("#### 📜 History")
        for item in st.session_state.calc_history[:15]:
            st.markdown(
                f'<div class="info-card" style="margin:6px 0;"><span style="color:#8b97b8;">{html.escape(str(item["expr"]))}</span><span style="color:#e94560;float:right;font-weight:800;">= {html.escape(str(item["result"]))}</span></div>',
                unsafe_allow_html=True,
            )
        if st.session_state.calc_history and st.button("🗑️ Clear History"):
            st.session_state.calc_history = []
            st.rerun()


def render_code_generator() -> None:
    st.markdown("### 💻 Code Generator")
    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### 🤖 AI Generate")
        with st.form("code_form", clear_on_submit=True):
            prompt = st.text_area(
                "What to build?",
                height=110,
                placeholder="e.g. Python function to read a CSV and plot a bar chart...",
            )
            lang = st.selectbox("Language", ["Python", "JavaScript", "HTML/CSS", "SQL", "Java", "C++", "Any"])
            generate = st.form_submit_button("⚡ Generate")
        if generate and prompt.strip():
            with st.spinner("✨ Generating code..."):
                response = get_gemini_response(
                    f"Write clean {lang} code for: {prompt}\nAdd brief comments.",
                    [],
                )
            st.markdown(response)

    with right:
        st.markdown("#### 📚 Templates")
        template_name = st.selectbox("Choose template", list(CODE_TEMPLATES.keys()))
        lang_hint, code = CODE_TEMPLATES[template_name]
        st.code(code, language=lang_hint)
        ext = {"python": "py", "javascript": "js", "html": "html", "sql": "sql"}.get(lang_hint, "txt")
        st.download_button(
            "📥 Download",
            code,
            file_name=f"anu_{template_name.lower().replace(' ', '_')}.{ext}",
            use_container_width=True,
        )


def render_jokes() -> None:
    st.markdown("### 😂 ANU Joke Machine")
    left, right = st.columns([1, 1])

    with left:
        if st.button("🎲 Random Joke", use_container_width=True):
            st.session_state.joke_list.insert(0, get_joke())
            st.rerun()
        if st.button("👨‍💻 Programming Joke", use_container_width=True):
            try:
                joke = pyjokes.get_joke(category="neutral")
            except Exception:
                joke = get_joke()
            st.session_state.joke_list.insert(0, joke)
            st.rerun()
        if st.button("🤖 AI-Generated Joke", use_container_width=True):
            with st.spinner("Crafting something funny..."):
                joke = get_gemini_response(
                    "Tell me one original clever joke. Just the joke, no preamble.",
                    [],
                )
            st.session_state.joke_list.insert(0, joke)
            st.rerun()

    with right:
        if st.session_state.joke_list:
            st.markdown(
                f'<div class="info-card" style="border-left:4px solid #e94560;font-size:1.05rem;line-height:1.6;">😄 {html.escape(st.session_state.joke_list[0])}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Hit one of the buttons to generate a joke.")

    if st.session_state.joke_list:
        st.markdown("---")
        for joke in st.session_state.joke_list[1:5]:
            st.markdown(
                f'<div class="info-card" style="margin:6px 0;">😂 {html.escape(joke)}</div>',
                unsafe_allow_html=True,
            )


def render_email() -> None:
    st.markdown("### 📧 Send Email via ANU")
    smtp_email = secret("SMTP_EMAIL")
    if not smtp_email:
        st.warning("Email is not configured yet. Add SMTP secrets before trying to send mail.")
    else:
        st.success(f"✅ Configured to send from: **{smtp_email}**")

    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### ✍️ Compose")
        with st.form("email_form", clear_on_submit=True):
            to = st.text_input("To", placeholder="recipient@example.com")
            subject = st.text_input("Subject")
            body = st.text_area("Message", height=200)
            send = st.form_submit_button("📨 Send Email")
        if send:
            if not to or not subject or not body:
                st.error("Fill in all fields.")
            else:
                ok, message = send_email(to, subject, body)
                if ok:
                    st.success(message)
                else:
                    st.error(message)

    with right:
        st.markdown("#### 🤖 AI Draft Helper")
        with st.form("draft_form", clear_on_submit=True):
            desc = st.text_area(
                "Describe the email you need",
                height=110,
                placeholder="e.g. Professional follow-up to a client about project status...",
            )
            tone = st.selectbox("Tone", ["Professional", "Friendly", "Formal", "Casual"])
            draft_btn = st.form_submit_button("✨ Draft with AI")
        if draft_btn and desc.strip():
            with st.spinner("ANU is writing..."):
                draft = get_gemini_response(
                    f"Write a {tone.lower()} email for: {desc}\nFormat: Subject line first, then body.",
                    [],
                )
            st.text_area("Copy this draft:", draft, height=250, key="draft_out")


def render_weather() -> None:
    st.markdown("### 🌤️ Weather")
    if not secret("WEATHER_API_KEY"):
        st.warning("Add `WEATHER_API_KEY` before deploying weather lookups.")
    with st.form("weather_form"):
        city = st.text_input("City", placeholder="e.g. Hyderabad")
        submit = st.form_submit_button("🔍 Get Weather")

    if submit and city.strip():
        with st.spinner("Fetching weather..."):
            data, err = get_weather(city.strip())
        if err:
            st.error(f"❌ {err}")
        elif data:
            st.markdown(
                f"""
                <div class="info-card" style="background: linear-gradient(135deg, rgba(17,24,39,0.96), rgba(18,33,58,0.96));">
                    <h2 style="margin:0;color:#e6f1ff;">🌍 {data['city']}</h2>
                    <div style="font-size:3.2rem;font-weight:800;color:#e94560;margin:10px 0;">{data['temp']:.1f}°C</div>
                    <div style="color:#8b97b8;">Feels like {data['feels']:.1f}°C · {data['desc']}</div>
                    <div style="display:flex;gap:24px;margin-top:16px;color:#e6f1ff;flex-wrap:wrap;">
                        <div>💧 Humidity: {data['humidity']}%</div>
                        <div>💨 Wind: {data['wind']} m/s</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_calls() -> None:
    st.markdown("### 📞 Calls")
    st.markdown(
        """
        <div class="call-box">
            <div style="font-size:3rem;">📞</div>
            <h3 style="margin:12px 0 6px;">Calling from the URL</h3>
            <p class="small-muted" style="max-width:760px;margin:0 auto;line-height:1.7;">
                This web version can place calls through Twilio if you provide your API secrets.
                That means it can still run on a public URL and make real outbound calls without needing a desktop app.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### 📋 Contact Book")
    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Name")
        phone = st.text_input("Phone Number")
        add = st.form_submit_button("➕ Save Contact")
    if add and name and phone:
        st.session_state.contacts.append({"name": name.strip(), "phone": phone.strip()})
        save_json(CONTACTS_FILE, st.session_state.contacts)
        st.success(f"Saved {name}")
        st.rerun()

    for idx, contact in enumerate(st.session_state.contacts):
        st.markdown(
            f'<div class="info-card" style="margin:6px 0;">👤 <b>{html.escape(contact["name"])} </b> — 📞 {html.escape(contact["phone"])} </div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### ☎️ Place a Twilio call")
    st.caption("Requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` secrets.")
    with st.form("twilio_call_form", clear_on_submit=True):
        call_to = st.text_input("Call To", placeholder="+1...")
        call_message = st.text_area("What should ANU say?", placeholder="Hello, this is ANU calling about...")
        call_submit = st.form_submit_button("📲 Place Call")
    if call_submit:
        sid = secret("TWILIO_ACCOUNT_SID")
        token = secret("TWILIO_AUTH_TOKEN")
        from_number = secret("TWILIO_PHONE_NUMBER")

        if not all([sid, token, from_number]):
            st.error("Twilio secrets are missing.")
        elif TwilioClient is None:
            st.error("Install the `twilio` package to enable calls.")
        elif not call_to or not call_message:
            st.error("Fill in both fields.")
        else:
            try:
                client = TwilioClient(sid, token)
                twiml = f'<Response><Say voice="alice">{html.escape(call_message)}</Say></Response>'
                call = client.calls.create(to=call_to, from_=from_number, twiml=twiml)
                st.success(f"✅ Call placed successfully. SID: {call.sid}")
            except Exception as exc:
                st.error(f"Failed to place call: {exc}")


def render_links() -> None:
    st.markdown("### 🔗 My Quick Links")
    st.info("All links are loaded from environment variables or Streamlit secrets.")

    link_defs = [
        ("📸 Instagram", secret("LINK_INSTAGRAM"), "#e1306c"),
        ("💼 LinkedIn", secret("LINK_LINKEDIN"), "#0077b5"),
        ("🐱 GitHub", secret("LINK_GITHUB", REPO_URL), "#6e5494"),
        ("🎥 YouTube", secret("LINK_YOUTUBE"), "#ff0000"),
        ("🐦 Twitter/X", secret("LINK_TWITTER"), "#1da1f2"),
    ]
    custom_1_label = secret("LINK_CUSTOM_1_LABEL")
    custom_1_url = secret("LINK_CUSTOM_1_URL")
    custom_2_label = secret("LINK_CUSTOM_2_LABEL")
    custom_2_url = secret("LINK_CUSTOM_2_URL")
    if custom_1_label and custom_1_url:
        link_defs.append((f"🌐 {custom_1_label}", custom_1_url, "#7c5cff"))
    if custom_2_label and custom_2_url:
        link_defs.append((f"🌐 {custom_2_label}", custom_2_url, "#7c5cff"))

    active = [(label, url, color) for label, url, color in link_defs if url]
    inactive = [(label, url, color) for label, url, color in link_defs if not url]

    if active:
        col1, col2 = st.columns(2)
        for idx, (label, url, color) in enumerate(active):
            target_col = col1 if idx % 2 == 0 else col2
            with target_col:
                st.markdown(
                    f'<a href="{html.escape(url)}" target="_blank" style="display:block;background:linear-gradient(180deg, rgba(16,25,43,0.96), rgba(12,18,31,0.96));border:1px solid {color};border-radius:14px;padding:14px 18px;color:#e6f1ff;text-decoration:none;margin:6px 0;font-weight:700;">{html.escape(label)}</a>',
                    unsafe_allow_html=True,
                )

    if inactive:
        st.markdown("---")
        st.markdown("#### ⚙️ Not yet configured")
        st.code(
            "\n".join(
                [
                    'LINK_INSTAGRAM = "https://your-instagram-here"',
                    'LINK_LINKEDIN = "https://your-linkedin-here"',
                    'LINK_YOUTUBE = "https://your-youtube-here"',
                    'LINK_TWITTER = "https://your-twitter-here"',
                ]
            ),
            language="toml",
        )


def render_about() -> None:
    st.markdown("### ℹ️ About ANU")
    left, right = st.columns([1, 1])

    with left:
        st.markdown(
            """
            <div class="info-card">
                <h3 style="color:#e94560;margin-top:0;">🤖 ANU — AI Nucleus Unit</h3>
                <p class="small-muted">A browser-friendly personal AI assistant with practical tools for chat, notes, calculations, weather, email, links, and system insights.</p>
                <h4 style="color:#e6f1ff;">✨ Web Features</h4>
                <ul style="color:#8b97b8;line-height:1.7;">
                    <li>💬 Gemini chat</li>
                    <li>🎤 Browser microphone transcription</li>
                    <li>📊 System monitor</li>
                    <li>📝 Notes with export</li>
                    <li>🧮 Calculator</li>
                    <li>💻 Code generator</li>
                    <li>📧 SMTP email + AI drafting</li>
                    <li>🌤️ Weather</li>
                    <li>😂 Joke machine</li>
                    <li>🔗 Personal links</li>
                    <li>📞 Twilio call support</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="info-card">
                <h3 style="color:#e94560;margin-top:0;">👨‍💻 Developer</h3>
                <p style="color:#e6f1ff;font-weight:700;font-size:1.1rem;">Nihal Talla</p>
                <h4 style="color:#e6f1ff;">🛠️ Tech Stack</h4>
                <ul style="color:#8b97b8;line-height:1.7;">
                    <li><b>AI:</b> Google Gemini</li>
                    <li><b>Web UI:</b> Streamlit</li>
                    <li><b>Voice:</b> Browser mic + SpeechRecognition</li>
                    <li><b>System:</b> psutil</li>
                    <li><b>Email:</b> smtplib (SMTP)</li>
                    <li><b>Calls:</b> Twilio API</li>
                    <li><b>Language:</b> Python</li>
                </ul>
                <a href="https://github.com/NihalTalla/ANU" target="_blank" style="display:inline-block;background:linear-gradient(135deg,#e94560,#c52f49);color:white;padding:10px 18px;border-radius:10px;text-decoration:none;font-weight:700;margin-top:8px;">📂 View on GitHub</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# App startup and main dispatch
# -----------------------------------------------------------------------------

def main() -> None:
    ensure_storage()
    init_state()
    sidebar_nav()
    render_header()

    tab = st.session_state.active_tab
    if tab == "Chat":
        render_chat()
    elif tab == "Voice":
        render_voice()
    elif tab == "System Monitor":
        render_system_monitor()
    elif tab == "Notes":
        render_notes()
    elif tab == "Calculator":
        render_calculator()
    elif tab == "Code Generator":
        render_code_generator()
    elif tab == "Jokes":
        render_jokes()
    elif tab == "Email":
        render_email()
    elif tab == "Weather":
        render_weather()
    elif tab == "Calls":
        render_calls()
    elif tab == "My Links":
        render_links()
    elif tab == "About":
        render_about()

    st.markdown(
        f'<div style="text-align:center;padding:20px;color:#8b97b8;font-size:0.82rem;border-top:1px solid rgba(255,255,255,0.12);margin-top:40px;">ANU · Built by Nihal Talla · Powered by Google Gemini · <a href="{REPO_URL}" target="_blank">GitHub</a></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
