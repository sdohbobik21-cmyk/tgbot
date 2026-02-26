import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─────────────────────────────────────────
# НАСТРОЙКИ — заполни перед запуском
# ─────────────────────────────────────────
BOT_TOKEN = "8587712492:AAFFHgDzfN6LV-BIQngaF9xWTstpNnVwHoI"          # токен от @BotFather
ADMIN_CHAT_ID = "-1003381583470"      # ID группы администраторов
# ─────────────────────────────────────────

logging.basicConfig(level=logging.INFO)

# Состояния диалога
LANGUAGE, ROLE, REQUEST = range(3)

# ──────────────────────────────────────────────
# ТЕКСТЫ
# ──────────────────────────────────────────────
TEXTS = {
    "ru": {
        "step2": (
            "Давайте познакомимся, чтобы наш Affiliate Manager "
            "мог подготовиться заранее 🙌\n\n"
            "Чтобы лучше вам помочь — как вы себя позиционируете?"
        ),
        "roles": [
            ("👤 Affiliate Manager", "Affiliate Manager"),
            ("🌐 Network",           "Network"),
            ("🏢 Brand Representative", "Brand Representative"),
            ("📊 Media Buying",      "Media Buying"),
        ],
        "ask_request": "Отлично! Напишите в паре слов, что вас интересует:",
        "done": (
            "✅ Спасибо! Передал вашу заявку нашему Affiliate Manager. "
            "Он напишет вам в ближайшее время."
        ),
    },
    "en": {
        "step2": (
            "Let's get acquainted so our Affiliate Manager "
            "can prepare in advance 🙌\n\n"
            "So we can help you better — what best describes you?"
        ),
        "roles": [
            ("👤 Affiliate Manager", "Affiliate Manager"),
            ("🌐 Network",           "Network"),
            ("🏢 Brand Representative", "Brand Representative"),
            ("📊 Media Buying",      "Media Buying"),
        ],
        "ask_request": "Great! Briefly tell us what you're looking for:",
        "done": (
            "✅ Thank you! Your request has been forwarded to our "
            "Affiliate Manager. They'll be in touch shortly."
        ),
    },
}

# ──────────────────────────────────────────────
# ШАГИ
# ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ]
    await update.message.reply_text(
        "👋 Здравствуйте! / Hello!\n"
        "Выберите пожалуйста язык / Please select a language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return LANGUAGE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]          # "ru" или "en"
    context.user_data["lang"] = lang
    t = TEXTS[lang]

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"role_{value}")]
        for label, value in t["roles"]
    ]
    await query.edit_message_text(t["step2"], reply_markup=InlineKeyboardMarkup(keyboard))
    return ROLE


async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    role = query.data.replace("role_", "")
    context.user_data["role"] = role
    lang = context.user_data["lang"]

    await query.edit_message_text(TEXTS[lang]["ask_request"])
    return REQUEST


async def receive_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = context.user_data.get("lang", "ru")
    role = context.user_data.get("role", "—")
    text = update.message.text

    # Автоответ пользователю
    await update.message.reply_text(TEXTS[lang]["done"])

    # Уведомление в чат администраторов
    username = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
    name = user.full_name or "—"
    flag = "🇷🇺" if lang == "ru" else "🇬🇧"

    admin_msg = (
        f"🔔 <b>Новая заявка!</b>\n\n"
        f"👤 {name} ({username})\n"
        f"{flag} Язык: {'RU' if lang == 'ru' else 'EN'}\n"
        f"🏷 Роль: {role}\n\n"
        f"💬 Запрос:\n{text}"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_msg,
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог прерван. Напишите /start чтобы начать заново.")
    return ConversationHandler.END


# ──────────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [CallbackQueryHandler(choose_language, pattern="^lang_")],
            ROLE:     [CallbackQueryHandler(choose_role,     pattern="^role_")],
            REQUEST:  [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_request)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("Бот запущен ✅")
    app.run_polling()


if __name__ == "__main__":
    main()
