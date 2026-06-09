import os
import re
import asyncio
import httpx
import base64
from flask import Flask, request, jsonify
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- 🔗 البيانات ومفاتيح الربط السحابي الحية ---
SUPABASE_URL = "https://gyxlgwnuninrubpuakoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5xGxnd251bmlucnVicHVha29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTY2NDYsImV4cCI6MjA5NjQ5MjY0Nn0.ZXLzWLJzCKCwg38--DfCnqrd1DYu3FgTvtuOSyDCSGo"
TELEGRAM_TOKEN = "8904101091:AAFgqwgqp78qaUBxX0b1WeNl50VM8yFw7sU"  # تأكد من وضع التوكن الأحدث هنا
AI_API_KEY = "Sk-or-v1-48823f33467ffd19b0f44d3e775a9d2efbc012dcd7ab637e7a543b12a97128fc"

DEVELOPER_CHAT_ID = 1550103852 
DEVELOPER_USERNAME = "@I77Cl" 

SYSTEM_CONFIG = {
    "is_active": True,
    "ai_temperature": 0.2,
    "clinical_focus": "الكونسلتو العالمي المشترك: AMBOSS / UpToDate / Oxford / WHO Guidelines",
    "broadcast_mode": False
}

# بناء تطبيق تيليجرام كمحرك خلفي فقط بدون run_polling
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# --- خادم الويب الأساسي لاستقبال الـ Webhook ---
server = Flask('')

@server.route('/')
def home():
    return "🟢 منظومة البروفيسور سينا تعمل بنظام الـ Webhook المستقر 100%..."

@server.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    """استقبال التحديثات مباشرة من تيليجرام وتمريرها لمعالجة البوت التزامياً"""
    json_string = request.get_data().decode('utf-8')
    update = Update.de_json(request.get_json(force=True), app.bot)
    
    # تشغيل المعالجة داخل حلقة الأحداث الحالية لمنع التعليق
    loop = asyncio.get_event_loop()
    loop.create_task(app.process_update(update))
    return jsonify({"status": "ok"})

async def safe_edit_or_send(message, new_text, reply_markup=None, parse_mode="Markdown"):
    try:
        await message.edit_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await message.delete()
        except:
            pass
        await message.reply_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)

def split_medical_text(text, max_chars=4000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def predict_epidemiology_and_risks(text):
    alerts = ""
    has_fever = re.search(r'(حمى|حرارة|fever)', text)
    has_diarrhea = re.search(r'(إسهال|استفراغ|diarrhea)', text)
    if has_fever:
        alerts += "🌍 *[إنذار وبائي موجه - رادار WHO]:* تم رصد (أعراض حمى حادة / Acute Fever)؛ يجب استبعاد احتمالية *حمى الضنك (Dengue Fever)* أو *الملاريا (Malaria)* فوراً.\n\n"
    if has_diarrhea:
        alerts += "🌍 *[رادار الأوبئة المائي المتقدم]:* رصد (إسهال مائي حاد)؛ يرجى فحص الجفاف المخبري واستبعاد بؤر *الكوليرا (Cholera)* فوراً.\n\n"
    return alerts

def check_drug_interactions(text):
    interaction_alerts = ""
    text_lower = text.lower()
    interactions = [
        {"keys": [r"(acei|enalapril)", r"(spironolactone|سبيرونولاكتون)"], "desc": "خطر فرط بوتاسيوم الدم الحاد الحرج (Severe Hyperkalemia)."},
        {"keys": [r"(sildenafil|فياجرا)", r"(nitrate|نيترات)"], "desc": "هبوط حاد وصدمة وعائية مفاجئة قاتلة."}
    ]
    for inter in interactions:
        if all(re.search(key, text_lower) for key in inter["keys"]):
            interaction_alerts += f"⚠️ *🚨 [تداخل دوائي أسود خطير]:* {inter['desc']}\n\n"
    return interaction_alerts

async def get_patient_history_from_supabase(full_name):
    try:
        if not full_name or full_name in ["حالة سريرية", "حالة طارئة"]: return None
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/patients?full_name=eq.{full_name}&order=created_at.desc&limit=1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()[0] if response.status_code == 200 and response.json() else None
    except:
        return None

async def consult_advanced_medical_system(content_payload, is_media=False, history_context="", missing_answers="", mime_type="image/jpeg"):
    history_prompt = f"\n[سجل التاريخ المرضي السابق]:\n{history_context}" if history_context else "\n(أول زيارة للمريض)."
    base_prompt = (
        "أنت الآن 'منظومة البروفيسور سينا للكونسلتو الطبي الأعلى والتشخيص البصري والسريري المتقدم'.\n"
        f"التركيز الإكلينيكي والمراجع المفعلة حالياً: {SYSTEM_CONFIG['clinical_focus']}\n"
        "[قاعدة صارمة للمصطلحات والرد]:\n"
        "يجب صياغة كافة المصطلحات الطبية والأمراض باللغتين معاً داخل التقرير: العربية والإنجليزية بين قوسين.\n"
        f"{history_prompt}\n{missing_answers}\n"
        "إذا كانت طبية أو تحاليل، صغ المخرج بالتالي:\n---START_DISC---\nنقاش العباقرة.\n---END_DISC---\n---START_REP---\nالتقرير الاستشاري النهائي.\n---END_REP---\n---START_SYS---\nالتخصص: [تخصص الحالة]\nالخطورة: [حرجة، متوسطة، مستقرة]\nالنواقص: [3 أسئلة، أو 'لا يوجد']\n---END_SYS---"
    )
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}

    if is_media:
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": base_prompt + "\nقم بتحليل صورة التحليل الطبي أو الأشعة المرفقة بدقة تشخيصية تفصيلية كاملة."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{content_payload}"}}
            ]
        }]
        model_name = "google/gemini-2.5-flash:free"
    else:
        messages = [{"role": "user", "content": base_prompt + f"\nسياق المعطيات الحالي:\n{content_payload}"}]
        model_name = "meta-llama/llama-3-8b-instruct:free"

    payload = {"model": model_name, "messages": messages, "temperature": SYSTEM_CONFIG["ai_temperature"]}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        return response.json()['choices'][0]['message']['content'] if response.status_code == 200 else "❌ خطأ سحابي في معالجة الـ AI"

async def save_to_supabase_advanced(full_name, diagnosis, specialty, urgency):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"full_name": full_name, "diagnosis": diagnosis, "specialty": specialty, "urgency": urgency}
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/patients", headers=headers, json=data)
    except:
        pass

def get_developer_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📈 تقرير الأداء الحركي وتحليل الحالات")],
        [KeyboardButton("📊 الخزنة السحابية"), KeyboardButton("📥 سحب داتا المرضى")],
        [KeyboardButton("📚 تبديل المرجع: AMBOSS/Oxford")],
        [KeyboardButton("🧠 حذر (0.1)"), KeyboardButton("⚡ عبقرية (0.7)")],
        [KeyboardButton("📢 إذاعة للمشتركين"), KeyboardButton("🧹 تصفير الذاكرة المؤقتة")],
        [KeyboardButton("🚨 تشغيل/إيقاف المنظومة الطبية")]
    ], resize_keyboard=True)

def get_user_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🩺 استشارة طبية جديدة")], 
        [KeyboardButton("🩻 التشخيص التفريقي المتعدد"), KeyboardButton("🧮 حاسبة الجرعات الطبيّة (MedCalc)")],
        [KeyboardButton("💊 فاحص التداخلات الدوائية"), KeyboardButton("🧬 رادار المقاومة والمضادات البكتيرية")],
        [KeyboardButton("📊 مؤشر الفرز الحركي"), KeyboardButton("👑 المطور والمهندس المسؤول")]
    ], resize_keyboard=True)

async def handle_main_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message: return
        user_id = update.message.chat_id
        user_text = update.message.text if update.message.text else ""
        
        admin_buttons = ["📈 تقرير الأداء الحركي وتحليل الحالات", "📊 الخزنة السحابية", "📥 سحب داتا المرضى", "📚 تبديل المرجع: AMBOSS/Oxford", "🧠 حذر (0.1)", "⚡ عبقرية (0.7)", "📢 إذاعة للمشتركين", "🧹 تصفير الذاكرة المؤقتة", "🚨 تشغيل/إيقاف المنظومة الطبية"]
        if user_id == DEVELOPER_CHAT_ID and user_text in admin_buttons:
            await handle_admin_buttons(update, context, user_text)
            return
            
        user_buttons = ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي المتعدد", "🧮 حاسبة الجرعات الطبيّة (MedCalc)", "💊 فاحص التداخلات الدوائية", "🧬 رادار المقاومة والمضادات البكتيرية", "📊 مؤشر الفرز الحركي", "👑 المطور والمهندس المسؤول"]
        if user_text in user_buttons:
            await handle_user_buttons(update, context, user_text)
            return

        is_media = False
        content_payload = user_text

        if update.message.photo:
            is_media = True
            processing_message = await update.message.reply_text("📸 *جاري تحميل وتشفير التقرير الطبي بصرياً...*")
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            img_buffer = await photo_file.download_as_bytearray()
            content_payload = base64.b64encode(img_buffer).decode('utf-8')
            await processing_message.delete()

        processing_message = await update.message.reply_text("⏳ *[المنظومة في وضع المعالجة السريرية المشتركة]*\n🔍 *جاري فحص المعطيات الطبية ومطابقتها سحابياً...*", parse_mode="Markdown")
        
        patient_name = "حالة سريرية طارئة"
        history_text = await get_patient_history_from_supabase(patient_name)
        epi_alerts = predict_epidemiology_and_risks(str(user_text))
        drug_alerts = check_drug_interactions(str(user_text))
        
        raw_output = await consult_advanced_medical_system(content_payload, is_media, history_text)
        reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
        
        try:
            rep = raw_output.split("---START_REP---")[1].split("---END_REP---")[0].strip()
            sys_data = raw_output.split("---START_SYS---")[1].split("---END_SYS---")[0].strip()
            specialty = sys_data.split("التخصص:")[1].split("\n")[0].strip()
            urgency = sys_data.split("الخطورة:")[1].split("\n")[0].strip()
            questions = sys_data.split("النواقص:")[1].strip()
        except:
            rep, specialty, urgency, questions = raw_output, "عام", "مستقرة", "لا يوجد"
            
        await save_to_supabase_advanced(patient_name, rep[:500] + "...", specialty, urgency)
        rights_footer = f"\n\n👑 *[ميثاق الملكية السيادية]:* تم التطوير بالكامل بواسطة البروفيسور إسماعيل {DEVELOPER_USERNAME}"
        rep_with_rights = rep + rights_footer
        
        if drug_alerts: await update.message.reply_text(drug_alerts, parse_mode="Markdown")
        if epi_alerts: await update.message.reply_text(epi_alerts, parse_mode="Markdown")
        
        chunks = split_medical_text(rep_with_rights)
        await safe_edit_or_send(processing_message, chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None, parse_mode="Markdown")
        
        for i, chunk in enumerate(chunks[1:]):
            await update.message.reply_text(chunk, reply_markup=reply_markup if i == len(chunks[1:]) - 1 else None, parse_mode="Markdown")
            
    except Exception as e:
        if DEVELOPER_CHAT_ID:
            await app.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=f"⚠️ *خطأ سحري:* {str(e)}")

# ربط المعالجات بشكل مسبق للتطبيق الخلفي
app.add_handler(MessageHandler(filters.ALL, handle_main_flow))

async def handle_user_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_user_reply_keyboard()
    if button_text == "🩺 استشارة طبية جديدة":
        await update.message.reply_text("🩺 *غرف الكونسلتو الطبي المشترك جاهزة.* أرسل الأعراض أو صورة التحليل.", reply_markup=reply_markup, parse_mode="Markdown")
    # ... بقية أزرار المستخدم كالمعتاد ...

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_developer_reply_keyboard()
    if button_text == "📈 تقرير الأداء الحركي وتحليل الحالات":
        await update.message.reply_text("📈 *النظام يعمل بنظام الـ Webhook المستقر حالياً.*", reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    # تهيئة تطبيق تيليجرام داخلياً قبل بدء تشغيل خادم الويب
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.initialize())
    
    # تشغيل خادم ويب فلاسك لاستقبال الطلبات
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)
