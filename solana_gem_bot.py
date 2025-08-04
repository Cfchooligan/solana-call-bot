import logging
import asyncio
import random
import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram bot token and chat/channel/user ID
TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHAT_ID = "-1002115985162"  # Your Telegram channel ID
OWNER_ID = 6954984074       # Your Telegram user ID

# DexScreener API for Solana
DEX_API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Format token post
def format_gem(gem):
    name = gem.get("baseToken", {}).get("name", "Unknown")
    symbol = gem.get("baseToken", {}).get("symbol", "N/A")
    price = float(gem.get("priceUsd", 0))
    liquidity = float(gem.get("liquidity", {}).get("usd", 0))
    volume = float(gem.get("volume", {}).get("h5", 0))
    buyers = gem.get("txns", {}).get("h5", {}).get("buys", 0)
    sellers = gem.get("txns", {}).get("h5", {}).get("sells", 0)
    address = gem.get("pairAddress", "")
    chart_url = gem.get("url", f"https://dexscreener.com/solana/{address}")

    return (
        f"💎 *{name}* ({symbol})\n"
        f"💰 Price: ${price:.4f}\n"
        f"💧 Liquidity: ${liquidity:,.0f}\n"
        f"📈 5m Volume: ${volume:,.0f}\n"
        f"🟢 Buyers: {buyers} | 🔴 Sellers: {sellers}\n"
        f"🔗 [Dexscreener Chart]({chart_url})\n"
        f"🧾 `{address}`"
    )

# Fetch gems from DexScreener
async def get_gems():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DEX_API_URL)
            data = response.json().get("pairs", [])
            if not data:
                logger.info("No gems found.")
                return []
            gems = random.sample(data, min(3, len(data)))
            return gems
    except Exception as e:
        logger.error(f"Failed to fetch gems: {e}")
        return []

# Post gems to Telegram
async def post_gems(application):
    gems = await get_gems()
    if not gems:
        logger.info("No gems to post.")
        return

    for gem in gems:
        message = format_gem(gem)
        await application.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

# /forcepost command
async def force_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) == str(CHAT_ID) or update.effective_user.id == OWNER_ID:
        await post_gems(context.application)
        await update.message.reply_text("✅ Gems posted.")
    else:
        await update.message.reply_text("⛔ You are not allowed to use this command.")

# Start everything
async def run_bot():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("forcepost", force_post))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(post_gems(application)), "cron", hour="9,15,21")
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await application.run_polling()

if __name__ == "__main__":
    logger.info("🚀 Bot script is executing...")
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    loop.run_forever()




