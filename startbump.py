from user_sessions import set_user_price
from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import start_message

def handle_start_bump(call):
    chat_id = call.message.chat.id
    text = """
The fastest and cheapest Telegram bot for creating bump orders.

Supported Platform: Pumpfun and Raydium.

Pumpfun BumpBot charges a one-time fee of 0.2 SOL per token, making it the cheapest bump bot ever!

📊 Trending channel: 
https://t.me/pumpmints
"""
    markup = InlineKeyboardMarkup()
    button3 = InlineKeyboardButton("🟢0.3 SOL B-B", callback_data="bump_0.3")
    button4 = InlineKeyboardButton("🟢0.4 SOL B-B", callback_data="bump_0.4")
    button5 = InlineKeyboardButton("🟢0.5 SOL B-B", callback_data="bump_0.5")
    button6 = InlineKeyboardButton("🟢0.6 SOL B-B", callback_data="bump_0.6")
    buttonback = InlineKeyboardButton("🔙 Back", callback_data="back")
    mainmenu = InlineKeyboardButton("🔝 Main Menu", callback_data="mainmenu")
    markup.row(button3)
    markup.row(button4, button5)
    markup.row(button6)
    markup.row(buttonback)
    markup.row(mainmenu)
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup,
        parse_mode="markdown"
    )

def handle_startbumps_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if call.data.startswith("bump_"):
        sol_amount = call.data.split("_")[1]
        set_user_price(chat_id, sol_amount)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"{e}")
        bot.send_message(
            chat_id,
            f"""
📄 *Enter Token Name or Contract Address (CA)*

You selected `{sol_amount} SOL`.

Please enter either:
• A token name (word length > 10) to search on DEX
• Or a Contract Address (CA) directly
""",
            parse_mode="Markdown"
        )
        # Set waiting for CA input
        from main import ca_retry_waiting
        ca_retry_waiting[chat_id] = True
    elif call.data == "back":
        # Go back to main menu (one step back from startbump)
        bot.delete_message(chat_id, message_id)
        start_message(call.message)
    elif call.data == "mainmenu":
        # Go to main menu
        bot.delete_message(chat_id, message_id)
        start_message(call.message)
