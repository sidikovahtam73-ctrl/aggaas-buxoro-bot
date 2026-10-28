
import os, re, time, glob, threading
from collections import defaultdict, deque
import telebot
from telebot import types
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8979707235
bot = telebot.TeleBot(TOKEN)

FLOOD_LIMIT = 20
FLOOD_WINDOW = 10
user_times = defaultdict(deque)
blocked_until = {}
last_req = {}
mijozlar_soni = 0
shogirdlar_soni = 0

def is_rate_limited(chat_id):
    now = time.time()
    if chat_id in blocked_until and now < blocked_until[chat_id]:
        return True, int(blocked_until[chat_id] - now)
    dq = user_times[chat_id]
    dq.append(now)
    while dq and now - dq[0] > FLOOD_WINDOW:
        dq.popleft()
    if len(dq) > FLOOD_LIMIT:
        blocked_until[chat_id] = now + 10
        return True, 10
    return False, 0

TARIF_MAT = {
    "Darvoza": 500000, "Kalitka": 450000, "Panjara": 400000, "Naves": 350000,
    "Kozyrek": 350000, "Perila": 450000, "Balkon": 400000, "Besedka": 500000,
    "Stellaj": 200000, "Topchan": 200000, "Zinapoya": 250000, "Stol": 200000,
}
TARIF_CUSTOM = 300000

TARIF_MATN = """Narxlar (material bilan):
- Darvoza - 500 mingdan m2
- Kalitka - 450 mingdan
- Panjara - 400 mingdan
- Naves - 350 mingdan
- Kozyrek - 350 mingdan
- Perila - 450 mingdan
- Balkon - 400 mingdan
- Besedka - 500 mingdan
- Stellaj - 200 mingdan
- Topchan - 200 mingdan
- Stol - 200 mingdan
- Zinapoya - 250 mingdan 1 qadam
- Mangal, krovat, eshik, reshotka - 300 mingdan
O'lchamni yozing: 3x4 naves
Bepul o'lchov - Buxoro bo'yicha!"""

TEMIR_KALITLAR = ["mangal","barbekyu","kamin","kazan","tandir","ochoq","krovat",
"karavot","divan","skameyka","lavochka","orindiq","temir eshik","rom","reshotka",
"setka","vorota","zabor","tosig","ayvon","soyabon","narvon","lesa","guldon",
"gulzor","issiqxona","javon","polka","tokcha","shkaf","verstak","parta","qafas",
"it uyi","tovuq katak","molxona","temir","metall","payvand","kovka","svar","pechka"]

def contact_kb(narx_bilan=True):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("Raqam qoldirish", request_contact=True))
    if narx_bilan:
        kb.add("Narxlar", "Bosh menyu")
    else:
        kb.add("Bosh menyu")
    return kb

def get_files(patterns):
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    files.extend(glob.glob("*.jpg"))
    files.extend(glob.glob("*.jpeg"))
    files.extend(glob.glob("*.png"))
    uniq, seen = [], set()
    for f in files:
        if os.path.exists(f) and f not in seen:
            seen.add(f)
            uniq.append(f)
    return sorted(uniq)

def send_photos(chat_id, file_list, first_caption=None, limit=10):
    cnt = 0
    for fname in file_list[:limit]:
        try:
            if os.path.exists(fname):
                with open(fname, "rb") as f:
                    cap = first_caption if (first_caption and cnt == 0) else None
                    bot.send_photo(chat_id, f, caption=cap, protect_content=True)
                cnt += 1
                time.sleep(0.3)
        except Exception as e:
            print(f"Rasm xato {fname}: {e}")

def find_service(txt):
    t = txt.lower()
    if "zina" in t: return "Zinapoya"
    if "topchan" in t or "tapchan" in t: return "Topchan"
    if "stol" in t: return "Stol"
    if "darvoza" in t or "vorota" in t: return "Darvoza"
    if "kalitka" in t: return "Kalitka"
    if "panjara" in t or "panj" in t or "zabor" in t or "reshotka" in t: return "Panjara"
    if "naves" in t: return "Naves"
    if "kozyrek" in t or "kazirek" in t: return "Kozyrek"
    if "perila" in t: return "Perila"
    if "balkon" in t: return "Balkon"
    if "besedka" in t: return "Besedka"
    if "stellaj" in t: return "Stellaj"
    return None

def is_custom(txt):
    t = txt.lower()
    return any(k in t for k in TEMIR_KALITLAR) or len(t.strip()) >= 3

def parse_size(txt):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*[xх*]\s*(\d+(?:[.,]\d+)?)", txt)
    if m:
        try:
            a = float(m.group(1).replace(",", "."))
            b = float(m.group(2).replace(",", "."))
            return a, b, a * b
        except ValueError:
            pass
    return None

def parse_qadam(txt):
    m = re.search(r"(\d+)\s*qadam", txt.lower())
    return int(m.group(1)) if m else None

@bot.message_handler(commands=["start", "help"])
def start_cmd(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Bizning ishlar", "Namunalar")
    markup.add("Manzil va Telefon", "Narxlar")
    markup.add("Darvoza", "Panjara", "Naves", "Kalitka")
    markup.add("Perila", "Balkon", "Kozyrek", "Besedka")
    markup.add("Zinapoya", "Topchan", "Stol", "Stellaj")
    markup.add("Boshqa buyum")
    markup.add("Shogird olish")
    bot.send_message(m.chat.id,
        "Assalomu alaykum! AggaaS Buxoro botiga xush kelibsiz!\n\n"
        "Qaysi xizmat kerak?\n\n"
        "Bizning ishlar - qilgan ishlarimiz\n"
        "Namunalar - chiroyli g'oyalar\n"
        "Narxlar - narxlar ro'yxati\n"
        "Shogird olish - ustaxona uchun shogird\n\n"
        "Yoki buyum nomini yozing: masalan darvoza, naves, 3x4 naves",
        reply_markup=markup, protect_content=True)

@bot.message_handler(commands=["stat"])
def stat_cmd(m):
    if m.chat.id != ADMIN_ID:
        return
    bot.send_message(m.chat.id, f"Statistika:\nMijozlar: {mijozlar_soni}\nShogirdlar: {shogirdlar_soni}")

@bot.message_handler(func=lambda m: m.text and "shogird" in m.text.lower())
def shogird_handler(m):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Raqamimni yuborish", request_contact=True))
    markup.add("Bosh menyu")
    bot.send_message(m.chat.id,
        "AGGAAS USTAXONASI SHOGIRD QABUL QILADI!\n\n"
        "Yosh: 18-35 yosh\n"
        "Joy: Buxoro shahri\n"
        "Maosh: Ishga qarab kelishiladi\n"
        "Tajriba: Shart emas, o'rgatamiz!\n\n"
        "Qiziqsangiz, pastdagi tugmani bosib raqamingizni yuboring.\n"
        "Biz siz bilan bog'lanamiz!",
        reply_markup=markup, protect_content=True)

@bot.message_handler(content_types=["contact"])
def contact_handler(m):
    global mijozlar_soni, shogirdlar_soni
    lim, wait = is_rate_limited(m.chat.id)
    if lim and wait > 0:
        bot.send_message(m.chat.id, f"{wait} sek kuting!", protect_content=True)
        return
    try:
        soz = last_req.get(m.chat.id, "Noma'lum")
        if "shogird" in soz.lower():
            shogirdlar_soni += 1
            bot.send_message(m.chat.id,
                "Rahmat! Shogirdlik arizangiz qabul qilindi! Usta tez orada siz bilan bog'lanadi!\n"
                "+998904432580", protect_content=True)
            bot.send_message(ADMIN_ID,
                f"YANGI SHOGIRD #{shogirdlar_soni}!\n"
                f"{m.contact.first_name}\n{m.contact.phone_number}\n"
                f"Buxoro")
        else:
            mijozlar_soni += 1
            bot.send_message(m.chat.id,
                "Rahmat! Qabul qildik! Usta tez orada siz bilan bog'lanadi!\n"
                "+998904432580\nBugun bepul o'lchovga boramiz!", protect_content=True)
            bot.send_message(ADMIN_ID,
                f"YANGI MIJOZ #{mijozlar_soni}!\n"
                f"{m.contact.first_name}\n{m.contact.phone_number}\n"
                f"{soz}\nBuxoro")
        bot.send_contact(ADMIN_ID, m.contact.phone_number, m.contact.first_name)
    except Exception as e:
        print("Contact xato:", e)

@bot.message_handler(func=lambda m: True)
def all_handler(m):
    try:
        if m.chat.type != "private" and m.chat.id != ADMIN_ID:
            return
        lim, wait = is_rate_limited(m.chat.id)
        if lim and wait > 0:
            bot.send_message(m.chat.id, f"{wait} sek kuting!", protect_content=True)
            return

        txt = m.text.lower() if m.text else ""
        original = m.text if m.text else ""
        last_req[m.chat.id] = original

        if "manzil" in txt or "telefon" in txt:
            bot.send_message(m.chat.id,
                "Manzil: Buxoro shahar\nTelefon: +998904432580\n"
                "Ish vaqti: 08:00 - 20:00\nBepul o'lchov - Buxoro bo'yicha!",
                protect_content=True)
            return
        if "narx" in txt:
            bot.send_message(m.chat.id, TARIF_MATN, protect_content=True)
            return
        if "bosh menyu" in txt:
            start_cmd(m)
            return

        if "bizning" in txt:
            bot.send_message(m.chat.id, "Bizning ishlar - AggaaS Buxoro!", protect_content=True)
            final = get_files(["*.jpg", "*.png", "*.jpeg"])
            if final:
                send_photos(m.chat.id, final, first_caption="AggaaS - Sifatli ishlar!")
            bot.send_message(m.chat.id, "Yoqgan ish bo'lsa raqamingizni qoldiring!",
                reply_markup=contact_kb(narx_bilan=True), protect_content=True)
            return

        if "namuna" in txt:
            bot.send_message(m.chat.id, "Namunalar - chiroyli g'oyalar!", protect_content=True)
            final = get_files(["*.jpg", "*.png", "*.jpeg"])
            if final:
                send_photos(m.chat.id, final, first_caption="Namunalar!")
            else:
                bot.send_message(m.chat.id, "Namunalar tez kunda!", protect_content=True)
            bot.send_message(m.chat.id, "Qaysi biri yoqdi? Raqam qoldiring!",
                reply_markup=contact_kb(narx_bilan=False), protect_content=True)
            return

        qadam = parse_qadam(txt)
        if qadam or ("zina" in txt and find_service(txt) == "Zinapoya"):
            steps = qadam if qadam else 10
            jami = steps * TARIF_MAT["Zinapoya"]
            bot.send_message(m.chat.id,
                f"Zinapoya {steps} qadam\n\nTaxminiy narx: {jami:,} so'm\n\n"
                "Usta bepul borib aniq o'lchaydi!",
                reply_markup=contact_kb(narx_bilan=False), protect_content=True)
            return

        size = parse_size(txt)
        serv = find_service(txt)
        if size:
            a, b, area = size
            narx = TARIF_MAT.get(serv, TARIF_CUSTOM) if serv else TARIF_CUSTOM
            jami = int(area * narx)
            nom = serv if serv else "Buyum"
            bot.send_message(m.chat.id,
                f"{nom} {a} x {b} = {area:.1f} kvadrat\n\n"
                f"Taxminiy narx: {jami:,} so'm (material bilan)",
                reply_markup=contact_kb(narx_bilan=False), protect_content=True)
            return

        if serv:
            bot.send_message(m.chat.id,
                f"{serv} yasaymiz!\nO'lchamini yozing: masalan 3x4 {serv.lower()}\n\n"
                "Bepul o'lchovga boramiz!",
                reply_markup=contact_kb(narx_bilan=False), protect_content=True)
            return

        if "boshqa" in txt:
            bot.send_message(m.chat.id,
                "Istalgan temir buyum yasaymiz!\n\n"
                "Mangal, krovat, eshik, reshotka, skameyka, javon, stol - hammasini!",
                reply_markup=contact_kb(narx_bilan=False), protect_content=True)
            return

        if is_custom(txt) and len(txt) >= 3:
            bot.send_message(m.chat.id,
                f"{original} ni yasaymiz! Ha, bo'ladi!\n"
                f"O'lchamini yozing: 2x1 {original}\n"
                "Raqam qoldirsangiz usta bepul borib ko'radi!",
                reply_markup=contact_kb(narx_bilan=True), protect_content=True)
            return

        bot.send_message(m.chat.id,
            f"Tushundim! {original}\nO'lchamini yozing: masalan 3x4 {original.lower()}\n"
            "Yoki raqam qoldiring, usta bepul borib ko'radi!",
            reply_markup=contact_kb(narx_bilan=True), protect_content=True)
    except Exception as e:
        print("Xato:", e)

app = Flask(__name__)

@app.route("/")
def home():
    return "AggaaS Buxoro - Live"

@app.route("/health")
def health():
    return "OK"

def run_bot():
    while True:
        try:
            bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print("Polling xato:", e)
            time.sleep(5)

if __name__ == "__main__":
    print("Bot ishga tushdi - AggaaS Buxoro")
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
