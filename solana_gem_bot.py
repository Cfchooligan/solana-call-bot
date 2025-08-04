import logging
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# === Configuration ===
TELEGRAM_BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHANNEL_ID = "@zero2heromfers"  # Use '@channel_username' or chat ID (e.g., -100...)
OWNER_ID = 6954984074  # Your Telegram user ID

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Fetch Tokens from Birdeye ===
async def fetch_new_tokens():
    url = "https://public-api.birdeye.so/public/token/solana/new?limit=50"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                logger.warning(f"Birdeye API error: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching tokens: {e}")
        return []

# === Format Token Info for Telegram Post ===
def format_token(token):
    name = token.get("name", "Unknown")
    symbol = token.get("symbol", "N/A")
    price = token.get("priceUsd", 0)
    liquidity = token.get("liquidity", 0)
    volume = token.get("volumeH5", 0)
    buyers = token.get("buyersH5", 0)
    sellers = token.get("sellersH5", 0)
    address = token.get("address", "")
    link = f"https://birdeye.so/token/{address}?chain=solana"

    return (
        f"💎 <b>{name} (${symbol})</b>\n"
        f"💰 Price: ${price:.6f}\n"
        f"📊 Liquidity: ${liquidity:,.0f}\n"
        f"📈 5m Volume: ${volume:,.0f}\n"
        f"🟢 Buyers: {buyers} | 🔴 Sellers: {sellers}\n"
        f"🔗 <a href='{link}'>View on Birdeye</a>\n"
        f"🧾 <code>{address}</code>"
    )

# === Post Gems to Telegram ===
async def post_gems(context: ContextTypes.DEFAULT_TYPE):
    logger.info("🔍 Checking for gems...")
    tokens = await fetch_new_tokens()
    if not tokens:
        logger.info("No gems found.")
        await context.bot.send_message(chat_id=CHANNEL_ID, text="🕵️ No gems found this round.")
        return

    gems_posted = 0
    for token in tokens:
        try:
            message = format_token(token)
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            gems_posted += 1
            if gems_posted >= 3:
                break
        except Exception as e:
            logger.error(f"Error sending token: {e}")
    logger.info(f"✅ Posted {gems_posted} gems.")

# === /forcepost Command Handler ===
async def forcepost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ You're not authorized to use this command.")
        return
    await update.message.reply_text("📬 Forcing gem post now...")
    await post_gems(context)

# === Bot Runner ===
async def run_bot():
    logger.info("🚀 Bot script is executing...")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("forcepost", forcepost))

    # Scheduler setup
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(post_gems(app.bot)), 'interval', hours=8)
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await app.run_polling()

# === Entry Point ===
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")


