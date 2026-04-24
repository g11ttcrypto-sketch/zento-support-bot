from telegram import Update
from telegram.ext import CommandHandler
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, Updater, CommandHandler, Filters
messages_store = {}
message_counter = 1


ADMIN_ID = 1346025315

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):


    user = update.effective_user
    text = update.message.text

    global message_counter


    msg_id = message_counter
    message_counter += 1 


    messages_store[msg_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "text": text,
        "status": "open"
    }    

    # ответ пользователю
    await update.message.reply_text(
        "Мы получили сообщение 🙌\nСкоро ответим!"
    )

    # переслать админу

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 #{msg_id}\n\n"
            f"👤 @{user.username or user.first_name}\n"
            f"ID: {user.id}\n\n"
            f"{text}\n\n"
            f"Статус: OPEN"
    )


    



async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    original_text = update.message.reply_to_message.text

    if "#" in original_text:
        try:
            msg_id = int(original_text.split("#")[1].split("\n")[0])
            if msg_id in messages_store:
                messages_store[msg_id]["status"] = "closed"
        except:
            pass

    if "ID:" not in original_text:
        return

    try:
        user_id = int(original_text.split("ID:")[1].split("\n")[0])
    except:
        return

    reply_text = update.message.text

    await context.bot.send_message(
        chat_id=user_id,
        text=f"💬 Ответ поддержки:\n\n{reply_text}"
    )


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



updater = Updater("8781903473:AAEPB-yBtv9ES6I4HVaZqRkUnNfaIwvO4Yc", use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.reply & Filters.text, admin_reply))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
dp.add_handler(CommandHandler("list", list_messages))

updater.start_polling()
updater.idle()