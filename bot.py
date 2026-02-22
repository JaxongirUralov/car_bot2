from suppliers import SUPPLIER_CHAT_IDS, SUPPLIER_PARTS

from db import init_db, save_order, get_all_orders
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 261688257

CAR_MODELS = ["S", "H", "V"]
CAR_OPTIONS = ["LS", "LT", "Premier"]
CAR_COLORS = ["Red", "Black", "White"]


# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("KingGhost brandining rasmiy telegram botiga Xush kelibsiz! 🚗\n/order bilan buyurtma qilishni boshlang")


async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    keyboard = [[InlineKeyboardButton(m, callback_data=f"model_{m}")]
                for m in CAR_MODELS]

    await update.message.reply_text(
        "Iltimos, o'zingiz yoqtirgan Modelni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= CALLBACK =================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # MODEL
    if data.startswith("model_"):
        context.user_data["model"] = data.replace("model_", "")

        keyboard = [[InlineKeyboardButton(o, callback_data=f"option_{o}")]
                    for o in CAR_OPTIONS]

        await query.edit_message_text(
            "Variantni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # OPTION
    elif data.startswith("option_"):
        context.user_data["option"] = data.replace("option_", "")

        keyboard = [[InlineKeyboardButton(c, callback_data=f"color_{c}")]
                    for c in CAR_COLORS]

        await query.edit_message_text(
            "Rangni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # COLOR
    elif data.startswith("color_"):
        context.user_data["color"] = data.replace("color_", "")

        context.user_data["step"] = "first_name"

        await query.edit_message_text("Iltimos ismingizni kiriting:")

    # CONFIRM YES
    elif data == "confirm_yes":
        await finalize_order(query, context)

    # CONFIRM NO
    elif data == "confirm_no":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Buyurtma bekor qilindi.\n/order bilan qayta boshlang."
        )


# ================= TEXT =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if not step:
        await update.message.reply_text("Iltimos /order bilan boshlang.")
        return

    if step == "first_name":
        context.user_data["first_name"] = update.message.text
        context.user_data["step"] = "last_name"
        await update.message.reply_text("Familyangizni kiriting:")

    elif step == "last_name":
        context.user_data["last_name"] = update.message.text
        context.user_data["step"] = "phone"

        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Telefon yuborish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await update.message.reply_text(
            "Iltimos, qayta aloqa uchun pastdagi tugma orqali telefon raqamingizni yuboring:",
            reply_markup=kb
        )


# ================= CONTACT =================

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "phone":
        return

    context.user_data["phone"] = update.message.contact.phone_number

    data = context.user_data

    summary = f"""
📝 Buyurtma ma’lumotlari:

🚗 Model: {data['model']}
⚙️ Variant: {data['option']}
🎨 Rang: {data['color']}
👤 Ism: {data['first_name']}
👤 Familya: {data['last_name']}
📞 Telefon: {data['phone']}

Tasdiqlaysizmi?
"""

    keyboard = [
        [
            InlineKeyboardButton("✅ Ha", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Yo‘q", callback_data="confirm_no"),
        ]
    ]

    await update.message.reply_text(
        summary,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= FINALIZE =================

async def finalize_order(query, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data

    needed = ["model", "option", "color", "first_name", "last_name", "phone"]

    for key in needed:
        if key not in data:
            await query.edit_message_text(
                "❌ Buyurtma ma’lumotlari to‘liq emas. /order bilan qayta boshlang."
            )
            context.user_data.clear()
            return

    order_data = {
        "user_id": query.from_user.id,
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "phone": data["phone"],
        "model": data["model"],
        "option": data["option"],
        "color": data["color"],
    }

    # 🔥 THIS LINE IS IMPORTANT
    order_code = save_order(order_data)

    # Send confirmation to user
    await query.edit_message_text(
        f"✅ Buyurtma muvaffaqiyatli qabul qilindi.\n\n🆔 Order ID: {order_code}"
    )

    # Send order to admin instantly
    admin_text = f"""
🚨 YANGI BUYURTMA 🚨

🆔 Order ID: {order_code}
👤 Mijoz: {data['first_name']} {data['last_name']}
📞 Tel: {data['phone']}
🚗 Mashina: {data['model']}/{data['option']}/{data['color']}
"""

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text
    )


    await notify_suppliers(
    context,
    order_code,
    data["model"],
    data["option"]
    )


    context.user_data.clear()

# ================= ADMIN =================

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Siz admin emassiz.")
        return

    orders = get_all_orders()

    if not orders:
        await update.message.reply_text("Buyurtmalar yo‘q.")
        return

    text = ""

    for o in orders:
        id_, order_code, user_id, first, last, phone, model, option, color, created = o

        text += f"""
ID: {id_}
Order ID: {order_code}
Mijoz: {first} {last}
Tel: {phone}
Mashina: {model}/{option}/{color}
Vaqt: {created}
--------------------
"""

    await update.message.reply_text(text)


async def notify_suppliers(context, order_code, model, option):
    supplier_orders = {}

    # 1️⃣ Filter matching parts
    for item in SUPPLIER_PARTS:
        if item["model"] == model and item["option"] == option:
            supplier = item["supplier"]

            if supplier not in supplier_orders:
                supplier_orders[supplier] = []

            supplier_orders[supplier].append(
                f"- {item['part']} x{item['qty']}"
            )

    # 2️⃣ Send message to each supplier
    for supplier, parts in supplier_orders.items():
        chat_id = SUPPLIER_CHAT_IDS.get(supplier)

        if not chat_id:
            continue

        text = f"""
🚗 NEW PARTS ORDER

🆔 Order ID: {order_code}
Model: {model}
Variant: {option}

Required Parts:
{chr(10).join(parts)}
"""

        await context.bot.send_message(
            chat_id=chat_id,
            text=text
        )


# ================= MAIN =================

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()