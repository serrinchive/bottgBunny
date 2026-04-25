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
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WELCOME_IMAGE = os.path.join(BASE_DIR, "1.jpg")

# ====== НАСТРОЙКИ ======
BOT_TOKEN = "8062677431:AAE3il3EfJDl0rbr9leLkfSMaPGtnEh5a_Y"
GROUP_CHAT_ID = -1003963616777  # <-- замени на свой
PRODUCTS = [
    "NOS 4 л (7000₽)",
    "NOS 5 л (8000₽)",
    "NOS 10 л (12000₽)",
]

# === СОСТОЯНИЯ ===
START_ORDER, CHOOSE_PRODUCTS, ENTER_NAME, ENTER_ADDRESS, ENTER_PHONE = range(5)


# === КЛАВИАТУРЫ ===
def start_keyboard():
    return ReplyKeyboardMarkup(
        [["Сделать заказ"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def repeat_keyboard():
    return ReplyKeyboardMarkup(
        [["🔁 Повторить заказ"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def products_keyboard():
    return ReplyKeyboardMarkup(
        [[p] for p in PRODUCTS],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    await update.message.reply_photo(
        photo=open(WELCOME_IMAGE, "rb"),
        caption="Рады вас видеть в нашем интернет магазине Bunny Ballon!"
                "                         У нас вы можете оформить заказ наших фирменных баллонов NOS"
                " (пищевая закись азота без примесей) с бесплатной доставкой.",
    )

    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы оформить заказ:",
        reply_markup=start_keyboard(),
    )

    return START_ORDER


# === НАЧАТЬ ЗАКАЗ ===
async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != "Сделать заказ":
        return START_ORDER

    await update.message.reply_text(
        "Выберите товар:",
        reply_markup=products_keyboard(),
    )

    return CHOOSE_PRODUCTS


# === ВЫБОР ТОВАРА ===
async def choose_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text not in PRODUCTS:
        await update.message.reply_text(
            "Выберите товар кнопкой:",
            reply_markup=products_keyboard(),
        )
        return CHOOSE_PRODUCTS

    context.user_data["product"] = text

    await update.message.reply_text(
        "Введите ваше имя:",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ENTER_NAME


# === ИМЯ ===
async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите адрес:")
    return ENTER_ADDRESS


# === АДРЕС ===
async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["address"] = update.message.text

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Отправить контакт", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Отправьте номер телефона:",
        reply_markup=keyboard,
    )

    return ENTER_PHONE


# === ТЕЛЕФОН + ФИНАЛ ===
async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone_number = update.message.contact.phone_number
    else:
        phone_number = update.message.text.strip()

    context.user_data["phone"] = phone_number

    product = context.user_data["product"]
    name = context.user_data["name"]
    address = context.user_data["address"]

    user = update.effective_user
    username = f"@{user.username}" if user.username else "нет username"

    # --- В ГРУППУ ---
    text_group = (
        "📦 НОВЫЙ ЗАКАЗ\n\n"
        f"🛍 Товар: {product}\n"
        f"👤 Имя: {name}\n"
        f"📍 Адрес: {address}\n"
        f"📞 Телефон: {phone_number}\n"
        f"👤 Telegram: {username}\n"
        f"🆔 ID: {user.id}"
    )

    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=text_group)

    # --- ПОЛЬЗОВАТЕЛЮ ---
    await update.message.reply_text(
        "✅ Заказ принят! В ближайшее время менеджер свяжется с вами для уточнения деталей.\n\n"
        "📦 Ваша заявка:\n"
        f"👤 Покупатель: {name}\n"
        f"📞 Телефон: {phone_number}\n"
        f"📍 Адрес: {address}\n"
        f"🛍 Товар: {product}",
        reply_markup=repeat_keyboard(),
    )

    context.user_data.clear()
    return ConversationHandler.END


# === ПОВТОР ЗАКАЗА ===
async def repeat_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "Выберите товар:",
        reply_markup=products_keyboard(),
    )

    context.user_data.clear()

    await update.message.reply_text(
        "Выберите товар:",
        reply_markup=products_keyboard(),
    )

    return CHOOSE_PRODUCTS


# === ОТМЕНА ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Заказ отменён.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ORDER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, start_order),
            ],
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

    app.add_handler(
        MessageHandler(filters.Regex("^🔁 Повторить заказ$"), repeat_order)
    )

    app.run_polling()


if __name__ == "__main__":
    main()