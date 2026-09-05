import telebot

TOKEN = "8641131217:AAGUdZ2I-Xhm-UxZXJvXyeWm2B_PY__cpuc"  # این یه توکن نمونه‌ست، حتماً عوضش کن!!!

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 سلام!")

print("✅ ربات در حال اجراست...")
bot.polling()
