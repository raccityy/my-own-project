from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from user_sessions import set_user_price, set_user_ca, get_user_price
from bot_interations import group_chat_id
import requests

# Temporary storage for CA info for volume flow
volume_temp_ca_info = {}

PACKAGE_PRICES = {
    'vol_iron': '1',
    'vol_bronze': '3',
    'vol_gold': '5.2',
    'vol_platinum': '7.5',
    'vol_silver': '10',
    'vol_diamond': '15',
}

def handle_volume(call):
    chat_id = call.message.chat.id
    image_url = 'https://github.com/raccityy/raccityy.github.io/blob/main/volume.jpg?raw=true'
    short_caption = "Choose the desired Volume Boost package:"
    text = (
        "🧪Iron Package - $40,200 Volume\n"
        "🧪Bronze Package - $92,000 Volume\n"
        "🧪Silver Package - $466,000 Volume\n"
        "🧪Gold Package - $932,000 Volume\n"
        "🧪Platinum Package - $1,400,000 Volume\n"
        "🧪 Diamond Package - $2,400,000 Volume\n\n"
        "Please select the package below:"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("1 SOL - Irion⛓️", callback_data="vol_iron"),
        InlineKeyboardButton("3 SOL - Bronze 🥉", callback_data="vol_bronze"),
        InlineKeyboardButton("5.2 SOL - Gold", callback_data="vol_gold"),
        InlineKeyboardButton("7.5 SOL - Platinum ⏺️", callback_data="vol_platinum"),
        InlineKeyboardButton("10 SOL - Silver 🥈", callback_data="vol_silver"),
        InlineKeyboardButton("15 SOL - Diamond💎", callback_data="vol_diamond"),
        InlineKeyboardButton("🔙 Back", callback_data="vol_back"),
        InlineKeyboardButton("🔝 Main Menu", callback_data="vol_mainmenu")
    )
    try:
        # bot.send_photo(chat_id, image_url, caption=short_caption)
        bot.send_photo(chat_id, image_url, caption=text, reply_markup=markup)
    except Exception:
        bot.send_message(chat_id, short_caption)

def handle_volume_package(call):
    chat_id = call.message.chat.id
    package = call.data
    price = PACKAGE_PRICES.get(package)
    if not price:
        bot.send_message(chat_id, "Unknown package selected.")
        return
    set_user_price(chat_id, price)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Back", callback_data="ca_back"))
    bot.send_message(
        chat_id,
        f"📄 *Enter Token Name or Contract Address (CA)*\n\nYou selected `{price} SOL` for Volume Boost.\n\nPlease enter either:\n• A token name (word length > 10) to search on DEX\n• Or a Contract Address (CA) directly",
        parse_mode="Markdown",
        reply_markup=markup
    )
    # Set waiting for CA input
    from main import ca_retry_waiting
    ca_retry_waiting[chat_id] = True

def handle_volume_ca(message, send_payment_instructions, temp_ca_info):
    chat_id = message.chat.id
    price = get_user_price(chat_id)
    if not price:
        return
    
    # Use the CA handling logic from CA_.py
    from CA_ import handle_token_input
    handle_token_input(message, price, temp_ca_info)
