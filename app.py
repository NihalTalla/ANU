import streamlit as st
import datetime
import os
import math
import re
import psutil
import pyjokes
import smtplib
import ssl
import io
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from supabase import create_client, Client

st.set_page_config(page_title="ANU", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ─── Supabase ─────────────────────────────────────────────────────────────────
@st.cache_resource
def init_supabase():
    url = key = ""
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        pass
    url = url or os.getenv("SUPABASE_URL", "")
    key = key or os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        st.error("⚠️ Supabase not configured.")
        st.stop()
    return create_client(url, key)

supabase: Client = init_supabase()

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{font-family:'Inter',sans-serif !important;}
.stApp,.main .block-container{background-color:#0a0a15 !important;}
[data-testid="stHeader"]{background-color:transparent !important;}
[data-testid="stSidebar"]{background-color:#0d0d1a !important;border-right:1px solid #1a1a2e !important;}
input,textarea{background-color:#1a1a2e !important;color:#ccd6f6 !important;border:1px solid #2a2a4a !important;border-radius:10px !important;}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stChatInput>div{background-color:#1a1a2e !important;color:#ccd6f6 !important;border:1px solid #2a2a4a !important;}
.stSelectbox>div>div>div{background-color:#1a1a2e !important;color:#ccd6f6 !important;}
.stNumberInput>div>div>input{background-color:#1a1a2e !important;color:#ccd6f6 !important;}
.stButton>button{background:linear-gradient(135deg,#e94560,#c62a47) !important;color:white !important;border:none !important;border-radius:10px !important;font-weight:600 !important;}
[data-testid="stForm"]{background:#12122a !important;border:1px solid #1e1e3a !important;border-radius:16px !important;padding:20px !important;}
.stProgress>div>div>div{background:linear-gradient(90deg,#e94560,#533483) !important;}
p,h1,h2,h3,h4,h5,h6,label,span,div{color:#e6f1ff !important;}
.stMarkdown p,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4{color:#e6f1ff !important;}
button[kind="icon"][data-testid="stToolbarAction"]{display:none !important;}

.auth-card{background:linear-gradient(135deg,#1a1a2e,#16213e);border:1px solid #e94560;border-radius:20px;padding:40px;max-width:480px;margin:60px auto;box-shadow:0 0 60px rgba(233,69,96,0.2);}
.auth-title{font-size:2.2rem;font-weight:700;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:4px;}
.auth-sub{text-align:center;color:#8892b0;font-size:0.95rem;margin-bottom:28px;}
.step-card{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:16px;padding:28px;margin:12px 0;}
.step-num{background:#e94560;color:white;border-radius:50%;width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;margin-right:10px;}
.step-title{color:#e6f1ff;font-size:1.15rem;font-weight:600;vertical-align:middle;}
.progress-bar{background:#2a2a4a;border-radius:99px;height:6px;margin:16px 0;}
.progress-fill{background:linear-gradient(90deg,#e94560,#533483);border-radius:99px;height:6px;}
.anu-header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);border-radius:16px;padding:14px 28px;margin-bottom:12px;border:1px solid #e94560;box-shadow:0 0 30px rgba(233,69,96,0.15);}
.anu-title{font-size:1.4rem;font-weight:700;background:linear-gradient(90deg,#e94560,#0f3460,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;}
.status-dot{display:inline-block;width:10px;height:10px;background:#00ff88;border-radius:50%;margin-right:8px;animation:pulse 2s infinite;box-shadow:0 0 6px #00ff88;}
@keyframes pulse{0%{opacity:1}50%{opacity:0.4}100%{opacity:1}}
.chat-user{background:linear-gradient(135deg,#0f3460,#1a1a4e);border-radius:16px 16px 4px 16px;padding:12px 16px;margin:8px 0;border-left:3px solid #0f3460;color:#ccd6f6;}
.chat-anu{background:linear-gradient(135deg,#1a1a2e,#2a1a3e);border-radius:16px 16px 16px 4px;padding:12px 16px;margin:8px 0;border-left:3px solid #e94560;color:#e6f1ff;}
.chat-action{background:linear-gradient(135deg,#1a2e1a,#0a2e0a);border-radius:12px;padding:10px 14px;margin:6px 0;border-left:3px solid #00ff88;color:#ccd6f6;font-size:0.9rem;}
.voice-box{background:linear-gradient(135deg,#0a1628,#1a0a28);border:2px solid #533483;border-radius:16px;padding:20px;text-align:center;margin:12px 0;}
.user-badge{background:#1a1a2e;border:1px solid #e94560;border-radius:99px;padding:6px 14px;color:#e94560;font-size:0.85rem;font-weight:600;display:inline-block;}

/* Mode switcher */
.mode-bar{display:flex;gap:8px;margin-bottom:16px;}
.mode-btn{flex:1;padding:12px;text-align:center;border-radius:12px;cursor:pointer;font-weight:600;font-size:0.95rem;border:2px solid #2a2a4a;background:#1a1a2e;color:#8892b0;transition:all 0.2s;}
.mode-btn.active{border-color:#e94560;background:linear-gradient(135deg,#e94560,#c62a47);color:white;}
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
defaults = {"auth_page":"login","user":None,"cfg":{},"messages":[],"notes":[],"active_tab":"Chat","voice_text":"","custom_links":[],"onboard_step":1}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v

# ─── Supabase Helpers ─────────────────────────────────────────────────────────
def signup_user(email,password,full_name):
    try:
        res=supabase.auth.sign_up({"email":email.strip().lower(),"password":password,"options":{"data":{"full_name":full_name.strip()}}})
        if res.user: return True,"Account created! You can now sign in."
        return False,"Signup failed."
    except Exception as e:
        err=str(e)
        if "already registered" in err.lower() or "duplicate" in err.lower(): return False,"Email already registered."
        return False,err

def login_user(email,password):
    try:
        res=supabase.auth.sign_in_with_password({"email":email.strip().lower(),"password":password})
        if res.user: return {"id":res.user.id,"email":res.user.email,"full_name":res.user.user_metadata.get("full_name","")}
        return None
    except Exception: return None

def get_profile(uid):
    try:
        res=supabase.table("user_profiles").select("*").eq("user_id",uid).execute()
        return res.data[0] if res.data else None
    except Exception: return None

def get_config(uid):
    try:
        res=supabase.table("user_config").select("*").eq("user_id",uid).execute()
        return res.data[0] if res.data else {}
    except Exception: return {}

def save_config(uid,**kw):
    try:
        p={"user_id":uid};p.update(kw)
        supabase.table("user_config").upsert(p,on_conflict="user_id").execute()
    except Exception: pass

def get_notes(uid):
    try:
        res=supabase.table("notes").select("*").eq("user_id",uid).order("created_at",desc=True).execute()
        return res.data or []
    except Exception: return []

def save_note(uid,title,content,tags=None):
    try:
        supabase.table("notes").insert({"user_id":uid,"title":title,"content":content,"tags":tags or []}).execute()
        return True
    except Exception: return False

def delete_note(nid):
    try:
        supabase.table("notes").delete().eq("id",nid).execute()
        return True
    except Exception: return False

def load_user_session(user):
    st.session_state.user=user
    st.session_state.cfg=get_config(user["id"])
    profile=get_profile(user["id"])
    st.session_state.notes=get_notes(user["id"])
    if profile and profile.get("onboarding_done"):
        st.session_state.auth_page="app"
        if profile.get("custom_links"): st.session_state.custom_links=profile["custom_links"]
    else:
        st.session_state.auth_page="onboarding"

def logout_user():
    try: supabase.auth.sign_out()
    except Exception: pass
    for k in ["user","cfg","messages","notes","active_tab","voice_text","custom_links"]:
        st.session_state[k]=[] if isinstance(defaults.get(k),list) else ({} if k=="cfg" else (None if k=="user" else ""))
    st.session_state.active_tab="Chat"
    st.session_state.custom_links=[]
    st.session_state.auth_page="login"

# ─── Helpers ──────────────────────────────────────────────────────────────────
def cfg(key,fallback=""): return st.session_state.cfg.get(key) or fallback

def send_email_action(to,subject,body):
    se=cfg("smtp_email");sp=cfg("smtp_password")
    if not se or not sp: return False,"Email not configured. Add Gmail + App Password in Settings."
    try:
        msg=MIMEMultipart("alternative");msg["From"],msg["To"],msg["Subject"]=se,to,subject
        msg.attach(MIMEText(body,"plain"))
        ctx=ssl.create_default_context()
        with smtplib.SMTP(cfg("smtp_host","smtp.gmail.com"),int(cfg("smtp_port",587) or 587)) as s:
            s.ehlo();s.starttls(context=ctx);s.login(se,sp);s.sendmail(se,to,msg.as_string())
        return True,f"Email sent to {to}."
    except Exception as e: return False,f"Failed: {e}"

def search_web(query):
    try:
        r=requests.get(f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(query)}&format=json&srlimit=1",timeout=5)
        d=r.json()
        results=d.get("query",{}).get("search",[])
        if results:
            title=results[0]["title"]
            snippet=results[0]["snippet"].replace("<span class='searchmatch'>","").replace("</span>","")
            return True,f"**{title}**\n\n{snippet}"
        return False,f"No results for '{query}'."
    except Exception as e: return False,f"Search failed: {e}"

def get_weather_action(city):
    key=cfg("weather_api_key")
    if not key: return False,"Weather API key not set. Add it in Settings."
    try:
        r=requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric",timeout=5)
        d=r.json()
        if r.status_code==200:
            return True,f"**{d['name']}**\n🌡️ {d['main']['temp']:.1f}°C (feels {d['main']['feels_like']:.1f}°C)\n{d['weather'][0]['description'].title()}\n💧 {d['main']['humidity']}% | 💨 {d['wind']['speed']} m/s"
        return False,d.get("message","City not found.")
    except Exception as e: return False,f"Weather failed: {e}"

def get_sys_info():
    c=psutil.cpu_percent(0.5);m=psutil.virtual_memory();d=psutil.disk_usage('/');b=psutil.sensors_battery()
    info=f"**System**\n🖥️ CPU: {c:.1f}%\n💾 RAM: {m.percent:.1f}% ({m.used/1024**3:.1f}/{m.total/1024**3:.1f} GB)\n💿 Disk: {d.percent:.1f}%"
    if b: info+=f"\n🔋 Battery: {b.percent}%"
    return True,info

def calc_action(expr):
    try:
        c=expr.lower()
        for o,n in [("x","*"),("÷","/"),("^","**"),("plus","+"),("minus","-"),("times","*"),("divided by","/"),("sqrt","math.sqrt"),("pi",str(math.pi))]:
            c=c.replace(o,n)
        return True,f"**{expr} = {round(eval(c,{'__builtins__':{},'math':math}),6)}**"
    except Exception: return False,f"Can't calculate '{expr}'."

def get_joke_action():
    try: return True,pyjokes.get_joke()
    except: return True,"Why do programmers prefer dark mode? Light attracts bugs! 🐛"

# ─── Local Command Parser ─────────────────────────────────────────────────────
def try_local_command(text):
    t=text.lower().strip()

    if any(w in t for w in ["what time","current time","what's the time","whats the time","time is it"]):
        now=datetime.datetime.now();return True,f"It's **{now.strftime('%I:%M %p')}** on {now.strftime('%A, %B %d, %Y')}.",None

    if any(w in t for w in ["what day","what date","today's date","todays date","what is today"]):
        now=datetime.datetime.now();return True,f"Today is **{now.strftime('%A, %B %d, %Y')}**.",None

    if any(w in t for w in ["system status","system info","cpu usage","ram usage","memory usage","disk usage","battery","how's my system","hows my system","system health"]):
        ok,msg=get_sys_info();return True,msg,None

    calc_match=re.match(r'(?:calculate|calc|compute|what is|solve|eval)\s*(.+)',t)
    if calc_match:
        ok,msg=calc_action(calc_match.group(1).strip());return True,msg,None

    if re.match(r'^[\d\s\+\-\*\/\.\(\)sqrtpi]+$',t) and any(c in t for c in '+-*/'):
        ok,msg=calc_action(t);return True,msg,None

    weather_match=re.match(r'(?:weather|temperature|temp)\s*(?:in|for|at|of)?\s*(.+)',t)
    if weather_match:
        ok,msg=get_weather_action(weather_match.group(1).strip());return True,msg,None

    if any(w in t for w in ["tell me a joke","tell a joke","make me laugh","something funny","joke please","got any jokes"]):
        ok,msg=get_joke_action();return True,msg,None

    note_match=re.match(r'(?:save|write|create|add)\s*(?:a\s*)?(?:note|memo)\s*(?:about|on|titled|called)?[:\s]*(.+)',t)
    if note_match:
        content=note_match.group(1).strip()
        title=content[:40]+("..." if len(content)>40 else "")
        ok=save_note(st.session_state.user["id"],title,content)
        if ok: return True,f"Note saved: **{title}**",None
        return True,"Failed to save note.",None

    if any(w in t for w in ["show notes","my notes","view notes","list notes","read notes"]):
        notes=get_notes(st.session_state.user["id"])
        if notes:
            nl="\n".join([f"📌 **{n['title']}** — {n['created_at']}" for n in notes[:10]])
            return True,f"**Your Notes:**\n\n{nl}",None
        return True,"No notes yet.",None

    del_match=re.match(r'(?:delete|remove)\s*(?:the\s*)?(?:last\s*)?note',t)
    if del_match:
        notes=get_notes(st.session_state.user["id"])
        if notes:
            delete_note(notes[0]["id"]);return True,f"Deleted: **{notes[0]['title']}**",None
        return True,"No notes to delete.",None

    email_match=re.match(r'(?:send|compose|write)\s*(?:an?\s*)?(?:email|mail)\s*(?:to|for)\s*(.+?)(?:\s*(?:about|with|regarding|subject|with subject))?\s*(.*)',t)
    if email_match:
        to=email_match.group(1).strip();body=email_match.group(2).strip() if email_match.group(2) else "Please see this message."
        ok,msg=send_email_action(to,"Message from ANU",body);return True,msg,None

    url_match=re.search(r'(?:https?://|www\.)[^\s]+',text)
    if url_match or any(w in t for w in ["open ","go to ","visit ","navigate to "]):
        if url_match: url=url_match.group(0)
        else: url=t.replace("open","").replace("go to","").replace("visit","").replace("navigate to","").strip()
        if not url.startswith("http"): url="https://"+url
        return True,f"🔗 [{url}]({url})",url

    search_match=re.match(r'(?:search|look up|find|google)\s+(?:for\s+)?(.+)',t)
    if search_match:
        ok,msg=search_web(search_match.group(1).strip());return True,msg,None

    greetings=["hi","hello","hey","good morning","good evening","good night","howdy","sup","what's up","whats up"]
    if any(t==g or t.startswith(g+" ") for g in greetings):
        name=st.session_state.user.get("full_name","there");return True,f"Hey {name}! 👋 What can I do for you?",None

    thanks=["thanks","thank you","thx","ty"]
    if any(t==th for th in thanks): return True,"You're welcome! 😊",None

    who=["who are you","what are you","what is anu","tell me about yourself"]
    if any(t==w for w in who):
        return True,"I'm **ANU** — your Virtual Desktop Assistant. I can send emails, search the web, check weather, open links, calculate, save notes, and more. Just tell me what to do! 🤖",None

    return False,None,None

# ─── Gemini ───────────────────────────────────────────────────────────────────
def get_gemini(prompt,history):
    key=cfg("gemini_key")
    if not key: return "⚠️ Gemini API key not set. Add it in Settings."
    genai.configure(api_key=key)
    model=genai.GenerativeModel(model_name="gemini-2.0-flash-lite",system_instruction=f"You are ANU, a virtual desktop assistant for {st.session_state.user.get('full_name','the user')}. Be concise. Keep responses short.")
    try:
        hist=[{"role":"user" if m["role"]=="user" else "model","parts":[m["content"]]} for m in history[-8:]]
        chat=model.start_chat(history=hist if hist else [])
        return chat.send_message(prompt).text
    except Exception as e: return f"❌ Gemini error: {e}"

now=datetime.datetime.now()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    st.markdown('<div style="text-align:center;margin-top:40px;"><div style="font-size:4rem;">🤖</div><h1 style="font-size:3rem;font-weight:800;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;">ANU</h1><p style="color:#8892b0;font-size:1.1rem;">Virtual Desktop Assistant</p></div>',unsafe_allow_html=True)
    col=st.columns([1,1.2,1])[1]
    with col:
        st.markdown('<div class="auth-card">',unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Welcome Back</div>',unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Sign in to your ANU account</div>',unsafe_allow_html=True)
        with st.form("login_form",clear_on_submit=False):
            email=st.text_input("📧 Email",placeholder="you@example.com",key="login_email")
            password=st.text_input("🔒 Password",type="password",placeholder="Your password",key="login_pw")
            submitted=st.form_submit_button("Sign In →",use_container_width=True)
        if submitted:
            em=email.strip() if email else "";pw=password.strip() if password else ""
            if not em: st.error("Please enter your email.")
            elif not pw: st.error("Please enter your password.")
            else:
                user=login_user(em,pw)
                if user: load_user_session(user);st.rerun()
                else: st.error("❌ Invalid email or password.")
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#8892b0;font-size:0.9rem;">Don\'t have an account?</div>',unsafe_allow_html=True)
        if st.button("Create Account",use_container_width=True,key="login_to_signup"): st.session_state.auth_page="signup";st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SIGNUP
# ══════════════════════════════════════════════════════════════════════════════
def page_signup():
    st.markdown('<div style="text-align:center;margin-top:40px;"><div style="font-size:4rem;">🤖</div><h1 style="font-size:3rem;font-weight:800;background:linear-gradient(90deg,#e94560,#533483);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;">ANU</h1><p style="color:#8892b0;font-size:1.1rem;">Create your personal AI assistant</p></div>',unsafe_allow_html=True)
    col=st.columns([1,1.2,1])[1]
    with col:
        st.markdown('<div class="auth-card">',unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Create Account</div>',unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Set up your own ANU in seconds</div>',unsafe_allow_html=True)
        with st.form("signup_form",clear_on_submit=False):
            full_name=st.text_input("👤 Full Name",placeholder="Your Name",key="su_name")
            email=st.text_input("📧 Email",placeholder="you@example.com",key="su_email")
            password=st.text_input("🔒 Password",type="password",placeholder="Min 6 characters",key="su_pw")
            confirm=st.text_input("🔒 Confirm Password",type="password",placeholder="Repeat password",key="su_cpw")
            submitted=st.form_submit_button("Create My ANU →",use_container_width=True)
        if submitted:
            fn=full_name.strip() if full_name else "";em=email.strip() if email else "";pw=password.strip() if password else "";cf=confirm.strip() if confirm else ""
            if not fn: st.error("Please enter your full name.")
            elif not em: st.error("Please enter your email.")
            elif not pw: st.error("Please enter a password.")
            elif not cf: st.error("Please confirm your password.")
            elif pw!=cf: st.error("Passwords don't match.")
            elif len(pw)<6: st.error("Password must be at least 6 characters.")
            else:
                ok,msg=signup_user(em,pw,fn)
                if ok: st.success(msg);st.info("You can now sign in!")
                else: st.error(f"❌ {msg}")
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#8892b0;font-size:0.9rem;">Already have an account?</div>',unsafe_allow_html=True)
        if st.button("Sign In",use_container_width=True,key="signup_to_login"): st.session_state.auth_page="login";st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
def page_onboarding():
    user=st.session_state.user;step=st.session_state.onboard_step;total=3
    st.markdown(f'<div style="text-align:center;margin:30px 0 10px;"><div style="font-size:2.5rem;">🤖</div><h2 style="color:#e6f1ff;">Welcome, {user.get("full_name","there")}!</h2><p style="color:#8892b0;">Quick setup — 1 minute.</p></div><div class="progress-bar"><div class="progress-fill" style="width:{int((step/total)*100)}%;"></div></div><div style="text-align:right;color:#8892b0;font-size:0.85rem;margin-bottom:24px;">Step {step} of {total}</div>',unsafe_allow_html=True)
    col=st.columns([1,2,1])[1]
    with col:
        if step==1:
            st.markdown('<div class="step-card"><span class="step-num">1</span><span class="step-title">Gemini API Key (Required)</span><p style="color:#8892b0;margin-top:12px;">ANU uses Gemini AI for complex tasks. Your key is stored securely.</p></div>',unsafe_allow_html=True)
            st.markdown("**Get free key:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)")
            gemini_key=st.text_input("Paste your Gemini API key",type="password",placeholder="AIza...",key="ob_gemini")
            c1,c2=st.columns([1,1])
            with c1:
                if st.button("Skip →",use_container_width=True): st.session_state.onboard_step=2;st.rerun()
            with c2:
                if st.button("Save & Continue →",use_container_width=True):
                    if gemini_key.strip(): save_config(user["id"],gemini_key=gemini_key.strip());st.session_state.cfg["gemini_key"]=gemini_key.strip()
                    st.session_state.onboard_step=2;st.rerun()
        elif step==2:
            st.markdown('<div class="step-card"><span class="step-num">2</span><span class="step-title">Email Setup (Optional)</span><p style="color:#8892b0;margin-top:12px;">Let ANU send emails for you. Needs a Gmail <b>App Password</b>.</p></div>',unsafe_allow_html=True)
            st.markdown("**Get App Password:** [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)")
            smtp_email=st.text_input("Gmail address",placeholder="you@gmail.com",key="ob_email")
            smtp_pw=st.text_input("App Password",type="password",placeholder="xxxx xxxx xxxx xxxx",key="ob_smtp_pw")
            c1,c2=st.columns([1,1])
            with c1:
                if st.button("← Back",use_container_width=True): st.session_state.onboard_step=1;st.rerun()
            with c2:
                if st.button("Save & Continue →",use_container_width=True):
                    if smtp_email.strip() and smtp_pw.strip(): save_config(user["id"],smtp_email=smtp_email.strip(),smtp_password=smtp_pw.strip());st.session_state.cfg.update({"smtp_email":smtp_email.strip(),"smtp_password":smtp_pw.strip()})
                    st.session_state.onboard_step=3;st.rerun()
        elif step==3:
            st.markdown('<div style="text-align:center;padding:40px 20px;"><div style="font-size:4rem;margin-bottom:16px;">🎉</div><h2 style="color:#e6f1ff;">ANU is ready!</h2><p style="color:#8892b0;">Just tell ANU what to do.</p></div>',unsafe_allow_html=True)
            weather_key=st.text_input("🌤️ Weather API Key (optional)",type="password",placeholder="openweathermap.org/api",key="ob_weather")
            if st.button("🚀 Launch ANU!",use_container_width=True):
                updates={"onboarding_done":True}
                if weather_key.strip(): updates["weather_api_key"]=weather_key.strip()
                save_config(user["id"],**updates)
                supabase.table("user_profiles").update({"onboarding_done":True}).eq("user_id",user["id"]).execute()
                st.session_state.cfg["onboarding_done"]=True;st.session_state.auth_page="app";st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def page_app():
    user=st.session_state.user;full_name=user.get("full_name","User")

    with st.sidebar:
        st.markdown(f'<div style="text-align:center;padding:16px 0 8px;"><div style="font-size:2.8rem;">🤖</div><div style="font-size:1.3rem;font-weight:700;color:#e94560;">ANU</div><div class="user-badge" style="margin-top:8px;">👤 {full_name}</div><div style="margin-top:8px;"><span class="status-dot"></span><span style="color:#00ff88;font-size:0.85rem;">Online</span></div></div>',unsafe_allow_html=True)
        st.markdown("---")
        tab=st.session_state.active_tab
        if st.button("💬  Chat",key="nav_chat",use_container_width=True,type="primary" if tab=="Chat" else "secondary"): st.session_state.active_tab="Chat";st.rerun()
        if st.button("🎤  Voice",key="nav_voice",use_container_width=True,type="primary" if tab=="Voice" else "secondary"): st.session_state.active_tab="Voice";st.rerun()
        if st.button("⚙️  Settings",key="nav_settings",use_container_width=True,type="primary" if tab=="Settings" else "secondary"): st.session_state.active_tab="Settings";st.rerun()
        st.markdown("---")
        st.markdown(f'<div style="background:#1a1a2e;border-radius:10px;padding:12px;border:1px solid #2a2a4a;"><div style="color:#8892b0;font-size:0.75rem;">DATE & TIME</div><div style="color:#e6f1ff;font-size:1.1rem;font-weight:600;">{now.strftime("%I:%M %p")}</div><div style="color:#8892b0;font-size:0.85rem;">{now.strftime("%A, %B %d, %Y")}</div></div>',unsafe_allow_html=True)
        st.markdown("<br>")
        if st.button("🚪 Sign Out",use_container_width=True): logout_user();st.rerun()

    st.markdown(f'<div class="anu-header"><h1 class="anu-title">🤖 ANU</h1></div>',unsafe_allow_html=True)

    # Mode switcher bar - always visible in main content
    tab=st.session_state.active_tab
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button("💬 Chat",key="mode_chat",use_container_width=True,type="primary" if tab=="Chat" else "secondary"): st.session_state.active_tab="Chat";st.rerun()
    with c2:
        if st.button("🎤 Voice",key="mode_voice",use_container_width=True,type="primary" if tab=="Voice" else "secondary"): st.session_state.active_tab="Voice";st.rerun()
    with c3:
        if st.button("⚙️ Settings",key="mode_settings",use_container_width=True,type="primary" if tab=="Settings" else "secondary"): st.session_state.active_tab="Settings";st.rerun()

    tab=st.session_state.active_tab

    if tab=="Chat":
        if not st.session_state.messages:
            st.markdown(f'<div class="chat-anu"><b>ANU 🤖</b><br>Hey {full_name}! What can I do for you?</div>',unsafe_allow_html=True)

        for m in st.session_state.messages:
            if m["role"]=="user": st.markdown(f'<div class="chat-user"><b>{full_name} 👤</b><br>{m["content"]}</div>',unsafe_allow_html=True)
            elif m["role"]=="assistant": st.markdown(f'<div class="chat-anu"><b>ANU 🤖</b><br>{m["content"]}</div>',unsafe_allow_html=True)
            elif m["role"]=="action": st.markdown(f'<div class="chat-action">{m["content"]}</div>',unsafe_allow_html=True)

        user_input=st.chat_input("Tell ANU what to do...")
        if user_input:
            st.session_state.messages.append({"role":"user","content":user_input})
            handled,response,action_url=try_local_command(user_input)
            if handled:
                st.session_state.messages.append({"role":"assistant","content":response})
                if action_url: st.session_state.messages.append({"role":"action","content":f"🔗 [Open]({action_url})"})
            else:
                with st.spinner("Thinking..."): response=get_gemini(user_input,st.session_state.messages[:-1])
                st.session_state.messages.append({"role":"assistant","content":response})
            st.rerun()

        if st.session_state.messages and st.button("🗑️ Clear"): st.session_state.messages=[];st.rerun()

    elif tab=="Voice":
        st.markdown("### 🎤 Voice Command")
        col1,col2=st.columns([1,1])
        with col1:
            try:
                from streamlit_mic_recorder import mic_recorder
                st.markdown('<div class="voice-box"><b style="color:#ccd6f6;">🎤 Browser Microphone</b><br><span style="color:#8892b0;font-size:0.9rem;">Click record → speak → stop</span></div>',unsafe_allow_html=True)
                audio=mic_recorder(start_prompt="🎤 Start",stop_prompt="⏹ Stop",just_once=True,use_container_width=True,key="mic")
                if audio and audio.get("bytes"):
                    with st.spinner("Transcribing..."):
                        try:
                            import speech_recognition as sr
                            rec=sr.Recognizer();af=io.BytesIO(audio["bytes"])
                            with sr.AudioFile(af) as src: ad=rec.record(src)
                            text=rec.recognize_google(ad)
                            st.success(f"🎙️ **{text}**");st.session_state.voice_text=text
                        except sr.UnknownValueError: st.warning("Couldn't understand. Try again.")
                        except Exception as e: st.error(f"Error: {e}")
            except ImportError: st.warning("Install `streamlit-mic-recorder` for voice.")
            if st.session_state.voice_text:
                if st.button("📨 Execute",use_container_width=True):
                    text=st.session_state.voice_text;st.session_state.messages.append({"role":"user","content":f"🎤 {text}"})
                    handled,response,action_url=try_local_command(text)
                    if handled:
                        st.session_state.messages.append({"role":"assistant","content":response})
                        if action_url: st.session_state.messages.append({"role":"action","content":f"🔗 [Open]({action_url})"})
                    else:
                        with st.spinner("Thinking..."): response=get_gemini(text,st.session_state.messages[:-1])
                        st.session_state.messages.append({"role":"assistant","content":response})
                    st.session_state.voice_text="";st.rerun()
        with col2:
            st.markdown("#### 💬 Recent")
            recent=[m for m in st.session_state.messages[-6:] if m["role"] in ("assistant","action")]
            if recent:
                for m in recent:
                    if m["role"]=="assistant": st.markdown(f'<div class="chat-anu"><b>ANU 🤖</b><br>{m["content"]}</div>',unsafe_allow_html=True)
                    else: st.markdown(f'<div class="chat-action">{m["content"]}</div>',unsafe_allow_html=True)
            else: st.info("Actions will appear here.")

    elif tab=="Settings":
        st.markdown("### ⚙️ Settings")
        with st.expander("🤖 Gemini AI",expanded=True):
            nk=st.text_input("Gemini API Key",value=cfg("gemini_key"),type="password",key="set_gk")
            if st.button("Save",key="save_gk"): save_config(user["id"],gemini_key=nk);st.session_state.cfg["gemini_key"]=nk;st.success("✅ Saved!")
        with st.expander("📧 Email / SMTP"):
            se2=st.text_input("Gmail address",value=cfg("smtp_email"),key="set_email")
            sp2=st.text_input("App Password",value=cfg("smtp_password"),type="password",key="set_smtppw")
            sh2=st.text_input("SMTP Host",value=cfg("smtp_host","smtp.gmail.com"),key="set_smtphost")
            spo=st.number_input("SMTP Port",value=int(cfg("smtp_port",587) or 587),step=1,key="set_smtpport")
            if st.button("Save Email",key="save_email"): save_config(user["id"],smtp_email=se2,smtp_password=sp2,smtp_host=sh2,smtp_port=int(spo));st.session_state.cfg.update({"smtp_email":se2,"smtp_password":sp2,"smtp_host":sh2,"smtp_port":spo});st.success("✅ Saved!")
        with st.expander("🌤️ Weather API"):
            wk=st.text_input("OpenWeatherMap API Key",value=cfg("weather_api_key"),type="password",key="set_weather")
            if st.button("Save",key="save_weather"): save_config(user["id"],weather_api_key=wk);st.session_state.cfg["weather_api_key"]=wk;st.success("✅ Saved!")
        with st.expander("📝 My Notes"):
            st.session_state.notes=get_notes(user["id"])
            if not st.session_state.notes: st.info("No notes yet. Tell ANU 'save a note about...' in chat!")
            else:
                for note in st.session_state.notes:
                    with st.expander(f"📌 {note['title']} — {note['created_at']}"):
                        st.write(note["content"])
                        if st.button(f"🗑️ Delete",key=f"del_{note['id']}"): delete_note(note["id"]);st.session_state.notes=get_notes(user["id"]);st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════
page=st.session_state.auth_page
if page=="login": page_login()
elif page=="signup": page_signup()
elif page=="onboarding": page_onboarding()
elif page=="app": page_app()
