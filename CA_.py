# CA_.py - Contract Address handling module
import requests
from bot_instance import bot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from user_sessions import set_user_ca, get_user_price, get_user_ca
from bot_interations import group_chat_id

def is_valid_token_name(token_name):
    """Check if input is a valid token name (word length > 10)"""
    if not token_name or not isinstance(token_name, str):
        return False
    # Remove extra whitespace and check if it's a single word with length > 10
    cleaned = token_name.strip()
    if len(cleaned) > 10 and ' ' not in cleaned:
        return True
    return False

def search_token_on_dex(token_name):
    """Search for token on DEXScreener by name and return CA if found"""
    try:
        # Search by token name
        search_url = f"https://api.dexscreener.com/latest/dex/search?q={token_name}"
        resp = requests.get(search_url, timeout=10)
        data = resp.json()
        
        if data.get('pairs') and len(data['pairs']) > 0:
            # Find the best match (exact name match first)
            for pair in data['pairs']:
                base_token = pair.get('baseToken', {})
                if base_token.get('name', '').lower() == token_name.lower():
                    return {
                        'ca': base_token.get('address'),
                        'name': base_token.get('name'),
                        'symbol': base_token.get('symbol'),
                        'chain': pair.get('chainId'),
                        'found': True
                    }
            
            # If no exact match, return the first result
            first_pair = data['pairs'][0]
            base_token = first_pair.get('baseToken', {})
            return {
                'ca': base_token.get('address'),
                'name': base_token.get('name'),
                'symbol': base_token.get('symbol'),
                'chain': first_pair.get('chainId'),
                'found': True
            }
        
        return {'found': False}
    except Exception as e:
        print(f"Error searching token on DEX: {e}")
        return {'found': False}

def is_valid_ca(addr):
    """Check if input is a valid contract address"""
    if 32 <= len(addr) <= 44:
        return True
    if len(addr) >= 4 and addr[-4:].isalpha():
        return True
    return False

def handle_token_input(message, price, temp_ca_info):
    """Handle token name input, search on DEX, and process accordingly"""
    chat_id = message.chat.id
    user_input = message.text.strip()
    print(f"CA_.py: handle_token_input called with chat_id={chat_id}, price={price}, user_input='{user_input}'")
    
    # Check if input is a valid token name (word length > 10)
    if is_valid_token_name(user_input):
        # Search for token on DEX
        dex_result = search_token_on_dex(user_input)
        
        if dex_result['found']:
            # Token found on DEX, use its CA
            ca = dex_result['ca']
            name = dex_result['name']
            symbol = dex_result['symbol']
            chain = dex_result['chain']
            
            # Store CA info
            set_user_ca(chat_id, ca)
            temp_ca_info[chat_id] = {
                'ca': ca,
                'chain': chain,
                'name': name,
                'symbol': symbol,
                'price': price
            }
            
            # Send confirmation to user
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Confirm", callback_data="confirm_ca"),
                InlineKeyboardButton("🔙 Back", callback_data="back_ca")
            )
            text = f"✅ Token found on DEX!\n\nChain: {chain}\nName: {name}\nSymbol: {symbol}\nCA: {ca}"
            bot.send_message(chat_id, text, reply_markup=markup)
            
            # Send to group
            user = message.from_user.username or message.from_user.id
            group_text = (
                f"NEW TOKEN SUBMISSION (DEX FOUND)\n"
                f"User: @{user} (ID: {chat_id})\n"
                f"Token Name: {user_input}\n"
                f"CA: {ca}\n"
                f"Chain: {chain}"
            )
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
                InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
            )
            bot.send_message(group_chat_id, group_text, reply_markup=markup)
            return True
        else:
            # Token not found on DEX, use alternative CA
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Use Alternative CA", callback_data="use_alternative_ca"),
                InlineKeyboardButton("🔙 Back", callback_data="back_ca")
            )
            text = f"❌ Token '{user_input}' not found on DEX.\n\nWould you like to use an alternative CA for this token?"
            bot.send_message(chat_id, text, reply_markup=markup)
            return False
    
    # Check if input is a valid CA address
    if is_valid_ca(user_input):
        # Input is a valid CA, proceed as before
        ca = user_input
        set_user_ca(chat_id, ca)
        
        # Check on DEX
        dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{ca}"
        try:
            resp = requests.get(dexscreener_url, timeout=5)
            data = resp.json()
            found = bool(data.get('pairs'))
            if found:
                pair = data['pairs'][0]
                chain = pair.get('chainId', 'Unknown')
                name = pair['baseToken'].get('name', 'Unknown')
                symbol = pair['baseToken'].get('symbol', 'Unknown')
                temp_ca_info[chat_id] = {
                    'ca': ca,
                    'chain': chain,
                    'name': name,
                    'symbol': symbol,
                    'price': price
                }
                markup = InlineKeyboardMarkup()
                markup.add(
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_ca"),
                    InlineKeyboardButton("🔙 Back", callback_data="back_ca")
                )
                text = f"selected token:\n\nChain: {chain}\nName: {name}\nSymbol: {symbol}\nCA: {ca}"
                bot.send_message(chat_id, text, reply_markup=markup)
                return True
        except Exception:
            pass
        
        # Send CA to group with reply/close buttons
        user = message.from_user.username or message.from_user.id
        group_text = (
            f"NEW CA SUBMISSION\n"
            f"User: @{user} (ID: {chat_id})\n"
            f"CA: {ca}"
        )
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("reply", callback_data=f"group_reply_{chat_id}"),
            InlineKeyboardButton("close", callback_data=f"group_close_{chat_id}")
        )
        bot.send_message(group_chat_id, group_text, reply_markup=markup)
        return True
    
    # Invalid input
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Retry", callback_data="ca_retry"),
        InlineKeyboardButton("Back", callback_data="ca_back")
    )
    bot.send_message(chat_id, "❌ Invalid input. Please enter a valid token name (word length > 10) or contract address.", reply_markup=markup)
    return False

# Temporary storage for CA info
temp_ca_info = {} 