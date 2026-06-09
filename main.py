import os
import re
import asyncio
import httpx
import base64
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- ⚙️ إعداد بيئة الـ Event Loop بأمان للسيرفر ---
try:
    global_loop = asyncio.get_event_loop()
except RuntimeError:
    global_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(global_loop)

# --- 🔗 مفاتيح الربط السحابي الحية ---
SUPABASE_URL = "https://gyxlgwnuninrubpuakoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5xGxnd251bmlucnVicHVha29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTY2NDYsImV4cCI6MjA5NjQ5MjY0Nn0.ZXLzWLJzCKCwg38--DfCnqrd1DYu3FgTvtuOSyDCSGo"

TELEGRAM_TOKEN = "8904101091:AAEvqTAMalxj0sXLdr9mJGIQRU1oWxTNquw"

# 🔑 تم وضع مفتاحك الجديد والنشط هنا بنجاح
AI_API_KEY = "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"

DEVELOPER_CHAT_ID = 1550103852 
DEVELOPER_USERNAME = "@I77Cl" 

SYSTEM_CONFIG = {
    "is_active": True,
    "ai_temperature": 0.2,
    "clinical_focus": "الكونسلتو العالمي المشترك: AMBOSS / UpToDate / Oxford / WHO Guidelines"
}

# --- ⚙️ بناء وتجهيز تطبيق تليجرام فوراً ---
tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# --- 🌐 خادم الويب والمستقبل السحابي (Webhook) ---
server = Flask('')

is_bot_initialized = False

async def init_bot_components():
    global is_bot_initialized
    if not is_bot_initialized:
        await tg_application.initialize()
        is_bot_initialized = True
        print("🚀 [تأكيد حركي]: تم تهيئة البوت الطبي والربط السحابي جاهز لمعالجة الرسائل!")

@server.before_request
def ensure_bot_is_ready():
    if not is_bot_initialized:
        try:
            global_loop.run_until_complete(init_bot_components())
        except Exception as e:
            print(f"⚠️ تنبيه التهيئة: {e}")

@server.route('/')
def home():
    return "🟢 منظومة البروفيسور سينا تعمل بكفاءة حركية سحابية تامة وجاهزة لاستقبال البيانات..."

@server.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    if request.method == "POST":
        try:
            update_json = request.get_json(force=True)
            update_obj = Update.de_json(update_json, tg_application.bot)
            global_loop.run_until_complete(tg_application.process_update(update_obj))
        except Exception as e:
            print(f"❌ Webhook Processing Error: {e}")
    return "OK", 200

# --- ⚙️ الدوال السريرية المساعدة ---
async def safe_edit_or_send(message, new_text, reply_markup=None, parse_mode="Markdown"):
    try:
        await message.edit_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try: await message.delete()
        except: pass
        await message.reply_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)

def split_medical_text(text, max_chars=4000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def predict_epidemiology_and_risks(text):
    alerts = ""
    if re.search(r'(حمى|حرارة|fever)', text.lower()):
        alerts += "🌍 *[إنذار وبائي موجه - رادار WHO]:* تم رصد أعراض حمى حادة؛ يجب استبعاد احتمالية *حمى الضنك* أو *الملاريا* فوراً.\n\n"
    if re.search(r'(إسهال|استفراغ|diarrhea)', text.lower()):
        alerts += "🌍 *[رادار الأوبئة المائي المتقدم]:* رصد إسهال مائي حاد؛ يرجى فحص الجفاف المخبري واستبعاد بؤر *الكوليرا* فوراً.\n\n"
    return alerts

def check_drug_interactions(text):
    interaction_alerts = ""
    text_lower = text.lower()
    if all(re.search(k, text_lower) for k in [r"(acei|enalapril)", r"(spironolactone|سبيرونولاكتون)"]):
        interaction_alerts += "⚠️ *🚨 [تداخل دوائي أسود خطير]:* خطر فرط بوتاسيوم الدم الحاد الحرج (Severe Hyperkalemia).\n\n"
    if all(re.search(k, text_lower) for k in [r"(sildenafil|فياجرا)", r"(nitrate|نيترات)"]):
        interaction_alerts += "⚠️ *🚨 [تداخل دوائي أسود خطير]:* هبوط حاد وصدمة وعائية مفاجئة قاتلة.\n\n"
    return interaction_alerts

async def get_patient_history_from_supabase(full_name):
    try:
        if not full_name or full_name in ["حالة سريرية", "حالة طارئة"]: return None
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        url = f"{SUPABASE_URL}/rest/v1/patients?full_name=eq.{full_name}&order=created_at.desc&limit=1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            return response.json()[0] if response.status_code == 200 and response.json() else None
    except: return None

async def consult_advanced_medical_system(content_payload, is_media=False, history_context=""):
    history_prompt = f"\n[سجل التاريخ المرضي السابق]:\n{history_context}" if history_context else "\n(أول زيارة للمريض)."
    base_prompt = (
        "أنت الآن 'منظومة البروفيسور سينا للكونسلتو الطبي الأعلى والتشخيص البصري والسريري المتقدم'.\n"
        f"التركيز الإكلينيكي والمراجع المفعلة حالياً: {SYSTEM_CONFIG['clinical_focus']}\n"
        "[قاعدة صارمة للمصطلحات والرد]:\n"
        "يجب صياغة كافة المصطلحات الطبية والأمراض باللغتين معاً داخل التقرير: العربية والإنجليزية بين قوسين.\n"
        f"{history_prompt}\n"
        "إذا كانت طبية أو تحاليل، صغ المخرج بالتالي:\n---START_DISC---\nنقاش العباقرة.\n---END_DISC---\n---START_REP---\nالتقرير الاستشاري النهائي للمريض.\n---END_REP---\n---START_SYS---\nالتخصص: عام\nالخطورة: مستقرة\nالنواقص: لا يوجد\n---END_SYS---"
    )
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # تحصين وقص أي فراغات زائدة قد تسقط أثناء النسخ
    sanitized_key = AI_API_KEY.strip()
    headers = {"Authorization": f"Bearer {sanitized_key}", "Content-Type": "application/json"}

    if is_media:
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": base_prompt + "\nقم بتحليل صورة التحليل الطبي أو الأشعة المرفقة بدقة."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{content_payload}"}}
            ]
        }]
        model_name = "google/gemini-2.5-flash:free"
    else:
        messages = [{"role": "user", "content": base_prompt + f"\nسياق المعطيات الحالي:\n{content_payload}"}]
        model_name = "meta-llama/llama-3-8b-instruct:free"

    payload = {"model": model_name, "messages": messages, "temperature": SYSTEM_CONFIG["ai_temperature"]}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"❌ OpenRouter Error Log: Status {response.status_code} - {response.text}")
                return f"❌ خطأ في خادم الذكاء الاصطناعي (كود الحالة: {response.status_code})"
        except Exception as api_err:
            print(f"❌ HTTP Request Exception: {api_err}")
            return f"❌ فشل الاتصال بمزود الذكاء الاصطناعي: {str(api_err)}"

async def save_to_supabase_advanced(full_name, diagnosis, specialty, urgency):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"full_name": full_name, "diagnosis": diagnosis, "specialty": specialty, "urgency": urgency}
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/patients", headers=headers, json=data)
    except: pass

# --- ⌨️ لوحات المفاتيح والتحكم ---
def get_developer_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📈 تقرير الأداء الحركي وتحليل الحالات")],
        [KeyboardButton("📊 الخزنة السحابية"), KeyboardButton("📥 سحب داتا المرضى")],
        [KeyboardButton("📚 تبديل المرجع: AMBOSS/Oxford")],
        [KeyboardButton("📢 إذاعة للمشتركين"), KeyboardButton("🧹 تصفير الذاكرة المؤقتة")],
        [KeyboardButton("🚨 تشغيل/إيقاف المنظومة الطبية")]
    ], resize_keyboard=True)

def get_user_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🩺 استشارة طبية جديدة")], 
        [KeyboardButton("🩻 التشخيص التفريقي المتعدد"), KeyboardButton("🧮 حاسبة الجرعات الطبيّة (MedCalc)")],
        [KeyboardButton("💊 فاحص التداخلات الدوائية"), KeyboardButton("🧬 رادار المقاومة والمضادات البكتيرية")]
    ], resize_keyboard=True)

# --- 🚀 المعالجة الأساسية للمستندات والرسائل ---
async def handle_main_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message: return
        user_id = update.message.chat_id
        user_text = update.message.text if update.message.text else ""
        
        print(f"📥 [تليجرام]: جاري معالجة طلب العميل {user_id}")
        
        if user_text == "/start":
            reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
            await update.message.reply_text(
                "🏥 *أهلاً بك في منظومة البروفيسور سينا للتشخيص الطبي المتقدم.*\n\nالمنظومة متصلة بالسحابة وجاهزة لاستقبال الحالات والتقارير الطبية بصرياً وسريرياً.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return

        admin_buttons = ["📈 تقرير الأداء الحركي وتحليل الحالات", "📊 الخزنة السحابية", "📥 سحب داتا المرضى", "📚 تبديل المرجع: AMBOSS/Oxford", "📢 إذاعة للمشتركين", "🧹 تصفير الذاكرة المؤقتة", "🚨 تشغيل/إيقاف المنظومة الطبية"]
        if user_id == DEVELOPER_CHAT_ID and user_text in admin_buttons:
            await handle_admin_buttons(update, context, user_text)
            return
            
        user_buttons = ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي المتعدد", "🧮 حاسبة الجرعات الطبيّة (MedCalc)", "💊 فاحص التداخلات الدوائية", "🧬 رادار المقاومة والمضادات البكتيرية"]
        if user_text in user_buttons:
            await handle_user_buttons(update, context, user_text)
            return

        is_media = False
        content_payload = user_text

        if update.message.photo:
            is_media = True
            processing_message = await update.message.reply_text("📸 *جاري استقبال التقرير الطبي وتشفيره بصرياً...*")
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            img_buffer = await photo_file.download_as_bytearray()
            content_payload = base64.b64encode(img_buffer).decode('utf-8')
            await processing_message.delete()

        processing_message = await update.message.reply_text("⏳ *[المنظومة في وضع المعالجة السريرية المشتركة]*\n🔍 *جاري قراءة المعطيات ومقاطعتها سحابياً...*", parse_mode="Markdown")
        
        patient_name = "حالة سريرية طارئة"
        history_text = await get_patient_history_from_supabase(patient_name)
        epi_alerts = predict_epidemiology_and_risks(str(user_text))
        drug_alerts = check_drug_interactions(str(user_text))
        
        raw_output = await consult_advanced_medical_system(content_payload, is_media, history_text)
        reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
        
        rep = raw_output
        if "---START_REP---" in raw_output:
            try:
                rep = raw_output.split("---START_REP---")[1].split("---END_REP---")[0].strip()
            except Exception:
                rep = raw_output

        await save_to_supabase_advanced(patient_name, rep[:500] + "...", "عام", "مستقرة")
        rights_footer = f"\n\n👑 *[ميثاق الملكية وحقوق البرمجة]:* تم التطوير بواسطة البروفيسور إسماعيل {DEVELOPER_USERNAME}"
        rep_with_rights = rep + rights_footer
        
        if drug_alerts: await update.message.reply_text(drug_alerts, parse_mode="Markdown")
        if epi_alerts: await update.message.reply_text(epi_alerts, parse_mode="Markdown")
        
        chunks = split_medical_text(rep_with_rights)
        await safe_edit_or_send(processing_message, chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None, parse_mode="Markdown")
        for chunk in chunks[1:]:
            await update.message.reply_text(chunk, parse_mode="Markdown")
            
    except Exception as e:
        print(f"❌ Critical Error in handle_main_flow: {e}")
        try: await update.message.reply_text(f"❌ حدث خطأ داخلي أثناء المعالجة: {str(e)}")
        except: pass

async def handle_user_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_user_reply_keyboard()
    if button_text == "🩺 استشارة طبية جديدة":
        await update.message.reply_text("🩺 *غرف الفرز جاهزة.* أرسل الأعراض السريرية أو صورة التحليل والمستندات الآن.", reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🩻 التشخيص التفريقي المتعدد":
        await update.message.reply_text("🩻 *اكتب العرض الرئيسي للمريض فقط* (مثل: ألم صدر حاد) لاستعراض مصفوفة الاحتمالات الطبية.", reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🧮 حاسبة الجرعات الطبيّة (MedCalc)":
        await update.message.reply_text("🧮 *اكتب وزن الطفل واسم المضاد* لحساب الجرعة السريرية بموجب بروتوكول Oxford.", reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "💊 فاحص التداخلات الدوائية":
        await update.message.reply_text("💊 *اكتب أسماء الأدوية مجتمعة في رسالة واحدة* لفحص التعارض الصدمي الحاد.", reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🧬 رادار المقاومة والمضادات البكتيرية":
        await update.message.reply_text("🧬 *اكتب موضع الالتهاب المخبري* لتوجيه العلاج التجريبي الذكي ومقاومة البكتيريا.", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_developer_reply_keyboard()
    if button_text == "📈 تقرير الأداء الحركي وتحليل الحالات":
        await update.message.reply_text("📈 *لوحة التحكم العليا تعمل باستقرار تام والسحابة متصلة.*", reply_markup=reply_markup, parse_mode="Markdown")

tg_application.add_handler(MessageHandler(filters.ALL, handle_main_flow))

async def set_webhook_url():
    async with tg_application.bot:
        await tg_application.bot.set_webhook(url=f"https://profsinabot-2.onrender.com/{TELEGRAM_TOKEN}")
        print("🔗 [تأكيد]: تم إعادة ضبط رابط الـ Webhook بنجاح!")

try:
    global_loop.run_until_complete(set_webhook_url())
except Exception as e:
    print(f"⚠️ تفادي خطأ تهيئة الـ Webhook الخارجي: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
