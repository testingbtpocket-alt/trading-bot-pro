import telebot
import requests
import sqlite3
import time

TOKEN = "8834762087:AAFXwue33RSsd0eIPfzUmeReNcSmVZCdiOk"
ADMIN_USERNAME = "@Kasper404_01"
ADMIN_ID = 8954805209

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# --- BAZA VA RUXSAT TIZIMI ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, has_access INTEGER DEFAULT 0)')
    conn.commit()
    conn.close()

def check_user_access(user_id):
    if user_id == ADMIN_ID: return True
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT has_access FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None and res[0] == 1

def register_user(user_id, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# --- ANALIZ MATEMATIKASI ---
def get_rsi(symbol, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=14"
        data = requests.get(url, timeout=5).json()
        prices = [float(k[4]) for k in data]
        gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
        losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        if avg_loss == 0: return 100
        return 100 - (100 / (1 + (avg_gain / avg_loss)))
    except: return 50

# --- TUGMALAR ---
def get_trading_keyboard():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    pairs = {"AUD/USD": "AUDUSDT", "EUR/USD": "EURUSDT", "GBP/USD": "GBPUSDT", 
             "USD/JPY": "USDJPY", "USD/CHF": "USDCHF", "NZD/USD": "NZDUSDT"}
    for name, symbol in pairs.items():
        markup.add(telebot.types.InlineKeyboardButton(text=name, callback_data=f"sig_{symbol}"))
    return markup

# --- START VA CALLBACK ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username or "NoName")
    
    if not check_user_access(user_id):
        text = f"📡 <b>TRADING SIGNALS BOT</b>\n--------------------------\n👋 Salom, <b>{message.from_user.first_name}</b>!\n\n🔒 <b>Kirish taqiqlangan.</b>\n📌 ID: <code>{user_id}</code>\n👤 Admin: {ADMIN_USERNAME}"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "📊 <b>Trading Terminal</b>\nJuftlikni tanlang:", reply_markup=get_trading_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("sig_"))
def callback_handler(call):
    symbol = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "🔍 Analiz...")
    
    r1, r5, r15 = get_rsi(symbol, "1m"), get_rsi(symbol, "5m"), get_rsi(symbol, "15m")
    
    if r1 < 40 and r5 < 45:
        sig, ex, col = "📈 BUY (KUCHLI)", "2-5 daqiqa", "✅"
    elif r1 > 60 and r5 > 55:
        sig, ex, col = "📉 SELL (KUCHLI)", "2-5 daqiqa", "✅"
    else:
        sig, ex, col = "⏳ KUTING", "Noaniq", "⚠️"
    
    text = (f"<b>📊 ANALIZ: {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{col} <b>SIGNAL: {sig}</b>\n"
            f"🕒 <b>VAQT: {ex}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏱ <b>M1 RSI:</b> {r1:.1f}\n"
            f"⏱ <b>M5 RSI:</b> {r5:.1f}\n"
            f"⏱ <b>M15 RSI:</b> {r15:.1f}")
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_trading_keyboard(), parse_mode="HTML")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi!")
    bot.polling(none_stop=True)
