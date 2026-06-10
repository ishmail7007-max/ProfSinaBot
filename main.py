import os
import re
import asyncio
import base64  
import gc  
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai  # 🧠 استخدام المكتبة الرسمية المباشرة والأسرع لجوجل

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

# 🔑 تفعيل إعدادات Google AI Studio الرسمية
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

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
server = Flask(__name__)
is_bot_initialized = False

async def init_bot_components():
    global is_bot_initialized
    if not is_bot_initialized:
        await tg_application.initialize()
        is_bot_initialized = True
        print("🚀 [تأكيد حركي]: تم تهيئة البوت الطبي بنجاح!")

@server.before_request
def ensure_bot_is_ready():
    if not is_bot_initialized:
        try:
            global_loop.run_until_complete(init_bot_components())
        except Exception as e:
            print(f"⚠️ تنبيه التهيئة: {e}")

@server.route('/')
def home():
    return "🟢 منظومة البروفيسور سينا تعمل بكفاءة تامة عبر بوابة Google المستقرة..."

@server.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    if request.method == "POST":
        try:
            update_json = request.get_json(force=True)
            update_obj = Update.de_json(update_json, tg_application.bot)
            # معالجة فورية وغير متزامنة تماماً لمنع تعليق خوادم الويب
            global_loop.create_task(tg_application.process_update(update_obj))
        except Exception as e:
            print(f"❌ Webhook Processing Error: {e}")
    return "OK", 200

# --- ⚙️ الدوال السريرية المساعدة ---
async def safe_edit_or_send(message, new_text, reply_markup=None):
    try:
        return await message.edit_text(new_text, reply_markup=reply_markup, parse_mode=None)
    except Exception:
        try:
            await message.delete()
        except:
            pass
        return await message.reply_text(new_text, reply_markup=reply_markup, parse_mode=None)

def split_medical_text(text, max_chars=3800):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def predict_epidemiology_and_risks(text):
    alerts = ""
    if re.search(r'(حمى|حرارة|fever)', text.lower()):
        alerts += "🌍 [إنذار وبائي موجه - رادار WHO]: تم رصد أعراض حمى حادة؛ يجب استبعاد احتمالية حمى الضنك أو الملاريا فوراً.\n\n"
    if re.search(r'(إسهال|استفراغ|diarrhea)', text.lower()):
        alerts += "🌍 [رادار الأوبئة المائي المتقدم]: رصد إسهال مائي حاد؛ يرجى فحص الجفاف المخبري واستبعاد بؤر الكوليرا فوراً.\n\n"
    return alerts

def check_drug_interactions(text):
    interaction_alerts = ""
    text_lower = text.lower()
    if all(re.search(k, text_lower) for k in [r"(acei|enalapril)", r"(spironolactone|سبيرونولاكتون)"]):
        interaction_alerts += "⚠️ 🚨 [تداخل دوائي أسود خطير]: خطر فرط بوتاسيوم الدم الحاد الحرج (Severe Hyperkalemia).\n\n"
    if all(re.search(k, text_lower) for k in [r"(sildenafil|فياجرا)", r"(nitrate|نيترات)"]):
        interaction_alerts += "⚠️ 🚨 [تداخل دوائي أسود خطير]: هبوط حاد وصدمة وعائية مفاجئة قاتلة.\n\n"
    return interaction_alerts

# --- 🚀 محرك الاتصال الرسمي المستقر والخارق للأداء مع Google ---
async def consult_advanced_medical_system_official(img_bytes=None, text_context=""):
    base_prompt = (
        "أنت الآن 'منظومة البروفيسور سينا للكونسلتو الطبي الأعلى والتشخيص البصري والسريري المتقدم'.\n"
        f"التركيز الإكلينيكي والمراجع المفعلة حالياً: {SYSTEM_CONFIG['clinical_focus']}\n"
        "[قاعدة صارمة للمصطلحات والرد]:\n"
        "يجب صياغة كافة المصطلحات الطبية والأمراض باللغتين معاً داخل التقرير: العربية والإنجليزية بين قوسين.\n"
        "أنت تستقبل الآن المعطيات مباشرة، صغ مخرج التقرير الاستشاري النهائي للمريض بالتفصيل وبدون علامات الماركداون العشوائية."
    )
    
    if not GOOGLE_API_KEY:
        return "❌ خطأ: لم يتم ضبط مفتاح GOOGLE_API_KEY في متغيرات البيئة السحابية."

    try:
        # استخدام موديل 1.5-flash الرسمي المستقر والمدعوم للصور والتقارير الطبية السريعة
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if img_bytes:
            # معالجة الصورة بشكل مباشر وآمن للذاكرة عيار 100%
            cookie_image = {'mime_type': 'image/jpeg', 'data': img_bytes}
            response = await model.generate_content_async(
                contents=[base_prompt, cookie_image],
                generation_config={"temperature": SYSTEM_CONFIG["ai_temperature"]}
            )
        else:
            response = await model.generate_content_async(
                contents=[base_prompt, text_context],
                generation_config={"temperature": SYSTEM_CONFIG["ai_temperature"]}
            )
            
        return response.text
    except Exception as api_err:
        return f"❌ فشل محرك الاتصال الرسمي: {str(api_err)}"

async def save_to_supabase_advanced(full_name, diagnosis, specialty, urgency):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"full_name": full_name, "diagnosis": diagnosis, "specialty": specialty, "urgency": urgency}
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/patients", headers=headers, json=data)
    except: 
        pass

# --- ⌨️ لوحات المفاتيح والتحكم ---
def get_developer_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📈 تقرير الأداء الحركي وتحليل الحالات")],
        [KeyboardButton("📊 الخزنة السحابية"), KeyboardButton("📥 سحب داتا المرضى")],
        [KeyboardButton("📢 إذاعة للمشتركين"), KeyboardButton("🧹 تصفير الذاكرة المؤقتة")]
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
        if not update.message: 
            return
        user_id = update.message.chat_id
        user_text = update.message.text if update.message.text else ""
        
        if user_text == "/start":
            reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
            await update.message.reply_text(
                "🏥 أهلاً بك في منظومة البروفيسور سينا الطبية (النسخة المستقرة الرسمية).\n\nالمنظومة متصلة وبأعلى كفاءة وجاهزة لقراءة الصور والتقارير فوراً.",
                reply_markup=reply_markup
            )
            return

        admin_buttons = ["📈 تقرير الأداء الحركي وتحليل الحالات", "📊 الخزنة السحابية", "📥 سحب داتا المرضى", "📢 إذاعة للمشتركين", "🧹 تصفير الذاكرة المؤقتة"]
        if user_id == DEVELOPER_CHAT_ID and user_text in admin_buttons:
            await update.message.reply_text("📈 لوحة التحكم مستقرة والربط المباشر مع Google جاهز.", reply_markup=get_developer_reply_keyboard())
            return
            
        user_buttons = ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي المتعدد", "🧮 حاسبة الجرعات الطبيّة (MedCalc)", "💊 فاحص التداخلات الدوائية", "🧬 رادار المقاومة والمضادات البكتيرية"]
        if user_text in user_buttons:
            await handle_user_buttons(update, context, user_text)
            return

        img_bytes_payload = None

        if update.message.photo:
            processing_message = await update.message.reply_text("📸 جاري استقبال التقرير الطبي ومعالجته رقمياً...")
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            img_bytes_payload = await photo_file.download_as_bytearray()
            
            try:
                await processing_message.delete()
            except:
                pass

        processing_message = await update.message.reply_text("⏳ [المنظومة في وضع المعالجة السريرية المباشرة]\n🔍 جاري تحليل المعطيات عبر محرك Google الموثوق...")
        
        epi_alerts = predict_epidemiology_and_risks(str(user_text))
        drug_alerts = check_drug_interactions(str(user_text))
        
        # استدعاء المحرك الرسمي المستقر والآمن
        rep = await consult_advanced_medical_system_official(img_bytes=img_bytes_payload, text_context=user_text)
        reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
        
        # تنظيف الذاكرة بشكل فوري بعد سحب البيانات وعودتها من جوجل
        if img_bytes_payload:
            del img_bytes_payload
            gc.collect()

        rep = rep.replace("`", "").replace("---START_REP---", "").replace("---END_REP---", "")

        patient_name = "حالة سريرية طارئة"
        await save_to_supabase_advanced(patient_name, rep[:500] + "...", "عام", "مستقرة")
        rights_footer = f"\n\n👑 [ميثاق الملكية وحقوق البرمجة]: تم التطوير بواسطة البروفيسور إسماعيل {DEVELOPER_USERNAME}"
        rep_with_rights = rep + rights_footer
        
        if drug_alerts: 
            await update.message.reply_text(drug_alerts)
        if epi_alerts: 
            await update.message.reply_text(epi_alerts)

        chunks = split_medical_text(rep_with_rights)
        await safe_edit_or_send(processing_message, chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None)
        for chunk in chunks[1:]:
            await update.message.reply_text(chunk)
            
        gc.collect()
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        try: 
            await update.message.reply_text(f"❌ حدث خطأ داخلي أثناء المعالجة: {str(e)}")
        except: 
            pass

async def handle_user_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_user_reply_keyboard()
    if button_text == "🩺 استشارة طبية جديدة":
        await update.message.reply_text("🩺 غرف الفرز جاهزة. أرسل الأعراض السريرية أو صورة التحليل والمستندات الآن.", reply_markup=reply_markup)
    elif button_text == "🩻 التشخيص التفريقي المتعدد":
        await update.message.reply_text("🩻 اكتب العرض الرئيسي للمريض فقط (مثل: ألم صدر حاد) لاستعراض مصفوفة الاحتمالات الطبية.", reply_markup=reply_markup)
    elif button_text == "🧮 حاسبة الجرعات الطبيّة (MedCalc)":
        await update.message.reply_text("🧮 اكتب وزن الطفل واسم المضاد لحساب الجرعة السريرية بموجب بروتوكول Oxford.", reply_markup=reply_markup)
    elif button_text == "💊 فاحص التداخلات الدوائية":
        await update.message.reply_text("💊 اكتب أسماء الأدوية مجتمعة في رسالة واحدة لفحص التعارض الصدمي الحاد.", reply_markup=reply_markup)
    elif button_text == "🧬 رادار المقاومة والمضادات البكتيرية":
        await update.message.reply_text("🧬 اكتب موضع الالتهاب المخبري لتوجيه العلاج التجريبي الذكي ومقاومة البكتيريا.", reply_markup=reply_markup)

tg_application.add_handler(MessageHandler(filters.ALL, handle_main_flow))

async def set_webhook_url():
    async with tg_application.bot:
        await tg_application.bot.set_webhook(url=f"https://profsinabot-2.onrender.com/{TELEGRAM_TOKEN}")
        print("🔗 [تأكيد]: تم ضبط رابط الـ Webhook بنجاح!")

try:
    global_loop.run_until_complete(set_webhook_url())
except Exception as e:
    print(f"⚠️ تفادي خطأ تهيئة الـ Webhook: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
