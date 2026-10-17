# LiveGram Clone

Anonymous user ⇄ admin relay bot on the Basic-bot skeleton (Pyrogram/kurigram, plugin-based, Koyeb-ready).

## Behaviour

- Users message the bot; everything lands in the **admin's** DM, with no profile, username or ID shown (users get an anonymous label like `User #A1B2C3` per run).
- The admin's DM is **connected to the last user who wrote**. Anything the admin sends goes to that user. A new user message moves the connection; a restart resets it.
- Swipe-reply to a specific message in the admin DM to answer that user directly (connection unchanged).
- **No forward tags** (messages are re-sent via `copy`), and **`protect_content`** is on, so nothing can be forwarded, saved or copied from the bot chat.
- **No database, no session file** (`in_memory=True`). Only message-id links are held in a size-bounded RAM cache (`cache.py`).
- Edits (text/captions) on either side are synced; replies are threaded on both sides.
- Albums arrive as individual messages (each is relayed separately).

## Commands

| Who | Command | Does |
|---|---|---|
| anyone | `/start` | greeting (admin gets help) |
| admin | `/status` | shows currently connected anonymous user |

## Config (env)

| Var | Required | Description |
|---|---|---|
| `API_ID`, `API_HASH` | ✅ | from my.telegram.org |
| `BOT_TOKEN` | ✅ | from @BotFather |
| `ADMIN_ID` | ✅ | numeric Telegram ID of the admin (must press /start on the bot once) |
| `START_TEXT` | – | user greeting |
| `CACHE_SIZE` | – | max stored message links (default 5000) |
| `PORT` | – | health-check port (default 8080) |

## Run

```bash
pip install -r requirements.txt
export API_ID=... API_HASH=... BOT_TOKEN=... ADMIN_ID=...
python bot.py
```

Docker / Koyeb: `docker build -t livegram . && docker run --env-file .env -p 8080:8080 livegram`

## Structure

```
bot.py            # Client (in-memory session), startup
config.py         # env config
cache.py          # RAM-only connection + message-id links
webserver.py      # /health for Koyeb
plugins/start.py  # /start, /status
plugins/relay.py  # user⇄admin relay + edit sync
```

## Notes

- Telegram only lets a bot DM someone who has started it, so the admin must `/start` the bot once.
- After a restart, replies to old messages fall back to the connected user (the id links are gone by design).
