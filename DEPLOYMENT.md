# ANU - Personal AI Desktop Assistant (Web Version)
## Deployment Guide for Streamlit Cloud + Supabase

---

## 1. Supabase Setup

### 1.1 Create a Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up
2. Click **New Project**
3. Choose a project name, database password, and region (pick closest to your users)
4. Wait ~2 minutes for the project to provision

### 1.2 Enable Email Auth
1. Go to **Authentication > Providers** in the Supabase dashboard
2. Click **Email** and make sure it is **Enabled**
3. Under **Email Auth Settings**:
   - Set **Confirm email** to OFF (for instant access) or ON (for email verification)
   - If ON, users must click a confirmation link before logging in
4. Save

### 1.3 Run the SQL Setup
1. Go to **SQL Editor** in the Supabase dashboard
2. Click **New Query**
3. Copy the entire contents of `supabase_setup.sql` and paste it
4. Click **Run** (or press Ctrl+Enter)
5. Verify the tables appear under **Table Editor**: `user_profiles`, `user_config`, `notes`

### 1.4 Get Your API Credentials
1. Go to **Settings > API** in the Supabase dashboard
2. Copy these two values:
   - **Project URL** (e.g., `https://abcdef123.supabase.co`)
   - **anon public key** (under Project API keys)
3. You will need both for Streamlit secrets

---

## 2. Prepare Your Repository

### 2.1 Required Files
Make sure your repo contains:
```
ANU/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── supabase_setup.sql      # SQL for Supabase tables
├── .streamlit/
│   └── secrets.toml.example  # Example secrets (NOT the real one)
└── .gitignore
```

### 2.2 Create .gitignore
```
.streamlit/secrets.toml
__pycache__/
*.pyc
.env
anu_users.db
```

### 2.3 Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: ANU web app with Supabase auth"
git remote add origin https://github.com/yourusername/ANU.git
git push -u origin main
```

---

## 3. Deploy to Streamlit Cloud

### 3.1 Connect Your Repo
1. Go to [share.streamlit.io](https://share.streamlit.io) or [streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click **New App**
4. Select your repository, branch (`main`), and main file (`app.py`)
5. Click **Deploy**

### 3.2 Add Secrets
1. After the app is created, go to your app's **Settings** page on Streamlit Cloud
2. Scroll to **Secrets**
3. Paste the following (replace with your actual values):
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
```
4. Click **Save**

### 3.3 Redeploy
1. Go to **Manage App > Redeploy** to apply the secrets
2. Your app should now be live!

---

## 4. Using the App

### 4.1 First-Time User Flow
1. Open your Streamlit Cloud URL
2. Click **Create Account**
3. Enter Full Name, Email, and Password
4. If email confirmation is ON, check your inbox and click the link
5. Sign in with your credentials
6. Complete the 4-step onboarding wizard:
   - **Step 1:** Add your Gemini API key (required)
   - **Step 2:** Add Gmail SMTP credentials (optional)
   - **Step 3:** Add your social/personal links (optional)
   - **Step 4:** Add OpenWeatherMap API key (optional) and launch!

### 4.2 Getting API Keys
- **Gemini API Key:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (free)
- **Gmail App Password:** [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2FA)
- **OpenWeatherMap API Key:** [openweathermap.org/api](https://openweathermap.org/api) (free tier)

---

## 5. Environment Variables (Alternative to secrets.toml)

If you prefer environment variables instead of secrets.toml, set:
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_KEY="your-supabase-anon-key"
```

The app checks `st.secrets` first, then falls back to `os.getenv()`.

---

## 6. Troubleshooting

| Issue | Solution |
|-------|----------|
| `Supabase credentials not configured` | Check secrets.toml or env vars are set correctly |
| `Email already registered` | User already exists; try signing in instead |
| `Relation "user_profiles" does not exist` | Run the SQL setup script in Supabase SQL Editor |
| `RLS policy violation` | Ensure the RLS policies from supabase_setup.sql are applied |
| Gemini API errors | Verify the API key is valid and has quota remaining |
| Email sending fails | Use an App Password, not your regular Gmail password |
| Voice input not working | Install `streamlit-mic-recorder` and `SpeechRecognition` |

---

## 7. Security Notes

- **Never commit `secrets.toml`** to your repository
- Supabase RLS policies ensure users can only access their own data
- API keys are stored in the database and never exposed to the client
- Passwords are handled by Supabase Auth (bcrypt hashed)
- For production, consider enabling email confirmation to prevent spam accounts

---

## 8. Scaling Tips

- **Supabase Free Tier:** 500MB database, 50,000 monthly active users
- **Streamlit Cloud Free:** Shared resources, sleeps after inactivity
- For higher traffic, upgrade to Supabase Pro ($25/mo) and Streamlit for Teams
- Consider adding rate limiting for Gemini API calls per user
- Add a `last_login` column to track active users
