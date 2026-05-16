# ANU - Personal AI Assistant

ANU has two runtimes:

- `app.py` for the deployable Streamlit web app
- `anu_dashboard.py` for the original Windows desktop assistant

## Web app

The deployable version includes:

- Gemini chat
- notes with export
- calculator
- weather lookup
- system monitor
- code generator templates
- jokes
- SMTP email sending and AI drafting
- optional browser microphone transcription
- optional Twilio call support
- personal links loaded from secrets/environment variables

### Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud secrets

Set these secrets in your app settings:

- `GEMINI_API_KEY`
- `SMTP_EMAIL`
- `SMTP_PASSWORD`
- `SMTP_HOST`
- `SMTP_PORT`
- `WEATHER_API_KEY`
- `LINK_INSTAGRAM`
- `LINK_LINKEDIN`
- `LINK_GITHUB`
- `LINK_YOUTUBE`
- `LINK_TWITTER`
- `LINK_CUSTOM_1_LABEL`
- `LINK_CUSTOM_1_URL`
- `LINK_CUSTOM_2_LABEL`
- `LINK_CUSTOM_2_URL`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

## Desktop app

The local Windows assistant remains in `anu_dashboard.py`.
Use `requirements-desktop.txt` for that version.

## Repository layout

```text
anu/
├── app.py                  # Streamlit web app
├── anu_dashboard.py        # Windows desktop assistant
├── requirements.txt        # Web app dependencies
├── requirements-desktop.txt# Desktop assistant dependencies
├── data/                   # Local notes/contacts storage
└── logs/                   # Log files
```

## Notes

- Secrets are not hardcoded in `app.py`.
- `data/notes.json` and `data/contacts.json` are created automatically.