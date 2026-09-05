import os
import re
import time
import json
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()

# تنظیمات از محیط
ADMIN_ID = int(os.getenv("ADMIN_ID", 8915086212))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@StoreSardaarApple")
BONUS_PERCENT = int(os.getenv("BONUS_PERCENT", 5))
BANK_CARD = os.getenv("BANK_CARD", "5022291331447233")
BANK_OWNER = os.getenv("BANK_OWNER", "ایمان سردار راد")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN در Environment Variables تنظیم نشده است.")

bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()

# باقی کد فروشگاهت رو اینجا قرار بده...
# (تمام کد اصلی‌ای که داری رو اینجا کپی کن، از خطی که تعرفه خدمات شروع میشه تا آخر)
