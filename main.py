import os
import re
import asyncio
import httpx
import time
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- خادم الويب للإنعاش ---
server = Flask('')
@server.route('/')
def home(): return "🟢 منظومة البروفيسور سينا تعمل بكفاءة استراتيجية 100% أونلاين."
def run_web_server(): server.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def self_ping_voodoo():
    time.sleep(30)
    while True:
        try: httpx.get("http://localhost:8080/")
        except: pass
        time.sleep(600)

# --- الإعدادات والمفاتيح ---
TELEGRAM_TOKEN = "8802669339:AAHNqI3IKQmk9HjygqrlT4UK0L5nCYYCb_c"
AI_API_KEY = "AQ.Ab8RN6J48hbWUgthd6A8x4HS8cPUfb9qoBhkVLF_mdfn-r1clA"
SUPABASE_URL = "https://gyxlgwnuninrubpuakoc.supabase.co"
SUPABASE_KEY = "EyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5eGxnd251bmlucnVicHVha29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTY2NDYsImV4cCI6MjA5NjQ5MjY0Nn0.ZXLzWLJzCKCwg38--DfCnqrd1DYu3FgTvtuOSyDCSGo"
DEVELOPER_CHAT_ID = 1550103852
SYSTEM_CONFIG = {"is_active": True, "ai_temperature": 0.2, "clinical_focus": "AMBOSS/UpToDate/Oxford", "broadcast_mode": False}

# --- لوحات التحكم ---
def get_user_keyboard():
    return ReplyKeyboardMarkup([
        ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي"],
        ["🧮 حاسبة الجرعات", "💊 فاحص التداخلات"],
        ["🧬 رادار المقاومة", "📊 مؤشر الفرز"],
        ["👑 المطور"]
    ], resize_keyboard=True)

# --- معالجة الذكاء الاصطناعي ---
async def consult_ai(content_text):
    prompt = f"أنت البروفيسور سينا. استخدم مراجع {SYSTEM_CONFIG['clinical_focus']}. أجب باللغة العربية والإنجليزية. السياق: {content_text}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            res = await client.post("https://api.openai.com/v1/chat/completions", 
                headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
                json={"model": "gpt-4-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": SYSTEM_CONFIG["ai_temperature"]})
            return res.json()['choices'][0]['message']['content']
        except: return "❌ خطأ في الاتصال بالسيرفر."

# --- المعالج الرئيسي ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text in ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي", "👑 المطور"]:
        await update.message.reply_text("تم تفعيل الخدمة.", reply_markup=get_user_keyboard())
        return
        
    status_msg = await update.message.reply_text("⏳ جاري التحليل السريري...")
    response = await consult_ai(user_text)
    await status_msg.edit_text(response, parse_mode="Markdown")

# --- التشغيل ---
if __name__ == '__main__':
    Thread(target=run_web_server, daemon=True).start()
    Thread(target=self_ping_voodoo, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("مرحباً بك يا بروفيسور.", reply_markup=get_user_keyboard())))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling()
    
