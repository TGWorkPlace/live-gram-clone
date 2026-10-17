"""
Configuration - reads from environment variables
"""
import os

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Telegram user ID of the person who receives and answers all messages
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

# Greeting shown to regular users on /start
START_TEXT = os.environ.get(
    "START_TEXT",
    "👋 Send me a message and the admin will reply right here.",
)

# Max number of message-id links kept in RAM (oldest are evicted first)
CACHE_SIZE = int(os.environ.get("CACHE_SIZE", 5000))

# Health-check web server port (Koyeb)
PORT = int(os.environ.get("PORT", 8080))
