import requests
import time
import random
import telebot
from datetime import datetime

# === CONFIGURATION ===
TELEGRAM_TOKEN = '7743771588:AAEOv4qFXOkvUBpIXYfrzqh6Y6CVoOxh-lQ'
CHAT_ID = '-1002866839481'  # Your private channel ID
MAX_POSTS_PER_DAY = 3
POST_HOURS = [10, 15, 20]  # Nigeria time (AM, Afternoon, Evening)
TIMEZONE_OFFSET = 1  # Nigeria is UTC+1

# === INITIALIZE TELEGRAM BOT ===
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === FILTER SETTINGS ===
MIN_LIQUIDITY = 5000
MAX_MARKET_CAP = 50000
MIN_VOLUME = 1000
BLACKLIST_KEYWORDS = ['rug', 'kill', 'rekt', 'dead', 'scam', 'honeypot']


def fetch_solana_pairs():
    url = 'https://api.dexscreener.com/latest/dex/pairs/solana'
    response = requests.get(url)
    data = response.json()
    return data.get('pairs', [])


def is_valid_token(pair):
    name = (pair.get('baseToken', {}).get('name', '') + pair.get('baseToken', {}).get('symbol', '')).lower()
    if any(bad_word in name for bad_word in BLACKLIST_KEYWORDS):
        return False
    try:
        liquidity = float(pair.get('liquidity', {}).get('usd', 0))
        market_cap = float(pair.get('fdv', 0))
        volume = float(pair.get('volume', {}).get('h5', 0))
        return liquidity >= MIN_LIQUIDITY and market_cap <= MAX_MARKET_CAP and volume >= MIN_VOLUME
    except:
        return False


def format_message(pair):
    name = pair['baseToken']['name']
    symbol = pair['baseToken']['symbol']
    mcap = round(float(pair['fdv']))
    liq = round(float(pair['liquidity']['usd']))
    vol = round(float(pair['volume']['h5']))
    chart = pair.get('url', '')
    msg = f"""🚀 *New Solana Meme Coin*

🔹 *Name:* ${symbol} ({name})
💰 *Market Cap:* ${mcap:,}
📊 *5m Volume:* ${vol:,}
🧊 *Liquidity:* ${liq:,}

📈 [View Chart]({chart})
#Solana #Gems #MemeCoin #ZeroToHero
"""
    return msg


def post_calls():
    print("Fetching pairs...")
    pairs = fetch_solana_pairs()
    good_ones = [p for p in pairs if is_valid_token(p)]
    random.shuffle(good_ones)
    posted = 0
    for pair in good_ones:
        if posted >= MAX_POSTS_PER_DAY:
            break
        try:
            msg = format_message(pair)
            bot.send_message(CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=False)
            posted += 1
            time.sleep(10)  # avoid spamming
        except Exception as e:
            print("Error posting:", e)


def main_loop():
    posted_today = []
    while True:
        now = datetime.utcnow()
        hour_local = (now.hour + TIMEZONE_OFFSET) % 24
        if hour_local in POST_HOURS and hour_local not in posted_today:
            post_calls()
            posted_today.append(hour_local)
            print(f"Posted for hour {hour_local}")
        elif hour_local == 0:
            posted_today = []  # reset daily tracker
        time.sleep(60)  # check every minute


if __name__ == '__main__':
    main_loop()
