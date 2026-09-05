@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id

    add_new_user(
        user_id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or ""
    )

    if is_member(user_id):
        balance = get_user_balance(user_id)

        bot.send_message(
            user_id,
            f"👋 سلام {message.from_user.first_name} عزیز!\n"
            f"به ربات فروشگاه SARDAR VIP خوش آمدید.\n"
            f"💰 موجودی شما: {balance:,} تومان",
            reply_markup=main_menu(user_id)
        )
    else:
        bot.send_message(
            user_id,
            "🔒 لطفاً ابتدا در کانال عضو شوید تا بتوانید از خدمات استفاده کنید.",
            reply_markup=join_channel_button()
        )
