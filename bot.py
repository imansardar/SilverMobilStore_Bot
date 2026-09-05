import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    markup.add(
        types.KeyboardButton("🛒 خرید محصول"),
        types.KeyboardButton("💰 افزایش موجودی"),
        types.KeyboardButton("📦 محصولات من"),
        types.KeyboardButton("💳 موجودی حساب"),
        types.KeyboardButton("📞 پشتیبانی"),
        types.KeyboardButton("🔙 برگشت")
    )

    bot.send_message(
        message.chat.id,
        "سلام رفیق 🌹\nبه ربات سردار خوش آمدید.\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=markup
    )

bot.infinity_polling()
