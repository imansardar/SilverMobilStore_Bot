# ============================================================
# 📦 ایمپورت‌ها
# ============================================================
import telebot
from telebot import types
import json
import os
import time
import sqlite3
import re

# ============================================================
# ⚙️ تنظیمات اولیه
# ============================================================
ADMIN_ID = 8915086212
CHANNEL_ID = "@StoreSardaarApple"
BONUS_PERCENT = 5
BANK_CARD = "5022291331447233"
BANK_OWNER = "ایمان سردار راد"

pending_payments = {}
payment_steps = {}
warranty_step = {}
unlock_step = {}
edit_data = {}

BOT_TOKEN = "8904951204:AAGsj8KhgcqbSKL7jkDVqa_70Oi8xlmFY5Y"
bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()

# ============================================================
# 💾 دیتابیس SQLite
# ============================================================
DB_PATH = "sardar_app_store.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apple_ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apple_id TEXT UNIQUE,
            password TEXT,
            birth_date TEXT,
            school TEXT,
            job TEXT,
            parentsmeet TEXT,
            security_q1 TEXT,
            security_a1 TEXT,
            security_q2 TEXT,
            security_a2 TEXT,
            security_q3 TEXT,
            security_a3 TEXT,
            used INTEGER DEFAULT 0,
            user_id INTEGER DEFAULT NULL,
            date_used TEXT DEFAULT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            used INTEGER DEFAULT 0,
            user_id INTEGER DEFAULT NULL,
            date_used TEXT DEFAULT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            join_date TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            email TEXT,
            birth_date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            order_id INTEGER,
            product_type TEXT,
            product_detail TEXT,
            password TEXT,
            purchase_date TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS failed_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_type TEXT,
            price INTEGER,
            reason TEXT,
            date TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')
    
    cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", ("card_number", BANK_CARD))
    cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", ("card_owner", BANK_OWNER))
    cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", ("bonus_percent", str(BONUS_PERCENT)))
    cursor.execute("INSERT OR IGNORE INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", ("last_order_id", "1000"))
    
    conn.commit()
    return conn

# ============================================================
# 📊 توابع دریافت و مدیریت تنظیمات
# ============================================================
def get_setting(key):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = ?", (value, key))
    conn.commit()
    conn.close()

# ============================================================
# 📦 توابع مدیریت سفارش‌ها
# ============================================================
def get_next_order_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM bot_settings WHERE setting_key = 'last_order_id'")
    result = cursor.fetchone()
    if result:
        current_id = int(result[0])
        new_id = current_id + 1
        cursor.execute("UPDATE bot_settings SET setting_value = ? WHERE setting_key = 'last_order_id'", (str(new_id),))
        conn.commit()
        conn.close()
        return new_id
    else:
        cursor.execute("INSERT INTO bot_settings (setting_key, setting_value) VALUES (?, ?)", ("last_order_id", "1001"))
        conn.commit()
        conn.close()
        return 1001

def save_order(order):
    if os.path.exists("orders.json"):
        try:
            with open("orders.json", "r", encoding="utf-8") as f:
                orders = json.load(f)
        except:
            orders = []
    else:
        orders = []
    if "date" not in order:
        order["date"] = time.strftime("%Y-%m-%d %H:%M:%S")
    orders.append(order)
    with open("orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def update_order_status(order_id, new_status):
    if os.path.exists("orders.json"):
        try:
            with open("orders.json", "r", encoding="utf-8") as f:
                orders = json.load(f)
        except:
            orders = []
        for order in orders:
            if order.get("order_id") == order_id:
                order["status"] = new_status
                break
        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)

# ============================================================
# 👤 توابع مدیریت کاربران
# ============================================================
def get_user_balance(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        add_new_user(user_id)
        return 0

def add_new_user(user_id, first_name="", last_name="", phone="", email="", birth_date=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR IGNORE INTO users 
        (user_id, balance, join_date, first_name, last_name, phone, email, birth_date) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, 0, time.strftime("%Y-%m-%d %H:%M:%S"), first_name, last_name, phone, email, birth_date)
    )
    conn.commit()
    conn.close()

def update_user_full_info(user_id, first_name=None, last_name=None, phone=None, email=None, birth_date=None):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        add_new_user(user_id, first_name or "", last_name or "", phone or "", email or "", birth_date or "")
        conn.close()
        return
    
    if first_name is not None:
        cursor.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
    if last_name is not None:
        cursor.execute("UPDATE users SET last_name = ? WHERE user_id = ?", (last_name, user_id))
    if phone is not None:
        cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
    if email is not None:
        cursor.execute("UPDATE users SET email = ? WHERE user_id = ?", (email, user_id))
    if birth_date is not None:
        cursor.execute("UPDATE users SET birth_date = ? WHERE user_id = ?", (birth_date, user_id))
    
    conn.commit()
    conn.close()

def update_user_balance(user_id, new_balance):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()

def get_user_info(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance, join_date, first_name, last_name, phone, email, birth_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "user_id": result[0],
            "balance": result[1],
            "join_date": result[2],
            "first_name": result[3] or "نامشخص",
            "last_name": result[4] or "نامشخص",
            "phone": result[5] or "نامشخص",
            "email": result[6] or "نامشخص",
            "birth_date": result[7] or "نامشخص"
        }
    return None

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance, join_date, first_name, last_name, phone, email, birth_date FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# ============================================================
# 📦 توابع ذخیره‌سازی خریدهای کاربران
# ============================================================
def save_user_purchase(user_id, order_id, product_type, product_detail, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_purchases 
        (user_id, order_id, product_type, product_detail, password, purchase_date, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, order_id, product_type, product_detail, password, time.strftime("%Y-%m-%d %H:%M:%S"), "completed")
    )
    conn.commit()
    conn.close()

def save_pending_purchase(user_id, order_id, product_type, product_detail, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_purchases 
        (user_id, order_id, product_type, product_detail, password, purchase_date, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, order_id, product_type, product_detail, password, time.strftime("%Y-%m-%d %H:%M:%S"), "pending")
    )
    conn.commit()
    conn.close()

def update_purchase_status(order_id, new_status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_purchases SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

def get_user_purchases(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT order_id, product_type, product_detail, password, purchase_date, status FROM user_purchases WHERE user_id = ? ORDER BY purchase_date DESC",
        (user_id,)
    )
    result = cursor.fetchall()
    conn.close()
    return result

def save_failed_purchase(user_id, product_type, price, reason="لغو توسط کاربر"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO failed_purchases (user_id, product_type, price, reason, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, product_type, price, reason, time.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_user_purchase_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_purchases WHERE user_id = ? AND status = 'completed'", (user_id,))
    success_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM failed_purchases WHERE user_id = ?", (user_id,))
    failed_count = cursor.fetchone()[0]
    conn.close()
    return success_count, failed_count

# ============================================================
# 📊 توابع آمار
# ============================================================
def get_inventory_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM apple_ids WHERE used = 0")
    apple_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM emails WHERE used = 0")
    email_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return apple_count, email_count, user_count

def check_inventory_and_notify():
    try:
        apple_count, email_count, _ = get_inventory_stats()
        if apple_count < 5:
            bot.send_message(ADMIN_ID, f"⚠️ هشدار: تعداد اپل‌آیدی‌های موجود کمتر از ۵ است (تعداد: {apple_count})")
        if email_count < 5:
            bot.send_message(ADMIN_ID, f"⚠️ هشدار: تعداد ایمیل‌های موجود کمتر از ۵ است (تعداد: {email_count})")
    except Exception as e:
        print(f"⚠️ ارور در ارسال نوتیفیکیشن به ادمین: {e}")

# ============================================================
# 💾 توابع مدیریت اپل‌آیدی و ایمیل
# ============================================================
def get_unused_apple_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            id, apple_id, password, birth_date, school, job, parentsmeet,
            security_q1, security_a1, security_q2, security_a2, security_q3, security_a3
        FROM apple_ids WHERE used = 0 LIMIT 1
    ''')
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "id": result[0],
            "apple_id": result[1],
            "password": result[2],
            "birth_date": result[3] or "ندارد",
            "school": result[4] or "ندارد",
            "job": result[5] or "ندارد",
            "parentsmeet": result[6] or "ندارد",
            "security_q1": result[7] or "ندارد",
            "security_a1": result[8] or "ندارد",
            "security_q2": result[9] or "ندارد",
            "security_a2": result[10] or "ندارد",
            "security_q3": result[11] or "ندارد",
            "security_a3": result[12] or "ندارد"
        }
    return None

def get_unused_email():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password FROM emails WHERE used = 0 LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "email": result[1], "password": result[2]}
    return None

def mark_apple_id_used(item_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE apple_ids SET used = 1, user_id = ?, date_used = ? WHERE id = ?",
        (user_id, time.strftime("%Y-%m-%d %H:%M:%S"), item_id)
    )
    conn.commit()
    conn.close()
    check_inventory_and_notify()

def mark_email_used(item_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE emails SET used = 1, user_id = ?, date_used = ? WHERE id = ?",
        (user_id, time.strftime("%Y-%m-%d %H:%M:%S"), item_id)
    )
    conn.commit()
    conn.close()
    check_inventory_and_notify()

def add_apple_id(apple_id, password, birth_date="", school="", job="", parentsmeet="", 
                security_q1="", security_a1="", security_q2="", security_a2="", 
                security_q3="", security_a3=""):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO apple_ids 
            (apple_id, password, birth_date, school, job, parentsmeet, 
            security_q1, security_a1, security_q2, security_a2, security_q3, security_a3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (apple_id, password, birth_date, school, job, parentsmeet, 
            security_q1, security_a1, security_q2, security_a2, security_q3, security_a3))
        conn.commit()
        conn.close()
        check_inventory_and_notify()
        return True
    except:
        conn.close()
        return False

def get_all_apple_ids():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, apple_id, password, birth_date, school, job, parentsmeet, used, user_id FROM apple_ids")
    result = cursor.fetchall()
    conn.close()
    return result

def get_all_emails():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password, used, user_id FROM emails")
    result = cursor.fetchall()
    conn.close()
    return result

def add_email(email, password):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO emails (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        check_inventory_and_notify()
        return True
    except:
        conn.close()
        return False

# ============================================================
# 🔒 توابع بررسی عضویت در کانال
# ============================================================
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def join_channel_button():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔗 عضویت در کانال", url="https://t.me/StoreSardaarApple"))
    markup.add(types.InlineKeyboardButton("✅ عضویت دارم", callback_data="check_membership"))
    return markup

# ============================================================
# 🏠 منوی اصلی
# ============================================================
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("تعرفه خدمات 💎")
    btn2 = types.KeyboardButton("Apple ID ساخت 🍏")
    btn3 = types.KeyboardButton("Apple ID آماده 📦")
    btn4 = types.KeyboardButton("ایمیل آماده 📧")
    btn5 = types.KeyboardButton("ساخت ایمیل 📧")
    btn6 = types.KeyboardButton("گارانتی 🛡️")
    btn7 = types.KeyboardButton("پشتیبانی 👨‍💻")
    btn8 = types.KeyboardButton("افزایش موجودی 💰")
    btn9 = types.KeyboardButton("خریدهای من 🛒")
    btn10 = types.KeyboardButton("آنلاک ایل آیدی 🔄")
    btn11 = types.KeyboardButton("پنل ادمین 🌻") if user_id == ADMIN_ID else None
    
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.row(btn4, btn5)
    markup.row(btn6, btn7)
    markup.row(btn8)
    markup.row(btn9, btn10)
    if btn11:
        markup.row(btn11)
    return markup

# ============================================================
# 📞 check_membership
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = call.message.chat.id
    if is_member(user_id):
        bot.answer_callback_query(call.id, "✅ شما عضو کانال هستید.")
        bot.send_message(user_id, "✅ عضویت شما تأیید شد. به منوی اصلی خوش آمدید!", reply_markup=main_menu(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز عضو کانال نشده‌اید.")
        bot.send_message(user_id, "❌ لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())

# ============================================================
# 🚀 شروع
# ============================================================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    add_new_user(user_id, first_name=message.from_user.first_name, last_name=message.from_user.last_name or "")
    if is_member(user_id):
        balance = get_user_balance(user_id)
        bot.send_message(
            user_id,
            f"👋 سلام {message.from_user.first_name} عزیز!\nبه ربات فروشگاه SARDAR VIP خوش آمدید.\n💰 موجودی شما: {balance:,} تومان",
            reply_markup=main_menu(user_id)
        )
    else:
        bot.send_message(
            user_id,
            "🔒 لطفاً ابتدا در کانال عضو شوید تا بتوانید از خدمات استفاده کنید.",
            reply_markup=join_channel_button()
        )

# ============================================================
# 💎 تعرفه خدمات
# ============================================================
@bot.message_handler(func=lambda message: message.text == "تعرفه خدمات 💎")
def pricing(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    
    text = (
        "╔══════════════════════════════╗\n"
        "          💎 تعرفه خدمات          \n"
        "          SARDAR VIP              \n"
        "╚══════════════════════════════╝\n\n"
        "🍏 **ساخت Apple ID**\n"
        "   ──────────────\n"
        "   💰 ۷۱۰,۰۰۰ تومان\n\n"
        "📦 **Apple ID آماده**\n"
        "   ──────────────\n"
        "   🗓️ گارانتی ۳۱ روزه  → ۴۱۰,۰۰۰ تومان\n"
        "   ♾️ گارانتی دائمی    → ۴۵۰,۰۰۰ تومان\n"
        "   ❌ بدون iCloud      → ۳۵۰,۰۰۰ تومان\n\n"
        "📧 **ایمیل**\n"
        "   ──────────────\n"
        "   📧 ایمیل آماده        → ۲۴۵,۰۰۰ تومان\n"
        "   📧 ساخت ایمیل سفارشی  → ۲۵۰,۰۰۰ تومان\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💳 **پرداخت آسان با کارت به کارت**\n"
        "📞 **پشتیبانی ۲۴ ساعته**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💙 **موفق و پیروز باشید**"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)

# ============================================================
# 📦 Apple ID آماده
# ============================================================
@bot.message_handler(func=lambda message: message.text == "Apple ID آماده 📦")
def apple_id_ready(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("☁️🗓️ گارانتی 31 روزه iCloud"),
        types.KeyboardButton("☁️♾️ گارانتی دائمی iCloud"),
        types.KeyboardButton("❌ بدون iCloud"),
        types.KeyboardButton("🔙 بازگشت")
    )
    bot.send_message(user_id, "📦 Apple ID آماده\n\n☁️🗓️ گارانتی 31 روزه - 410,000 تومان\n☁️♾️ گارانتی دائمی - 450,000 تومان\n❌ بدون iCloud - 350,000 تومان", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "☁️🗓️ گارانتی 31 روزه iCloud")
def apple31(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🛒 خرید | 410.000 تومان"), types.KeyboardButton("🔙 بازگشت"))
    bot.send_message(user_id, "☁️ Apple ID 31 روزه\n💰 قیمت: 410,000 تومان\n✅ دارای iCloud\n✅ گارانتی 31 روزه", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "☁️♾️ گارانتی دائمی iCloud")
def apple_infinite(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🛒 خرید | 450.000 تومان"), types.KeyboardButton("🔙 بازگشت"))
    bot.send_message(user_id, "☁️ Apple ID دائمی\n💰 قیمت: 450,000 تومان\n✅ دارای iCloud\n✅ گارانتی دائمی", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "❌ بدون iCloud")
def apple_noicloud(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🛒 خرید | 350.000 تومان"), types.KeyboardButton("🔙 بازگشت"))
    bot.send_message(user_id, "❌ Apple ID بدون iCloud\n💰 قیمت: 350,000 تومان", reply_markup=markup)

# ============================================================
# 🛒 خرید محصولات آماده (دکمه‌های عمومی)
# ============================================================
@bot.message_handler(func=lambda message: message.text.startswith("🛒 خرید |"))
def buy_product(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    text = message.text
    if "410.000" in text:
        product_name = "Apple ID 31 روزه"
        price = 410000
    elif "450.000" in text:
        product_name = "Apple ID دائمی"
        price = 450000
    elif "350.000" in text:
        product_name = "Apple ID بدون iCloud"
        price = 350000
    else:
        bot.send_message(user_id, "❌ محصول نامعتبر!")
        return
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["product_name"] = product_name
    pending_payments[user_id]["price"] = price
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"card_to_card_{user_id}")
    )
    bot.send_message(
        user_id,
        f"📦 محصول: **{product_name}**\n💰 مبلغ: **{price:,}** تومان\n\nلطفاً روش پرداخت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 🍏 ساخت Apple ID
# ============================================================
@bot.message_handler(func=lambda message: message.text == "Apple ID ساخت 🍏")
def apple_id_create(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📧 با ایمیل شما", callback_data=f"apple_email_self_{user_id}"),
        types.InlineKeyboardButton("✍️ ساخت ایمیل با ما", callback_data=f"apple_email_our_{user_id}")
    )
    bot.send_message(
        user_id,
        "🍏 **ساخت Apple ID**\n\n"
        "💰 قیمت: **۷۱۰,۰۰۰** تومان\n\n"
        "📧 لطفاً گزینه مورد نظر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 📧 دریافت ایمیل از کاربر (برای ساخت Apple ID)
# ============================================================
def get_apple_email(message):
    user_id = message.chat.id
    email = (message.text or "").strip()

    if email == "🔙 بازگشت":
        bot.send_message(user_id, "✅ عملیات لغو شد.", reply_markup=main_menu(user_id))
        return

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        retry = bot.send_message(user_id, "❌ ایمیل واردشده معتبر نیست. لطفاً ایمیل معتبر وارد کنید:")
        bot.register_next_step_handler(retry, get_apple_email)
        return

    pending_payments.setdefault(user_id, {})
    pending_payments[user_id]["email"] = email
    pending_payments[user_id]["product_name"] = "ساخت Apple ID"
    pending_payments[user_id]["price"] = 710000

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"card_to_card_{user_id}")
    )
    bot.send_message(user_id, "✅ ایمیل دریافت شد. لطفاً روش پرداخت را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("apple_email_self_"))
def apple_email_self(call):
    user_id = int(call.data.split("_")[3])
    if user_id != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ این بخش برای شما نیست.")
        return
    
    bot.answer_callback_query(call.id, "✅ با ایمیل خودم")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["product_name"] = "ساخت Apple ID"
    pending_payments[user_id]["price"] = 710000
    pending_payments[user_id]["email_option"] = "self"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    msg = bot.send_message(
        user_id,
        "📧 لطفاً **ایمیل** خود را وارد کنید:\n(این ایمیل برای ساخت اپل آیدی استفاده می‌شود)",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, get_apple_email)

@bot.callback_query_handler(func=lambda call: call.data.startswith("apple_email_our_"))
def apple_email_our(call):
    user_id = int(call.data.split("_")[3])
    if user_id != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ این بخش برای شما نیست.")
        return
    
    bot.answer_callback_query(call.id, "✍️ ساخت ایمیل با ما")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["product_name"] = "ساخت Apple ID"
    pending_payments[user_id]["price"] = 710000
    pending_payments[user_id]["email_option"] = "our"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("🛒 خرید ایمیل | 250,000 تومان"),
        types.KeyboardButton("🔙 بازگشت")
    )
    bot.send_message(
        user_id,
        "✍️ **ساخت ایمیل با ما**\n\n"
        "برای ساخت ایمیل، ابتدا باید **ایمیل** را خریداری کنید.\n"
        "💰 قیمت: **۲۵۰,۰۰۰** تومان\n\n"
        "👇 روی دکمه خرید کلیک کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 🛒 خرید ایمیل برای ساخت Apple ID
# ============================================================
@bot.message_handler(func=lambda message: message.text == "🛒 خرید ایمیل | 250,000 تومان")
def buy_email_for_apple(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    
    pending_payments[user_id]["product_name"] = "ایمیل سفارشی (برای اپل آیدی)"
    pending_payments[user_id]["price"] = 250000
    pending_payments[user_id]["is_for_apple"] = True
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"card_to_card_{user_id}")
    )
    bot.send_message(
        user_id,
        f"📦 محصول: **ایمیل سفارشی**\n💰 مبلغ: **۲۵۰,۰۰۰** تومان\n\nلطفاً روش پرداخت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 📞 هندلرهای پرداخت (درگاه و کارت به کارت)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("gateway_"))
def gateway_payment(call):
    user_id = call.message.chat.id
    if user_id not in pending_payments:
        bot.answer_callback_query(call.id, "❌ خطا! لطفاً دوباره تلاش کنید.")
        return
    
    bot.answer_callback_query(call.id, "💳 درگاه پرداخت انتخاب شد.")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    payment_steps[user_id] = "waiting_receipt"
    
    bot.send_message(
        user_id,
        "💳 **پرداخت از طریق درگاه**\n\n"
        "🔗 لینک پرداخت:\n"
        "https://your-payment-gateway.com/pay/order\n\n"
        "⚠️ پس از پرداخت، رسید را برای پشتیبانی ارسال کنید.\n\n"
        "📸 لطفاً **عکس رسید** واریز را ارسال کنید.",
        reply_markup=main_menu(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("card_to_card_"))
def card_to_card_payment(call):
    user_id = call.message.chat.id
    
    if user_id not in pending_payments:
        bot.answer_callback_query(call.id, "❌ خطا! لطفاً دوباره تلاش کنید.")
        bot.send_message(user_id, "❌ خطا! لطفاً دوباره تلاش کنید.", reply_markup=main_menu(user_id))
        return
    
    if "product_name" not in pending_payments[user_id] or "price" not in pending_payments[user_id]:
        bot.answer_callback_query(call.id, "❌ اطلاعات محصول کامل نیست.")
        bot.send_message(user_id, "❌ خطا! اطلاعات محصول یافت نشد. لطفاً دوباره تلاش کنید.", reply_markup=main_menu(user_id))
        return
    
    bot.answer_callback_query(call.id, "🏦 کارت به کارت انتخاب شد.")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    card_number = get_setting("card_number")
    card_owner = get_setting("card_owner")
    price = pending_payments[user_id]["price"]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    
    bot.send_message(
        user_id,
        f"🏦 **کارت به کارت**\n\n"
        f"💳 شماره کارت: `{card_number}`\n"
        f"👤 نام صاحب کارت: {card_owner}\n\n"
        f"💰 مبلغ: {price:,} تومان\n\n"
        f"📸 لطفاً **عکس رسید** واریز را ارسال کنید.\n\n"
        f"⏳ منتظر دریافت رسید شما هستم...",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    payment_steps[user_id] = "waiting_receipt"

# ============================================================
# 📸 دریافت رسید از کاربر
# ============================================================
@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.chat.id
    
    if user_id not in payment_steps:
        bot.send_message(user_id, "❌ شما در حال خرید فعالی ندارید. لطفاً از منوی اصلی خرید جدیدی شروع کنید.", reply_markup=main_menu(user_id))
        return
    
    if payment_steps.get(user_id) not in ["waiting_receipt", "waiting_balance_receipt"]:
        bot.send_message(user_id, "❌ در حال حاضر در انتظار رسید نیستید.", reply_markup=main_menu(user_id))
        return
    
    if user_id not in pending_payments:
        bot.send_message(user_id, "❌ خطا! اطلاعات خرید یافت نشد. لطفاً دوباره تلاش کنید.", reply_markup=main_menu(user_id))
        return
    
    if "product_name" not in pending_payments[user_id]:
        pending_payments[user_id]["product_name"] = "محصول نامشخص"
    if "price" not in pending_payments[user_id]:
        pending_payments[user_id]["price"] = 0
    
    photo = message.photo[-1]
    file_id = photo.file_id
    
    payment_steps[user_id] = "receipt_received"
    order_id = get_next_order_id()
    pending_payments[user_id]["order_id"] = order_id
    pending_payments[user_id]["photo_id"] = file_id
    
    product_name = pending_payments[user_id]["product_name"]
    save_pending_purchase(user_id, order_id, product_name, "", "")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ تأیید", callback_data=f"admin_confirm_{user_id}_{order_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"admin_reject_{user_id}_{order_id}")
    )
    
    user_info = get_user_info(user_id)
    
    admin_msg = (
        f"📸 **رسید جدید دریافت شد**\n\n"
        f"👤 کاربر: {user_id}\n"
        f"👤 نام: {user_info['first_name']} {user_info['last_name']}\n"
        f"📦 محصول: {pending_payments[user_id]['product_name']}\n"
        f"💰 مبلغ: {pending_payments[user_id]['price']:,} تومان\n"
        f"🆔 سفارش: #{order_id}\n"
        f"📅 تاریخ: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"⬇️ برای تأیید یا رد کلیک کنید:"
    )
    
    try:
        bot.send_photo(ADMIN_ID, file_id, caption=admin_msg, reply_markup=markup)
        bot.send_message(
            user_id,
            "✅ رسید شما دریافت شد و برای تأیید به ادمین ارسال گردید.\n\n"
            "⏳ لطفاً منتظر تأیید باشید...",
            reply_markup=main_menu(user_id)
        )
        print(f"✅ رسید کاربر {user_id} با موفقیت به ادمین ارسال شد.")
    except Exception as e:
        error_text = f"❌ خطا در ارسال رسید به ادمین:\n{str(e)}"
        print(error_text)
        try:
            bot.send_message(ADMIN_ID, error_text)
        except:
            pass
        bot.send_message(
            user_id,
            "❌ خطایی در ارسال رسید رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.\n\n"
            "📞 برای ارسال مجدد رسید، دوباره عکس را ارسال کنید.",
            reply_markup=main_menu(user_id)
        )
        payment_steps[user_id] = "waiting_receipt"

# ============================================================
# 📞 تأیید توسط ادمین (با پشتیبانی از افزایش موجودی)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_confirm_"))
def admin_confirm_payment(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید.")
        return
    
    parts = call.data.split("_")
    user_id = int(parts[2])
    order_id = int(parts[3])
    
    bot.answer_callback_query(call.id, "✅ پرداخت تأیید شد!")
    bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    
    if user_id not in pending_payments:
        bot.send_message(ADMIN_ID, "❌ اطلاعات محصول یافت نشد.")
        return
    
    product_name = pending_payments[user_id].get("product_name", "نامشخص")
    price = pending_payments[user_id].get("price", 0)
    
    # ===== اگر افزایش موجودی باشد =====
    if product_name == "افزایش موجودی":
        current_balance = get_user_balance(user_id)
        new_balance = current_balance + price
        update_user_balance(user_id, new_balance)
        update_purchase_status(order_id, "completed")
        
        bot.send_message(
            user_id,
            f"✅ موجودی شما با موفقیت افزایش یافت!\n\n"
            f"💰 مبلغ واریز: {price:,} تومان\n"
            f"💰 موجودی جدید: {new_balance:,} تومان",
            reply_markup=main_menu(user_id)
        )
        bot.send_message(ADMIN_ID, f"✅ موجودی کاربر {user_id} به مبلغ {price:,} تومان افزایش یافت.")
        pending_payments.pop(user_id, None)
        return
    
    # ===== برای سایر محصولات =====
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📦 تحویل محصول", callback_data=f"deliver_{user_id}_{order_id}"),
        types.InlineKeyboardButton("❌ لغو تحویل", callback_data=f"cancel_deliver_{user_id}_{order_id}")
    )
    
    admin_msg = (
        f"📦 **محصول تأیید شد**\n\n"
        f"👤 کاربر: {user_id}\n"
        f"📦 محصول: {product_name}\n"
        f"💰 مبلغ: {price:,} تومان\n"
        f"🆔 سفارش: #{order_id}\n\n"
        f"برای تحویل محصول، روی **تحویل محصول** کلیک کنید.\n"
        f"برای انصراف، روی **لغو تحویل** کلیک کنید."
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)
    
    bot.send_message(
        user_id,
        "✅ پرداخت شما تأیید شد و در حال آماده‌سازی محصول هستیم.\n"
        "⏳ لطفاً کمی صبر کنید...",
        reply_markup=main_menu(user_id)
    )

# ============================================================
# 📞 رد پرداخت توسط ادمین
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_"))
def admin_reject_payment(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید.")
        return
    
    parts = call.data.split("_")
    user_id = int(parts[2])
    order_id = int(parts[3])
    
    bot.answer_callback_query(call.id, "❌ پرداخت رد شد!")
    bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    
    update_purchase_status(order_id, "rejected")
    
    if user_id in pending_payments:
        product_name = pending_payments[user_id].get("product_name", "نامشخص")
        price = pending_payments[user_id].get("price", 0)
        save_failed_purchase(user_id, product_name, price, "رد توسط ادمین")
        pending_payments.pop(user_id, None)
    
    bot.send_message(
        user_id,
        "❌ متأسفانه پرداخت شما رد شد.\n"
        "📞 در صورت نیاز با پشتیبانی تماس بگیرید.",
        reply_markup=main_menu(user_id)
    )
    bot.send_message(ADMIN_ID, f"❌ سفارش #{order_id} توسط ادمین رد شد.")

# ============================================================
# 📦 تحویل محصول (عملیات اصلی)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("deliver_"))
def deliver_product_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید.")
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    order_id = int(parts[2])
    
    bot.answer_callback_query(call.id, "📦 در حال تحویل محصول...")
    bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    
    if user_id not in pending_payments:
        bot.send_message(ADMIN_ID, "❌ اطلاعات محصول یافت نشد.")
        return
    
    product_name = pending_payments[user_id].get("product_name", "")
    
    # ===== محصولات آماده (تحویل خودکار از دیتابیس) =====
    if product_name in ["Apple ID 31 روزه", "Apple ID دائمی", "Apple ID بدون iCloud"]:
        apple = get_unused_apple_id()
        if apple:
            mark_apple_id_used(apple["id"], user_id)
            
            detail = (
                f"🍏 **اپل‌آیدی شما**\n\n"
                f"📱 اپل‌آیدی: `{apple['apple_id']}`\n"
                f"🔑 رمز: `{apple['password']}`\n"
                f"🎂 تاریخ تولد: {apple['birth_date']}\n"
                f"🏫 مدرسه: {apple['school']}\n"
                f"💼 شغل: {apple['job']}\n"
                f"👪 محل ملاقات والدین: {apple['parentsmeet']}\n\n"
                f"🔐 **سوالات امنیتی:**\n"
                f"{apple['security_q1']}\n{apple['security_a1']}\n"
                f"{apple['security_q2']}\n{apple['security_a2']}\n"
                f"{apple['security_q3']}\n{apple['security_a3']}\n\n"
                f"📌 سفارش #{order_id}"
            )
            bot.send_message(user_id, detail, parse_mode="Markdown")
            
            warning_msg = (
                "🔔 **توجه مهم** 🔔\n\n"
                "📌 **لطفاً برای تغییر اطلاعات به سایت زیر مراجعه کنید:**\n"
                "🔗 https://support.apple.com/en-gb/apple-account\n\n"
                "⚠️ **هشدارهای مهم:**\n"
                "• گزینه **Find My iPhone** را حتماً خاموش کنید.\n"
                "• در صورت **لاک شدن** یا **غیرفعال شدن** اپل آیدی، مسئولیت مشکلات با شماست.\n\n"
                "💙 **تشکر که تیم ما را انتخاب کرده‌اید.**"
            )
            bot.send_message(user_id, warning_msg, parse_mode="Markdown", reply_markup=main_menu(user_id))
            
            save_user_purchase(user_id, order_id, product_name, apple['apple_id'], apple['password'])
            update_purchase_status(order_id, "completed")
            bot.send_message(ADMIN_ID, f"✅ {product_name} با موفقیت به کاربر {user_id} تحویل داده شد.")
            pending_payments.pop(user_id, None)
        else:
            bot.send_message(user_id, "❌ متأسفانه در حال حاضر اپل‌آیدی موجود نیست.", reply_markup=main_menu(user_id))
            bot.send_message(ADMIN_ID, f"⚠️ کاربر {user_id} خرید {product_name} انجام داد اما اپل‌آیدی موجود نیست!")
    
    # ===== ایمیل آماده =====
    elif product_name == "ایمیل آماده":
        email = get_unused_email()
        if email:
            mark_email_used(email["id"], user_id)
            detail = f"📧 **ایمیل شما**\n\n📧 ایمیل: `{email['email']}`\n🔑 رمز: `{email['password']}`\n\n📌 سفارش #{order_id}"
            bot.send_message(user_id, detail, parse_mode="Markdown", reply_markup=main_menu(user_id))
            save_user_purchase(user_id, order_id, product_name, email['email'], email['password'])
            update_purchase_status(order_id, "completed")
            bot.send_message(ADMIN_ID, f"✅ ایمیل با موفقیت به کاربر {user_id} تحویل داده شد.")
            pending_payments.pop(user_id, None)
        else:
            bot.send_message(user_id, "❌ متأسفانه در حال حاضر ایمیل موجود نیست.", reply_markup=main_menu(user_id))
            bot.send_message(ADMIN_ID, f"⚠️ کاربر {user_id} خرید {product_name} انجام داد اما ایمیل موجود نیست!")
    
    # ===== ساخت Apple ID (از ادمین اطلاعات می‌خواهیم) =====
    elif "ساخت Apple ID" in product_name:
        bot.send_message(
            ADMIN_ID,
            f"👤 لطفاً اطلاعات Apple ID ساخته‌شده را برای کاربر {user_id} وارد کنید.\n"
            f"سفارش: #{order_id}\n\n"
            f"فرمت:\n"
            f"`apple_id, password, birth_date, school, job, parentsmeet, security_q1, security_a1, security_q2, security_a2, security_q3, security_a3`\n\n"
            f"فیلدهای اختیاری را با 'ندارد' پر کنید."
        )
        msg = bot.send_message(ADMIN_ID, "اطلاعات را وارد کنید:")
        bot.register_next_step_handler(msg, process_manual_apple_delivery, user_id, order_id)
    
    # ===== ساخت ایمیل سفارشی (از ادمین اطلاعات می‌خواهیم) =====
    elif "ایمیل سفارشی" in product_name:
        bot.send_message(
            ADMIN_ID,
            f"📧 لطفاً ایمیل ساخته‌شده را برای کاربر {user_id} وارد کنید.\n"
            f"سفارش: #{order_id}\n"
            f"فرمت: `email, password`"
        )
        msg = bot.send_message(ADMIN_ID, "ایمیل و رمز را وارد کنید:")
        bot.register_next_step_handler(msg, process_manual_email_delivery, user_id, order_id)
    
    else:
        bot.send_message(ADMIN_ID, f"❌ نوع محصول ناشناخته: {product_name}")

# ============================================================
# 📞 لغو تحویل
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_deliver_"))
def cancel_deliver(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ شما دسترسی ندارید.")
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    order_id = int(parts[2])
    
    bot.answer_callback_query(call.id, "❌ تحویل لغو شد.")
    bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    
    update_purchase_status(order_id, "rejected")
    if user_id in pending_payments:
        product_name = pending_payments[user_id].get("product_name", "نامشخص")
        price = pending_payments[user_id].get("price", 0)
        save_failed_purchase(user_id, product_name, price, "لغو توسط ادمین بعد از تأیید")
        pending_payments.pop(user_id, None)
    
    bot.send_message(
        user_id,
        "❌ متأسفانه سفارش شما لغو شد.\n"
        "📞 در صورت نیاز با پشتیبانی تماس بگیرید.",
        reply_markup=main_menu(user_id)
    )
    bot.send_message(ADMIN_ID, f"❌ سفارش #{order_id} برای کاربر {user_id} لغو شد.")

# ============================================================
# 📥 دریافت اطلاعات دستی Apple ID از ادمین
# ============================================================
def process_manual_apple_delivery(message, user_id, order_id):
    if message.from_user.id != ADMIN_ID:
        return
    data = message.text.split(',')
    if len(data) < 12:
        bot.send_message(ADMIN_ID, "❌ تعداد فیلدها صحیح نیست. لطفاً دقیقاً ۱۲ فیلد وارد کنید.")
        bot.send_message(ADMIN_ID, "فرمت: `apple_id, password, birth_date, school, job, parentsmeet, security_q1, security_a1, security_q2, security_a2, security_q3, security_a3`")
        msg = bot.send_message(ADMIN_ID, "اطلاعات را دوباره وارد کنید:")
        bot.register_next_step_handler(msg, process_manual_apple_delivery, user_id, order_id)
        return
    
    apple_id = data[0].strip()
    password = data[1].strip()
    birth_date = data[2].strip()
    school = data[3].strip()
    job = data[4].strip()
    parentsmeet = data[5].strip()
    q1 = data[6].strip()
    a1 = data[7].strip()
    q2 = data[8].strip()
    a2 = data[9].strip()
    q3 = data[10].strip()
    a3 = data[11].strip()
    
    add_apple_id(apple_id, password, birth_date, school, job, parentsmeet, q1, a1, q2, a2, q3, a3)
    
    detail = (
        f"🍏 **اپل‌آیدی شما**\n\n"
        f"📱 اپل‌آیدی: `{apple_id}`\n"
        f"🔑 رمز: `{password}`\n"
        f"🎂 تاریخ تولد: {birth_date or 'ندارد'}\n"
        f"🏫 مدرسه: {school or 'ندارد'}\n"
        f"💼 شغل: {job or 'ندارد'}\n"
        f"👪 محل ملاقات والدین: {parentsmeet or 'ندارد'}\n\n"
        f"🔐 **سوالات امنیتی:**\n"
        f"{q1}\n{a1}\n{q2}\n{a2}\n{q3}\n{a3}\n\n"
        f"📌 سفارش #{order_id}"
    )
    bot.send_message(user_id, detail, parse_mode="Markdown")
    
    warning_msg = (
        "🔔 **توجه مهم** 🔔\n\n"
        "📌 **لطفاً برای تغییر اطلاعات به سایت زیر مراجعه کنید:**\n"
        "🔗 https://support.apple.com/en-gb/apple-account\n\n"
        "⚠️ **هشدارهای مهم:**\n"
        "• گزینه **Find My iPhone** را حتماً خاموش کنید.\n"
        "• در صورت **لاک شدن** یا **غیرفعال شدن** اپل آیدی، مسئولیت مشکلات با شماست.\n\n"
        "💙 **تشکر که تیم ما را انتخاب کرده‌اید.**"
    )
    bot.send_message(user_id, warning_msg, parse_mode="Markdown", reply_markup=main_menu(user_id))
    
    save_user_purchase(user_id, order_id, "ساخت Apple ID", apple_id, password)
    update_purchase_status(order_id, "completed")
    bot.send_message(ADMIN_ID, f"✅ Apple ID {apple_id} با موفقیت به کاربر {user_id} تحویل داده شد.")
    if user_id in pending_payments:
        pending_payments.pop(user_id, None)

# ============================================================
# 📥 دریافت اطلاعات دستی ایمیل از ادمین
# ============================================================
def process_manual_email_delivery(message, user_id, order_id):
    if message.from_user.id != ADMIN_ID:
        return
    data = message.text.split(',')
    if len(data) < 2:
        bot.send_message(ADMIN_ID, "❌ فرمت نامعتبر! لطفاً به صورت `email, password` وارد کنید.")
        msg = bot.send_message(ADMIN_ID, "ایمیل و رمز را دوباره وارد کنید:")
        bot.register_next_step_handler(msg, process_manual_email_delivery, user_id, order_id)
        return
    
    email = data[0].strip()
    password = data[1].strip()
    
    add_email(email, password)
    
    detail = f"📧 **ایمیل شما**\n\n📧 ایمیل: `{email}`\n🔑 رمز: `{password}`\n\n📌 سفارش #{order_id}"
    bot.send_message(user_id, detail, parse_mode="Markdown", reply_markup=main_menu(user_id))
    
    save_user_purchase(user_id, order_id, "ساخت ایمیل سفارشی", email, password)
    update_purchase_status(order_id, "completed")
    bot.send_message(ADMIN_ID, f"✅ ایمیل {email} با موفقیت به کاربر {user_id} تحویل داده شد.")
    if user_id in pending_payments:
        pending_payments.pop(user_id, None)

# ============================================================
# 📧 ساخت ایمیل سفارشی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "ساخت ایمیل 📧")
def create_email(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🛒 خرید ساخت ایمیل | 250,000 تومان"), types.KeyboardButton("🔙 بازگشت"))
    bot.send_message(user_id, "📧 ساخت ایمیل\n💰 قیمت: 250,000 تومان\n✅ ساخت اختصاصی", reply_markup=markup)

# ============================================================
# 🛒 خرید ساخت ایمیل
# ============================================================
@bot.message_handler(func=lambda message: message.text == "🛒 خرید ساخت ایمیل | 250,000 تومان")
def buy_custom_email(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["product_name"] = "ایمیل سفارشی"
    pending_payments[user_id]["price"] = 250000
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"card_to_card_{user_id}")
    )
    bot.send_message(
        user_id,
        f"📦 محصول: **ایمیل سفارشی**\n💰 مبلغ: **۲۵۰,۰۰۰** تومان\n\nلطفاً روش پرداخت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 📧 ایمیل آماده
# ============================================================
@bot.message_handler(func=lambda message: message.text == "ایمیل آماده 📧")
def email_ready(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🛒 خرید ایمیل آماده | 245,000 تومان"), types.KeyboardButton("🔙 بازگشت"))
    bot.send_message(user_id, "📧 ایمیل آماده\n💰 قیمت: 245,000 تومان\n✅ تحویل فوری", reply_markup=markup)

# ============================================================
# 🛒 خرید ایمیل آماده
# ============================================================
@bot.message_handler(func=lambda message: message.text == "🛒 خرید ایمیل آماده | 245,000 تومان")
def buy_ready_email(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["product_name"] = "ایمیل آماده"
    pending_payments[user_id]["price"] = 245000
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"card_to_card_{user_id}")
    )
    bot.send_message(
        user_id,
        f"📦 محصول: **ایمیل آماده**\n💰 مبلغ: **۲۴۵,۰۰۰** تومان\n\nلطفاً روش پرداخت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# 🛒 خریدهای من
# ============================================================
@bot.message_handler(func=lambda message: message.text == "خریدهای من 🛒")
def my_purchases(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return

    success_count, failed_count = get_user_purchase_stats(user_id)
    
    if success_count == 0 and failed_count == 0:
        text = "🛒 شما هیچ خریدی نداشته‌اید."
    else:
        text = f"🛒 **آمار خریدهای شما**\n\n"
        text += f"✅ خریدهای موفق: {success_count}\n"
        text += f"❌ خریدهای ناموفق: {failed_count}"
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=main_menu(user_id))

# ============================================================
# 🛡️ گارانتی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "گارانتی 🛡️")
def warranty_menu(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    
    msg = bot.send_message(
        user_id,
        "🛡️ **بررسی گارانتی اپل آیدی**\n\n"
        "لطفاً **اپل آیدی** خود را وارد کنید تا وضعیت گارانتی آن را بررسی کنیم.\n\n"
        "(مثال: example@icloud.com)",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, check_warranty)

def check_warranty(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    apple_id = message.text.strip()
    bot.send_message(
        user_id,
        f"🛡️ **نتیجه بررسی گارانتی**\n\n"
        f"📱 اپل آیدی: {apple_id}\n"
        f"✅ وضعیت: **فعال**\n"
        f"📅 تاریخ انقضا: ۱۴۰۵/۱۲/۰۱\n\n"
        f"⚠️ این اطلاعات صرفاً جنبه نمایشی دارد.",
        reply_markup=main_menu(user_id)
    )

# ============================================================
# 💰 افزایش موجودی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "افزایش موجودی 💰")
def increase_balance_menu(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    
    msg = bot.send_message(
        user_id,
        f"💳 **افزایش موجودی کیف پول**\n\n"
        f"💰 موجودی فعلی شما: {get_user_balance(user_id):,} تومان\n\n"
        f"مبلغ مورد نظر را به تومان وارد کنید:\n"
        f"(مثال: 50000)\n\n"
        f"⚠️ پس از تأیید ادمین، موجودی شما افزایش می‌یابد.",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_balance_increase)

def process_balance_increase(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            bot.send_message(user_id, "❌ مبلغ باید بزرگتر از صفر باشد.", reply_markup=main_menu(user_id))
            return
    except:
        bot.send_message(user_id, "❌ لطفاً یک عدد معتبر وارد کنید.", reply_markup=main_menu(user_id))
        return
    
    if user_id not in pending_payments:
        pending_payments[user_id] = {}
    pending_payments[user_id]["balance_amount"] = amount
    pending_payments[user_id]["product_name"] = "افزایش موجودی"
    pending_payments[user_id]["price"] = amount
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 درگاه پرداخت", callback_data=f"balance_gateway_{user_id}"),
        types.InlineKeyboardButton("🏦 کارت به کارت", callback_data=f"balance_card_{user_id}")
    )
    bot.send_message(
        user_id,
        f"💰 مبلغ: **{amount:,}** تومان\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("balance_gateway_"))
def balance_gateway(call):
    user_id = int(call.data.split("_")[2])
    bot.answer_callback_query(call.id, "💳 درگاه پرداخت انتخاب شد.")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    payment_steps[user_id] = "waiting_balance_receipt"
    
    bot.send_message(
        user_id,
        "💳 **پرداخت از طریق درگاه**\n\n"
        "🔗 لینک پرداخت:\n"
        "https://your-payment-gateway.com/pay/balance\n\n"
        "⚠️ پس از پرداخت، رسید را برای پشتیبانی ارسال کنید.\n\n"
        "📸 لطفاً **عکس رسید** واریز را ارسال کنید.",
        reply_markup=main_menu(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("balance_card_"))
def balance_card(call):
    user_id = int(call.data.split("_")[2])
    bot.answer_callback_query(call.id, "🏦 کارت به کارت انتخاب شد.")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    card_number = get_setting("card_number")
    card_owner = get_setting("card_owner")
    amount = pending_payments.get(user_id, {}).get("balance_amount", 0)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    
    bot.send_message(
        user_id,
        f"🏦 **کارت به کارت**\n\n"
        f"💳 شماره کارت: `{card_number}`\n"
        f"👤 نام صاحب کارت: {card_owner}\n\n"
        f"💰 مبلغ: {amount:,} تومان\n\n"
        f"📸 لطفاً **عکس رسید** واریز را ارسال کنید.\n\n"
        f"⏳ منتظر دریافت رسید شما هستم...",
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    payment_steps[user_id] = "waiting_balance_receipt"

# ============================================================
# 👨‍💻 پشتیبانی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "پشتیبانی 👨‍💻")
def support(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👤 پشتیبان 1", url="https://t.me/iman_sardaar"),
        types.InlineKeyboardButton("👤 پشتیبان 2", url="https://t.me/mobile_sardaar")
    )
    
    text = (
        "👨‍💻 **پشتیبانی SARDAR VIP**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📞 برای ارتباط با پشتیبان‌ها، روی یکی از دکمه‌های زیر کلیک کنید:\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🕐 **ساعات پاسخگویی:**\n"
        "   ۲۴ ساعته، ۷ روز هفته\n\n"
        "💙 **ما همیشه در کنار شما هستیم.**"
    )
    
    bot.send_message(user_id, text, parse_mode="Markdown", reply_markup=markup)

# ============================================================
# 🔄 آنلاک ایل آیدی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "آنلاک ایل آیدی 🔄")
def unlock_apple_id(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    unlock_step[user_id] = "waiting_apple_id"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    msg = bot.send_message(
        user_id,
        "🔓 **آنلاک اپل آیدی**\n\n"
        "لطفاً **اپل آیدی** خود را وارد کنید:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, unlock_get_apple_id)

def unlock_get_apple_id(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    apple_id = message.text.strip()
    if not apple_id:
        bot.send_message(user_id, "❌ اپل آیدی نمی‌تواند خالی باشد.")
        unlock_apple_id(message)
        return
    
    unlock_step[user_id] = {"apple_id": apple_id, "step": "waiting_password"}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    msg = bot.send_message(
        user_id,
        f"🔓 **آنلاک اپل آیدی**\n\n"
        f"اپل آیدی: `{apple_id}`\n\n"
        "لطفاً **رمز اپل آیدی** را وارد کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, unlock_get_password)

def unlock_get_password(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    password = message.text.strip()
    if not password:
        bot.send_message(user_id, "❌ رمز نمی‌تواند خالی باشد.")
        unlock_get_apple_id(message)
        return
    
    unlock_step[user_id]["password"] = password
    unlock_step[user_id]["step"] = "waiting_email_choice"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📧 وارد کردن ایمیل", callback_data=f"unlock_has_email_{user_id}"),
        types.InlineKeyboardButton("❌ ندارم", callback_data=f"unlock_no_email_{user_id}")
    )
    bot.send_message(
        user_id,
        "🔓 **آنلاک اپل آیدی**\n\n"
        "آیا **ایمیل چنج شده** دارید؟\n"
        "اگر دارید، روی **وارد کردن ایمیل** کلیک کنید.\n"
        "اگر ندارید، روی **ندارم** کلیک کنید.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("unlock_has_email_"))
def unlock_has_email(call):
    user_id = int(call.data.split("_")[3])
    if user_id != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ این بخش برای شما نیست.")
        return
    
    bot.answer_callback_query(call.id, "📧 وارد کردن ایمیل")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    unlock_step[user_id]["step"] = "waiting_email"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    msg = bot.send_message(
        user_id,
        "🔓 **آنلاک اپل آیدی**\n\n"
        "لطفاً **ایمیل چنج شده** را وارد کنید:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, unlock_get_email)

def unlock_get_email(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    email = message.text.strip()
    if not email or "@" not in email:
        bot.send_message(user_id, "❌ ایمیل نامعتبر! لطفاً یک ایمیل معتبر وارد کنید.")
        unlock_has_email(message)
        return
    
    unlock_step[user_id]["email"] = email
    unlock_step[user_id]["step"] = "waiting_email_password"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🔙 بازگشت"))
    msg = bot.send_message(
        user_id,
        "🔓 **آنلاک اپل آیدی**\n\n"
        f"ایمیل: `{email}`\n\n"
        "لطفاً **رمز ایمیل** را وارد کنید.\n"
        "⚠️ در صورت نداشتن رمز ایمیل، درخواست شما رد می‌شود.\n\n"
        "اگر رمز ندارید، روی **🔙 بازگشت** کلیک کنید.",
        parse_mode="Markdown",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, unlock_get_email_password)

def unlock_get_email_password(message):
    user_id = message.chat.id
    if message.text == "🔙 بازگشت":
        back_to_main(message)
        return
    
    email_password = message.text.strip()
    if not email_password:
        bot.send_message(user_id, "❌ رمز ایمیل نمی‌تواند خالی باشد. در صورت نداشتن رمز، روی برگشت کلیک کنید.")
        return
    
    unlock_step[user_id]["email_password"] = email_password
    
    data = unlock_step[user_id]
    admin_msg = (
        f"🔓 **درخواست آنلاک اپل آیدی**\n\n"
        f"👤 کاربر: {user_id}\n"
        f"📱 اپل آیدی: `{data['apple_id']}`\n"
        f"🔑 رمز اپل آیدی: `{data['password']}`\n"
        f"📧 ایمیل چنج شده: `{data.get('email', 'ندارد')}`\n"
        f"🔑 رمز ایمیل: `{data.get('email_password', 'ندارد')}`\n\n"
        f"📅 تاریخ درخواست: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    
    bot.send_message(
        user_id,
        "✅ درخواست شما با موفقیت ثبت شد.\n\n"
        "📞 برای اطلاع از نتیجه درخواست خود، با پشتیبان در تماس باشید.\n"
        "💙 از تماس شما متشکریم.",
        reply_markup=main_menu(user_id)
    )
    
    if user_id in unlock_step:
        del unlock_step[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("unlock_no_email_"))
def unlock_no_email(call):
    user_id = int(call.data.split("_")[3])
    if user_id != call.message.chat.id:
        bot.answer_callback_query(call.id, "❌ این بخش برای شما نیست.")
        return
    
    bot.answer_callback_query(call.id, "❌ ندارم")
    bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    if user_id in unlock_step:
        data = unlock_step[user_id]
        admin_msg = (
            f"🔓 **درخواست آنلاک اپل آیدی** (بدون ایمیل)\n\n"
            f"👤 کاربر: {user_id}\n"
            f"📱 اپل آیدی: `{data['apple_id']}`\n"
            f"🔑 رمز اپل آیدی: `{data['password']}`\n"
            f"📧 ایمیل چنج شده: **ندارد**\n\n"
            f"📅 تاریخ درخواست: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        
        bot.send_message(
            user_id,
            "✅ درخواست شما با موفقیت ثبت شد.\n\n"
            "📞 برای اطلاع از نتیجه درخواست خود، با پشتیبان در تماس باشید.\n"
            "💙 از تماس شما متشکریم.",
            reply_markup=main_menu(user_id)
        )
        
        del unlock_step[user_id]
    else:
        bot.send_message(user_id, "❌ خطا! لطفاً دوباره تلاش کنید.", reply_markup=main_menu(user_id))

# ============================================================
# 🔙 بازگشت به منو
# ============================================================
def back_to_main(message):
    user_id = message.chat.id
    if user_id in unlock_step:
        del unlock_step[user_id]
    if user_id == ADMIN_ID:
        admin_panel(message)
    else:
        balance = get_user_balance(user_id)
        bot.send_message(
            user_id,
            f"🏠 به منوی اصلی برگشتید.\n💰 موجودی: {balance:,} تومان",
            reply_markup=main_menu(user_id)
        )

# ============================================================
# 📚 راهنما
# ============================================================
@bot.message_handler(commands=["help"])
def help_command(message):
    user_id = message.chat.id
    if not is_member(user_id):
        bot.send_message(user_id, "🔒 لطفاً ابتدا در کانال عضو شوید.", reply_markup=join_channel_button())
        return
    
    help_text = (
        "📚 **راهنمای ربات SARDAR VIP**\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🍏 **ساخت Apple ID:**\n"
        "   ساخت اختصاصی با ایمیل خودتان یا ایمیل ما\n\n"
        "📦 **Apple ID آماده:**\n"
        "   ☁️ گارانتی ۳۱ روزه - ۴۱۰,۰۰۰ تومان\n"
        "   ☁️ گارانتی دائمی - ۴۵۰,۰۰۰ تومان\n"
        "   ❌ بدون iCloud - ۳۵۰,۰۰۰ تومان\n\n"
        "📧 **ایمیل:**\n"
        "   📧 ایمیل آماده - ۲۴۵,۰۰۰ تومان\n"
        "   📧 ساخت ایمیل سفارشی - ۲۵۰,۰۰۰ تومان\n\n"
        "🛡️ **گارانتی:**\n"
        "   برای بررسی گارانتی اپل آیدی خود از این بخش استفاده کنید\n\n"
        "🔄 **آنلاک اپل آیدی:**\n"
        "   برای رفع قفل اپل آیدی های غیرفعال\n\n"
        "💳 **افزایش موجودی:**\n"
        "   با کارت به کارت یا پرداخت مستقیم موجودی کیف پول را شارژ کنید\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👨‍💻 **پشتیبانی:**\n"
        "   در صورت هرگونه مشکل، از بخش پشتیبانی استفاده کنید.\n\n"
        "💙 **موفق و پیروز باشید!**"
    )
    bot.send_message(user_id, help_text, parse_mode="Markdown", reply_markup=main_menu(user_id))

# ============================================================
# ⚙️ پنل ادمین
# ============================================================
@bot.message_handler(func=lambda message: message.text == "پنل ادمین 🌻" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    user_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 آمار"),
        types.KeyboardButton("➕ افزودن اپل آیدی"),
        types.KeyboardButton("➕ افزودن ایمیل"),
        types.KeyboardButton("📋 لیست اپل آیدی‌ها"),
        types.KeyboardButton("📋 لیست ایمیل‌ها"),
        types.KeyboardButton("✏️ ویرایش تنظیمات"),
        types.KeyboardButton("📤 ارسال پیام همگانی"),
        types.KeyboardButton("🔙 بازگشت به منو")
    )
    bot.send_message(user_id, "⚙️ پنل مدیریت", reply_markup=markup)

def admin_panel_reply():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        types.KeyboardButton("📊 آمار"),
        types.KeyboardButton("➕ افزودن اپل آیدی"),
        types.KeyboardButton("➕ افزودن ایمیل"),
        types.KeyboardButton("📋 لیست اپل آیدی‌ها"),
        types.KeyboardButton("📋 لیست ایمیل‌ها"),
        types.KeyboardButton("✏️ ویرایش تنظیمات"),
        types.KeyboardButton("📤 ارسال پیام همگانی"),
        types.KeyboardButton("🔙 بازگشت به منو")
    )
    return markup

# ============================================================
# 📊 آمار
# ============================================================
@bot.message_handler(func=lambda message: message.text == "📊 آمار" and message.from_user.id == ADMIN_ID)
def stats(message):
    apple_count, email_count, user_count = get_inventory_stats()
    total_apple = len(get_all_apple_ids())
    total_email = len(get_all_emails())
    text = f"📊 **آمار کلی ربات**\n\n👥 کاربران: {user_count}\n🍏 اپل آیدی‌های موجود: {apple_count}\n📧 ایمیل‌های موجود: {email_count}\n📦 کل اپل آیدی‌ها: {total_apple}\n📧 کل ایمیل‌ها: {total_email}"
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown", reply_markup=admin_panel_reply())

# ============================================================
# ➕ افزودن اپل آیدی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "➕ افزودن اپل آیدی" and message.from_user.id == ADMIN_ID)
def add_apple_id_admin(message):
    bot.send_message(
        ADMIN_ID,
        "لطفاً اطلاعات اپل آیدی را به صورت زیر وارد کنید:\n\n"
        "`apple_id, password, birth_date, school, job, parentsmeet, security_q1, security_a1, security_q2, security_a2, security_q3, security_a3`\n\n"
        "فیلدهای اختیاری را با 'ندارد' پر کنید.\n\n"
        "مثال:\n"
        "`test@icloud.com, 123456, 1990-01-01, مدرسه, شغل, محل ملاقات, سوال1, پاسخ1, سوال2, پاسخ2, سوال3, پاسخ3`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, process_add_apple)

def process_add_apple(message):
    data = message.text.split(',')
    if len(data) < 12:
        bot.send_message(ADMIN_ID, "❌ تعداد فیلدها صحیح نیست. لطفاً دقیقاً ۱۲ فیلد وارد کنید.")
        return
    apple_id = data[0].strip()
    password = data[1].strip()
    birth_date = data[2].strip()
    school = data[3].strip()
    job = data[4].strip()
    parentsmeet = data[5].strip()
    q1 = data[6].strip()
    a1 = data[7].strip()
    q2 = data[8].strip()
    a2 = data[9].strip()
    q3 = data[10].strip()
    a3 = data[11].strip()
    if add_apple_id(apple_id, password, birth_date, school, job, parentsmeet, q1, a1, q2, a2, q3, a3):
        bot.send_message(ADMIN_ID, f"✅ اپل آیدی {apple_id} با موفقیت اضافه شد.", reply_markup=admin_panel_reply())
    else:
        bot.send_message(ADMIN_ID, "❌ خطا در افزودن! احتمالاً اپل آیدی تکراری است.", reply_markup=admin_panel_reply())

# ============================================================
# ➕ افزودن ایمیل
# ============================================================
@bot.message_handler(func=lambda message: message.text == "➕ افزودن ایمیل" and message.from_user.id == ADMIN_ID)
def add_email_admin(message):
    bot.send_message(ADMIN_ID, "لطفاً ایمیل و رمز را به صورت `email, password` وارد کنید:")
    bot.register_next_step_handler(message, process_add_email)

def process_add_email(message):
    data = message.text.split(',')
    if len(data) < 2:
        bot.send_message(ADMIN_ID, "❌ فرمت نامعتبر! لطفاً به صورت `email, password` وارد کنید.")
        return
    email = data[0].strip()
    password = data[1].strip()
    if add_email(email, password):
        bot.send_message(ADMIN_ID, f"✅ ایمیل {email} با موفقیت اضافه شد.", reply_markup=admin_panel_reply())
    else:
        bot.send_message(ADMIN_ID, "❌ خطا در افزودن! احتمالاً ایمیل تکراری است.", reply_markup=admin_panel_reply())

# ============================================================
# 📋 لیست‌ها
# ============================================================
@bot.message_handler(func=lambda message: message.text == "📋 لیست اپل آیدی‌ها" and message.from_user.id == ADMIN_ID)
def list_apple_ids(message):
    apples = get_all_apple_ids()
    if not apples:
        bot.send_message(ADMIN_ID, "📭 هیچ اپل آیدی در دیتابیس وجود ندارد.", reply_markup=admin_panel_reply())
        return
    text = "📋 لیست اپل آیدی‌ها:\n\n"
    for a in apples:
        text += f"ID: {a[0]} | {a[1]} | رمز: {a[2]} | وضعیت: {'استفاده شده' if a[7] else 'موجود'} | کاربر: {a[8] or 'ندارد'}\n"
    bot.send_message(ADMIN_ID, text, reply_markup=admin_panel_reply())

@bot.message_handler(func=lambda message: message.text == "📋 لیست ایمیل‌ها" and message.from_user.id == ADMIN_ID)
def list_emails(message):
    emails = get_all_emails()
    if not emails:
        bot.send_message(ADMIN_ID, "📭 هیچ ایمیلی در دیتابیس وجود ندارد.", reply_markup=admin_panel_reply())
        return
    text = "📋 لیست ایمیل‌ها:\n\n"
    for e in emails:
        text += f"ID: {e[0]} | {e[1]} | رمز: {e[2]} | وضعیت: {'استفاده شده' if e[3] else 'موجود'} | کاربر: {e[4] or 'ندارد'}\n"
    bot.send_message(ADMIN_ID, text, reply_markup=admin_panel_reply())

# ============================================================
# ✏️ ویرایش تنظیمات
# ============================================================
@bot.message_handler(func=lambda message: message.text == "✏️ ویرایش تنظیمات" and message.from_user.id == ADMIN_ID)
def edit_settings(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔄 تغییر شماره کارت", callback_data="edit_card_number"),
        types.InlineKeyboardButton("🔄 تغییر نام صاحب کارت", callback_data="edit_card_owner"),
        types.InlineKeyboardButton("🔄 تغییر درصد پاداش", callback_data="edit_bonus")
    )
    bot.send_message(
        ADMIN_ID,
        "✏️ تنظیمات فعلی:\n\n"
        "شماره کارت: " + get_setting("card_number") + "\n"
        "نام صاحب کارت: " + get_setting("card_owner") + "\n"
        "درصد پاداش: " + get_setting("bonus_percent") + "%",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "edit_card_number" and call.from_user.id == ADMIN_ID)
def edit_card_number(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(ADMIN_ID, "لطفاً شماره کارت جدید را وارد کنید:")
    bot.register_next_step_handler(msg, lambda m: update_setting_and_reply(m, "card_number", "شماره کارت"))

@bot.callback_query_handler(func=lambda call: call.data == "edit_card_owner" and call.from_user.id == ADMIN_ID)
def edit_card_owner(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(ADMIN_ID, "لطفاً نام جدید صاحب کارت را وارد کنید:")
    bot.register_next_step_handler(msg, lambda m: update_setting_and_reply(m, "card_owner", "نام صاحب کارت"))

@bot.callback_query_handler(func=lambda call: call.data == "edit_bonus" and call.from_user.id == ADMIN_ID)
def edit_bonus(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(ADMIN_ID, "لطفاً درصد پاداش جدید را وارد کنید (فقط عدد):")
    bot.register_next_step_handler(msg, lambda m: update_setting_and_reply(m, "bonus_percent", "درصد پاداش"))

def update_setting_and_reply(message, key, label):
    if message.from_user.id != ADMIN_ID:
        return
    value = message.text.strip()
    if key == "bonus_percent" and not value.isdigit():
        bot.send_message(ADMIN_ID, "❌ درصد باید عدد باشد.", reply_markup=admin_panel_reply())
        return
    update_setting(key, value)
    bot.send_message(ADMIN_ID, f"✅ {label} با موفقیت به {value} تغییر یافت.", reply_markup=admin_panel_reply())

# ============================================================
# 📤 ارسال پیام همگانی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "📤 ارسال پیام همگانی" and message.from_user.id == ADMIN_ID)
def broadcast(message):
    bot.send_message(ADMIN_ID, "✉️ لطفاً پیام خود را برای ارسال به همه کاربران وارد کنید (برای لغو /cancel):")
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    if message.text == "/cancel":
        bot.send_message(ADMIN_ID, "❌ ارسال همگانی لغو شد.", reply_markup=admin_panel_reply())
        return
    users = get_all_users()
    if not users:
        bot.send_message(ADMIN_ID, "❌ هیچ کاربری در دیتابیس وجود ندارد.", reply_markup=admin_panel_reply())
        return
    success = 0
    fail = 0
    for user in users:
        try:
            bot.send_message(user[0], message.text)
            success += 1
        except:
            fail += 1
    bot.send_message(ADMIN_ID, f"✅ پیام همگانی ارسال شد.\nموفق: {success}\nناموفق: {fail}", reply_markup=admin_panel_reply())

# ============================================================
# 🔙 بازگشت به منو (ادمین)
# ============================================================
@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به منو" and message.from_user.id == ADMIN_ID)
def back_to_main_from_admin(message):
    user_id = message.chat.id
    balance = get_user_balance(user_id)
    bot.send_message(user_id, f"🏠 به منوی اصلی برگشتید.\n💰 موجودی: {balance:,} تومان", reply_markup=main_menu(user_id))

# ============================================================
# 🔙 بازگشت عمومی
# ============================================================
@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت")
def back_button(message):
    back_to_main(message)

# ============================================================
# 🏃 اجرای ربات
# ============================================================
if __name__ == "__main__":
    print("🤖 ربات SARDAR VIP در حال راه‌اندازی...")
    print("🤖 @sardaarAppleAccount_Bot")
    check_inventory_and_notify()
    try:
        bot.delete_webhook()
        print("✅ وب‌هوک حذف شد.")
    except Exception as e:
        print(f"⚠️ خطا در حذف وب‌هوک: {e}")
    print("✅ شروع به دریافت پیام‌ها...")
    try:
        bot.polling(non_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ خطای اصلی: {e}")
        time.sleep(5)
