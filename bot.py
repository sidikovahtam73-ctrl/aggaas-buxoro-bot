import telebot, re, os, time, glob
from telebot import types
from collections import defaultdict, deque

# === TOKENNI SHU ERGA YOZING ===
TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
# Masalan: TOKEN = "1234567890:AAHxyz..."

# Agar Render da BOT_TOKEN yozilgan bo'lsa, o'shani ishlatadi
if os.environ.get("BOT_TOKEN"):
    TOKEN = os.environ.get("BOT_TOKEN")
if os.environ.get("TELEGRAM_BOT_TOKEN"):
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not TOKEN or "PASTE_YOUR" in TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! TOKEN o'zgaruvchisiga BotFather dan olingan tokenni yozing!")

bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 123456789

last_req = {}
user_times = defaultdict(lambda: deque())
user_last_msg = {}
blocked_until = {}

RATE_LIMIT_SEC = 1.5
FLOOD_LIMIT = 5
FLOOD_WINDOW = 10
BLOCK_TIME = 60

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
    last = user_last_msg.get(chat_id, 0)
    if now - last < RATE_LIMIT_SEC:
        return True, 0
    user_last_msg[chat_id] = now
    return False, 0

TARIF_MAT = {
    "Darvoza":500000,"Kalitka":450000,"Panjara":400000,"Naves":350000,
    "Kozyrek":350000,"Perila":450000,"Balkon":400000,"Besedka":500000,
    "Stellaj":200000,"Topchan":200000,"Zinapoya":250000,"Stol":200000
}
TARIF_ISH = 150000
TARIF_CUSTOM = 300000

TARIF_MATN = """💰 Material bilan (kelishuvchan):
• Darvoza - 500.000
• Kalitka - 450.000
• Panjara - 400.000
• Naves - 350.000
• Kozyrek - 350.000
• Perila - 450.000
• Balkon - 400.000
• Besedka - 500.000
• Stellaj - 200.000
• Topchan - 200.000
• Stol - 200.000
• Zinapoya - 250.000/qadam
• Boshqa temir buyum - 300.000

💪 Faqat ish haqi: 150.000 dan
📐 Yozing: 3x4 darvoza yoki 2x1 mangal"""

TEMIR_KALITLAR = [
    "mangal","barbekyu","kamin","kazan","tandir","ochoq",
    "krovat","karavot","divan","skameyka","lavochka","orindiq",
    "temir eshik","rom","reshotka","setka",
    "vorota","zabor","tosig","ayvon","soyabon",
    "narvon","lesa","guldon","gulzor","issiqxona",
    "javon","polka","tokcha","shkaf","verstak","parta",
    "qafas","it uyi","tovuq katak","molxona",
    "temir","metall","payvand","kovka","svar"
]

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
    m=re.search(r'(\d+(?:[.,]\d+)?)\s*[xх*]\s*(\d+(?:[.,]\d+)?)', txt)
    if m:
        try:
            a=float(m.group(1).replace(',','.'))
            b=float(m.group(2).replace(',','.'))
            return a,b,a*b
        except: pass
    return None

def parse_qadam(txt):
    m=re.search(r'(\d+)\s*qadam', txt.lower())
    if m:
        return int(m.group(1))
    return None

@bot.message_handler(content_types=['new_chat_members'])
def anti_group(m):
    try:
        if m.chat.type!='private':
            bot.send_message(m.chat.id,"❌ AggaaS faqat shaxsiy chatda ishlaydi!",protect_content=True)
            bot.leave_chat(m.chat.id)
    except: pass

@bot.message_handler(content_types=['contact'])
def contact_handler(m):
    lim,wait=is_rate_limited(m.chat.id)
    if lim:
        if wait>0:
            bot.send_message(m.chat.id,f"⏳ {wait} soniya kuting!",protect_content=True)
        return
    if m.forward_from or m.forward_from_chat:
        bot.send_message(m.chat.id,"❌ Forward mumkin emas!",protect_content=True)
        return
    try:
        bot.send_message(m.chat.id,"✅ Рахмат! Usta tez orada bog'lanadi!\n📞 +998904432580\n📍 Bepul o'lchovga bugun boramiz!",protect_content=True)
        soz=last_req.get(m.chat.id,"Noma'lum")
        try:
            print(f"🔔 YANGI MIJOZ: {m.contact.first_name} {m.contact.phone_number} {soz}")
            if ADMIN_ID and ADMIN_ID != 123456789:
                bot.send_message(ADMIN_ID,f"🔔 YANGI MIJOZ!\n👤 {m.contact.first_name}\n📞 +{m.contact.phone_number}\n📝 {soz}\n📍 Buxoro Uglovoy Park")
                bot.send_contact(ADMIN_ID,m.contact.phone_number,m.contact.first_name)
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)

@bot.message_handler(commands=['start','help'])
def start(m):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚪 Darvoza","🚶 Kalitka","🪟 Panjara")
    kb.add("🏠 Naves","🏖️ Kozyrek","🪜 Perila")
    kb.add("🏢 Balkon","🏡 Besedka","📚 Stellaj")
    kb.add("🛏️ Topchan","🪜 Zinapoya","🪑 Stol")
    kb.add("🔧 Boshqa temir buyum","📸 Bizning ishlar","💰 Narxlar")
    kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
    bot.send_message(m.chat.id,"👋 Salom! AggaaS Buxoro - istalgan temir buyum yasaymiz!\n\nQaysi buyum kerak? Tanlang yoki yozing: 3x4 darvoza, 2x1 mangal, 2x1 krovat\n\n📞 +998904432580\n📍 Buxoro Uglovoy Park",reply_markup=kb,protect_content=True)

@bot.message_handler(content_types=['photo'])
def photo_handler(m):
    lim,wait=is_rate_limited(m.chat.id)
    if lim:
        if wait>0:
            bot.send_message(m.chat.id,f"⏳ {wait} soniya kuting!",protect_content=True)
        return
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
    kb.add("🏠 Bosh menyu")
    bot.send_message(m.chat.id,"✅ Rasm qabul qilindi! Usta ko'rib, narxni aytadi!\n📍 Joy rasmi bo'lsa bepul o'lchovga boramiz!\n📞 Raqam qoldiring!",reply_markup=kb,protect_content=True)

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    try:
        lim,wait=is_rate_limited(m.chat.id)
        if lim:
            if wait>0:
                bot.send_message(m.chat.id,f"⏳ {wait} soniya kuting!",protect_content=True)
            return
        if m.forward_from or m.forward_from_chat:
            bot.send_message(m.chat.id,"❌ Forward mumkin emas!",protect_content=True)
            return
        txt=m.text.lower().strip() if m.text else ""
        original=m.text.strip() if m.text else ""
        last_req[m.chat.id]=original

        if txt in ["salom","assalom","hello","hi","/start"]:
            start(m)
            return
        if txt in ["bosh menyu","🏠 bosh menyu","menu","/help"]:
            start(m)
            return
        if txt in ["narx","narxlar","💰 narxlar","price"]:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,TARIF_MATN,reply_markup=kb,protect_content=True)
            return
        if "bizning ish" in txt or "ishlar" in txt or txt=="📸 bizning ishlar":
            files=get_files(["*.jpg","*.jpeg","*.png","images/*.jpg","images/*.jpeg"])
            if not files:
                kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
                kb.add("🏠 Bosh menyu")
                bot.send_message(m.chat.id,"📸 Tez orada rasmlar!",reply_markup=kb,protect_content=True)
                return
            send_photos(m.chat.id,files[:5],first_caption="Bizning ishlar!",limit=5)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"{len(files)} ta namuna! Tanlang!",reply_markup=kb,protect_content=True)
            return

        # Rasm qidirish
        if any(x in txt for x in ["rasm","foto","surat","ko'rsat","kursat","namuna"]):
            serv=find_service(txt)
            if serv:
                patterns=[f"*{serv.lower()}*.jpg", f"*{serv.lower()}*.jpeg", f"images/*{serv.lower()}*.jpg"]
                files=get_files(patterns)
                if files:
                    send_photos(m.chat.id,files,first_caption=f"{serv} namunalari!",limit=10)
                    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
                    kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
                    kb.add("🏠 Bosh menyu")
                    bot.send_message(m.chat.id,f"{len(files)} ta {serv} namuna! Tanlang!",reply_markup=kb,protect_content=True)
                    return

        serv=find_service(txt)
        size=parse_size(txt)
        qadam=parse_qadam(txt)
        custom=is_custom(txt)

        if serv=="Zinapoya" or (qadam and "zina" in txt):
            steps=qadam if qadam else 1
            if steps>100:
                bot.send_message(m.chat.id,"❌ 100 dan kam yozing!",protect_content=True)
                return
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"✅ Zinapoya\n📐 {steps} qadam\n💰 Material bilan: 250.000/qadam\n💵 Taxminiy: {steps*250000:,}\n❗ Taxminiy, aniq joyida, 3D bilan! Raqam + joy rasmi qoldiring! Bepul!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if size:
            a,b,area=size
            if a>50 or b>50:
                bot.send_message(m.chat.id,"❌ 50m dan kichik yozing!",protect_content=True)
                return
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            if serv:
                narx=TARIF_MAT.get(serv,TARIF_CUSTOM)
                jami=int(area*narx)
                bot.send_message(m.chat.id,f"✅ {serv}\n📐 {a} x {b} = {area:.2f} m²\n💰 Material bilan: {narx:,}/m²\n💵 Taxminiy: {jami:,}\nIsh haqi: {int(area*TARIF_ISH):,}\n❗ Taxminiy! Aniq joyida o'lchab, 3D bilan! Joy rasmi + raqam, bepul boramiz!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
                return
            else:
                jami=int(area*TARIF_CUSTOM)
                if len(original)>=3 and original.lower() not in ["3x4","2x3","salom"]:
                    bot.send_message(m.chat.id,f"✅ {original} ni ham yasaymiz!\n📐 {a} x {b} = {area:.2f} m²\n💰 Taxminiy: {jami:,} (material bilan)\nIsh haqi: {int(area*TARIF_ISH):,}\n❗ Taxminiy, aniq joyida! Joy rasmi + raqam, bepul!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
                else:
                    bot.send_message(m.chat.id,f"📐 {a} x {b} = {area:.2f} m²\nNaves {int(area*350000):,}, Panjara {int(area*400000):,}, Darvoza {int(area*500000):,}, Boshqa {jami:,}\nQaysi buyum? {a}x{b} darvoza yoki {a}x{b} mangal deb yozing! Aniq joyida!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
                return

        if serv:
            narx=TARIF_MAT.get(serv,TARIF_CUSTOM)
            bir="qadamdan" if serv=="Zinapoya" else "m² dan"
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"✅ {serv}\n💰 Material bilan {narx:,}/{bir}\nIsh haqi {TARIF_ISH:,}/{bir}\nO'lcham yozing: 3x4 {serv.lower()}\n❗ Aniq joyida!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if "boshqa" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"✍️ Istalgan temir buyum!\nYozing: mangal, 2x1 temir eshik, 1.5x2 krovat, javon 2x1, skameyka\n💰 300.000/m² dan, ish haqi 150.000 dan\n✅ Hammasini yasaymiz! Bepul o'lchov!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if custom and len(txt)>=2 and txt not in ["salom","assalom","hello","hi","rahmat","ok"]:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"✅ {original} ni ham yasaymiz! 💪\nAggaaS - istalgan temir buyum: Darvoza, Panjara, Naves, Mangal, Kamin, Krovat, Eshik, Reshotka, Skameyka, Javon, Stol, Stellaj\n💰 Material bilan {TARIF_CUSTOM:,} dan\n💪 Ish haqi {TARIF_ISH:,} dan\n📐 O'lcham: 2x1 {original}\n❗ Taxminiy, aniq joyida 3D bilan! Joy rasmi + raqam qoldiring!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if len(txt)>=2:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"✅ {original} ni ham yasaymiz!\nBiz istalgan temir buyumni yasaymiz!\n📐 O'lcham: 3x4 naves yoki 2x1 mangal\n✅ Bepul o'lchov Buxoro, kafolat!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

    except Exception as e:
        print(f"Xato {e}")
        try:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            bot.send_message(m.chat.id,f"✅ {m.text} ni ham yasaymiz! O'lchamini yozing!",reply_markup=kb,protect_content=True)
        except: pass

print("✅ Bot ishga tushdi - AggaaS ideal")
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook tozalandi")
except Exception as e:
    print(f"Webhook xato: {e}")

from flask import Flask
app=Flask(__name__)
@app.route('/')
def home():
    return "AggaaS Buxoro - Ideal - Live"
@app.route('/health')
def health():
    return "OK"

def run_bot():
    while True:
        try:
            print("🤖 Bot polling boshlandi...")
            bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60, skip_pending=True, allowed_updates=["message","callback_query"])
        except Exception as e:
            print(f"⚠️ Bot xato: {e}")
            time.sleep(5)

if __name__=="__main__":
    import threading
    threading.Thread(target=run_bot, daemon=True).start()
    print("✅ IDEAL TOZA - Flask main threadda")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
