import logging
import requests
import asyncio
from telegram import Bot
from telegram.ext import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Setup
TELEGRAM_BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
TELEGRAM_CHANNEL_ID = "-1002866839481"

def fetch_solana_gem():
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data["pairs"]:
            return None

        top_pair = data["pairs"][0]
        name = top_pair.get("baseToken", {}).get("name", "Unknown")
        symbol = top_pair.get("baseToken", {}).get("symbol", "N/A")
        price = top_pair.get("priceUsd", "N/A")
        liquidity = top_pair.get("liquidity", {}).get("usd", "N/A")
        volume_5m = top_pair.get("volume", {}).get("m5", "N/A")
        buyers = top_pair.get("txns", {}).get("m5", {}).get("buys", 0)
        sellers = top_pair.get("txns", {}).get("m5", {}).get("sells", 0)
        pair_url = top_pair.get("url", "")
        contract = top_pair.get("pairAddress", "N/A")

        message = f"""
🔥 <b>New Solana Gem Detected</b>

<b>Name:</b> {name}
<b>Symbol:</b> {symbol}
<b>Price:</b> ${float(price):.6f}
<b>Liquidity:</b> ${float(liquidity):,.0f}
<b>5m Volume:</b> ${float(volume_5m):,.0f}
<b>Buyers:</b> {buyers} | <b>Sellers:</b> {sellers}
<b>Contract:</b> <code>{contract}</code>
🔗 <a href="{pair_url}">DexScreener Link</a>
"""
        return message.strip()
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return None

async def send_solana_gem():
    gem_info = fetch_solana_gem()
    if gem_info:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=gem_info, parse_mode="HTML", disable_web_page_preview=False)
        logger.info("✅ Message sent to Telegram")
    else:
        logger.info("No Solana gem found.")

async def run_bot():
    logger.info("🚀 Bot script is executing...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(send_solana_gem()), "cron", hour="10,15,20")  # UTC time
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# 🧪 Force an immediate call on start
if __name__ == "__main__":
    try:
        import sys
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.create_task(send_solana_gem())   # Immediate forced post
        loop.create_task(run_bot())           # Normal polling + scheduler
        loop.run_forever()

    except Exception as e:
        logger.error(f"❌ Exception in run_polling: {e}")



