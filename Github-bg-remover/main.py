import telebot
from telebot import types
import os
import time
import requests
from remove import remove_bg
from PIL import Image, ImageEnhance
import database
import urllib.parse

bot = telebot.TeleBot("7383464358:AAEeLTtfqdjb2qMjXX6mUpjwzM1OBX8d7p0")

# Function to create the main keyboard markup
def create_main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🖼 Remove Background"))
    markup.add(types.KeyboardButton("🪙 Check Tokens"), types.KeyboardButton("🎁 Get Tokens"))
    markup.add(types.KeyboardButton("ℹ️ Help"), types.KeyboardButton("💬 FeedBack"))
    return markup

# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    database.add_user(message.from_user.id)  # Add user to the database if not already present
    welcome_msg = """
    ✨ *Welcome to Magic Background Remover!* ✨

_You have 1 free token to start!_
_1 token = 1 background removal_

📊 Your tokens: {tokens}

👉 Click '🖼 Remove Background' to start
👉 Need more tokens? Click '🎁 Get Tokens'
    """.format(tokens=database.get_tokens(message.from_user.id))
    
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown', reply_markup=create_main_markup())

# Remove Background button handler
@bot.message_handler(func=lambda message: message.text == "🖼 Remove Background")
def handle_remove_bg_request(message):
    user_id = message.from_user.id
    tokens = database.get_tokens(user_id)
    
    if tokens < 1:
        bot.send_message(message.chat.id, 
                       "❌ *Out of tokens!*\nWatch a short ad to get more tokens!",
                       parse_mode='Markdown',
                       reply_markup=types.InlineKeyboardMarkup().add(
                           types.InlineKeyboardButton("📺 Watch Ad", callback_data="watch_ad")
                       ))
        return
    
    # Ask user to send the image
    msg = bot.send_message(message.chat.id, "📤 Please send the image to process:")
    bot.register_next_step_handler(msg, process_image)

# Process the image and remove background
def process_image(message):
    if not message.photo:
        bot.send_message(message.chat.id, "⚠️ Please send a valid image.")
        return

    try:
        progress_msg = bot.send_message(message.chat.id, 
                                      "🔍 *Analyzing image...*\n⏳ Estimated time: 10-15 seconds", 
                                      parse_mode='Markdown')
        
        # Download the image
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        timestamp = str(int(time.time()))
        input_path = f"input_{timestamp}.jpg"
        output_path = f"output_{timestamp}.png"

        # Save the input image
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)

        # Process the image (remove background)
        result_path = remove_bg(input_path, output_path)

        # Deduct token only after successful background removal
        database.update_tokens(message.from_user.id, -1)

        # Send the processed image to the user
        bot.edit_message_text("🎨 *Finalizing results...*", message.chat.id, progress_msg.message_id, parse_mode='Markdown')
        with open(result_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="✅ *Background removed successfully!*\n🔄 Want to try another image?", parse_mode='Markdown', reply_markup=create_action_markup())

    except Exception as e:
        error_handler(message, e)
    finally:
        cleanup_files(input_path, output_path)
        try: bot.delete_message(message.chat.id, progress_msg.message_id)
        except: pass

# Create inline keyboard for actions
def create_action_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✨ Enhance Quality", callback_data="enhance"),
               types.InlineKeyboardButton("🔄 New Image", callback_data="new"))
    return markup

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "new":
        bot.send_message(call.message.chat.id, "🖼 Send a new image to process!")
    elif call.data == "enhance":
        handle_enhance_request(call.message)

# Handle enhance request
def handle_enhance_request(message):
    user_id = message.from_user.id
    tokens = database.get_tokens(user_id)
    
    if tokens < 1:
        bot.send_message(message.chat.id, 
                       "❌ *Out of tokens!*\nWatch a short ad to get more tokens!",
                       parse_mode='Markdown',
                       reply_markup=types.InlineKeyboardMarkup().add(
                           types.InlineKeyboardButton("📺 Watch Ad", callback_data="watch_ad")
                       ))
        return
    
    # Ask for confirmation
    confirm_markup = types.InlineKeyboardMarkup()
    confirm_markup.add(
        types.InlineKeyboardButton("✅ Confirm", callback_data="confirm_enhance"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_enhance")
    )
    bot.send_message(message.chat.id, 
                    "✨ *Enhance Quality*\nThis will cost 1 token. Confirm?",
                    parse_mode='Markdown', reply_markup=confirm_markup)

# Handle enhance confirmation
@bot.callback_query_handler(func=lambda call: call.data == "confirm_enhance")
def confirm_enhance(call):
    user_id = call.from_user.id
    tokens = database.get_tokens(user_id)
    
    if tokens < 1:
        bot.send_message(call.message.chat.id, 
                       "❌ *Out of tokens!*\nWatch a short ad to get more tokens!",
                       parse_mode='Markdown',
                       reply_markup=types.InlineKeyboardMarkup().add(
                           types.InlineKeyboardButton("📺 Watch Ad", callback_data="watch_ad")
                       ))
        return
    
    # Deduct token
    database.update_tokens(user_id, -1)
    
    # Enhance the image
    enhance_image(call.message)

# Handle enhance cancellation
@bot.callback_query_handler(func=lambda call: call.data == "cancel_enhance")
def cancel_enhance(call):
    bot.send_message(call.message.chat.id, "❌ Enhancement canceled.")

# Enhance image quality
def enhance_image(message):
    try:
        timestamp = str(int(time.time()))
        input_path = f"output_{timestamp}.png"
        enhanced_path = f"enhanced_{timestamp}.png"

        img = Image.open(input_path)
        enhancer = ImageEnhance.Sharpness(img)
        enhanced_img = enhancer.enhance(2.0)
        enhanced_img.save(enhanced_path)

        with open(enhanced_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="✅ *Image Enhanced Successfully!*", parse_mode='Markdown')

        cleanup_files(enhanced_path)
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ *Enhancement Failed!* Error: {str(e)}", parse_mode='Markdown')

# Check Tokens button handler
@bot.message_handler(func=lambda message: message.text == "🪙 Check Tokens")
def check_tokens(message):
    tokens = database.get_tokens(message.from_user.id)
    bot.send_message(message.chat.id, 
                   f"📊 *Your Token Balance:*\n{tokens} tokens remaining",
                   parse_mode='Markdown')

# Get Tokens button handler
@bot.message_handler(func=lambda message: message.text == "🎁 Get Tokens")
def get_tokens(message):
    user_id = message.from_user.id
    ad_url = f"https://my-ad-page.onrender.com/ad_page.html?user_id={user_id}"
    bot.send_message(
        message.chat.id,
        "Click below to watch an ad:",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("📺 Watch Ad", url=ad_url)
        )
    )
    
    bot.send_message(message.chat.id, """
🎁 *Earn Tokens:*
1. Click below to watch an ad
2. Complete the full video
3. Return to bot to claim token

Note: Ads may take 5-10 seconds to load
    """, parse_mode='Markdown', reply_markup=markup)

# Handle deep linking for ad completion
@bot.message_handler(commands=['start'])
def handle_start(message):
    if 'ad_completed' in message.text:
        user_id = message.text.split('_')[-1]
        bot.send_message(user_id, "✅ Ad verified! +1 token added!")
    else:
        send_welcome(message)

# Help button handler
@bot.message_handler(func=lambda message: message.text == "ℹ️ Help")
def show_help(message):
    help_text = """
    ℹ️ *Help Guide*
    
1. Click '🖼 Remove Background'
2. Send/upload your image
3. Wait 10-15 seconds for processing
4. Get your transparent-background image!
    
Max file size: 5MB
Supported formats: JPG/PNG
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Feedback button handler
@bot.message_handler(func=lambda message: message.text == "💬 FeedBack")
def handle_feedback(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Send Feedback", url="https://t.me/your_feedback_bot"))
    bot.send_message(message.chat.id, "We value your feedback! Click below:", reply_markup=markup)

# Error handler
def error_handler(message, error):
    error_msg = f"⚠️ *Processing Failed!*\nError: {str(error)}"
    if "API quota" in str(error):
        error_msg = "🚫 API limit exceeded. Please try again later."
    bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')

# Cleanup files
def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)

# Start the bot
print('Bot is running...')
if __name__ == "__main__":
    bot.polling(none_stop=True)
