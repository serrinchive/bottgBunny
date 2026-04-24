import logging
import os

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

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ===== PATH =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WELCOME_IMAGE = os.path.join(BASE_DIR, "1.jpg")

# ===== SETTINGS =====
BOT_TOKEN = "8062677431:AAE3il3EfJDl0rbr9leLkfSMaPGtnEh5a_Y"
GROUP_CHAT_ID = -1003963616777  # <-- замени на свой

PRODUCTS = [
    "NOS 4 л (7000₽)",
    "NOS 5 л (8000₽)",
    "NOS 10 л (12000₽)",
]

# ===== STATES =====
START_ORDER, CHOOSE_PRODUCTS, ENTER_NAME, ENTER_ADDRESS, ENTER_PHONE = range(5)


# ===== KEYBOARDS =====
def start_keyboard():
    return ReplyKeyboardMarkup(
        [["Сделать заказ"]],
        resize_keyboard=True,
    )


def repeat_keyboard():
    return ReplyKeyboardMarkup(
        [["🔁 Повторить заказ"]],
        resize_keyboard=True,
    )


def products_keyboard():
    return ReplyKeyboardMarkup(
        [[p] for p in PRODUCTS],
        resize_keyboard=True,
    )


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    with open(WELCOME_IMAGE, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="Рады вас видеть в Bunny Ballon! Закажите NOS с доставкой 🚀",
        )

    await update.message.reply_text(
        "Нажмите кнопку ниже:",
        reply_markup=start_keyboard(),
    )

    return START_ORDER


# ===== START ORDER =====
async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "Сделать заказ":
        return START_ORDER

    await update.message.reply_text(
        "Выберите товар:",
        reply_markup=products_keyboard(),
    )

    return CHOOSE_PRODUCTS


# ===== CHOOSE PRODUCT =====
async def choose_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text not in PRODUCTS:
        await update.message.reply_text("Выберите товар кнопкой")
        return CHOOSE_PRODUCTS

    context.user_data["product"] = text

    await update.message.reply_text(
        "Введите имя:",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ENTER_NAME


# ===== NAME =====
async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите адрес:")
    return ENTER_ADDRESS


# ===== ADDRESS =====
async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
    )

    await update.message.reply_text(
        "Отправьте телефон:",
        reply_markup=keyboard,
    )

    return ENTER_PHONE


# ===== PHONE + FINISH =====
async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text

    user = update.effective_user

    product = context.user_data["product"]
    name = context.user_data["name"]
    address = context.user_data["address"]

    username = f"@{user.username}" if user.username else "нет username"

    text = (
        "📦 НОВЫЙ ЗАКАЗ\n\n"
        f"🛍 {product}\n"
        f"👤 {name}\n"
        f"📍 {address}\n"
        f"📞 {phone}\n"
        f"TG: {username}\n"
        f"ID: {user.id}"
    )

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)

    await update.message.reply_text(
        "Заказ принят ✅",
        reply_markup=repeat_keyboard(),
    )

    context.user_data.clear()
    return ConversationHandler.END


# ===== REPEAT =====
async def repeat_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start_order(update, context)


# ===== CANCEL =====
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Отменено")
    return ConversationHandler.END


# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ORDER: [MessageHandler(filters.TEXT, start_order)],
            CHOOSE_PRODUCTS: [MessageHandler(filters.TEXT, choose_products)],
            ENTER_NAME: [MessageHandler(filters.TEXT, enter_name)],
            ENTER_ADDRESS: [MessageHandler(filters.TEXT, enter_address)],
            ENTER_PHONE: [
                MessageHandler(filters.CONTACT, enter_phone),
                MessageHandler(filters.TEXT, enter_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)

    app.add_handler(
        MessageHandler(filters.Regex("^🔁 Повторить заказ$"), repeat_order)
    )

    app.run_polling()


if __name__ == "__main__":
    main()