import telebot

TOKEN = "7559040500:AAHhIuB7N7R0m2qNCPPwT0aRYR1z8kfE2Do"  # این یه توکن نمونه‌ست، حتماً عوضش کن!!!

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 سلام!")

print("✅ ربات در حال اجراست...")
bot.polling()
