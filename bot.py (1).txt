import telebot
from telebot import types
import os

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(TOKEN)

# Asosiy menyu
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍 Маҳсулотлар"),
        types.KeyboardButton("🛒 Сават"),
        types.KeyboardButton("📦 Буюртмаларим"),
        types.KeyboardButton("📞 Алоқа"),
        types.KeyboardButton("ℹ️ Биз ҳақимизда")
    )
    return markup

# Маҳсулотлар inline
def products_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👟 Кроссовкалар", callback_data="cat_kross"),
        types.InlineKeyboardButton("👕 Футболкалар", callback_data="cat_futbolka"),
        types.InlineKeyboardButton("👖 Шимлар", callback_data="cat_shim"),
        types.InlineKeyboardButton("🧢 Кепкалар", callback_data="cat_kepka"),
        types.InlineKeyboardButton("🔙 Орқага", callback_data="back_main")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    text = f"""
👋 Салом {message.from_user.first_name}!

🛍 **Aggaas Buxoro** расмий ботига хуш келибсиз!

✅ Бу ерда сиз:
• Маҳсулотларни кўришингиз
• Буюртма беришингиз
• Тўлов қилишингиз мумкин

👇 Пастдаги менюдан танланг:
"""
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛍 Маҳсулотлар")
def show_products(message):
    bot.send_message(message.chat.id, "🛍 Категорияни танланг:", reply_markup=products_menu())

@bot.message_handler(func=lambda m: m.text == "🛒 Сават")
def cart(message):
    bot.send_message(message.chat.id, "🛒 Саватингиз бўш. Маҳсулот қўшинг!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📦 Буюртмаларим")
def orders(message):
    bot.send_message(message.chat.id, "📦 Ҳали буюртмаларингиз йўқ.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📞 Алоқа")
def contact(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📞 Телефон", url="tel:+998901234567"))
    markup.add(types.InlineKeyboardButton("✈️ Telegram", url="https://t.me/aggaas_buxoro"))
    markup.add(types.InlineKeyboardButton("📍 Манзил", callback_data="location"))
    bot.send_message(message.chat.id, "📞 Алоқа учун:\n\n📱 +998 90 123-45-67\n✈️ @aggaas_buxoro\n📍 Бухоро ш., Пиридастгир кўчаси", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "ℹ️ Биз ҳақимизда")
def about(message):
    bot.send_message(message.chat.id, "🏢 **Aggaas Buxoro** - 2020 йилдан бери сифатли кийимлар!\n\n✅ 100% оригинал\n✅ Тез етказиб бериш\n✅ Алмаштириш кафолати", parse_mode="Markdown", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("cat_"):
        # Намунавий маҳсулот
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛒 Саватга қўшиш", callback_data="add_1"))
        markup.add(types.InlineKeyboardButton("💳 Соҳибига ёзиш", url="https://t.me/aggaas_buxoro"))
        markup.add(types.InlineKeyboardButton("🔙 Орқага", callback_data="back_products"))
        
        bot.send_message(call.message.chat.id, f"👟 **Nike Air Max**\n\n💰 Нархи: 450 000 сўм\n📏 Размер: 40-44\n🎨 Ранг: Қора, Оқ\n\n✅ Мавжуд", parse_mode="Markdown", reply_markup=markup)
    
    elif call.data == "back_main":
        bot.send_message(call.message.chat.id, "Асосий меню:", reply_markup=main_menu())
    
    elif call.data == "back_products":
        bot.send_message(call.message.chat.id, "Категорияни танланг:", reply_markup=products_menu())
    
    elif call.data == "add_1":
        bot.answer_callback_query(call.id, "✅ Саватга қўшилди!")
        bot.send_message(call.message.chat.id, "🛒 Саватга қўшилди! Давом этамизми?", reply_markup=main_menu())
    
    bot.answer_callback_query(call.id)

# Keep alive for Render
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Aggaas Buxoro Bot is running!"

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    print("Bot started...")
    bot.infinity_polling()
