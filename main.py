import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
GROUP_CHAT_ID = -1001234567890  # сюда вставь id своей группы

PRODUCTS = [
    "Товар 1",
    "Товар 2",
    "Товар 3",
    "Товар 4",
]

# Состояния диалога
CHOOSE_PRODUCTS, ENTER_NAME, ENTER_ADDRESS, ENTER_PHONE = range(4)


def products_keyboard(selected: list[str]) -> ReplyKeyboardMarkup:
    rows = []
    for product in PRODUCTS:
        mark = "✅ " if product in selected else ""
        rows.append([f"{mark}{product}"])

    rows.append(["Готово"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["selected_products"] = []

    await update.message.reply_text(
        "Выберите 2 товара. Нажимайте на кнопки.\n"
        "Когда выберете 2 товара, нажмите «Готово».",
        reply_markup=products_keyboard([]),
    )
    return CHOOSE_PRODUCTS


async def choose_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    selected = context.user_data.get("selected_products", [])

    if text == "Готово":
        if len(selected) != 2:
            await update.message.reply_text(
                f"Сейчас выбрано {len(selected)} из 2 товаров. "
                f"Пожалуйста, выберите ровно 2 товара.",
                reply_markup=products_keyboard(selected),
            )
            return CHOOSE_PRODUCTS

        await update.message.reply_text(
            "Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ENTER_NAME

    clean_text = text.replace("✅ ", "")

    if clean_text not in PRODUCTS:
        await update.message.reply_text(
            "Пожалуйста, выбирайте товары только кнопками.",
            reply_markup=products_keyboard(selected),
        )
        return CHOOSE_PRODUCTS

    if clean_text in selected:
        selected.remove(clean_text)
    else:
        if len(selected) >= 2:
            await update.message.reply_text(
                "Можно выбрать только 2 товара. "
                "Снимите один выбор, если хотите заменить.",
                reply_markup=products_keyboard(selected),
            )
            return CHOOSE_PRODUCTS
        selected.append(clean_text)

    context.user_data["selected_products"] = selected

    await update.message.reply_text(
        f"Выбрано: {', '.join(selected) if selected else 'ничего'}",
        reply_markup=products_keyboard(selected),
    )
    return CHOOSE_PRODUCTS


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data["name"] = name

    await update.message.reply_text("Введите адрес:")
    return ENTER_ADDRESS


async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text.strip()
    context.user_data["address"] = address

    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Теперь отправьте номер телефона кнопкой ниже:",
        reply_markup=contact_keyboard,
    )
    return ENTER_PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.contact:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопку «Отправить контакт»."
        )
        return ENTER_PHONE

    contact = update.message.contact
    phone_number = contact.phone_number

    # Можно дополнительно проверить, что контакт принадлежит самому пользователю:
    if contact.user_id and update.effective_user and contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "Пожалуйста, отправьте именно свой контакт кнопкой."
        )
        return ENTER_PHONE

    context.user_data["phone"] = phone_number

    selected_products = context.user_data.get("selected_products", [])
    name = context.user_data.get("name", "")
    address = context.user_data.get("address", "")

    user = update.effective_user
    username = f"@{user.username}" if user and user.username else "без username"

    text_for_group = (
        "📦 Новая заявка\n\n"
        f"🛍 Товары: {', '.join(selected_products)}\n"
        f"👤 Имя: {name}\n"
        f"📍 Адрес: {address}\n"
        f"📞 Телефон: {phone_number}\n"
        f"👤 Telegram: {username}\n"
        f"🆔 User ID: {user.id if user else 'unknown'}"
    )

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=text_for_group,
    )

    await update.message.reply_text(
        "Спасибо! Ваша заявка отправлена.",
        reply_markup=ReplyKeyboardRemove(),
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Заказ отменен.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(False)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_PRODUCTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_products)
            ],
            ENTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)
            ],
            ENTER_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address)
            ],
            ENTER_PHONE: [
                MessageHandler(filters.CONTACT, enter_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
    