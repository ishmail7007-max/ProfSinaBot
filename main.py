import os
import re
import asyncio
import gc  
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai  
import httpx

# --- ⚙️ تهيئة بيئة العمل والمفاتيح ---
TELEGRAM_TOKEN = "8904101091:AAEvqTAMalxj0sXLdr9mJGIQRU1oWxTNquw"
SUPABASE_URL = "https://gyxlgwnuninrubpuakoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5xGxnd251bmlucnVicHVha29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTY2NDYsImV4cCI6MjA5NjQ5MjY0Nn0.ZXLzWLJzCKCwg38--DfCnqrd1DYu3FgTvtuOSyDCSGo"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

DEVELOPER_CHAT_ID = 1550103852 
DEVELOPER_USERNAME = "@I77Cl" 

# بناء التطبيق
tg_application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
server = Flask(__name__)

# الاستجابة لطلب فحص الخادم من Render لضمان بقائه Live دائماً
@server.route('/')
def home():
    return "🟢 Server Status: Active & Fully Functional"

# المستقبل الرئيسي للرسائل من تليجرام
@server.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    if request.method == "POST":
        try:
            update_json = request.get_json(force=True)
            update_obj = Update.de_json(update_json, tg_application.bot)
            
            # تشغيل معالجة الرسالة في الخلفية فوراً دون تأخير خادم الويب
            loop = asyncio.get_event_loop()
            loop.create_task(tg_application.process_update(update_obj))
        except Exception as e:
            print(f"❌ Webhook Core Error: {e}")
    return "OK", 200

# --- ⚙️ دوال الفرز والتحليل السريري ---
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

# --- 🧠 محرك جوجل المستقر لمعالجة التقارير والصور الطبية ---
async def consult_medical_engine(img_bytes=None, text_context=""):
    base_prompt = (
        "أنت الآن 'منظومة البروفيسور سينا للكونسلتو الطبي الأعلى والتشخيص البصري والسريري المتقدم'.\n"
        "التركيز الإكلينيكي والمراجع المفعلة حالياً: الكونسلتو العالمي المشترك: AMBOSS / UpToDate / Oxford / WHO Guidelines\n"
        "[قاعدة صارمة للمصطلحات والرد]:\n"
        "يجب صياغة كافة المصطلحات الطبية والأمراض باللغتين معاً داخل التقرير: العربية والإنجليزية بين قوسين.\n"
        "صغ مخرج التقرير الاستشاري النهائي للمريض بالتفصيل وبدون علامات الماركداون العشوائية."
    )
    
    if not GOOGLE_API_KEY:
        return "❌ خطأ سحابي: لم يتم ضبط مفتاح GOOGLE_API_KEY بنجاح في السيرفر."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        if img_bytes:
            image_data = {'mime_type': 'image/jpeg', 'data': bytes(img_bytes)}
            response = await model.generate_content_async(contents=[base_prompt, image_data])
        else:
            response = await model.generate_content_async(contents=[base_prompt, text_context])
        return response.text
    except Exception as e:
        return f"❌ خطأ استجابة من محرك جوجل الطبي: {str(e)}"

async def save_to_supabase_advanced(full_name, diagnosis):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
        data = {"full_name": full_name, "diagnosis": diagnosis, "specialty": "عام", "urgency": "مستقرة"}
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/patients", headers=headers, json=data)
    except: 
        pass

# --- ⌨️ لوحات التحكم الثابتة ---
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

# --- 🚀 معالجة التدفق الرئيسي للمنظومة ---
async def handle_main_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message: 
            return
        user_id = update.message.chat_id
        user_text = update.message.text if update.message.text else ""
        
        if user_text == "/start":
            reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
            await update.message.reply_text(
                "🏥 أهلاً بك في منظومة البروفيسور سينا الطبية المحدثة والمستقرة.\nالمنظومة متصلة وجاهزة للعمل الفوري واستقبال التقارير الطبية.",
                reply_markup=reply_markup
            )
            return

        admin_buttons = ["📈 تقرير الأداء الحركي وتحليل الحالات", "📊 الخزنة السحابية", "📥 سحب داتا المرضى", "📢 إذاعة للمشتركين", "🧹 تصفير الذاكرة المؤقتة"]
        if user_id == DEVELOPER_CHAT_ID and user_text in admin_buttons:
            await update.message.reply_text("📈 لوحة التحكم السحابية مستقرة تماماً وجاهزة.", reply_markup=get_developer_reply_keyboard())
            return
            
        user_buttons = ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي المتعدد", "🧮 حاسبة الجرعات الطبيّة (MedCalc)", "💊 فاحص التداخلات الدوائية", "🧬 رادار المقاومة والمضادات البكتيرية"]
        if user_text in user_buttons:
            await handle_user_buttons(update, context, user_text)
            return

        img_bytes = None
        if update.message.photo:
            processing_msg = await update.message.reply_text("📸 جاري استقبال وثيقة التقرير الطبي ومعالجتها بصرياً...")
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            img_bytes = await photo_file.download_as_bytearray()
            try:
                await processing_msg.delete()
            except:
                pass

        status_msg = await update.message.reply_text("⏳ [المنظومة في وضع المعالجة السريرية المباشرة]\n🔍 جاري إعداد وتدقيق التقرير الطبي عبر مصفوفة مراجع Google الطبية الحية...")
        
        epi_alerts = predict_epidemiology_and_risks(str(user_text))
        drug_alerts = check_drug_interactions(str(user_text))
        
        # طلب استشارة من محرك الذكاء الاصطناعي
        rep = await consult_medical_engine(img_bytes=img_bytes, text_context=user_text)
        reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
        
        # تفريغ فوري وحاسم للذاكرة لتفادي انهيار العقد السحابية (Out of Memory)
        if img_bytes:
            del img_bytes
            gc.collect()

        rep = rep.replace("`", "")
        await save_to_supabase_advanced("حالة سريرية طارئة", rep[:500] + "...")
        
        final_report = rep + f"\n\n👑 [ميثاق الملكية وحقوق البرمجة]: تم التطوير بواسطة البروفيسور إسماعيل {DEVELOPER_USERNAME}"
        
        if drug_alerts: 
            await update.message.reply_text(drug_alerts)
        if epi_alerts: 
            await update.message.reply_text(epi_alerts)

        chunks = split_medical_text(final_report)
        try:
            await status_msg.edit_text(chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None)
        except:
            await update.message.reply_text(chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None)
            
        for chunk in chunks[1:]:
            await update.message.reply_text(chunk)
            
        gc.collect()
    except Exception as e:
        print(f"❌ Core flow error: {e}")

async def handle_user_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_user_reply_keyboard()
    if button_text == "🩺 استشارة طبية جديدة":
        await update.message.reply_text("🩺 غرف الفرز جاهزة. أرسل الأعراض السريرية أو صورة التحليل والمستندات الآن.", reply_markup=reply_markup)
    elif button_text == "🩻 التشخيص التفريقي المتعدد":
        await update.message.reply_text("🩻 اكتب العرض الرئيسي للمريض فقط لاستعراض مصفوفة الاحتمالات الطبية.", reply_markup=reply_markup)
    elif button_text == "🧮 حاسبة الجرعات الطبيّة (MedCalc)":
        await update.message.reply_text("🧮 اكتب وزن الطفل واسم المضاد لحساب الجرعة السريرية بموجب بروتوكول Oxford.", reply_markup=reply_markup)
    elif button_text == "💊 فاحص التداخلات الدوائية":
        await update.message.reply_text("💊 اكتب أسماء الأدوية مجتمعة في رسالة واحدة لفحص التعارض الصدمي الحاد.", reply_markup=reply_markup)
    elif button_text == "🧬 رادار المقاومة والمضادات البكتيرية":
        await update.message.reply_text("🧬 اكتب موضع الالتهاب المخبري لتوجيه العلاج التجريبي الذكي ومقاومة البكتيريا.", reply_markup=reply_markup)

tg_application.add_handler(MessageHandler(filters.ALL, handle_main_flow))

# تفعيل الويب هوك بشكل مستقل وآمن تماماً
async def initialize_app():
    await tg_application.initialize()
    await tg_application.bot.set_webhook(url=f"https://profsinabot-2.onrender.com/{TELEGRAM_TOKEN}")
    print("🔗 Webhook activated successfully inside background event loop.")

# تشغيل عملية الربط والتهيئة تزامناً مع تشغيل التطبيق
asyncio.run_coroutine_threadsafe(initialize_app(), asyncio.get_event_loop())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
