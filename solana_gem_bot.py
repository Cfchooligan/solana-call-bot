import logging
import requests
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

# =======================
# ✅ SET YOUR VARIABLES
# =======================
BOT_TOKEN = "7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ"  # Replace with your actual bot token
CHANNEL_ID = -1002866839481   # Your Telegram channel ID

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

# =======================
# 📜 SETUP LOGGING
# =======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# =======================
# 📥 FETCH & FORMAT GEMS
# =======================
def fetch_solana_gems():
    try:
        response = requests.get(DEXSCREENER_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        gems = []
        for pair in data.get("pairs", []):
            if not pair.get("baseToken") or not pair.get("liquidity", {}).get("usd"):
                continue

            base = pair["baseToken"]
            metrics = {
                "name": base.get("name", "N/A"),
                "symbol": base.get("symbol", "N/A"),
                "price": pair.get("priceUsd", "N/A"),
                "liquidity": pair["liquidity"].get("usd", 0),
                "volume_5m": pair["volume"].get("m5", 0),
                "buyers": pair.get("txns", {}).get("m5", {}).get("buys", 0),
                "sellers": pair.get("txns", {}).get("m5", {}).get("sells", 0),
                "url": pair.get("url", "N/A"),
                "address": base.get("address", "N/A"),
            }

            if metrics["volume_5m"] >= 1000 and metrics["buyers"] > metrics["sellers"]:
                gems.append(metrics)

        return gems
    except Exception as e:
        logger.error(f"Failed to fetch or parse data: {e}")
        return []

# =======================
# 📤 SEND TO TELEGRAM
# =======================
async def post_solana_gems(context: ContextTypes.DEFAULT_TYPE):
    gems = fetch_solana_gems()

    if not gems:
        logger.info("No gems found.")
        return

    for gem in gems[:3]:  # Limit to 3 posts
        message = (
            f"🚀 *New Solana Meme Gem!*\n\n"
            f"*Name:* {gem['name']} ({gem['symbol']})\n"
            f"*Price:* ${float(gem['price']):.6f}\n"
            f"*Liquidity:* ${float(gem['liquidity']):,.0f}\n"
            f"*5m Volume:* ${float(gem['volume_5m']):,.0f}\n"
            f"*Buyers:* {gem['buyers']} / *Sellers:* {gem['sellers']}\n"
            f"*Contract:* `{gem['address']}`\n"
            f"[View on DexScreener]({gem['url']})"
        )

        tr
