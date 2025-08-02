import requests
import logging
import datetime
from telegram import Bot
from telegram.ext import Application, CallbackContext
from telegram.ext import JobQueue
import asyncio
import os

# Telegram bot token and channel ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
CHANNEL_ID = os.getenv("CHANNEL_ID", "your_channel_id_here")  # example: -1001234567890

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Print startup marker
print("🚀 Bot script is executing...")

# Fetch Solana pairs
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

# Filter gems based on rules
def filter_gems(pairs):
    gems = []
    for pair in pairs:
        try:
            if not pair.get('baseToken') or not pair.get('priceUsd'):
                continue

            base_token = pair['baseToken']
            if not base_token.get('name') or not base_token.get('symbol'):
                continue

            price_usd = float(pair['priceUsd'])
            if not (0.000001 <= price_usd <= 0.005):
                continue

            if (pair.get('txns', {}).get('m5', {}).get('buys', 0) < 10 or 
                pair.get('txns', {}).get('h1', {}).get('buys', 0) < 10):
                continue

            if pair.get('fdv') is None or pair.get('liquidity', {}).get('usd', 0) < 1000:
                continue

            if (pair.get('fdv') > 5_000_000 or 
                pair.get('liquidity', {}).get('usd', 0) > 50_000):
                continue

            if not pair.get('pairCreatedAt'):
                continue

            pair_created_at = datetime.datetime.fromtimestamp(pair['pairCreatedAt'] / 1000)
            now = datetime.datetime.now(datetime.timezone.utc)
            age_minutes = (now - pair_created_at.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60

            if age_minutes > 180:  # 3 hours
                continue

            gems.append(pair)

        except Exception as e:
            logger.warning(f"Error processing pair: {e}")
            continue
    return gems

# Format gem message
def format_gem_message(pair):
    base = pair['baseToken']
    quote = pair['quoteToken']
    info = f"""
🚀 *New Solana Gem Spotted!*

🔹 *Token*: [{base['name']}]({pair['url']}) (${base['symbol']})
💰 *Price*: ${pair['priceUsd']}
📈 *FDV*: ${int(pair.get('fdv', 0)):,}
💦 *Liquidity*: ${int(pair.get('liquidity', {}).get('usd', 0)):,}
🕒 *Created*: <code>{datetime.datetime.fromtimestamp(pair['pairCreatedAt'] / 1000).strftime('%Y-%m-%d %H:%M:%S')}</code>
🔗 [View on Dexscreener]({pair['url']})

#Solana #MemeCoin #ZeroToHero
"""
    return info

# Main function to find and post gems
async def post_gems(context: CallbackContext):
    logger.info("Checking for Solana gems...")
    pairs = fetch_solana_pairs()
    gems = filter_gems(pairs)

    if not gems:
        logger.info("No gems found.")
        return

    for gem in gems[:3]:  # Post only top 3
        message = format_gem_message(gem)
        try:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            logger.info(f"Posted gem: {gem['baseToken']['symbol']}")
        except Exception as e:
            logger.error(f"Failed to post to Telegram: {e}")

# Schedule the job
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Post on startup
    await post_gems(CallbackContext.from_update(None, app))

    # Schedule repeating job
    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(post_gems, interval=3600, first=3600)  # every 1 hour

    try:
        print("✅ Bot is starting polling...")
        await app.run_polling()
    except Exception as e:
        print(f"❌ An error occurred while starting the bot: {e}")
        logger.error(f"Exception in run_polling: {e}")

# Start bot
if __name__ == "__main__":
    asyncio.run(main())


