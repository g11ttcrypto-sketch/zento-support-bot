from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1346025315

# ================= STORAGE =================
messages_store = {}
message_counter = 1
reply_targets = {}

# ================= HANDLE USER MESSAGE =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global message_counter

    user = update.effective_user
    text = update.message.text

    msg_id = message_counter
    message_counter += 1

    messages_store[msg_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "text": text,
        "status": "open",
    }

    # ответ пользователю
    await update.message.reply_text(
        "Мы получили сообщение 🙌\nСкоро ответим!"
    )

    # кнопка
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Ответить", callback_data=f"reply_{msg_id}")]
    ])

    # сообщение админу
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 #{msg_id}\n\n"
             f"👤 @{user.username or user.first_name}\n"
             f"ID: {user.id}\n\n"
             f"{text}\n\n"
             f"Статус: OPEN",
        reply_markup=keyboard
    )

# ================= BUTTON HANDLER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    data = query.data

    if data.startswith("reply_"):
        msg_id = int(data.split("_")[1])
        msg = messages_store.get(msg_id)

        if not msg:
            return

        reply_targets[ADMIN_ID] = msg["user_id"]

        await query.message.reply_text("✏️ Напиши ответ пользователю:")

# ================= ADMIN REPLY =================
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    # ответ через кнопку
    target = reply_targets.get(ADMIN_ID)
    if target:
        await context.bot.send_message(
            chat_id=target,
            text=f"💬 Ответ поддержки:\n\n{update.message.text}"
        )
        reply_targets.pop(ADMIN_ID)
        return

    # fallback (старый reply способ)
    if not update.message.reply_to_message:
        return

    original_text = update.message.reply_to_message.text

    if "ID:" not in original_text:
        return

    try:
        user_id = int(original_text.split("ID:")[1].split("\n")[0])
    except:
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=f"💬 Ответ поддержки:\n\n{update.message.text}"
    )

# ================= LIST COMMAND =================
async def list_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "📋 Открытые обращения:\n\n"

    for mid, msg in messages_store.items():
        if msg["status"] == "open":
            text += f"#{mid} @{msg['username']}\n{msg['text']}\n\n"

    if text.strip() == "📋 Открытые обращения:":
        text += "Нет открытых сообщений"

    await update.message.reply_text(text)

# ================= WEB SERVER (для Render) =================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

# ================= START =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, admin_reply))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("list", list_messages))

app.run_polling()