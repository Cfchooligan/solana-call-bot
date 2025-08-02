import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel_id")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def fetch_solana_pairs():
    url = 'https://api.dexscreener.com/latest/dex/pairs'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        all_pairs = data.get('pairs', [])
        solana_pairs = [pair for pair in all_pairs if pair.get('chainId') == 'solana']
        return solana_pairs
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return []

def filter_solana_gems(pairs):
    gems = []
    for pair in pairs:
        if (
            pair.get("fdv", 0) < 1_000_000 and
            pair.get("liquidity", {}).get("usd", 0) > 30_000 and
            pair.get("txns", {}).get("h1", {}).get("buys", 0) > 50 and
            pair.get("txns", {}).get("h1", {}).get("sells", 0) < 10
        ):
            gems.append(pair)
    return gems

async def post_to_channel(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for Solana gems...")
    solana_pairs = fetch_solana_pairs()
    gems = filter_solana_gems(solana_pairs)

    if gems:
        for gem in gems:
            msg = f"🔥 *New Solana Gem Alert!*\n\n" \
                  f"*Pair:* {gem.get('baseToken', {}).get('symbol')} / {gem.get('quoteToken', {}).get('symbol')}\n" \
                  f"*FDV:* ${gem.get('fdv', 0):,.0f}\n" \
                  f"*Liquidity:* ${gem.get('liquidity', {}).get('usd', 0):,.0f}\n" \
                  f"*H1 Buys:* {gem.get('txns', {}).get('h1', {}).get('buys', 0)}\n" \
                  f"*H1 Sells:* {gem.get('txns', {}).get('h1', {}).get('sells', 0)}\n" \
                  f"[View Pair]({gem.get('url')})"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
    else:
        logger.info("No gems found.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! This bot automatically posts filtered Solana gems 3 times daily.")

async def main():
    logger.info("🚀 Bot script is executing...")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Schedule the gem posting job 3 times a day
    job_queue: JobQueue = app.job_queue
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: job_queue.run_once(post_to_channel, 0), "cron", hour="7,14,22")
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Exception in run_polling: {e}")

