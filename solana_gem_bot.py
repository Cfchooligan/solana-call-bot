import logging
import asyncio
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    JobQueue,
)

# Replace with your actual bot token and channel ID
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHANNEL_ID = '@yourchannelname'  # Include '@' before your channel username

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Function to fetch Solana token pairs from dexscreener
def fetch_solana_pairs():
    url = 'https://api.dexscreener.com/latest/dex/pairs'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        solana_pairs = [
            pair for pair in data.get('pairs', [])
            if pair.get('chainId') == 'solana'
        ]
        return solana_pairs
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return []


# Function to identify potential "gems" from token pairs
def find_gems(pairs):
    gems = []
    for pair in pairs:
        try:
            price_change = float(pair.get("priceChange", {}).get("h1", 0))
            volume_usd = float(pair.get("volume", {}).get("h1", 0))
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0))

            if price_change > 10 and volume_usd > 500 and liquidity_usd > 1000:
                gems.append(pair)
        except Exception as e:
            logger.warning(f"Skipping pair due to error: {e}")
    return gems


# Function to format a message from a gem pair
def format_gem_message(pair):
    try:
        base = pair.get("baseToken", {})
        name = base.get("name", "Unknown")
        symbol = base.get("symbol", "N/A")
        address = base.get("address", "N/A")
        price = pair.get("priceUsd", "N/A")
        price_change = pair.get("priceChange", {}).get("h1", "N/A")
        volume = pair.get("volume", {}).get("h1", "N/A")
        liquidity = pair.get("liquidity", {}).get("usd", "N/A")
        url = pair.get("url", "#")

        return (
            f"🔥 *Solana Gem Spotted!*\n\n"
            f"*Name:* {name}\n"
            f"*Symbol:* {symbol}\n"
            f"*Price:* ${price}\n"
            f"*1h Change:* {price_change}%\n"
            f"*1h Volume:* ${volume}\n"
            f"*Liquidity:* ${liquidity}\n"
            f"[View on Dexscreener]({url})\n"
            f"`Token Address:` `{address}`"
        )
    except Exception as e:
        logger.error(f"Error formatting message: {e}")
        return "Error formatting token data."


# Job function to post gems to channel
async def post_gems(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Checking for Solana gems...")
    pairs = fetch_solana_pairs()
    gems = find_gems(pairs)

    if not gems:
        logger.info("No gems found.")
        return

    for gem in gems[:3]:  # Limit to top 3 gems per hour
        message = format_gem_message(gem)
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
        except Exception as e:
            logger.error(f"Failed to send message: {e}")


# Start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 I'm alive and watching the Solana chain for gems!")


# Main function to start bot and job scheduler
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))

    job_queue = app.job_queue
    job_queue.run_repeating(post_gems, interval=3600, first=10)  # every hour

    logger.info("✅ Bot is starting polling...")
    await app.run_polling()


# Run it safely depending on environment
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Cannot close a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise

