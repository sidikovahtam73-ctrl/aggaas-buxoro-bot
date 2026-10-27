qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      bot.send_message(m.chat.id,f"{serv} yasaymiz! 👍\nO'lchamini yozing: masalan 3x4 {serv.lower()}\n\nBepul o'lchovga boramiz!",reply_markup=kb,protect_content=True)
      return

    if "boshqa" i⁷n txt:
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      bot.send_message(m.chat.id,"Istalgan temir buyum yasaymiz! 💪\n\nMangal, krovat, eshik, reshotka, skameyka, javon, stol - hammasini!",reply_markup=kb,protect_content=True)
      return

    if is_custom(txt) and len(txt)>=3:
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("💰 Narxlar","🏠 Bosh menyu")
      bot.send_message(m.chat.id,f"{original} ni yasaymiz! Ha, bo'ladi! 👍\nO'lchamini yozing: 2x1 {original}\nRaqam qoldirsangiz usta bepul borib ko'radi!",reply_markup=kb,protect_content=True)
      return

    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
    kb.add("💰 Narxlar","🏠 Bosh menyu")
    bot.send_message(m.chat.id,f"Tushundim! {original} 👍\nO'lchamini yozing: masalan 3x4 {original.lower()}\nYoki raqam qoldiring, usta bepul borib ko'radi!",reply_markup=kb,protect_content=True)
  except Exception as e:
    print(f"Xato {e}")

print("✅ Bot ishga tushdi - Ideal + Namunalar toza")
try:
  bot.remove_webhook()
  time.sleep(1)
  bot.delete_webhook(drop_pending_updates=True)
except: pass
from flask import Flask
app=Flask(__name__)
@app.route('/')
def home():
  return "AggaaS Buxoro - Ideal + Namunalar toza - Live"
@app.route('/health')
def health():
  return "OK"
def run_bot():
  while True:
    try:
      bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60, skip_pending=True)
    except Exception as e:
      print(e)
      time.sleep(5)
if __name__=="__main__":
  import threading
  threading.Thread(target=run_bot, daemon=True).start()
  app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
