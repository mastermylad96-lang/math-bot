import asyncio
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================== إعداداتك الشخصية ==================
TOKEN = "8956000105:AAGa1EX0w9S-m9cOut24FyaobVDbfvFR1WA"
OWNER_ID = 8395774065
OWNER_USERNAME = "Mastermylad"

# أرقام الدفع
SHAM_CASH_ID = "a481e296a7c3ca7ecef6c76f13edcf84"
HERM_PHONE = "0959612868"
HERM_NAME = "ميلاد أنيس ملحم"

# الأسعار
NOTE_PRICE = 500
EXAMS_PRICE = 200

# روابط الملفات
FILE_URLS = {
    "note": "https://files.catbox.moe/7u3gcg.pdf",
    "exams": "https://files.catbox.moe/gfphkb.pdf",
    "questions": "https://files.catbox.moe/x8xkvn.pdf"
}

# متغيرات
pending_orders = {}
waiting_for_issue = {}

# ================== قاعدة بيانات المستخدمين ==================

def init_db():
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  first_seen DATE,
                  last_active DATE)''')
    conn.commit()
    conn.close()

def add_or_update_user(user_id, username, first_name):
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    today = datetime.now().date()
    c.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, first_seen, last_active) VALUES (?, ?, ?, ?, ?)',
              (user_id, username, first_name, today, today))
    c.execute('UPDATE users SET last_active = ?, username = ?, first_name = ? WHERE user_id = ?',
              (today, username, first_name, user_id))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    thirty_days_ago = (datetime.now().date() - timedelta(days=30))
    c.execute('SELECT COUNT(*) FROM users WHERE last_active >= ?', (thirty_days_ago,))
    active_30_days = c.fetchone()[0]
    seven_days_ago = (datetime.now().date() - timedelta(days=7))
    c.execute('SELECT COUNT(*) FROM users WHERE first_seen >= ?', (seven_days_ago,))
    new_7_days = c.fetchone()[0]
    conn.close()
    return total_users, active_30_days, new_7_days

# ================== الأوامر الرئيسية ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_user(user.id, user.username, user.first_name)
    keyboard = [
        [InlineKeyboardButton("📚 شراء نوطة رياضيات (500 ل.س)", callback_data="buy_note")],
        [InlineKeyboardButton("📝 شراء نماذج امتحانية (200 ل.س)", callback_data="buy_exams")],
        [InlineKeyboardButton("❓ أسئلة دورات (مجاني)", callback_data="buy_questions_free")],
        [InlineKeyboardButton("🆘 مساعدة", callback_data="help")]
    ]
    await update.message.reply_text(
        "📚 **أهلاً بك في بوت حقيبة الرياضيات!**\n\nاختر ما تريد:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر متاح فقط للمالك.")
        return
    total, active_30, new_7 = get_stats()
    await update.message.reply_text(
        f"📊 **إحصائيات بوت حقيبة الرياضيات**\n\n"
        f"👥 **إجمالي المستخدمين:** {total}\n"
        f"📅 **نشطاء آخر 30 يوماً:** {active_30}\n"
        f"🆕 **جدد آخر 7 أيام:** {new_7}\n\n"
        f"📈 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode="Markdown"
    )

async def questions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_user(user.id, user.username, user.first_name)
    file_url = FILE_URLS.get("questions")
    if file_url:
        await update.message.reply_document(
            document=file_url,
            caption="❓ **أسئلة دورات سابقة مع الحلول**\n\n✅ مجاني بالكامل!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ الرابط غير متوفر.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 صف مشكلتك", callback_data="describe_issue")],
        [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="contact_owner")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]
    ]
    await update.message.reply_text(
        "🆘 **مركز المساعدة**\n\n"
        "• **صف مشكلتك**: اكتب مشكلتك وسيتم إرسالها\n"
        "• **التواصل المباشر**: تحدث مع الدعم\n\n"
        "نعتذر عن أي تأخير.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def contact_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"📞 **للتواصل مع الدعم الفني:**\n\n"
        f"• **الحساب:** @{OWNER_USERNAME}\n"
        f"• **الرابط:** [اضغط هنا](https://t.me/{OWNER_USERNAME})\n\n"
        f"يرجى ذكر مشكلتك بوضوح.",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def describe_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    waiting_for_issue[user_id] = True
    await query.edit_message_text(
        "📝 **صف مشكلتك بالتفصيل**\n\nاكتب مشكلتك الآن:",
        parse_mode="Markdown"
    )

async def handle_issue_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if not waiting_for_issue.get(user_id, False):
        return
    issue_text = update.message.text
    waiting_for_issue[user_id] = False
    await update.message.reply_text(
        "✅ **تم استلام مشكلتك!**\nسيتم التواصل معك قريباً.",
        parse_mode="Markdown"
    )
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🆘 **مشكلة جديدة!**\n\n"
             f"👤 الاسم: {user.first_name}\n"
             f"🆔 المعرف: {username}\n"
             f"📱 الرقم: `{user.id}`\n"
             f"📝 المشكلة:\n{issue_text}",
        parse_mode="Markdown"
    )

# ================== معالج الأزرار ==================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "buy_note":
        keyboard = [
            [InlineKeyboardButton("💰 شام كاش", callback_data="pay_note_sham")],
            [InlineKeyboardButton("💎 الهرم", callback_data="pay_note_herm")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "📚 **نوطة رياضيات بكلوريا مهني**\n"
            f"💰 السعر: 500 ل.س (جديد) / 50,000 ل.س (قديم)\n\nاختر طريقة الدفع:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "buy_exams":
        keyboard = [
            [InlineKeyboardButton("💰 شام كاش", callback_data="pay_exams_sham")],
            [InlineKeyboardButton("💎 الهرم", callback_data="pay_exams_herm")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "📝 **نماذج رياضيات بكلوريا مهني**\n"
            f"💰 السعر: 200 ل.س (جديد) / 20,000 ل.س (قديم)\n\nاختر طريقة الدفع:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "buy_questions_free":
        file_url = FILE_URLS.get("questions")
        if file_url:
            await query.edit_message_text("✅ جاري إرسال الملف...")
            await query.message.reply_document(
                document=file_url,
                caption="❓ **أسئلة دورات سابقة مع الحلول**\n\n✅ مجاني بالكامل!",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ الرابط غير متوفر.")
    
    elif query.data == "help":
        keyboard = [
            [InlineKeyboardButton("📝 صف مشكلتك", callback_data="describe_issue")],
            [InlineKeyboardButton("📞 التواصل مع الدعم", callback_data="contact_owner")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_menu")]
        ]
        await query.edit_message_text(
            "🆘 **مركز المساعدة**\n\n"
            "• **صف مشكلتك**: اكتب مشكلتك وسيتم إرسالها\n"
            "• **التواصل المباشر**: تحدث مع الدعم\n\n"
            "نعتذر عن أي تأخير.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "contact_owner":
        await query.edit_message_text(
            f"📞 **للتواصل مع الدعم الفني:**\n\n"
            f"• **الحساب:** @{OWNER_USERNAME}\n"
            f"• **الرابط:** [اضغط هنا](https://t.me/{OWNER_USERNAME})\n\n"
            f"يرجى ذكر مشكلتك بوضوح.",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    
    elif query.data == "describe_issue":
        user_id = query.from_user.id
        waiting_for_issue[user_id] = True
        await query.edit_message_text(
            "📝 **صف مشكلتك بالتفصيل**\n\nاكتب مشكلتك الآن:",
            parse_mode="Markdown"
        )
    
    elif query.data == "back_to_menu":
        await start(update, context)
    
    # ================== خيارات الدفع ==================
    
    elif query.data == "pay_note_sham":
        context.user_data['pending_product'] = "note"
        context.user_data['pending_product_name'] = "نوطة رياضيات"
        context.user_data['pending_price'] = NOTE_PRICE
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="buy_note")]]
        await query.edit_message_text(
            f"💰 **شام كاش**\n\n"
            f"📊 المنتج: نوطة رياضيات\n"
            f"💵 المبلغ: 500 ل.س (جديد) / 50,000 ل.س (قديم)\n\n"
            f"🔗 رابط التحويل:\nhttps://sham.cash/transfer/{SHAM_CASH_ID}\n\n"
            f"✅ بعد التحويل، أرسل صورة الإيصال هنا",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "pay_note_herm":
        context.user_data['pending_product'] = "note"
        context.user_data['pending_product_name'] = "نوطة رياضيات"
        context.user_data['pending_price'] = NOTE_PRICE
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="buy_note")]]
        await query.edit_message_text(
            f"💎 **الهرم**\n\n"
            f"📊 المنتج: نوطة رياضيات\n"
            f"💵 المبلغ: 500 ل.س (جديد) / 50,000 ل.س (قديم)\n\n"
            f"📱 الرقم: {HERM_PHONE}\n"
            f"👤 الاسم: {HERM_NAME}\n\n"
            f"✅ بعد التحويل، أرسل صورة الإيصال هنا",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "pay_exams_sham":
        context.user_data['pending_product'] = "exams"
        context.user_data['pending_product_name'] = "نماذج امتحانية"
        context.user_data['pending_price'] = EXAMS_PRICE
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="buy_exams")]]
        await query.edit_message_text(
            f"💰 **شام كاش**\n\n"
            f"📊 المنتج: نماذج امتحانية\n"
            f"💵 المبلغ: 200 ل.س (جديد) / 20,000 ل.س (قديم)\n\n"
            f"🔗 رابط التحويل:\nhttps://sham.cash/transfer/{SHAM_CASH_ID}\n\n"
            f"✅ بعد التحويل، أرسل صورة الإيصال هنا",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif query.data == "pay_exams_herm":
        context.user_data['pending_product'] = "exams"
        context.user_data['pending_product_name'] = "نماذج امتحانية"
        context.user_data['pending_price'] = EXAMS_PRICE
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="buy_exams")]]
        await query.edit_message_text(
            f"💎 **الهرم**\n\n"
            f"📊 المنتج: نماذج امتحانية\n"
            f"💵 المبلغ: 200 ل.س (جديد) / 20,000 ل.س (قديم)\n\n"
            f"📱 الرقم: {HERM_PHONE}\n"
            f"👤 الاسم: {HERM_NAME}\n\n"
            f"✅ بعد التحويل، أرسل صورة الإيصال هنا",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# ================== استقبال الإيصالات ==================

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_or_update_user(user.id, user.username, user.first_name)
    
    if 'pending_product' not in context.user_data:
        await update.message.reply_text("⚠️ يرجى اختيار المنتج أولاً عبر /start")
        return
    
    product_name = context.user_data.get('pending_product_name')
    product_price = context.user_data.get('pending_price')
    
    short_id = f"{str(user.id)[-6:]}_{int(datetime.now().timestamp()) % 10000}"
    
    pending_orders[short_id] = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'product': context.user_data.get('pending_product'),
        'product_name': product_name,
        'price': product_price,
        'timestamp': datetime.now(),
        'status': 'pending'
    }
    
    await update.message.reply_text(
        f"✅ **تم استلام إيصالك!**\n\n"
        f"📋 المنتج: {product_name}\n"
        f"💵 المبلغ: {product_price} ل.س (جديد)\n"
        f"🆔 رقم الطلب: `{short_id}`\n\n"
        f"⏳ سيتم مراجعة طلبك خلال 24 ساعة.",
        parse_mode="Markdown"
    )
    
    price_text = f"{product_price} ل.س (جديد)"
    price_text += " / 50,000 ل.س (قديم)" if "نوطة" in product_name else " / 20,000 ل.س (قديم)"
    
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🆕 **طلب دفع جديد!**\n\n"
             f"📋 الطلب: `{short_id}`\n"
             f"👤 المستخدم: {user.first_name}\n"
             f"📚 المنتج: {product_name}\n"
             f"💵 المبلغ: {price_text}\n\n"
             f"✅ `/approve_{short_id}`\n"
             f"❌ `/reject_{short_id}`",
        parse_mode="Markdown"
    )
    
    if update.message.photo:
        photo = update.message.photo[-1]
        await context.bot.send_photo(chat_id=OWNER_ID, photo=photo, caption=f"إيصال الطلب: {short_id}")

# ================== الموافقة على الطلب ==================

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر للمالك فقط.")
        return
    
    text = update.message.text
    if "_" not in text:
        await update.message.reply_text("⚠️ الاستخدام الصحيح: `/approve_رقم_الطلب`")
        return
    
    short_id = text.split("_", 1)[1]
    
    order = pending_orders.get(short_id)
    if not order:
        await update.message.reply_text(f"❌ الطلب `{short_id}` غير موجود.")
        return
    
    order['status'] = 'approved'
    user_id = order['user_id']
    product = order['product']
    product_name = order['product_name']
    file_url = FILE_URLS.get(product)
    
    if not file_url:
        await update.message.reply_text(f"❌ خطأ: رابط المنتج '{product}' غير موجود")
        return
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ **تمت الموافقة على طلبك!**\n\n📚 المنتج: {product_name}\n📎 جاري إرسال الملف..."
    )
    
    if product == "note":
        caption = "📚 **نوطة رياضيات بكلوريا مهني**\nنوطة شاملة مع تمارين محلولة"
    elif product == "exams":
        caption = "📝 **نماذج رياضيات بكلوريا مهني**\nأسئلة رسمية مع الحلول النموذجية"
    else:
        caption = "📚 شكراً لثقتك"
    
    try:
        await context.bot.send_document(
            chat_id=user_id,
            document=file_url,
            caption=caption,
            parse_mode="Markdown"
        )
        await update.message.reply_text(f"✅ تم إرسال ملف '{product_name}' للمستخدم {order['first_name']} بنجاح!")
    except Exception as e:
        await update.message.reply_text(
            f"❌ فشل إرسال الملف!\n\n"
            f"الخطأ: {str(e)[:200]}\n\n"
            f"🔗 رابط الملف (أرسله يدوياً):\n{file_url}"
        )

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ هذا الأمر للمالك فقط.")
        return
    
    text = update.message.text
    if "_" not in text:
        await update.message.reply_text("⚠️ الاستخدام: `/reject_رقم_الطلب`")
        return
    
    short_id = text.split("_", 1)[1]
    
    order = pending_orders.get(short_id)
    if not order:
        await update.message.reply_text(f"❌ الطلب {short_id} غير موجود.")
        return
    
    order['status'] = 'rejected'
    await context.bot.send_message(
        chat_id=order['user_id'],
        text=f"❌ **عذراً، تم رفض طلبك.**\n\nللتواصل مع الدعم: @{OWNER_USERNAME}"
    )
    await update.message.reply_text(f"✅ تم رفض الطلب {short_id}.")

# ================== تشغيل البوت ==================

def main():
    init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("questions", questions_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("approve", approve_payment))
    app.add_handler(CommandHandler("reject", reject_payment))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_issue_message))
    
    print("✅ البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
