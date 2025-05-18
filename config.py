import os
import json

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

HASHTAG_TO_CHANNEL = json.loads(os.getenv("HASHTAG_TO_CHANNEL", "{}"))
