import logging
import sys

from pyrogram import Client, enums

from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from webserver import run_webserver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LiveGramBot(Client):
    def __init__(self):
        super().__init__(
            name="livegram_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            # No session file on disk — nothing persists between restarts.
            in_memory=True,
            parse_mode=enums.ParseMode.HTML,
            # Auto-discovers and imports every module in plugins/ on start,
            # which is what actually registers any @Client.on_message handlers.
            plugins=dict(root="plugins"),
        )

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        me = await self.get_me()
        logger.info(f"Bot started: @{me.username}")

        self._web_runner = await run_webserver()

        try:
            await self.send_message(ADMIN_ID, "✅ Bot online. No user connected yet.")
        except Exception as e:
            logger.warning(f"Couldn't DM admin (has the admin pressed /start?): {e}")

    async def stop(self, *args, **kwargs):
        if hasattr(self, "_web_runner"):
            await self._web_runner.cleanup()
        await super().stop(*args, **kwargs)
        logger.info("Bot stopped.")


if __name__ == "__main__":
    missing = [k for k, v in
               {"API_ID": API_ID, "API_HASH": API_HASH,
                "BOT_TOKEN": BOT_TOKEN, "ADMIN_ID": ADMIN_ID}.items() if not v]
    if missing:
        sys.exit(f"Missing required env vars: {', '.join(missing)}")
    LiveGramBot().run()
