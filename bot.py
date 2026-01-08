import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ===== DEBUG (VERY IMPORTANT FOR NOW) =====
print("DEBUG: BOT_TOKEN =", os.getenv("BOT_TOKEN"))
print("DEBUG: ADMIN_ID  =", os.getenv("ADMIN_ID"))


# ===== HELPERS =====
def get_admin_id():
    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        return None
    return int(admin_id)


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is running ✅")


# ===== /admin =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = get_admin_id()

    if admin_id is None:
        await update.message.reply_text(
            "❌ ADMIN_ID is not loaded from Railway variables"
        )
        return

    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not admin")
        return

    keyboard = [
        [InlineKeyboardButton("🧾 All orders", callback_data="all_orders")],
        [InlineKeyboardButton("🚗 View by supplier", callback_data="by_supplier")],
        [InlineKeyboardButton("❌ Delete order", callback_data="delete_order")]
    ]

    await update.message.reply_text(
        "🔐 Super admin panel:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===== BUTTON HANDLER =====
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "all_orders":
        await query.edit_message_text("📋 Here will be all orders")

    elif query.data == "by_supplier":
        await query.edit_message_text("🚗 Here will be orders by supplier")

    elif query.data == "delete_order":
        await query.edit_message_text("❌ Send order ID to delete")


# ===== MAIN =====
def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN is not set in Railway Variables")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
