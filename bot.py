import os, json, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
BOT_TOKEN=os.getenv("BOT_TOKEN","").strip()
ADMIN_ID=int(os.getenv("ADMIN_ID","8863357122"))
STORE_NAME=os.getenv("STORE_NAME","Habesha Game Store")
TELEBIRR_PHONE=os.getenv("TELEBIRR_PHONE","0906869740")
TELEBIRR_NAME=os.getenv("TELEBIRR_NAME","Tekalegn Tarku")
CBE_ACCOUNT=os.getenv("CBE_ACCOUNT","1000670104994")
CBE_NAME=os.getenv("CBE_NAME","Mr. Melaku Mesay")
PACKAGES=[("60 UC",180),("120 UC",380),("180 UC",550),("325 UC",880),("385 UC",1100),("660 UC",1750),("720 UC",1950),("780 UC",2150),("985 UC",2750),("1800 UC",4450),("2125 UC",5400),("3850 UC",9000)]
ORDERS_FILE="orders.json"
states={}

def keyboard(rows): return InlineKeyboardMarkup(rows)
def menu(): return keyboard([[InlineKeyboardButton("🎮 PUBG UC ግዛ",callback_data="buy")],[InlineKeyboardButton("ℹ️ እገዛ",callback_data="help")]])
def packages_menu():
    rows=[[InlineKeyboardButton(f"💎 {p} — {v:,} ብር",callback_data=f"pkg:{i}")] for i,(p,v) in enumerate(PACKAGES)]
    rows.append([InlineKeyboardButton("⬅️ መነሻ",callback_data="home")])
    return keyboard(rows)

def save_order(o):
    data=[]
    try:
        with open(ORDERS_FILE,encoding="utf-8") as f: data=json.load(f)
    except (OSError,ValueError): pass
    data.append(o)
    with open(ORDERS_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎮 እንኳን ወደ {STORE_NAME} በደህና መጡ!\nየPUBG UC ፓኬጅ ለመግዛት ከታች ይምረጡ።",reply_markup=menu())

async def buttons(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); uid=q.from_user.id; d=q.data
    if d=="home": await q.edit_message_text(f"🎮 {STORE_NAME}",reply_markup=menu())
    elif d=="buy": await q.edit_message_text("የሚፈልጉትን UC ፓኬጅ ይምረጡ፦",reply_markup=packages_menu())
    elif d=="help": await q.edit_message_text("ለእገዛ ከAdmin ጋር ይገናኙ። ክፍያ ከመፈጸምዎ በፊት ዋጋውን ያረጋግጡ።",reply_markup=keyboard([[InlineKeyboardButton("⬅️ መነሻ",callback_data="home")]]))
    elif d.startswith("pkg:"):
        i=int(d.split(":")[1]); p,v=PACKAGES[i]
        states[uid]={"package":p,"price":v,"step":"id"}
        await q.edit_message_text(f"መርጠዋል: {p} — {v:,} ብር\nPUBG Player ID ይላኩ። የይለፍ ቃል አያስፈልግም።")
    elif d.startswith("pay:"):
        s=states.get(uid,{})
        if s.get("step")!="pay": await q.edit_message_text("ትዕዛዙ አልተገኘም። /start ይጫኑ።"); return
        s["method"]=d.split(":")[1]; s["step"]="receipt"
        details=f"Telebirr: {TELEBIRR_PHONE}\nስም: {TELEBIRR_NAME}" if s["method"]=="Telebirr" else f"CBE: {CBE_ACCOUNT}\nስም: {CBE_NAME}"
        await q.edit_message_text(f"💳 የክፍያ መረጃ\n{details}\nትዕዛዝ: {s['order']}\n{s['package']} — {s['price']:,} ብር\nክፍያ ከፈጸሙ በኋላ የደረሰኝ ፎቶ ይላኩ።")

async def text(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user; s=states.get(u.id)
    if not s: await update.message.reply_text("ለመጀመር /start ይጫኑ።"); return
    if s["step"]=="id":
        pid=update.message.text.strip()
        if not pid.isdigit() or len(pid)<5: await update.message.reply_text("ትክክለኛ PUBG Player ID ቁጥር ይላኩ።"); return
        s["player_id"]=pid; s["step"]="pay"; s["order"]=f"HG{datetime.now():%y%m%d%H%M%S}{u.id%1000:03d}"
        await update.message.reply_text(f"ትዕዛዝ: {s['order']}\nPUBG ID: {pid}\n{s['package']} — {s['price']:,} ብር\nየክፍያ ዘዴ ይምረጡ፦",reply_markup=keyboard([[InlineKeyboardButton("📱 Telebirr",callback_data="pay:Telebirr")],[InlineKeyboardButton("🏦 CBE Birr / CBE",callback_data="pay:CBE")]]))
    elif s["step"]=="receipt": await update.message.reply_text("እባክዎ የክፍያ ደረሰኝ ፎቶ ይላኩ።")

async def photo(update:Update,context:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user; s=states.get(u.id)
    if not s or s.get("step")!="receipt": await update.message.reply_text("መጀመሪያ /start በማለት ትዕዛዝ ይጀምሩ።"); return
    o={"order":s["order"],"user_id":u.id,"username":u.username,"player_id":s["player_id"],"package":s["package"],"price":s["price"],"payment":s["method"],"status":"receipt_submitted","created_at":datetime.now().isoformat()}
    save_order(o)
    await update.message.reply_text("✅ ደረሰኙ ተቀብሏል። Admin ክፍያውን በሂሳቡ ላይ ካረጋገጠ በኋላ ይቀጥላል።")
    try:
        await context.bot.send_message(ADMIN_ID,f"🆕 ትዕዛዝ {s['order']}\nUser ID: {u.id}\nPUBG ID: {s['player_id']}\n{s['package']} — {s['price']:,} ብር\nክፍያ: {s['method']}")
        await context.bot.send_photo(ADMIN_ID,update.message.photo[-1].file_id,caption=f"ደረሰኝ {s['order']}")
    except Exception: logging.exception("Admin notification failed")
    states.pop(u.id,None)

async def orders(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text("ይህ ትዕዛዝ Admin ብቻ ይጠቀምበታል።"); return
    try:
        with open(ORDERS_FILE,encoding="utf-8") as f: data=json.load(f)
    except (OSError,ValueError): data=[]
    await update.message.reply_text("\n".join(f"{x['order']} | {x['package']} | {x['price']} ብር | {x['status']}" for x in data[-10:]) or "ገና ትዕዛዝ የለም።")

def main():
    if not BOT_TOKEN: raise RuntimeError("Set BOT_TOKEN environment variable")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start)); app.add_handler(CommandHandler("orders",orders))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.PHOTO,photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text))
    app.run_polling(drop_pending_updates=True)
if __name__=="__main__": main()
