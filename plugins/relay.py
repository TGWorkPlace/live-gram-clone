"""
Anonymous two-way relay between users and the admin.

- Messages are re-sent with copy (no "Forwarded from" header, no profile info).
- protect_content=True blocks forwarding / saving / copying inside Telegram.
- Only message-id links are kept, in RAM (see cache.py). No database.
"""
import inspect
import logging

from pyrogram import Client, enums, filters
from pyrogram.types import Message

from cache import cache
from config import ADMIN_ID

logger = logging.getLogger(__name__)

_COPY_PARAMS = set(inspect.signature(Message.copy).parameters)


# ---------------------------------------------------------------- helpers
def _replied_id(message: Message):
    rid = getattr(message, "reply_to_message_id", None)
    if rid:
        return rid
    r = getattr(message, "reply_to_message", None)
    return r.id if r else None


def _reply_kw(reply_to):
    if not reply_to:
        return {}
    if "reply_parameters" in _COPY_PARAMS:  # newer kurigram
        from pyrogram.types import ReplyParameters

        return {"reply_parameters": ReplyParameters(message_id=reply_to)}
    return {"reply_to_message_id": reply_to}


async def _copy(message: Message, chat_id: int, reply_to=None) -> Message:
    base = {"protect_content": True} if "protect_content" in _COPY_PARAMS else {}
    if reply_to:
        try:
            return await message.copy(chat_id, **base, **_reply_kw(reply_to))
        except Exception as e:  # replied message gone → send without reply
            logger.debug("copy with reply failed (%s), retrying plain", e)
    return await message.copy(chat_id, **base)


# ------------------------------------------------------------ user → admin
@Client.on_message(
    filters.private
    & ~filters.service
    & ~filters.user(ADMIN_ID)
    & ~filters.command("start")
)
async def user_to_admin(client: Client, message: Message):
    if not message.from_user:
        return
    uid = message.from_user.id

    # newest writer becomes the admin's active connection
    if cache.connected != uid:
        cache.connected = uid
        try:
            await client.send_message(
                ADMIN_ID,
                f"🔄 Now connected to <b>{cache.alias(uid)}</b>.\n"
                "Your next messages go to this user.",
            )
        except Exception as e:
            logger.warning("Couldn't notify admin: %s", e)

    reply_to = cache.resolve_user_reply(uid, _replied_id(message))
    try:
        sent = await _copy(message, ADMIN_ID, reply_to)
    except Exception as e:
        logger.warning("user→admin failed: %s", e)
        await message.reply("⚠️ Couldn't deliver that message. Try again later.")
        return
    cache.link_user_msg(uid, message.id, sent.id)


# ------------------------------------------------------------ admin → user
@Client.on_message(
    filters.private
    & ~filters.service
    & filters.user(ADMIN_ID)
    & ~filters.command(["start", "status"])
)
async def admin_to_user(client: Client, message: Message):
    target = cache.resolve_admin_reply(_replied_id(message))
    if target:
        uid, reply_to = target
    elif cache.connected:
        uid, reply_to = cache.connected, None
    else:
        await message.reply("⚪ No user connected. Wait for someone to message the bot.")
        return

    try:
        sent = await _copy(message, uid, reply_to)
    except Exception as e:
        logger.warning("admin→user failed: %s", e)
        await message.reply(
            f"❌ Not delivered to <b>{cache.alias(uid)}</b> ({type(e).__name__})."
        )
        return
    cache.link_admin_msg(message.id, uid, sent.id)


# ------------------------------------------------------------ edit syncing
@Client.on_edited_message(filters.private & ~filters.service)
async def sync_edit(client: Client, message: Message):
    if not message.from_user:
        return
    if message.from_user.id == ADMIN_ID:
        link = cache.delivered.get(message.id)
        if not link:
            return
        chat_id, target_id = link
    else:
        target_id = cache.user_view.get((message.from_user.id, message.id))
        chat_id = ADMIN_ID
        if not target_id:
            return

    try:
        if message.text:
            await client.edit_message_text(
                chat_id, target_id, message.text.html, parse_mode=enums.ParseMode.HTML
            )
        elif message.caption:
            await client.edit_message_caption(
                chat_id, target_id, message.caption.html, parse_mode=enums.ParseMode.HTML
            )
    except Exception as e:  # MessageNotModified, deleted, media edits, ...
        logger.debug("edit sync skipped: %s", e)
