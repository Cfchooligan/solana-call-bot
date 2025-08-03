import logging
import asyncio
import requests
from telegram import Bot
from telegram.ext import Application, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHANNEL_ID = "-1002866839481"  # Your Telegram channel ID

# === LOGGING ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FUNCTION: Fetch Gems ===
def fetch_solana_gems():
    try:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        gems = []
        for pair in data.get("pairs", []):
            base_token = pair.get("baseToken", {})
            quote_token = pair.get("quoteToken", {})

            if (
                base_token.get("symbol") 
                and "W" not in base_token["symbol"]
                and pair.get("liquidity", {}).get("usd", 0) > 1000
                and pair.get("priceChange", {}).get("h1", 0) > 10
            ):
                gems.append({
                    "name": base_token.get("name"),
                    "symbol": base_token.get("symbol"),
                    "price": pair.get("priceUsd"),
                    "volume": pair.get("volume", {}).get("h1"),
                    "liquidity": pair.get("liquidity", {}).get("usd"),
                    "url": pair.get("url"),
                })

        return gems

    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return []

# === FUNCTION: Send to Telegram ===
async def send_to_telegram(message: str):
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

# === FUNCTION: Compose and Send Gem Alert ===
async def check_and_post_gems():
    logger.info("🔍 Checking for Solana gems...")
    gems = fetch_solana_gems()
    if not gems:
        logger.info("No gems found.")
        return

    for gem in gems[:3]:  # Limit to top 3
        msg = (
            f"🚀 <b>New Solana Gem Found</b>\n\n"
            f"<b>Name:</b> {gem['name']}\n"
            f"<b>Symbol:</b> {gem['symbol']}\n"
            f"<b>Price:</b> ${gem['price']}\n"
            f"<b>Volume (1h):</b> ${gem['volume']}\n"
            f"<b>Liquidity:</b> ${gem['liquidity']}\n"
            f"<b>Chart:</b> <a href='{gem['url']}'>Click to view</a>"
        )
        await send_to_telegram(msg)

# === FUNCTION: Manual test post ===
async def test_post():
    await send_to_telegram("🚨 This is a manual test post to confirm the bot works!")

# === FUNCTION: Main Bot Runner ===
async def main():
    logger.info("🚀 Bot script is executing...")

    app = Application.builder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(check_and_post_gems()), "interval", hours=8)
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await app.run_polling()

# === ENTRY POINT ===
if __name__ == "__main__":
    import sys
    if "test" in sys.argv:
        asyncio.run(test_post())
    else:
        asyncio.run(main())



