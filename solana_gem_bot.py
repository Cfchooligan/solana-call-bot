import asyncio
import logging
from datetime import datetime
import httpx
from telegram import Bot
from telegram.ext import Application, ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ====== SETUP ======
TELEGRAM_BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
TELEGRAM_CHANNEL_ID = "@zero2heromfers"

DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

# ====== LOGGER ======
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ====== GET DATA ======
async def fetch_solana_gem():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DEXSCREENER_API_URL)
            response.raise_for_status()
            data = response.json()

        if not data.get("pairs"):
            logger.info("No Solana pairs found.")
            return None

        # Filter top coin by volume with some conditions (e.g. low mcap, low liquidity)
        filtered = [
            pair for pair in data["pairs"]
            if pair.get("baseToken", {}).get("name")
            and pair.get("liquidity", {}).get("usd", 0) > 1000
            and pair.get("liquidity", {}).get("usd", 0) < 30000
            and pair.get("volume", {}).get("h5", 0) > 2000
        ]

        if not filtered:
            logger.info("No Solana gem found.")
            return None

        gem = sorted(filtered, key=lambda x: x["volume"]["h5"], reverse=True)[0]
        return gem

    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return None

# ====== FORMAT MESSAGE ======
def format_gem_message(pair):
    try:
        name = pair["baseToken"]["name"]
        symbol = pair["baseToken"]["symbol"]
        price = pair["priceUsd"]
        liquidity = pair["liquidity"]["usd"]
        volume = pair["volume"]["h5"]
        txns = pair["txns"]["h5"]
        buyers = txns["buys"]
        sellers = txns["sells"]
        dex_url = pair["url"]
        contract = pair["pairAddress"]

        message = (
            f"🚀 *SOLANA GEM ALERT*\n\n"
            f"*Name:* {name}\n"
            f"*Symbol:* {symbol}\n"
            f"*Price:* ${price}\n"
            f"*Liquidity:* ${liquidity}\n"
            f"*5m Volume:* ${volume}\n"
            f"*Buyers/Sellers (5m):* {buyers}/{sellers}\n"
            f"*DexScreener:* [Link]({dex_url})\n"
            f"*Contract:* `{contract}`\n\n"
            f"#Solana #MemeCoin #Gem"
        )
        return message
    except Exception as e:
        logger.error(f"Failed to format message: {e}")
        return None

# ====== SEND TO TELEGRAM ======
async def send_to_telegram(bot: Bot):
    gem = await fetch_solana_gem()
    if not gem:
        return

    message = format_gem_message(gem)
    if not message:
        return

    try:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, parse_mode="Markdown")
        logger.info("✅ Sent Solana gem to Telegram channel.")
    except Exception as e:
        logger.error(f"❌ Failed to send message to Telegram: {e}")

# ====== MAIN BOT FUNCTION ======
async def run_bot():
    logger.info("🚀 Bot script is executing...")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Bot is starting polling...")

    # ⚡️ FORCE CALL HERE
    await send_to_telegram(bot)

    # Scheduled job
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_to_telegram(bot)), "cron", hour="9,13,18")  # Nigeria time
    scheduler.start()

    # Keep alive
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.wait_until_closed()

# ====== ENTRY POINT ======
if __name__ == "__main__":
    asyncio.run(run_bot())



