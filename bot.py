x = TARIF_MAT.get(serv, TARIF_CUSTOM) if serv else TARIF_CUSTOM
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
