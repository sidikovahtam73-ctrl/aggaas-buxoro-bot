import telebot, re, os, time, glob
from telebot import types
from collections import defaultdict, deque

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "8980986366:AAGjew-L_kVH_BJH5UdLJVYr5W8fGGlKCVc"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8979707235

last_req = {}
user_times = defaultdict(lambda: deque())
user_last_msg = {}
blocked_until = {}

FLOOD_LIMIT = 20
FLOOD_WINDOW = 10
BLOCK_TIME = 10

def is_rate_limited(chat_id):
  now = time.time()
  if chat_id in blocked_until and now < blocked_until[chat_id]:
    return True, int(blocked_until[chat_id] - now)
  dq = user_times[chat_id]
  dq.append(now)
  while dq and now - dq[0] > FLOOD_WINDOW:
    dq.popleft()
  if len(dq) > FLOOD_LIMIT:
    blocked_until[chat_id] = now + BLOCK_TIME
    return True, BLOCK_TIME
  user_last_msg[chat_id] = now
  return False, 0

TARIF_MAT = {
  "Darvoza":500000,"Kalitka":450000,"Panjara":400000,"Naves":350000,
  "Kozyrek":350000,"Perila":450000,"Balkon":400000,"Besedka":500000,
  "Stellaj":200000,"Topchan":200000,"Zinapoya":250000,"Stol":200000
}
TARIF_CUSTOM = 300000
TARIF_MATN = """💰 Narxlar (material bilan birga):
• Darvoza - 500 mingdan m2
• Kalitka - 450 mingdan
• Panjara - 400 mingdan
• Naves - 350 mingdan
• Kozyrek - 350 mingdan
• Perila - 450 mingdan
• Balkon - 400 mingdan
• Besedka - 500 mingdan
• Stellaj - 200 mingdan
• Topchan - 200 mingdan
• Stol - 200 mingdan
• Zinapoya - 250 mingdan 1 qadam
• Mangal, krovat, eshik, reshotka, skameyka, javon - 300 mingdan
📏 O'lchamni yozing: Masalan 3x4 naves yoki 2x1 mangal
👨‍🔧 Bepul o'lchov - Buxoro bo'yicha usta boradi!"""
TEMIR_KALITLAR = ["mangal","barbekyu","kamin","kazan","tandir","ochoq","krovat","karavot","divan","skameyka","lavochka","orindiq","temir eshik","rom","reshotka","setka","vorota","zabor","tosig","ayvon","soyabon","narvon","lesa","guldon","gulzor","issiqxona","javon","polka","tokcha","shkaf","verstak","parta","qafas","it uyi","tovuq katak","molxona","temir","metall","payvand","kovka","svar","pechka"]

def get_files(patterns):
  files=[]
  for pat in patterns:
    files.extend(glob.glob(pat))
  uniq=[]
  seen=set()
  for f in files:
    if os.path.exists(f) and f not in seen:
      seen.add(f)
      uniq.append(f)
  return sorted(uniq)

def send_photos(chat_id, file_list, first_caption=None, limit=10):
  cnt=0
  for fname in file_list:
    if cnt>=limit: break
    try:
      if os.path.exists(fname):
        with open(fname,'rb') as f:
          if first_caption and cnt==0:
            bot.send_photo(chat_id,f,caption=first_caption,protect_content=True)
          else:
            bot.send_photo(chat_id,f,protect_content=True)
        cnt+=1
        time.sleep(0.3)
    except Exception as e:
      print(f"Rasm xato {fname}: {e}")

def find_service(txt):
  t=txt.lower()
  if "lestn" in t or "лестн" in t or "zina" in t: return "Zinapoya"
  if "topchan" in t or "tapchan" in t or "топчан" in t: return "Topchan"
  if "stol" in t or "стол" in t: return "Stol"
  if "darvoza" in t or "ворота" in t: return "Darvoza"
  if "kalitka" in t or "калитка" in t: return "Kalitka"
  if "panjara" in t or "panj" in t or "забор" in t: return "Panjara"
  if "naves" in t or "навес" in t: return "Naves"
  if "kozyrek" in t or "козырек" in t or "kazirek" in t: return "Kozyrek"
  if "perila" in t or "перила" in t: return "Perila"
  if "balkon" in t or "балкон" in t: return "Balkon"
  if "besedka" in t or "беседка" in t: return "Besedka"
  if "stellaj" in t or "стеллаж" in t: return "Stellaj"
  return None

def is_custom(txt):
  t=txt.lower()
  for k in TEMIR_KALITLAR:
    if k in t:
      return True
  return len(t.strip())>=3

def parse_size(txt):
  import re
  m=re.search(r'(\d+(?:[.,]\d+)?)\s*[xх*]\s*(\d+(?:[.,]\d+)?)', txt)
  if m:
    try:
      a=float(m.group(1).replace(',','.'))
      b=float(m.group(2).replace(',','.'))
      return a,b,a*b
    except: pass
  return None

def parse_qadam(txt):
  import re
  m=re.search(r'(\d+)\s*qadam', txt.lower())
  if m:
    return int(m.group(1))
  return None

@bot.message_handler(content_types=['new_chat_members'])
def anti_group(m):
  try:
    if m.chat.type!='private':
      bot.send_message(m.chat.id,"❌ Bu bot faqat shaxsiy chatda ishlaydi!",protect_content=True)
      bot.leave_chat(m.chat.id)
  except: pass

@bot.message_handler(content_types=['contact'])
def contact_handler(m):
  lim,wait=is_rate_limited(m.chat.id)
  if lim and wait>0:
    bot.send_message(m.chat.id,f"⏳ {wait} sek kuting!",protect_content=True)
    return
  if m.forward_from or m.forward_from_chat:
    bot.send_message(m.chat.id,"❌ Forward taqiqlangan!",protect_content=True)
    return
  try:
    bot.send_message(m.chat.id,"✅ Rahmat! Qabul qildik! Usta tez orada siz bilan bog'lanadi!\n📞 +998904432580\n📍 Bugun bepul o'lchovga boramiz!",protect_content=True)
    soz=last_req.get(m.chat.id,"Noma'lum")
    try:
      bot.send_message(ADMIN_ID,f"🔔 YANGI MIJOZ!\n👤 {m.contact.first_name}\n📞 {m.contact.phone_number}\n📝 {soz}\n📍 Buxoro")
      bot.send_contact(ADMIN_ID,m.contact.phone_number,m.contact.first_name)
    except: pass
  except: pass

@bot.message_handler(commands=['start','help'])
def start_cmd(m):
  if m.chat.type!='private' and m.chat.id!=ADMIN_ID:
    return
  markup=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
  markup.add("📸 Bizning ishlar","💡 Namunalar")
  markup.add("📍 Manzil va Telefon","💰 Narxlar")
  markup.add("Darvoza","Panjara","Naves","Kalitka")
  markup.add("Perila","Balkon","Kozyrek","Besedka")
  markup.add("Zinapoya","Topchan","Stol","Stellaj")
  markup.add("Boshqa buyum ✍️")
  bot.send_message(m.chat.id,"Assalomu alaykum! AggaaS Buxoro botiga xush kelibsiz! 👋\n\nQaysi xizmat kerak?\n\n📸 Bizning ishlar - qilgan ishlarimiz\n💡 Namunalar - chiroyli g'oyalar (toza suratlarga)\n💰 Narxlar - narxlar ro'yxati\n\nYoki buyum nomini yozing: masalan darvoza, naves, 3x4 naves",reply_markup=markup,protect_content=True)

@bot.message_handler(func=lambda m: True)
def all_handler(m):
  try:
    if m.chat.type!='private' and m.chat.id!=ADMIN_ID:
      return
    if m.forward_from or m.forward_from_chat:
      bot.send_message(m.chat.id,"❌ Forward taqiqlangan!",protect_content=True)
      return
    lim,wait=is_rate_limited(m.chat.id)
    if lim and wait>0:
      bot.send_message(m.chat.id,f"⏳ {wait} sek kuting!",protect_content=True)
      return
    txt=m.text.lower() if m.text else ""
    original=m.text if m.text else ""
    last_req[m.chat.id]=original

    if "manzil" in txt or "📍" in txt or "telefon" in txt:
      bot.send_message(m.chat.id,"📍 Manzil: Buxoro shahar\n📞 Telefon: +998904432580\n🕘 Ish vaqti: 08:00 - 20:00\n🚚 Bepul o'lchov - Buxoro bo'yicha!",protect_content=True)
      return
    if "narx" in txt or "💰" in txt:
      bot.send_message(m.chat.id,TARIF_MATN,protect_content=True)
      return
    if "bosh menyu" in txt or "🏠" in txt:
      start_cmd(m)
      return

    if "bizning" in txt or "📸" in txt:
      bot.send_message(m.chat.id,"📸 Bizning ishlar - AggaaS Buxoro - kafolat! Biz qilgan haqiqiy ishlar!",protect_content=True)
      files=get_files(["bizning_ish/*.jpg","bizning_ish/*.png","*.jpg"])
      biz=[f for f in files if "bizning_ish" in f]
      other=[f for f in files if "bizning_ish" not in f and "namuna" not in f.lower()]
      final=biz+other
      if final:
        send_photos(m.chat.id,final[:10],first_caption="AggaaS - Sifatli ishlar!",limit=10)
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("💰 Narxlar","🏠 Bosh menyu")
      bot.send_message(m.chat.id,"Yoqgan ish bo'lsa raqamingizni qoldiring!",reply_markup=kb,protect_content=True)
      return

    if "namuna" in txt or "💡" in txt:
      bot.send_message(m.chat.id,"💡 Namunalar - chiroyli g'oyalar! Toza suratlar - mijozlar tanlagan eng zo'r dizaynlar!",protect_content=True)
      files=get_files(["namunalar/*.jpg","namunalar/*.png","*namuna*.jpg"])
      uniq=[]
      seen=set()
      for f in files:
        if f not in seen:
          seen.add(f)
          uniq.append(f)
      if uniq:
        send_photos(m.chat.id,uniq[:10],first_caption="💡 Namunalar - toza suratlarga!",limit=10)
      else:
        bot.send_message(m.chat.id,"💡 Namunalar tez kunda! Raqam qoldiring, tanlab beramiz!",protect_content=True)
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      bot.send_message(m.chat.id,"Qaysi biri yoqdi? Raqam qoldiring, chizib beramiz!",reply_markup=kb,protect_content=True)
      return

    qadam=parse_qadam(txt)
    if qadam or ("zina" in txt and find_service(txt)=="Zinapoya"):
      steps=qadam if qadam else 10
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      jami=steps*TARIF_MAT["Zinapoya"]
      bot.send_message(m.chat.id,f"Zinapoya {steps} qadam\n\nTaxminiy narx: {jami:,} so'm\n\nUsta bepul borib aniq o'lchaydi!",reply_markup=kb,protect_content=True)
      return

    size=parse_size(txt)
    serv=find_service(txt)
    if size:
      a,b,area=size
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      if serv:
        narx=TARIF_MAT.get(serv,TARIF_CUSTOM)
        jami=int(area*narx)
        bot.send_message(m.chat.id,f"{serv} {a} x {b} = {area:.1f} kvadrat\n\nTaxminiy narx: {jami:,} so'm (material bilan)",reply_markup=kb,protect_content=True)
      else:
        jami=int(area*TARIF_CUSTOM)
        bot.send_message(m.chat.id,f"{a} x {b} = {area:.1f} kvadrat\n\nTaxminiy narx: {jami:,} so'm",reply_markup=kb,protect_content=True)
      return

    if serv:
      kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
      kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
      kb.add("🏠 Bosh menyu")
      bot.send_message(m.chat.id,f"{serv} yasaymiz! 👍\nO'lchamini yozing: masalan 3x4 {serv.lower()}\n\nBepul o'lchovga boramiz!",reply_markup=kb,protect_content=True)
      return

    if "boshqa" in txt:
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
