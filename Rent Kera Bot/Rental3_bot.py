import logging
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from functools import wraps

# --- CONFIGURATION ---
# IMPORTANT: Fill in these three values
BOT_TOKEN = "7643226611:AAGjI3CU28teLzWx3sep27-GDD-nLVswlmY"
GROUP_CHAT_ID = -1003216770769  # Your Management Group ID (e.g., -100...)
ADMIN_ID = 773623047            # YOUR personal User ID

# --- LOGGING ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- LANGUAGE & MESSAGES (Includes English and Amharic) ---

LANG = {
    'EN': {
        'SUBMIT_RECEIPT': "🧾 Submit Receipt",
        'ADD_TENANT': "➕ Add Tenant",
        'DELETE_TENANT': "❌ Delete Tenant",
        'LIST_TENANTS': "📋 List Tenants",
        'WELCOME': "👋 Welcome! Please select an option below.",
        'ACCESS_DENIED': "🚫 Access denied. Only the administrator can use this command.",
        'SELECT_LANG': "🌍 Please select your preferred language:",
        'NO_TENANTS': "⚠ No tenants registered yet. Contact Admin.",
        'SELECT_NAME': "👤 **Select your name from the list:**",
        'CANCEL': "❌ Cancel",
        'ACTION_CANCELLED': "❌ Action cancelled.",
        'SELECTED': "✅ Selected:",
        'HOW_MANY_MONTHS': "🗓️ **How many months are you paying for?**",
        'SELECT_MONTH': "📅 **Which month is the start of this payment period?**", # NEW
        'PAYMENT_PERIOD': "🗓️ Payment period:",
        'PAYMENT_FOR': "Payment Start Month:", # NEW
        'MONTHS': [ # NEW: English Months
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ],
        'UPLOAD_PROOF': "📸 **Please upload your payment proof now.** (Photo, PDF, Document, or a Payment Link text)",
        'SESSION_EXPIRED': "⚠ Session expired. Please start over with /start.",
        'TENANT_NOT_FOUND': "Error: Tenant not found in database. Please contact admin.",
        'NEW_RECEIPT': "🧾 **New Receipt from {name}**",
        'PERIOD': "Period: {months} month(s)",
        'USER': "User: {username}",
        'DATE': "Date: {date}",
        'RECEIPT_SUCCESS': "✅ Receipt submitted successfully!",
        'RECEIPT_ERROR': "❌ Error sending receipt. Check bot permissions and Topic ID.",
        'ENTER_NAME': "📝 Enter the **Name** of the new tenant:",
        'ENTER_TOPIC': "🔢 Now enter the **Topic ID** for this tenant.\n(You can find this ID in the browser URL when viewing the topic, e.g., 45)",
        'ADDED': "✅ Added **{name}** (Topic: {topic_id})",
        'NAME_EXISTS': "❌ Error: Name already exists.",
        'INVALID_ID': "❌ Invalid ID. Please enter a number.",
        'TAP_TO_REMOVE': "❌ **Tap a tenant to remove them:**",
        'NO_TENANTS_DEL': "No tenants to delete.",
        'TENANT_DELETED': "✅ Tenant **{name}** deleted.",
        'NO_TENANTS_CFG': "📋 **No tenants are currently configured.**",
        'CURRENT_TENANTS': "📋 **Current Tenants:**",
        'OPERATION_CANCELLED': "🚫 Operation cancelled.",
    },
    'AM': {
        'SUBMIT_RECEIPT': "🧾 ደረሰኝ አስገባ",
        'ADD_TENANT': "➕ ተከራይ አክል",
        'DELETE_TENANT': "❌ ተከራይ ሰርዝ",
        'LIST_TENANTS': "📋 ተከራዮችን ዝርዝር",
        'WELCOME': "👋 እንኳን ደህና መጡ! እባክዎ አማራጭ ይምረጡ።",
        'ACCESS_DENIED': "🚫 መዳረሻ ተከልክሏል. አስተዳዳሪ ብቻ ነው ሊጠቀም የሚችለው።",
        'SELECT_LANG': "🌍 እባክዎ የሚመርጡትን ቋንቋ ይምረጡ:",
        'NO_TENANTS': "⚠ እስካሁን ተከራይ አልተመዘገበም። አስተዳዳሪውን ያነጋግሩ።",
        'SELECT_NAME': "👤 **እባክዎ ስምዎን ይምረጡ:**",
        'CANCEL': "❌ ሰርዝ",
        'ACTION_CANCELLED': "❌ ተግባር ተሰርዟል።",
        'SELECTED': "✅ ተመርጧል:",
        'HOW_MANY_MONTHS': "🗓️ **ለስንት ወር ነው የሚከፍሉት?**",
        'SELECT_MONTH': "📅 **ይህ የክፍያ ጊዜ የሚጀምረው በየትኛው ወር ነው?**", # NEW
        'PAYMENT_PERIOD': "🗓️ የክፍያ ጊዜ:",
        'PAYMENT_FOR': "የክፍያ መጀመሪያ ወር:", # NEW
        'MONTHS': [ # NEW: Amharic/Ethiopian Calendar Months
            "መስከረም", "ጥቅምት", "ህዳር", "ታህሳስ", "ጥር", "የካቲት", 
            "መጋቢት", "ሚያዝያ", "ግንቦት", "ሰኔ", "ሐምሌ", "ነሐሴ"
        ], 
        'UPLOAD_PROOF': "📸 **እባክዎ አሁን የክፍያ ማረጋገጫዎን ይላኩ።** (ፎቶ፣ ሰነድ፣ ወይም አገናኝ)",
        'SESSION_EXPIRED': "⚠ ክፍለ ጊዜው አልፏል። እባክዎ በ /start እንደገና ይጀምሩ።",
        'TENANT_NOT_FOUND': "ስህተት: ተከራይ በዳታቤዝ ውስጥ አልተገኘም። እባክዎ አስተዳዳሪውን ያነጋግሩ።",
        'NEW_RECEIPT': "🧾 **ከ{name} አዲስ ደረሰኝ**",
        'PERIOD': "የክፍያ ጊዜ: {months} ወር",
        'USER': "ተጠቃሚ: {username}",
        'DATE': "ቀን: {date}",
        'RECEIPT_SUCCESS': "✅ ደረሰኝ በተሳካ ሁኔታ ገብቷል!",
        'RECEIPT_ERROR': "❌ ደረሰኝ በመላክ ላይ ስህተት። የቦት ፍቃዶችን እና የርዕስ መታወቂያውን ያረጋግጡ።",
        'ENTER_NAME': "📝 የአዲሱን ተከራይ **ስም** ያስገቡ:",
        'ENTER_TOPIC': "🔢 አሁን ለዚህ ተከራይ **የርዕስ መታወቂያውን** (Topic ID) ያስገቡ።\n(ይህን መታወቂያ በTopics ውስጥ በማየት ማግኘት ይችላሉ፣ ለምሳሌ 45)",
        'ADDED': "✅ **{name}** (ርዕስ: {topic_id}) ታክሏል",
        'NAME_EXISTS': "❌ ስህተት: ስሙ አስቀድሞ አለ።",
        'INVALID_ID': "❌ ልክ ያልሆነ መታወቂያ። እባክዎ ቁጥር ያስገቡ።",
        'TAP_TO_REMOVE': "❌ **ለማስወገድ ተከራይን ይንኩ:**",
        'NO_TENANTS_DEL': "የሚሰረዙ ተከራዮች የሉም።",
        'TENANT_DELETED': "✅ ተከራይ **{name}** ተሰርዟል።",
        'NO_TENANTS_CFG': "📋 **ምንም ተከራዮች በአሁኑ ጊዜ አልተዋቀሩም።**",
        'CURRENT_TENANTS': "📋 **አሁን ያሉት ተከራዮች:**",
        'OPERATION_CANCELLED': "🚫 ተግባር ተሰርዟል።",
    }
}

def get_message(key, context, lang_code='EN', **kwargs):
    """Retrieves a localized message string, defaulting to English if no language is set."""
    # For Admin flow, default to English (Admin buttons are EN only), otherwise use stored language
    # This also handles the case where lang is not set yet (e.g., in start_submission)
    if context.user_data.get('lang') in LANG:
        lang_code = context.user_data['lang']
    
    # Use the provided lang_code if context doesn't have one, or if it's explicitly passed
    msg = LANG.get(lang_code, LANG['EN']).get(key, f"MISSING_KEY_{key}")
    return msg.format(**kwargs)

# --- DATABASE SETUP ---
DB_NAME = "tenants.db"

def init_db():
    """Initialize the database table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            topic_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_tenants():
    """Fetch all tenants as a list of dictionaries."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, topic_id FROM tenants ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [{"name": r[0], "topic_id": r[1]} for r in rows]

def get_tenant_topic_id(name):
    """Fetch topic ID by tenant name."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT topic_id FROM tenants WHERE name = ?", (name,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def add_tenant_to_db(name, topic_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO tenants (name, topic_id) VALUES (?, ?)", (name, topic_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_tenant_from_db(name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tenants WHERE name = ?", (name,))
    conn.commit()
    conn.close()

# --- STATES ---
(
    SELECT_LANG,        # 0
    SELECT_TENANT,      # 1
    SELECT_PERIOD,      # 2
    SELECT_MONTH,       # 3 <--- NEW STATE
    WAIT_FOR_RECEIPT,   # 4
    ADD_NAME,           # 5
    ADD_TOPIC,          # 6
    DELETE_SELECT       # 7
) = range(8) # Updated range to 8

# --- UTILITY ---
def admin_only(func):
    """Decorator to restrict access to admin users."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            if update.message:
                # Use English default for admin denial message
                await update.message.reply_text(get_message('ACCESS_DENIED', context, 'EN')) 
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapper

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the main menu."""
    # Use English strings for fixed menu buttons for consistency in the message filter regex
    keyboard = [[KeyboardButton(LANG['EN']['SUBMIT_RECEIPT'])]]
    
    # If user is Admin, show extra controls
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([
            KeyboardButton(LANG['EN']['ADD_TENANT']), 
            KeyboardButton(LANG['EN']['DELETE_TENANT'])
        ])
        keyboard.append([KeyboardButton(LANG['EN']['LIST_TENANTS'])])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        LANG['EN']['WELCOME'], # Use English welcome for universal start command
        reply_markup=reply_markup
    )

async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: Prompt tenant to select language."""
    
    # Inline keyboard for language selection (English for button labels here)
    lang_keyboard = [
        [InlineKeyboardButton("English (EN)", callback_data="lang_EN")],
        [InlineKeyboardButton("አማርኛ (AM)", callback_data="lang_AM")],
        [InlineKeyboardButton(LANG['EN']['CANCEL'], callback_data="cancel")]
    ]
    
    await update.message.reply_text(
        LANG['EN']['SELECT_LANG'], # Use English key, will be translated if context has lang
        reply_markup=InlineKeyboardMarkup(lang_keyboard)
    )
    return SELECT_LANG

async def lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Save language and proceed to tenant selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        # Use English since we haven't selected a language yet, but it's safe to use get_message
        await query.edit_message_text(get_message('ACTION_CANCELLED', context, 'EN')) 
        return ConversationHandler.END

    # Extract lang code: lang_EN
    _, lang_code = query.data.split("_")
    context.user_data["lang"] = lang_code
    
    # Now proceed to SELECT_TENANT state
    tenants = get_tenants()
    
    if not tenants:
        await query.edit_message_text(get_message('NO_TENANTS', context))
        return ConversationHandler.END

    # Create a list of buttons (2 per row)
    keyboard = []
    row = []
    for t in tenants:
        btn = InlineKeyboardButton(t['name'], callback_data=f"select_{t['name']}")
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(get_message('CANCEL', context), callback_data="cancel")])
    
    await query.edit_message_text(
        get_message('SELECT_NAME', context),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_TENANT

async def tenant_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Save tenant name and ask for payment period."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(get_message('ACTION_CANCELLED', context))
        return ConversationHandler.END

    # Extract data: select_John Doe
    _, name = query.data.split("_", 1)
    
    # Save to user context
    context.user_data["tenant_name"] = name
    
    # Generate period selection keyboard
    period_keyboard = [
        [InlineKeyboardButton("1 Month", callback_data="period_1"),
         InlineKeyboardButton("2 Months", callback_data="period_2")],
        [InlineKeyboardButton("3 Months", callback_data="period_3"),
         InlineKeyboardButton("6 Months", callback_data="period_6")],
        [InlineKeyboardButton(get_message('CANCEL', context), callback_data="cancel")]
    ]
    
    await query.edit_message_text(
        f"{get_message('SELECTED', context)} **{name}**\n\n{get_message('HOW_MANY_MONTHS', context)}",
        reply_markup=InlineKeyboardMarkup(period_keyboard),
        parse_mode="Markdown"
    )
    return SELECT_PERIOD

async def select_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Save period and ask for the starting month."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(get_message('ACTION_CANCELLED', context))
        return ConversationHandler.END
    
    # Extract data: period_3
    _, months = query.data.split("_")
    
    # Save to user context
    context.user_data["payment_months"] = months
    
    # Get language and month names
    lang_code = context.user_data.get('lang', 'EN')
    months_list = LANG[lang_code]['MONTHS']
    
    # Create month selection keyboard (3 buttons per row)
    month_keyboard = []
    row = []
    for month in months_list:
        btn = InlineKeyboardButton(month, callback_data=f"month_{month}")
        row.append(btn)
        if len(row) == 3:
            month_keyboard.append(row)
            row = []
    if row:
        month_keyboard.append(row)
        
    month_keyboard.append([InlineKeyboardButton(get_message('CANCEL', context), callback_data="cancel")])

    # Format the period message
    period_msg = LANG[lang_code]['PAYMENT_PERIOD']
    try:
        # Use PERIOD key to correctly extract the localized unit ('month(s)' or 'ወር')
        months_unit = LANG[lang_code]['PERIOD'].split(': ')[1].split(' ')[1] 
    except IndexError:
        months_unit = "month(s)" # Fallback

    await query.edit_message_text(
        f"{period_msg} **{months} {months_unit}**\n\n"
        f"{get_message('SELECT_MONTH', context)}",
        reply_markup=InlineKeyboardMarkup(month_keyboard),
        parse_mode="Markdown"
    )
    return SELECT_MONTH # <--- TRANSITION TO NEW STATE

async def select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Save the starting month and ask for receipt proof."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(get_message('ACTION_CANCELLED', context))
        return ConversationHandler.END
    
    # Extract data: month_January or month_መስከረም
    _, month = query.data.split("_", 1)
    
    # Save to user context
    context.user_data["start_month"] = month
    
    # Prepare the confirmation message
    name = context.user_data.get("tenant_name", "Tenant")
    months = context.user_data.get("payment_months", "N/A")

    # Get localized unit for display
    lang_code = context.user_data.get('lang', 'EN')
    try:
        months_unit = LANG[lang_code]['PERIOD'].split(': ')[1].split(' ')[1] 
    except IndexError:
        months_unit = "month(s)" # Fallback

    summary_text = (
        f"{get_message('SELECTED', context)} **{name}**\n"
        f"{get_message('PAYMENT_PERIOD', context)} **{months} {months_unit}**\n"
        f"{get_message('PAYMENT_FOR', context)} **{month}**\n\n"
        f"{get_message('UPLOAD_PROOF', context)}"
    )

    await query.edit_message_text(
        summary_text,
        parse_mode="Markdown"
    )
    return WAIT_FOR_RECEIPT # <--- TRANSITION TO FINAL STATE


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Forward the receipt (Photo, Doc, or Link) to the group topic."""
    name = context.user_data.get("tenant_name")
    months = context.user_data.get("payment_months")
    start_month = context.user_data.get("start_month") # <--- NEW VARIABLE
    
    if not name or not months or not start_month:
        await update.message.reply_text(get_message('SESSION_EXPIRED', context))
        return ConversationHandler.END

    topic_id = get_tenant_topic_id(name)
    
    if not topic_id:
        await update.message.reply_text(get_message('TENANT_NOT_FOUND', context))
        return ConversationHandler.END

    # Get user info for log
    user = update.effective_user
    username_for_log = f"@{user.username}" if user.username else "N/A (No Telegram Username)"

    # Build the caption using localized strings
    caption_text = (
        get_message('NEW_RECEIPT', context, name=name) + "\n"
        + get_message('PERIOD', context, months=months) + "\n"
        + get_message('PAYMENT_FOR', context) + f" **{start_month}**\n" # <--- ADDED MONTH
        + get_message('USER', context, username=username_for_log) + "\n"
        + get_message('DATE', context, date=update.message.date.strftime('%Y-%m-%d %H:%M:%S'))
    )

    try:
        # Use a list of message send functions to simplify the logic
        send_funcs = []
        if update.message.photo:
            send_funcs.append((context.bot.send_photo, update.message.photo[-1].file_id))
        elif update.message.document:
            send_funcs.append((context.bot.send_document, update.message.document.file_id))
        elif update.message.text:
            link_caption = f"{caption_text}\n\n🔗 Proof Link/Details:\n{update.message.text}"
            send_funcs.append((context.bot.send_message, link_caption))
        
        if send_funcs:
            for send_func, content in send_funcs:
                kwargs = {
                    'chat_id': GROUP_CHAT_ID,
                    'message_thread_id': topic_id,
                    'parse_mode': "Markdown",
                }
                if send_func == context.bot.send_message:
                    kwargs['text'] = content
                else:
                    kwargs['caption'] = caption_text
                    if send_func == context.bot.send_photo:
                        kwargs['photo'] = content
                    elif send_func == context.bot.send_document:
                        kwargs['document'] = content

                await send_func(**kwargs)
        else:
            # Handle the case where a user sent something unsupported (e.g. sticker, video)
            await update.message.reply_text(get_message('UPLOAD_PROOF', context)) 
            return WAIT_FOR_RECEIPT # Stay in this state

        await update.message.reply_text(get_message('RECEIPT_SUCCESS', context))
    except Exception as e:
        logger.error(f"Error forwarding receipt to Topic ID {topic_id}: {e}")
        await update.message.reply_text(get_message('RECEIPT_ERROR', context))

    return ConversationHandler.END

# --- ADMIN FLOW (Add Tenant) ---

@admin_only
async def add_tenant_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin flow uses English for simplicity
    await update.message.reply_text(get_message('ENTER_NAME', context, 'EN'), parse_mode="Markdown")
    return ADD_NAME

@admin_only
async def get_new_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_name"] = update.message.text
    await update.message.reply_text(
        get_message('ENTER_TOPIC', context, 'EN'),
        parse_mode="Markdown"
    )
    return ADD_TOPIC

@admin_only
async def get_new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        topic_id = int(update.message.text)
        name = context.user_data.pop("new_name")
        
        if add_tenant_to_db(name, topic_id):
            await update.message.reply_text(get_message('ADDED', context, 'EN', name=name, topic_id=topic_id), parse_mode="Markdown")
        else:
            await update.message.reply_text(get_message('NAME_EXISTS', context, 'EN'))
    except ValueError:
        await update.message.reply_text(get_message('INVALID_ID', context, 'EN'))
    
    return ConversationHandler.END

# --- ADMIN FLOW (Delete Tenant) ---

@admin_only
async def delete_tenant_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenants = get_tenants()
    if not tenants:
        await update.message.reply_text(get_message('NO_TENANTS_DEL', context, 'EN'))
        return ConversationHandler.END

    keyboard = []
    for t in tenants:
        keyboard.append([InlineKeyboardButton(f"🗑 {t['name']}", callback_data=f"delete_{t['name']}")])
    
    keyboard.append([InlineKeyboardButton(get_message('CANCEL', context, 'EN'), callback_data="cancel")])
    
    await update.message.reply_text(
        get_message('TAP_TO_REMOVE', context, 'EN'),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return DELETE_SELECT

@admin_only
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text(get_message('OPERATION_CANCELLED', context, 'EN'))
        return ConversationHandler.END

    _, name = query.data.split("_", 1)
    delete_tenant_from_db(name)
    
    await query.edit_message_text(get_message('TENANT_DELETED', context, 'EN', name=name), parse_mode="Markdown")
    return ConversationHandler.END

@admin_only
async def list_tenants_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tenants = get_tenants()
    if not tenants:
        await update.message.reply_text(get_message('NO_TENANTS_CFG', context, 'EN'), parse_mode="Markdown")
        return
        
    msg = get_message('CURRENT_TENANTS', context, 'EN') + "\n"
    for t in tenants:
        msg += f"- {t['name']} (Topic: {t['topic_id']})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the current conversation."""
    # Determine the language based on whether context data exists, default to EN
    lang_code = context.user_data.get('lang', 'EN')
    
    try:
        if update.message:
            await update.message.reply_text(get_message('OPERATION_CANCELLED', context, lang_code))
        elif update.callback_query:
            await update.callback_query.edit_message_text(get_message('OPERATION_CANCELLED', context, lang_code))
    except Exception:
         # Handle case where the message might be too old to edit
         if update.callback_query:
             await update.callback_query.answer(get_message('OPERATION_CANCELLED', context, lang_code))
             
    context.user_data.clear()
    return ConversationHandler.END

# --- MAIN ---

def main():
    # 1. Initialize the SQLite database
    init_db()
    
    # 2. Build the application instance
    app = Application.builder().token(BOT_TOKEN).build()

    # Tenant Receipt Conversation (Flow: Lang -> Name -> Period -> Month -> Receipt)
    receipt_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{LANG['EN']['SUBMIT_RECEIPT']}$"), start_submission)],
        states={
            # Step 1: Language selection
            SELECT_LANG: [CallbackQueryHandler(lang_selected, pattern="^lang_|^cancel$")],
            # Step 2: Tenant name selection
            SELECT_TENANT: [CallbackQueryHandler(tenant_selected, pattern="^select_|^cancel$")],
            # Step 3: Payment period selection
            SELECT_PERIOD: [CallbackQueryHandler(select_period, pattern="^period_|^cancel$")],
            # Step 4: Month selection (NEW STEP)
            SELECT_MONTH: [CallbackQueryHandler(select_month, pattern="^month_|^cancel$")], 
            # Step 5: Wait for the payment proof (photo, document, or text link)
            WAIT_FOR_RECEIPT: [
                MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND, handle_receipt)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Admin Add Conversation
    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{LANG['EN']['ADD_TENANT']}$") & filters.User(ADMIN_ID), add_tenant_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_name)],
            ADD_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_new_topic)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Admin Delete Conversation
    del_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{LANG['EN']['DELETE_TENANT']}$") & filters.User(ADMIN_ID), delete_tenant_start)],
        states={
            # Ensured pattern filter is specific
            DELETE_SELECT: [CallbackQueryHandler(confirm_delete, pattern="^delete_|^cancel$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Basic Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(f"^{LANG['EN']['LIST_TENANTS']}$") & filters.User(ADMIN_ID), list_tenants_cmd))
    
    # Conversation Handlers
    app.add_handler(receipt_conv)
    app.add_handler(add_conv)
    app.add_handler(del_conv)

    logger.info("Bot is running...")
    # 3. Start the bot polling for updates
    app.run_polling()

if __name__ == "__main__":
    main()