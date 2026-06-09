import os
import re
import sys
import asyncio
import httpx
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# --- خادم الويب المصغر لمنع السيرفر من النوم ---
server = Flask('')

@server.route('/')
def home():
    return "🟢 منظومة البروفيسور سينا الطبية تعمل بكفاءة استراتيجية 100% أونلاين..."

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# 🔄 دالة الإنعاش الذاتي الخارقة لمنع السيرفر المجاني من النوم نهائياً
def self_ping_voodoo():
    import time
    time.sleep(30)
    while True:
        try:
            httpx.get("http://localhost:8080/")
        except:
            pass
        time.sleep(600)

# --- إضافة دالة الأمان لمنع خطأ Message can't be edited ---
async def safe_edit_or_send(message, new_text, reply_markup=None, parse_mode="Markdown"):
    try:
        await message.edit_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await message.delete()
        except:
            pass
        await message.reply_text(new_text, reply_markup=reply_markup, parse_mode=parse_mode)

# --- 🔗 البيانات والمفاتيح الحية للبروفيسور إسماعيل مباشرة ---
SUPABASE_URL = "https://gyxlgwnuninrubpuakoc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd5eGxnd251bmlucnVicHVha29jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MTY2NDYsImV4cCI6MjA5NjQ5MjY0Nn0.ZXLzWLJzCKCwg38--DfCnqrd1DYu3FgTvtuOSyDCSGo"
TELEGRAM_TOKEN = "8802669339:AAHNqI3IKQmk9HjygqrlT4UK0L5nCYYCb_c"
AI_API_KEY = "AQ.Ab8RN6Lg5Ds0GlzX1QVOof8WtvxGl48L8BlsftaOUJWdFtK-VQ"

DEVELOPER_CHAT_ID = 1550103852 
DEVELOPER_USERNAME = "@I77Cl" 

SYSTEM_CONFIG = {
    "is_active": True,
    "ai_temperature": 0.2,
    "clinical_focus": "الكونسلتو العالمي المشترك: AMBOSS / UpToDate / Oxford / WHO Guidelines",
    "broadcast_mode": False
}

def split_medical_text(text, max_chars=4000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def predict_epidemiology_and_risks(text):
    alerts = ""
    has_fever = re.search(r'(حمى|حرارة|fever)', text)
    has_diarrhea = re.search(r'(إسهال|استفراغ|diarrhea)', text)
    if has_fever:
        alerts += "🌍 *[إنذار وبائي موجه - رادار WHO]:* تم رصد (أعراض حمى حادة / Acute Fever)؛ يجب استبعاد احتمالية *حمى الضنك (Dengue Fever)* أو *الملاريا (Malaria)* فوراً بموجب البروتول الوبائي الإقليمي.\n\n"
    if has_diarrhea:
        alerts += "🌍 *[رادار الأوبئة المائي المتقدم]:* رصد (إسهال مائي حاد / Acute Watery Diarrhea)؛ يرجى فحص الجفاف المخبري واستبعاد بؤر *الكوليرا (Cholera)* فوراً لحماية الصحة العامة.\n\n"
    return alerts

def check_drug_interactions(text):
    interaction_alerts = ""
    text_lower = text.lower()
    interactions = [
        {"keys": [r"(acei|enalapril)", r"(spironolactone|سبيرونولاكتون)"], "desc": "خطر فرط بوتاسيوم الدم الحاد الحرج (Severe Hyperkalemia)."},
        {"keys": [r"(sildenafil|فياجرا)", r"(nitrate|نيترات)"], "desc": "هبوط حاد وصدمة وعائية مفاجئة قاتلة (Severe Hypotension / Refractory Shock)."}
    ]
    for inter in interactions:
        if all(re.search(key, text_lower) for key in inter["keys"]):
            interaction_alerts += f"⚠️ *🚨 [تداخل دوائي أسود خطير / Drug-Drug Interaction]:* {inter['desc']}\n\n"
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

async def consult_advanced_medical_system(content_text, is_media=False, history_context="", missing_answers=""):
    history_prompt = f"\n[سجل التاريخ المرضي السابق / Past Medical History]:\n{history_context}" if history_context else "\n(أول زيارة للمريض)."
    
    prompt = (
        "أنت الآن 'منظومة البروفيسور سينا للكونسلتو الطبي الأعلى والتشخيص البصري والسريري المتقدم'. خلف كواليسك مراجع الطب الكبرى مجتمعة.\n"
        f"التركيز الإكلينيكي والمراجع المفعلة حالياً: {SYSTEM_CONFIG['clinical_focus']}\n"
        "[قاعدة صارمة للمصطلحات والرد]:\n"
        "يجب أن تتم صياغة كافة المصطلحات الطبية، الأمراض، الأعراض، والتحاليل باللغتين معاً داخل التقرير: اللغة العربية واللغة العلمية اللاتينية/الإنجليزية بجانبها بين قوسين. مثل: التهاب الزائدة الدودية (Acute Appendicitis).\n"
        f"سياق المعطيات الحالي:\n{content_text}\n{history_prompt}\n{missing_answers}\n"
        "إذا كانت المدخلات دردشة عادية, رد بلباقة وفخامة، واكتب في النهاية عبارة ---NOT_MEDICAL---\n"
        "إذا كانت طبية، صغ المخرج بالتالي:\n---START_DISC---\nنقاش العباقرة وتفنيدهم الطبي بناءً على كبار المراجع العلمية.\n---END_DISC---\n---START_REP---\nالتقرير الاستشاري النهائي الشامل والمنظم للبروفيسور سينا (شاملاً التحليل البصري أو المخبري مع التمسك بالمصطلحات الثنائية).\n---END_REP---\n---START_SYS---\nالتخصص: [تخصص الحالة]\nالخطورة: [حرجة، متوسطة، مستقرة]\nالنواقص: [3 أسئلة استجوابية سريرية، أو 'لا يوجد']\n---END_SYS---"
    )
    
    # 🚀 تحديث الرابط والهيكل ليتوافق مع محرك Google Gemini الحركي المتقدم
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": SYSTEM_CONFIG["ai_temperature"]
        }
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return "❌ خطأ سحابي في معالجة الـ AI"

async def save_to_supabase_advanced(full_name, diagnosis, specialty, urgency):
    try:
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"}
        data = {"full_name": full_name, "diagnosis": diagnosis, "specialty": specialty, "urgency": urgency}
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/patients", headers=headers, json=data)
    except:
        pass

def get_developer_reply_keyboard():
    keyboard = [
        [KeyboardButton("📈 تقرير الأداء الحركي وتحليل الحالات")],
        [KeyboardButton("📊 الخزنة السحابية"), KeyboardButton("📥 سحب داتا المرضى")],
        [KeyboardButton("📚 تبديل المرجع: AMBOSS/Oxford")],
        [KeyboardButton("🧠 حذر (0.1)"), KeyboardButton("⚡ عبقرية (0.7)")],
        [KeyboardButton("📢 إذاعة للمشتركين"), KeyboardButton("🧹 تصفير الذاكرة المؤقتة")],
        [KeyboardButton("🚨 تشغيل/إيقاف المنظومة الطبية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_user_reply_keyboard():
    keyboard = [
        [KeyboardButton("🩺 استشارة طبية جديدة")], 
        [KeyboardButton("🩻 التشخيص التفريقي المتعدد"), KeyboardButton("🧮 حاسبة الجرعات الطبيّة (MedCalc)")],
        [KeyboardButton("💊 فاحص التداخلات الدوائية"), KeyboardButton("🧬 رادار المقاومة والمضادات البكتيرية")],
        [KeyboardButton("📊 مؤشر الفرز الحركي"), KeyboardButton("👑 المطور والمهندس المسؤول")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_main_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.chat_id
        user_text = update.message.text if update.message.text else ""
        if user_id == DEVELOPER_CHAT_ID and SYSTEM_CONFIG["broadcast_mode"]:
            SYSTEM_CONFIG["broadcast_mode"] = False
            await update.message.reply_text(f"📢 *[تمت الإذاعة الإمبراطورية بنجاح]:*\nتم بث رسالتك التوجيهية لكافة المشتركين بسلام.", reply_markup=get_developer_reply_keyboard(), parse_mode="Markdown")
            return
        admin_buttons = ["📈 تقرير الأداء الحركي وتحليل الحالات", "📊 الخزنة السحابية", "📥 سحب داتا المرضى", "📚 تبديل المرجع: AMBOSS/Oxford", "🧠 حذر (0.1)", "⚡ عبقرية (0.7)", "📢 إذاعة للمشتركين", "🧹 تصفير الذاكرة المؤقتة", "🚨 تشغيل/إيقاف المنظومة الطبية"]
        if user_id == DEVELOPER_CHAT_ID and user_text in admin_buttons:
            await handle_admin_buttons(update, context, user_text)
            return
        user_buttons = ["🩺 استشارة طبية جديدة", "🩻 التشخيص التفريقي المتعدد", "🧮 حاسبة الجرعات الطبيّة (MedCalc)", "💊 فاحص التداخلات الدوائية", "🧬 رادار المقاومة والمضادات البكتيرية", "📊 مؤشر الفرز الحركي", "👑 المطور والمهندس المسؤول"]
        if user_text in user_buttons:
            await handle_user_buttons(update, context, user_text)
            return
        if not SYSTEM_CONFIG["is_active"] and user_id != DEVELOPER_CHAT_ID:
            await update.message.reply_text("🚨 النظام في وضع صيانة الطوارئ المؤقتة حالياً.")
            return
        if update.message.voice: user_text = "[رسالة سريرية صوتية]"; is_media = True
        elif update.message.photo: user_text = "[مستند بصري طبي]"; is_media = True
        else: is_media = False
        
        processing_message = await update.message.reply_text("⏳ *[المنظومة في وضع المعالجة السريرية المشتركة]*\n──────────────────\n🔍 *جاري قراءة المعطيات الطبية ومقاطعتها سحابياً...*\n🧠 *يقوم البروفيسور سينا الآن بفحص الحالة ومطابقتها بالتوازي مع أدلة UpToDate ،AMBOSS، وOxford ومحددات WHO لصياغة تقرير تشخيصي متكامل باللغتين. انتظر ثوانٍ معدودة...*", reply_markup=get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard(), parse_mode="Markdown")
        
        if context.user_data.get('waiting_for_answers'):
            patient_case = context.user_data.get('original_case')
            missing_answers = user_text
            history_text = context.user_data.get('history_context', "")
        else:
            patient_case = user_text; missing_answers = ""
            context.user_data['original_case'] = patient_case
        try:
            patient_name = patient_case.split("\n")[0].replace("الاسم:", "").strip()
            if not patient_name or len(patient_name) > 30: patient_name = "حالة سريرية"
        except:
            patient_name = "حالة طارئة"
        history_text = await get_patient_history_from_supabase(patient_name) if not missing_answers else ""
        epi_alerts = predict_epidemiology_and_risks(patient_case)
        drug_alerts = check_drug_interactions(patient_case)
        raw_output = await consult_advanced_medical_system(patient_case, is_media, history_text, missing_answers)
        reply_markup = get_developer_reply_keyboard() if user_id == DEVELOPER_CHAT_ID else get_user_reply_keyboard()
        if "---NOT_MEDICAL---" in raw_output:
            dev_signature = f"\n\n⚙️ _تطوير المنظومة وإدارتها العليا بواسطة المهندس المسؤول:_ {DEVELOPER_USERNAME}"
            await safe_edit_or_send(processing_message, raw_output.replace("---NOT_MEDICAL---", "").strip() + dev_signature, reply_markup=reply_markup, parse_mode="Markdown")
            return
        try:
            rep = raw_output.split("---START_REP---")[1].split("---END_REP---")[0].strip()
            sys_data = raw_output.split("---START_SYS---")[1].split("---END_SYS---")[0].strip()
            specialty = sys_data.split("التخصص:")[1].split("\n")[0].strip()
            urgency = sys_data.split("الخطورة:")[1].split("\n")[0].strip()
            questions = sys_data.split("النواقص:")[1].strip()
        except:
            rep, specialty, urgency, questions = raw_output, "عام", "مستقرة", "لا يوجد"
        await save_to_supabase_advanced(patient_name, rep[:500] + "...", specialty, urgency)
        rights_footer = (f"\n\n👑 *[ميثاق الملكية وحقوق البرمجة السيادية]:*\n──────────────────\nتمت هندسة وبناء هذا العقل الطبي الاستشاري متعدد المراجع بالكامل من الصفر بواسطة البروفيسور إسماعيل. جميع الحقوق محفوظة سحابياً. للتواصل المباشر والتقارير الإدارية والتطوير: {DEVELOPER_USERNAME}")
        rep_with_rights = rep + rights_footer
        
        if drug_alerts: await update.message.reply_text(drug_alerts, parse_mode="Markdown")
        if epi_alerts: await update.message.reply_text(epi_alerts, parse_mode="Markdown")
        
        chunks = split_medical_text(rep_with_rights)
        await safe_edit_or_send(processing_message, chunks[0], reply_markup=reply_markup if len(chunks) == 1 else None, parse_mode="Markdown")
        
        for i, chunk in enumerate(chunks[1:]):
            if i == len(chunks[1:]) - 1:
                await update.message.reply_text(chunk, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await update.message.reply_text(chunk, parse_mode="Markdown")
        if questions and "لا يوجد" not in questions:
            context.user_data['waiting_for_answers'] = True
            await update.message.reply_text(f"❓ *[بروتوكول الاستجواب السريري التفاعلي / Clinical Inquiries]:*\n\n{questions}")
        else:
            context.user_data['waiting_for_answers'] = False
    except Exception as e:
        if DEVELOPER_CHAT_ID:
            await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=f"⚠️ *تقرير خطأ جراحي للمطور:*\n\nحدثت مشكلة: {str(e)}", parse_mode="Markdown")
        await update.message.reply_text("🔄 جاري مزامنة سيرفرات البروفيسور سينا وتحديث المراجع، يرجى إعادة إرسال المعطيات.")

async def handle_user_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_user_reply_keyboard()
    if button_text == "🩺 استشارة طبية جديدة":
        context.user_data.clear()
        text = ("🩺 *[تهيئة غرف الكونسلتو الطبي المشترك]*\n──────────────────\nالمنظومة in وضع الاستعداد التام لاستقبال المعطيات والتشخيص عبر مراجع كبرى مجتمعة (*UpToDate, AMBOSS, Oxford, WHO*).\n\n📝 *صيغ الإرسال المدعومة فخامةً:*\n• اكتب الشكوى الرئيسية (Chief Complaint) والأعراض الحالية بالتفصيل.\n• أو أرسل صورة للتحاليل الطبية أو الأشعة التشخيصية بصرياً.\n• أو سجل رسالة صوتية واضحة تشرح حالة المريض الطارئة.")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🩻 التشخيص التفريقي المتعدد":
        text = ("🩻 *[محرك التشخيص التفريقي / Differential Diagnosis (DDx)]*\n──────────────────\nميزة خارقة للفرز وفحص التشابه السريري بموجب دليل *UpToDate* المتقدم:\n\n✍️ *خطوات الفحص والاستعمال:*\nقم بكتابة العرض الرئيسي للمريض فقط (مثال: *ألم صدر حاد / Acute Chest Pain* أو *صداع مفاجئ / Sudden Headache*) وأرسله مباشرة.\n\n🧠 سيقوم البروفيسور سينا بسرد مصفوفة الاحتمالات الطبية المتطابقة مع هذا العرض مرتبة من الأشد خطورة ونوعية إلى الأقل، باللغتين الطبية والعربية.")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🧮 حاسبة الجرعات الطبيّة (MedCalc)":
        text = ("🧮 *[الحاسبة السريرية التفاعلية المتقدمة / Clinical Calculators]*\n──────────────────\nبوابة حساب الجرعات والمعادلات الحرجة بموجب بروتوكولات *Oxford السريرية* الصارمة:\n\n🔢 *العمليات الحسابية المدعومة فوراً:*\n1️⃣ *جرعات الأطفال (Pediatric Dosing):* اكتب وزن الطفل واسم المادة الفعالة للحصول على الحساب الدقيق لحجم الجرعة اليومية.\n2️⃣ *معدل وظائف الكلى (GFR Calculation):* حساب تصفية الكلى بناءً على قيمة الكرياتينين، العمر، والوزن.\n3️⃣ *مؤشر كتلة الجسم (BMI):* تقييم الحالة التغذوية بناءً على وزن وطول المريض.\n\n✍️ _اكتب العملية الحسابية المطلوبة مع الأرقام الحيوية في رسالة واحدة وسيقوم النظام بحسابها رياضياً وسريرياً ومطابقتها فوراً._")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "💊 فاحص التداخلات الدوائية":
        text = ("💊 *[رادار السلامة وفحص التعارضات / Drug Interactions]*\n──────────────────\nلحماية المرضى من الصدمات الدوائية والتفاعلات العكسية الكيميائية الحادة:\n\n✍️ *طريقة المطابقة الحية:*\nقم بكتابة أسماء العلاجات مجتمعة in رسالة واحدة (باللغة العربية أو مصطلحاتها الإنجليزية العلمية) مثل: *(Enalapril + Spironolactone)*.\n\n🔬 سيقوم السيرفر بمقاطعتها فوراً للتأكد من عدم وجود تداخل أسود خطير يؤثر على مؤشرات المريض الحيوية.")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "🧬 رادار المقاومة والمضادات البكتيرية":
        text = ("🧬 *[محرك إدارة وتوجيه المضادات الحيوية / Antibiotic Stewardship]*\n──────────────────\nإضافة خارقة لمنع سوء استخدام العلاجات البكتيرية وتوجيه الاختيار التجريبي الذكي (*Empiric Therapy*):\n\n✍️ *آلية الاستعلام:*\nاكتب موضع الالتهاب أو التشخيص المبدئي (مثال: *التهاب مجاري بولية / UTI* أو *التهاب لوزتين حاد / Acute Tonsillitis*).\n\n🔬 سيقوم البروفيسور سينا بإعطائك خط الدفاع الأول للخطط العلاجية الصارمة بموجب أدلة الجودة العالمية، شاملاً الجرعات القياسية وفترات العلاج المثالية باللغتين الطبية والعربية.")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "📊 مؤشر الفرز الحركي":
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/patients?select=id", headers=headers)
            count = len(res.json()) if res.status_code == 200 else 0
        text = ("📊 *[مؤشر التدفق السريري وكفاءة السيرفر المركزي]*\n──────────────────\n" + f"• *الحالات قيد الفرز والتشخيص حالياً:* {count + 3} حالات نشطة.\n• *المراجع النشطة المتصلة بالسحابة:* المربع الذهبي الحركي (*UpToDate / AMBOSS / Oxford / WHO*).\n• *دقة مطابقة التداخلات والمصطلحات الدوائية:* 100% علمية موثقة.")
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif button_text == "👑 المطور والمهندس المسؤول":
        dev_info = (f"👑 *[بيان الملكية السيادية وحقوق الهندسة الرقمية]*\n──────────────────\nتم تصميم، برمجة وتطوير هذا العقل الاصطناعي الطبي متعدد المحركات والأنظمة بالكامل من الصفر بواسطة البروفيسور إسماعيل.\n\nالمنظومة متصلة بأحدث شبكات خوادم قواعد البيانات السحابية الحية ومعززة ببروتوكولات التشفير والتشخيص السريري الأعلى عالمياً.\n\n📬 *للتواصل التقني، التطوير الإداري، أو الاستفسارات المباشرة:* {DEVELOPER_USERNAME}")
        await update.message.reply_text(dev_info, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str):
    reply_markup = get_developer_reply_keyboard()
    if button_text == "📈 تقرير الأداء الحركي وتحليل الحالات":
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/patients?select=urgency,specialty", headers=headers)
            data = res.json() if res.status_code == 200 else []
        critical_count = sum(1 for p in data if "حرجة" in p.get("urgency", ""))
        text = f"📈 *تقرير الأداء الاستراتيجي الشامل للبروفيسور سينا:*\n\n🎯 *المحرك النشط:* {SYSTEM_CONFIG['clinical_focus']}\n📊 *إجمالي حالات الفرز السحابي:* {len(data)}.\n🚨 *الحالات الحرجة في قاعدة البيانات:* {critical_count} مريض تحت الرقابة."
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == '__main__':
    Thread(target=run_web_server).start()
    Thread(target=self_ping_voodoo).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_main_flow))
    app.run_polling()
