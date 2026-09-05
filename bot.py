import os
import telebot
from telebot import types

TOKEN = os.getenv("8641131217:AAGUdZ2I-Xhm-UxZXJvXyeWm2B_PY__cpuc")

bot = telebot.TeleBot(TOKEN)

if __name__ == "__main__":
    print("✅ ربات در حال اجراست...")
    bot.infinity_polling()
