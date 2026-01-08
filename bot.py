import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome!\nUse /admin if you are admin."
    )


# ===== /admin =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return

    keyboard = [
        [InlineKeyboardButton("🧾 All orders", callback_data="all_orders")],
        [InlineKeyboardButton("🚗 View by supplier", callback_data="by_supplier")],
        [InlineKeyboardButton("❌ Delete order", callback_data="delete_order")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔐 Super admin panel:",
        reply_markup=reply_markup
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
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.run_polling()


if __name__ == "__main__":
    main()
