import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#SLACK_LAST_FETCH_TS = os.getenv("SLACK_LAST_FETCH_TS", "")

GMAIL_LABEL_NAME = os.getenv(
    "GMAIL_LABEL_NAME",
    "ReferralBotProcessed"
)


