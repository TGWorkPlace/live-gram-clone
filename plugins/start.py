from pyrogram import Client, filters
from pyrogram.types import Message

from cache import cache
from config import ADMIN_ID, START_TEXT

ADMIN_HELP = (
    "👑 <b>Admin panel</b>\n\n"
    "Users who write to this bot appear here as anonymous messages.\n"
    "• Anything you send goes to the <b>currently connected user</b>.\n"
    "• Swipe-reply to a specific message to answer that user directly.\n"
    "• The connection moves to whoever wrote last, and resets on bot restart.\n\n"
    "/status — show the connected user"
)


@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if message.from_user and message.from_user.id == ADMIN_ID:
        await message.reply(ADMIN_HELP)
    else:
        await message.reply(START_TEXT, protect_content=True)


@Client.on_message(filters.command("status") & filters.private & filters.user(ADMIN_ID))
async def status_handler(client: Client, message: Message):
    if cache.connected:
        await message.reply(f"🟢 Connected to <b>{cache.alias(cache.connected)}</b>")
    else:
        await message.reply("⚪ No user connected yet.")
