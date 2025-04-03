from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from modules.reset import extract_latest_netflix_reset_link
from modules.signin import extract_latest_netflix_signin_code
from database import init_db, add_emails, remove_email, get_emails, block_user, unblock_user, is_blocked, update_gmail_credentials, get_gmail_credentials

API_ID = "2104057670"
API_HASH = "bf87adfbc2c24c66904f3c36f3c0af3a"
BOT_TOKEN = "7521862287:AAEnZbQv72I6ATVkSWNpBrfQQKBBn7a3ju8"
ADMIN_ID = 123456789  # Replace with your Telegram user ID (integer)

app = Client("netflix_reset_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize database
init_db()

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = (
        "**Welcome to the Netflix Reset Bot!**\n\n"
        "This service allows you to retrieve your Netflix password reset link or sign-in code efficiently.\n\n"
        "*Commands:*\n"
        "- `/reset <email>` - Get your reset link\n"
        "- `/signin <email>` - Get your sign-in code\n"
        "- `/mymails` - View your whitelisted emails\n"
        "- `/remove <email>` - Remove an email from your whitelist\n\n"
        "**Note:** Links and codes must be from emails received within the last hour.\n"
        "Contact the admin to get whitelisted."
    )
    await message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("add") & filters.user(ADMIN_ID))
async def add_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/add <user_id> email1 email2 ...`", parse_mode=ParseMode.MARKDOWN)
        return

    text = command_parts[1].strip()
    parts = text.split(maxsplit=1)
    try:
        user_id = int(parts[0].strip())
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID. Use: `/add <user_id> email1 email2 ...`", parse_mode=ParseMode.MARKDOWN)
        return

    if len(parts) < 2:
        await message.reply_text("**Error:** Provide at least one email.", parse_mode=ParseMode.MARKDOWN)
        return

    emails_text = parts[1].strip()
    new_emails = [email.strip() for email in emails_text.split() if '@' in email]

    if not new_emails:
        await message.reply_text("**Error:** No valid email addresses provided.", parse_mode=ParseMode.MARKDOWN)
        return

    add_emails(user_id, new_emails)
    email_list = "\n".join([f"- `{email}`" for email in get_emails(user_id)])
    await message.reply_text(
        f"**Success:** User ID `{user_id}` updated with:\n{email_list}",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command("remove"))
async def remove_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/remove <email>`", parse_mode=ParseMode.MARKDOWN)
        return

    target_email = command_parts[1].strip()
    sender_id = message.from_user.id
    if is_blocked(sender_id):
        await message.reply_text("**Error:** You are blocked from using this bot.", parse_mode=ParseMode.MARKDOWN)
        return

    emails = get_emails(sender_id)
    if not emails:
        await message.reply_text("**Error:** You are not whitelisted.", parse_mode=ParseMode.MARKDOWN)
        return

    if remove_email(sender_id, target_email):
        email_list = "\n".join([f"- `{email}`" for email in get_emails(sender_id)])
        response_text = f"**Success:** Removed `{target_email}`.\nRemaining emails:\n{email_list}" if email_list else f"**Success:** Removed `{target_email}`. No emails remain."
        await message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("**Error:** Email not found in your whitelist.", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("mymails"))
async def mymails_command(client, message):
    sender_id = message.from_user.id
    if is_blocked(sender_id):
        await message.reply_text("**Error:** You are blocked from using this bot.", parse_mode=ParseMode.MARKDOWN)
        return

    emails = get_emails(sender_id)
    if not emails:
        await message.reply_text("**Error:** You are not whitelisted. Contact the admin.", parse_mode=ParseMode.MARKDOWN)
        return

    email_list = "\n".join([f"- `{email}`" for email in emails])
    response_text = (
        f"**Your Whitelisted Emails:**\n"
        f"Associated with your account (ID: `{sender_id}`):\n"
        f"{email_list}"
    )
    await message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("block") & filters.user(ADMIN_ID))
async def block_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/block <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        user_id = int(command_parts[1].strip())
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID.", parse_mode=ParseMode.MARKDOWN)
        return

    block_user(user_id)
    await message.reply_text(f"**Success:** User ID `{user_id}` has been blocked.", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("unblock") & filters.user(ADMIN_ID))
async def unblock_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/unblock <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        user_id = int(command_parts[1].strip())
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID.", parse_mode=ParseMode.MARKDOWN)
        return

    unblock_user(user_id)
    await message.reply_text(f"**Success:** User ID `{user_id}` has been unblocked.", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("gmail") & filters.user(ADMIN_ID))
async def gmail_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/gmail <email>:<app_password>`", parse_mode=ParseMode.MARKDOWN)
        return

    text = command_parts[1].strip()
    if ':' not in text:
        await message.reply_text("**Error:** Invalid format. Use: `/gmail <email>:<app_password>`", parse_mode=ParseMode.MARKDOWN)
        return

    email, app_password = text.split(':', 1)
    update_gmail_credentials(email.strip(), app_password.strip())
    await message.reply_text(f"**Success:** Gmail credentials updated to `{email}`.", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("reset"))
async def reset_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/reset <email>`", parse_mode=ParseMode.MARKDOWN)
        return

    sender_id = message.from_user.id
    if is_blocked(sender_id):
        await message.reply_text("**Error:** You are blocked from using this bot.", parse_mode=ParseMode.MARKDOWN)
        return

    target_email = command_parts[1].strip()
    emails = get_emails(sender_id)
    if not emails or target_email not in emails:
        await message.reply_text("**Error:** Email not in your whitelist or you’re not authorized.", parse_mode=ParseMode.MARKDOWN)
        return

    gmail_email, gmail_app_password = get_gmail_credentials()
    sending_msg = await message.reply_text("*Sending...* Processing your request.", parse_mode=ParseMode.MARKDOWN)
    reset_link, error_message = extract_latest_netflix_reset_link(gmail_email, gmail_app_password, target_email)

    if reset_link:
        response_text = (
            f"**Success!** Reset link for `{target_email}`:\n\n"
            "*Click below to reset your password.*"
        )
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("Reset Password", url=reset_link)]])
        await sending_msg.edit_text(response_text, reply_markup=buttons, parse_mode=ParseMode.MARKDOWN)
    else:
        response_text = f"**Error:** {error_message}"
        await sending_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("signin"))
async def signin_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/signin <email>`", parse_mode=ParseMode.MARKDOWN)
        return

    sender_id = message.from_user.id
    if is_blocked(sender_id):
        await message.reply_text("**Error:** You are blocked from using this bot.", parse_mode=ParseMode.MARKDOWN)
        return

    target_email = command_parts[1].strip()
    emails = get_emails(sender_id)
    if not emails or target_email not in emails:
        await message.reply_text("**Error:** Email not in your whitelist or you’re not authorized.", parse_mode=ParseMode.MARKDOWN)
        return

    gmail_email, gmail_app_password = get_gmail_credentials()
    sending_msg = await message.reply_text("*Sending...* Processing your request.", parse_mode=ParseMode.MARKDOWN)
    signin_code, error_message = extract_latest_netflix_signin_code(gmail_email, gmail_app_password, target_email)

    if signin_code:
        response_text = (
            f"**Success!** Sign-in code for `{target_email}`:\n\n"
            f"**Code:** `{signin_code}`\n"
            "*Use this code to sign in to Netflix.*"
        )
        await sending_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        response_text = f"**Error:** {error_message}"
        await sending_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

print("The Bot is now active...")
app.run()
