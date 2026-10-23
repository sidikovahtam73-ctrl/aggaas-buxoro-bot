import telebot, re, os, time, glob
from telebot import types
from collections import defaultdict, deque

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "8980986366:AAGjew-L_kVH_BJH5UdLJVYr5W8fGGlKCVc"
if not TOKEN or "PASTE_YOUR" in TOKEN:
    TOKEN = "8980986366:AAGjew-L_kVH_BJH5UdLJVYr5W8fGGlKCVc"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8979707235  # Sizning ID - 8979707235

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

TEMIR_KALITLAR = [
    "mangal","barbekyu","kamin","kazan","tandir","ochoq",
    "krovat","karavot","divan","skameyka","lavochka","orindiq",
    "temir eshik","rom","reshotka","setka",
    "vorota","zabor","tosig","ayvon","soyabon",
    "narvon","lesa","guldon","gulzor","issiqxona",
    "javon","polka","tokcha","shkaf","verstak","parta",
    "qafas","it uyi","tovuq katak","molxona",
    "temir","metall","payvand","kovka","svar","pechka"
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
            bot.send_message(m.chat.id,"❌ Bu bot faqat shaxsiy chatda ishlaydi!",protect_content=True)
            bot.leave_chat(m.chat.id)
    except: pass

@bot.message_handler(content_types=['contact'])
def contact_handler(m):
    lim,wait=is_rate_limited(m.chat.id)
    if lim:
        if wait>0:
            bot.send_message(m.chat.id,f"⏳ {wait} sek kuting!",protect_content=True)
        return
    if m.forward_from or m.forward_from_chat:
        bot.send_message(m.chat.id,"❌ Forward taqiqlangan!",protect_content=True)
        return
    try:
        bot.send_message(m.chat.id,"✅ Rahmat! Qabul qildik! Usta tez orada siz bilan bog'lanadi!\n📞 +998904432580\n📍 Bugun bepul o'lchovga boramiz!",protect_content=True)
        soz=last_req.get(m.chat.id,"Noma'lum")
        try:
            print(f"🔔 YANGI MIJOZ: {m.contact.first_name} {m.contact.phone_number} {soz}")
            bot.send_message(ADMIN_ID,f"🔔 YANGI MIJOZ!\n👤 {m.contact.first_name}\n📞 {m.contact.phone_number}\n📝 {soz}\n📍 Buxoro")
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

        # === TUZATILDI: Salom, rahmat kabi so'zlar ===
        if txt in ["salom","assalom","assalomu alaykum","salom alaykum","hello","hi","привет","salom aka","assalom aka"]:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
            kb.add("📸 Bizning ishlar","💰 Narxlar")
            kb.add("📍 Manzil va Telefon","🏠 Bosh menyu")
            bot.send_message(m.chat.id,"Va alaykum assalom aka! 👋\n\nAggaaS ustaxona - Buxoro, Uglovoy Park\nNima yasab beraylik?\nO'lchamni yozing: 3x4 darvoza",reply_markup=kb,protect_content=True)
            return
        if txt in ["rahmat","raxmat","rahmat aka","thanks","thank you","спасибо","ok","xo'p","xop","tushunarli","yaxshi","yaxshi rahmat","rahmat kattakon"]:
            bot.send_message(m.chat.id,"Arzimaydi aka! 👍\nYana buyurtma bo'lsa yozing!\n📞 +998904432580\nBepul o'lchovga boramiz!",protect_content=True)
            return

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
                bir="qadamdan" if serv=="Zinapoya" else "m2 dan"
                bot.send_message(m.chat.id,f"💰 {serv}\nMaterial bilan: {narx:,} so'm/{bir}\nIsh haqi: {TARIF_ISH:,}/{bir}\nO'lcham yozing: 3x4 {serv.lower()}\nAnıq narx uchun raqam + joy rasmi, bepul boramiz!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
            else:
                if is_custom(txt) and len(txt)>4 and txt not in ["narx","qancha","narxlar"]:
                    bot.send_message(m.chat.id,f"💰 {original} uchun:\nMaterial bilan: {TARIF_CUSTOM:,} dan\nIsh haqi: {TARIF_ISH:,} dan\nO'lcham yozing: 2x1 {original}\nAniq narx usta borib aytadi!",parse_mode="Markdown",reply_markup=kb,protect_content=True)
                    bot.send_message(m.chat.id,TARIF_MATN,parse_mode="Markdown",reply_markup=kb,protect_content=True)
                else:
                    bot.send_message(m.chat.id,TARIF_MATN,parse_mode="Markdown",reply_markup=kb,protect_content=True)
            return

        if "bosh menyu" in txt or "🏠" in txt:
            start_cmd(m)
            return

        if "bizning" in txt or "📸" in txt:
            bot.send_message(m.chat.id,"📸 Bizning ishlar - AggaaS Buxoro - kafolat!",protect_content=True)
            files=get_files(["*.jpg","*.png","images/*.jpg","photo/*.jpg","*AggaaS*.jpg"])
            if files:
                send_photos(m.chat.id,files[:8],first_caption="AggaaS - Sifatli ishlar!",limit=8)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,"Yoqgan ish bo'lsa raqamingizni qoldiring! Usta bepul borib ko'radi!",reply_markup=kb,protect_content=True)
            return

        if "namuna" in txt or "💡" in txt:
            bot.send_message(m.chat.id,"💡 Namunalar - chiroyli g'oyalar!",protect_content=True)
            files=get_files(["*namuna*.jpg","*naves*.jpg","*darvoza*.jpg","*.jpg"])
            if files:
                send_photos(m.chat.id,files[:8],limit=8)
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,"Qaysi biri yoqdi? Raqam qoldiring!",reply_markup=kb,protect_content=True)
            return

        # Qadam
        qadam=parse_qadam(txt)
        if qadam or ("zina" in txt and find_service(txt)=="Zinapoya"):
            steps=qadam if qadam else 10
            if steps>100:
                bot.send_message(m.chat.id,"❌ Juda ko'p! 100 dan kam yozing!",protect_content=True)
                return
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            jami=steps*TARIF_MAT["Zinapoya"]
            bot.send_message(m.chat.id,f"Zinapoya {steps} qadam\n\nTaxminiy narx material bilan: {jami:,} so'm\n\nUsta bepul borib aniq o'lchaydi! Raqam qoldiring!",reply_markup=kb,protect_content=True)
            return

        # Hajm
        size=parse_size(txt)
        serv=find_service(txt)
        if size:
            a,b,area=size
            if a>50 or b>50:
                bot.send_message(m.chat.id,"❌ Juda katta! 50 metrdan kichik yozing!",protect_content=True)
                return
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            if serv:
                narx=TARIF_MAT.get(serv,TARIF_CUSTOM)
                jami=int(area*narx)
                bot.send_message(m.chat.id,f"{serv} {a} x {b} = {area:.1f} kvadrat\n\nTaxminiy narx: {jami:,} so'm (material bilan)\n\nBu taxminiy narx. Usta borib aniq aytadi! Bepul o'lchov!",reply_markup=kb,protect_content=True)
            else:
                jami=int(area*TARIF_CUSTOM)
                bot.send_message(m.chat.id,f"{a} x {b} = {area:.1f} kvadrat\n\nTaxminiy narx: {jami:,} so'm atrofida\nQaysi buyum ekanini yozing: masalan {a}x{b} darvoza\n\nUsta bepul boradi!",reply_markup=kb,protect_content=True)
            return

        if serv:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"{serv} yasaymiz! 👍\n\nO'lchamini yozing: masalan 3x4 {serv.lower()}\n\nBepul o'lchovga boramiz!",reply_markup=kb,protect_content=True)
            return

        if "boshqa" in txt:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("🏠 Bosh menyu")
            bot.send_message(m.chat.id,"Istalgan temir buyum yasaymiz! 💪\n\nMangal, krovat, eshik, reshotka, skameyka, javon, stol - hammasini!\n\nNima kerakligini yozing: masalan 2x1 mangal\nBepul borib ko'ramiz!",reply_markup=kb,protect_content=True)
            return

        if is_custom(txt) and len(txt)>=3:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            kb.add("💰 Narxlar","🏠 Bosh menyu")
            bot.send_message(m.chat.id,f"{original} ni yasaymiz! Ha, bo'ladi! 👍\n\nO'lchamini yozing: 2x1 {original}\n\nRaqam qoldirsangiz usta bepul borib ko'radi!",reply_markup=kb,protect_content=True)
            return

        # Fallback - tushunarsiz bo'lsa ham chala gap emas, to'g'ri yo'naltirish
        kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
        kb.add("💰 Narxlar","🏠 Bosh menyu")
        bot.send_message(m.chat.id,f"Tushundim aka! {original} 👍\n\nO'lchamini yozing: masalan 3x4 {original.lower()}\nYoki raqam qoldiring, usta bepul borib ko'radi!",reply_markup=kb,protect_content=True)

    except Exception as e:
        print(f"Xato {e}")
        try:
            kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(types.KeyboardButton("📞 Raqam qoldirish",request_contact=True))
            bot.send_message(m.chat.id,f"{m.text} ni yasaymiz! O'lchamini yozing!",reply_markup=kb,protect_content=True)
        except: pass

print("✅ Bot ishga tushdi - AggaaS ideal - barcha biznes reja")
try:
    bot.remove_webhook()
    time.sleep(1)
    bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook tozalandi")
except Exception as e:
    print(f"Webhook xato (e'tiborsiz): {e}")

from flask import Flask
app=Flask(__name__)
@app.route('/')
def home():
    return "AggaaS Buxoro - Ideal - Live - ID 8979707235"
@app.route('/health')
def health():
    return "OK"

def run_bot():
    while True:
        try:
            print("🤖 Bot polling boshlandi...")
            bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60, skip_pending=True, allowed_updates=["message","callback_query"])
        except Exception as e:
            print(f"⚠️ Bot xato, qayta ishga tushmoqda: {e}")
            time.sleep(5)

if __name__=="__main__":
    import threading
    threading.Thread(target=run_bot, daemon=True).start()
    print("✅ IDEAL TOZA - BIZNES REJA - Flask main threadda")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
