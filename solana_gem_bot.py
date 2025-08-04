import os
import asyncio
import logging
import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Your Bot Credentials ===
BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"
CHANNEL_ID = "-1002120479960"  # Your Telegram channel ID
OWNER_ID = 6954984074          # Your Telegram user ID

# === Logging Setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Scheduler Setup ===
scheduler = AsyncIOScheduler()

# === Fetch Solana Meme Coins from Birdeye ===
async def fetch_gems():
    url = "https://public-api.birdeye.so/public/token/solana/new?limit=50"
    headers = {"X-API-KEY": "public"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            data = response.json()

            if "data" not in data:
                logger.info("No gems found.")
                return []

            gems = []
            for gem in data["data"]:
                token_name = gem.get("name")
                token_symbol = gem.get("symbol")
                token_address = gem.get("address")
                price = gem.get("price", {}).get("value", "N/A")
                liquidity = gem.get("liquidity", "N/A")
                volume_5m = gem.get("volume_5m", "N/A")
                buyers = gem.get("buyers", "N/A")
                sellers = gem.get("sellers", "N/A")

                link = f"https://birdeye.so/token/{token_address}?chain=solana"

                post = (
                    f"🔥 New Solana Meme Coin Detected!\n\n"
                    f"💠 *{token_name}* (`{token_symbol}`)\n"
                    f"💵 Price: ${price}\n"
                    f"💧 Liquidity: ${liquidity}\n"
                    f"📈 5m Volume: ${volume_5m}\n"
                    f"🟢 Buyers: {buyers} | 🔴 Sellers: {sellers}\n\n"
                    f"[📊 View on Birdeye]({link})\n"
                    f"`{token_address}`"
                )

                gems.append(post)

            return gems

    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []

# === Post Gems to Telegram Channel ===
async def post_gems(context=None):
    logger.info("Posting gems...")

    gems = await fetch_gems()

    if not gems:
        logger.info("No gems to post.")
        return

    app = context.application if context else None

    for gem in gems[:3]:  # Post top 3 gems only
        await app.bot.send_message(
            chat_id=CHANNEL_ID,
            text=gem,
            parse_mode="Markdown",
            disable_web_page_preview=False,
        )

# === Force Post Command ===
async def force_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    await update.message.reply_text("📢 Posting latest gems...")
    await post_gems(context)

# === Start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Solana Gem Bot is active.")

# === Main Bot Logic ===
async def run_bot():
    logger.info("🚀 Bot script is executing...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("forcepost", force_post))

    # Schedule auto post every 8 hours
    scheduler.add_job(lambda: asyncio.create_task(post_gems(app)), "interval", hours=8)
    scheduler.start()

    logger.info("✅ Bot is starting polling...")
    await app.run_polling()

# === Entry Point (Fixed Event Loop) ===
if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_bot())
    except Exception as e:
        logger.error(f"❌ Runtime error: {e}")

