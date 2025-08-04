import asyncio
import logging
import httpx
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === SETTINGS ===
BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHANNEL_ID = "@zero2heromfers"
BIRDEYE_URL = "https://public-api.birdeye.so/public/token/solana/new?limit=50"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === GET GEMS ===
async def get_gems():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BIRDEYE_URL)
            data = response.json().get("data", [])
            if not data:
                logger.info("No gems found.")
                return []
            gems = random.sample(data, min(3, len(data)))
            return gems
    except Exception as e:
        logger.error(f"Failed to fetch Birdeye data: {e}")
        return []

# === FORMAT GEM MESSAGE ===
def format_gem(gem):
    name = gem.get("name")
    symbol = gem.get("symbol")
    price = gem.get("priceUsd")
    liquidity = gem.get("liquidity", {}).get("usd", 0)
    volume = gem.get("volume", {}).get("h5", 0)
    buys = gem.get("txns", {}).get("h5", {}).get("buys", 0)
    sells = gem.get("txns", {}).get("h5", {}).get("sells", 0)
    address = gem.get("address")
    birdeye_link = f"https://birdeye.so/token/{address}?chain=solana"

    return (
        f"💎 *{name}* ({symbol})\n"
        f"💰 Price: ${price:.4f}\n"
        f"💧 Liquidity: ${liquidity:,.0f}\n"
        f"📈 5m Volume: ${volume:,.0f}\n"
        f"🟢 Buyers: {buys} | 🔴 Sellers: {sells}\n"
        f"🔗 [Birdeye Chart]({birdeye_link})\n"
        f"🧾 `{address}`"
    )

# === POST TO TELEGRAM ===
async def post_gems(application):
    gems = await get_gems()
    if not gems:
        logger.info("No gems to post.")
        return
    for gem in gems:
        msg = format_gem(gem)
        await application.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")

# === /forcepost COMMAND ===
async def forcepost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Posting gems now...")
    await post_gems(context.application)

# === MAIN LOGIC ===
async def main():
    logger.info("🚀 Bot script is executing...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(post_gems(application)), "cron", hour="10,14,20")
    scheduler.start()

    # Handlers
    application.add_handler(CommandHandler("forcepost", forcepost))

    logger.info("✅ Bot is starting polling...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

# === ENTRY POINT ===
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "already running" in str(e):
            logger.warning("Event loop already running. Using create_task fallback.")
            asyncio.create_task(main())
        else:
            raise

