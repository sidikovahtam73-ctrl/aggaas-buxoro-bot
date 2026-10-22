import telebot, re, os, time, glob
from telebot import types
from collections import defaultdict, deque

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8979707235

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

# === IDEAL TARIF - NO DUPLICATE ===
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

# NO DUPLICATE - har biri 1 marta
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
            bot.send_message(ADMIN_ID,f"🔔 YANGI MIJOZ!\n👤 {m.contact.first_name}\n📞 +{m.contact.phone_number}\n📝 {soz}\n📍 Buxoro Uglovoy Park")
            bot.send_contact(ADMIN_ID,m.contact.phone_number,m.contact.first_name)
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)

@bot.message_handler(commands=['start','help'])
def start_cmd(m):
    lim,wait=is_rate_limited(m.chat.id)
    if lim:
        if wait>0:
            bot.send_message(m.chat.id,f"⏳ {wait} sek",protect_content=True)
        return
    if m.chat.type!='private' and m.chat.id!=ADMIN_ID:
        return
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    markup.add("📸 Bizning ishlar","💡 Namunalar")
    markup.add("📍 Manzil va Telefon","💰 Narxlar")
    markup.add("Darvoza","Panjara","Naves","Kalitka")
    markup.add("Perila","Balkon","Kozyrek","Besedka")
    markup.add("Zinapoya","Topchan","Stol","Stellaj")
    markup.add("Boshqa buyum ✍️")

    try:
        for logo in ["AggaaS_logo_cutout.png","logo.png"]:
            if os.path.exists(logo):
                with open(logo,'rb') as f:
                    bot.send_photo(m.chat.id,f,protect_content=True)
                break
    except: pass

    txt="""Assalomu Alaykum! *AggaaS* oilaviy ustaxonaga xush kelibsiz!

*AggaaS - Oila nomidan sifatga javob beramiz!*
Oila a'zolari ismi bosh harflari - shuning uchun har ishni o'z uyimizga qilgandek halol bajaramiz.

📍 Buxoro, Uglovoy, Park
📞 +998904432580
🕒 08:00-20:00
✅ Bepul o'lchov Buxoro bo'yicha
✅ Kafolat
✅ Materialni birga bozordan tanlaymiz

🔨 12 asosiy + istalgan temir buyum!
Mangal, krovat, eshik, reshotka, skameyka, javon - hammasini yasaymiz!

Yozing: 3x4 naves yoki 2x1 mangal"""
    bot.send_message(m.chat.id,txt,parse_mode="Markdown",reply_markup=markup,protect_content=True)

@bot.message_handler(commands=['olx'])
def olx_cmd(m):
    bot.send_message(m.chat.id,"""OLX uchun e'lon:

Sarlavha: AggaaS - Buxoroda Naves, Darvoza, Panjara, Mangal - oilaviy ustaxona

Matn:
AggaaS - Oilaviy temirchilik. Buxoro Uglovoy Park.
Nomimiz oila a'zolarimiz ismidan - halol ishlaymiz.

Yasaymiz:
Naves, kozyrek, besedka, darvoza, kalitka, panjara, perila, balkon, zinapoya, topchan, stellaj, stol, mangal, kamin, krovat, temir eshik, reshotka, skameyka, javon va boshqa istalgan temir buyum

Narx material bilan 200-500 ming/m2. Ish haqi 150 mingdan.
Materialni birga bozordan olamiz. O'lchov bepul! Kafolat bor!

Bot: @AggaaS_Bukhara_bot
Tel: +998904432580""",protect_content=True)

@bot.message_handler(commands=['instagram','insta'])
def insta_cmd(m):
    bot.send_message(m.chat.id,"""Instagram shapka:

AggaaS | Oilaviy ustaxona Buxoro
Naves•Darvoza•Mangal•Panjara
Oila nomidan sifatga javob!
Bepul o'lchov Botda hisob

#aggaas #buxoro #naves #darvoza #mangal""",protect_content=True)

@bot.message_handler(func=lambda m: True, content_types=['text'])
def all_msg(m):
    lim,wait=is_rate_limited(m.chat.id)
    if lim:
        if wait>0:
            bot.send_message(m.chat.id,f"⏳ Ko'p xabar! {wait} sek kuting!",protect_content=True)
        return
    if m.forward_from or m.forward_from_chat:
        bot.send_message(m.chat.id,"❌ Forward taqiqlangan!",protect_content=True)
        return
    if m.chat.type!='private' and m.chat.id!=ADMIN_ID:
        return
    if len(m.text)>500:
        bot.send_message(m.chat.id,"❌ Juda uzun! Qisqaroq yozing!",protect_content=True)
        return
    try:
        original=m.text.strip()
        txt=original.lower()
        last_req[m.chat.id]=original

        if "manzil" in txt or "📍" in txt or "adres" in txt or "qayer" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("📸 Bizning ishlar","💡 Namunalar","💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,"📍 Buxoro, Uglovoy, Park\n📞 +998904432580\n🕒 08:00-20:00\n✅ Bepul o'lchov\n✅ Kafolat\n✅ Materialni birga olamiz\n✅ Oila nomidan sifat!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if "material" in txt or "truba" in txt or "polikarbonat" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,"🔩 Materialni birga bozordan tanlaymiz! Sifatli profildan.\nRo'yxat bera olmaymiz, joy qiyshiq bo'lsa o'zgaradi.\n📞 Raqam qoldiring, bepul borib, 3D ko'rsatamiz!\nBepul o'lchov, majburiyat yo'q!",reply_markup=kb,protect_content=True)
            return

        if "kafolat" in txt or "garant" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,"✅ Kafolat beramiz! Mustahkam, chiroyli!\nAggaaS - oila nomi, yomon ish qilmaymiz!\nRaqam qoldiring!",reply_markup=kb,protect_content=True)
            return

        if "zamer" in txt or "o'lchov" in txt or "bepul" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,"📏 Bepul o'lchov! Buxoro bo'yicha usta boradi!\n✅ O'lchov bepul\n✅ Maslahat bepul\n✅ 3D bepul\n✅ Majburiyat yo'q!\nFaqat raqam qoldiring!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if "narx" in txt or "qancha" in txt or "necha pul" in txt or "💰" in txt or "pul" in txt:
            serv=find_service(txt)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            if serv:
                narx=TARIF_MAT.get(serv, TARIF_CUSTOM)
                bir="qadamdan" if serv=="Zinapoya" else "m² dan"
                bot.send_message(m.chat.id,f"💰 {serv}\nMaterial bilan: {narx:,} so'm/{bir}\nIsh haqi: {TARIF_ISH:,}/{bir}\nO'lcham yozing: 3x4 {serv.lower()}\n❗ Taxminiy. Joy qiyshiq bo'lsa o'zgaradi. Aniq narx uchun raqam + joy rasmi, bepul boramiz!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            else:
                if is_custom(txt) and len(txt)>4 and txt not in ["narx","qancha","narxlar"]:
                    bot.send_message(m.chat.id,f"💰 {original} uchun:\nMaterial bilan: {TARIF_CUSTOM:,} dan\nIsh haqi: {TARIF_ISH:,} dan\nO'lcham yozing: 2x1 {original}\n❗ Taxminiy, aniq joyida!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
                    bot.send_message(m.chat.id,TARIF_MATN,parse_mode="Markdown",reply_markup=kb,protect_content=True)
                else:
                    bot.send_message(m.chat.id,TARIF_MATN,parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if "bosh menyu" in txt or "🏠" in txt:
            start_cmd(m)
            return

        if "bizning" in txt or "📸" in txt:
            bot.send_message(m.chat.id,"📸 Bizning ishlar - AggaaS Buxoro - kafolat!",protect_content=True)
            files=get_files(["bizning_ish_new_*.jpg","enhanced_*.jpg","bizning_*.jpg"])
            send_photos(m.chat.id,files,limit=10)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("💡 Namunalar","💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"Jami {len(files)} ta ish! Bepul o'lchov uchun raqam qoldiring!",reply_markup=kb,protect_content=True)
            return

        if "namuna" in txt or "💡" in txt:
            bot.send_message(m.chat.id,"💡 Siz xohlagan dizaynda yasab beramiz!",protect_content=True)
            files=get_files(["final_namuna_*.jpg","namuna_*.jpg","image_*_final.jpg"])
            send_photos(m.chat.id,files,first_caption="Xuddi shunday dizaynda!",limit=15)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("📸 Bizning ishlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"{len(files)} ta namuna! Tanlang!",reply_markup=kb,protect_content=True)
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

print("✅ Bot ishga tushdi - AggaaS ideal - barcha biznes reja")
from flask import Flask
app=Flask(__name__)
@app.route('/')
def home():
    return "AggaaS Buxoro - Ideal - Oila nomidan sifat - ID 8979707235"
if __name__=="__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))).start()
    print("✅ IDEAL TOZA - BIZNES REJA")
    bot.infinity_polling(none_stop=True,timeout=60,long_polling_timeout=60)
