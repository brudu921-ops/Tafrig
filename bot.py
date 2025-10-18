import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ====== تنظیمات ======
TOKEN = 'YOUR_BOT_TOKEN'  # جایگزین کن با توکن بات‌فادر
CHANNEL_ID = '@your_channel'  # جایگزین کن با آدرس کانالت
ADMINS = [123456789]  # آی‌دی تلگرام خودت
DB_PATH = 'data.db'

# ====== لاگ ======
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====== دیتابیس ======
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_name TEXT,
            user_name TEXT,
            part TEXT,
            content TEXT)''')
conn.commit()

# ====== دستورات ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 منو", callback_data='menu')]]
    await update.message.reply_text('سلام! من ربات دروس هستم.', reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # نمایش درس‌ها (از دیتابیس)
    c.execute("SELECT DISTINCT lesson_name FROM lessons")
    lessons = c.fetchall()
    keyboard = [[InlineKeyboardButton(lesson[0], callback_data=f"lesson_{lesson[0]}")] for lesson in lessons]
    await query.edit_message_text('درس‌ها:', reply_markup=InlineKeyboardMarkup(keyboard))

async def lesson_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lesson_name = query.data.replace('lesson_', '')
    # نمایش مخاطبین
    c.execute("SELECT DISTINCT user_name FROM lessons WHERE lesson_name=?", (lesson_name,))
    users = c.fetchall()
    keyboard = [[InlineKeyboardButton(user[0], callback_data=f"user_{lesson_name}_{user[0]}")] for user in users]
    await query.edit_message_text(f'مخاطبین درس {lesson_name}:', reply_markup=InlineKeyboardMarkup(keyboard))

async def user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace('user_', '').split('_', 1)
    lesson_name = data[0]
    user_name = data[1]
    # نمایش مطالب
    c.execute("SELECT id, content FROM lessons WHERE lesson_name=? AND user_name=?", (lesson_name, user_name))
    contents = c.fetchall()
    text = ''
    for content in contents:
        text += f"{content[1]}\n\n"
    await query.edit_message_text(f'مطالب {user_name} در درس {lesson_name}:\n\n{text}')

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = msg.text or ''
    # چک قالب هشتگ‌ها
    if text.count('#') >= 3:
        lines = text.splitlines()
        lesson_name = lines[0].replace('#','').strip()
        user_name = lines[1].replace('#','').strip()
        part = lines[2].replace('#','').strip()
        # ذخیره در دیتابیس
        c.execute("INSERT INTO lessons (lesson_name,user_name,part,content) VALUES (?,?,?,?)", (lesson_name,user_name,part,text))
        conn.commit()
        # حذف پیام از کانال (اگر ربات ادمین باشه)
        try:
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
        except:
            pass
        await msg.reply_text("مطالبت ذخیره شد ✅")
    else:
        await msg.reply_text("لطفاً قالب درست را رعایت کنید.")

# ====== اپلیکیشن ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(lesson_handler, pattern="^lesson_"))
app.add_handler(CallbackQueryHandler(user_handler, pattern="^user_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("ربات آماده است...")
app.run_polling()
