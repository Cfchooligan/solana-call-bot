import os
import logging
import requests
import asyncio
from telegram import Bot
from telegram.ext import Application, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ====== HARD-CODE YOUR CREDENTIALS HERE ======
BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHANNEL_ID = "-1002866839481"  # Must be a string!
# =============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def fetch_solana_gems():
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        gems = []

        for pair in data.get("pairs", []):
            base_token = pair["baseToken"]
            price_usd = pair.get("priceUsd")
            fdv = pair.get("fdv")
            tx_count = pair.get("txCount", {}).get("h1", 0)
            price_change = float(pair.get("priceChange", {}).get("h1", 0))

            if (
                base_token["symbol"] != "SOL"
                and price_usd and float(price_usd) < 0.01
                and fdv and fdv < 500000
                and tx_count and tx_count > 100
                and price_change > 0
            ):
                gems.append({
                    "name": base_token["name"],
                    "symbol": base_token["symbol"],
                    "price": price_usd,
                    "tx_count": tx_count,
                    "price_change": price_change,
                    "fdv": fdv,
                    "url": pair["url"]
                })

        return gems
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return []

async def send_gem_alerts(context: ContextTypes.DEFAULT_TYPE):
    gems = fetch_solana_gems()
    if not gems:
        logger.info("No gems found.")
        return

    for gem in gems:
        message = (
            f"🚨 New Solana Gem Alert 🚨\n\n"
            f"Name: {gem['name']}\n"
            f"Symbol: {gem['symbol']}\n"
            f"Price: ${gem['price']}\n"
            f"FDV: ${gem['fdv']:,.0f}\n"
            f"Tx Count (1h): {gem['tx_count']}\n"
            f"Price Change (1h): {gem['price_change']}%\n\n"
            f"📊 Chart: {gem['url']}"
        )
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)

async def start(update, context):
    await update.message.reply_text("Solana Gems Bot is active!")

async def main():
    logger.info("🚀 Bot script is executing...")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Schedule the job
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: application.create_task(send_gem_alerts(ContextTypes.DEFAULT_TYPE(bot=application.bot))), CronTrigger(hour="*/6"))
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await application.run_polling()

if __name__ == "__main__":
    import asyncio

    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

    # This is the fix: use create_task on an already-running loop
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.get_event_loop().create_task(main())

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Bot stopped manually.")



