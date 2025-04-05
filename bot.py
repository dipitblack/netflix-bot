from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from modules.reset import extract_latest_netflix_reset_link
from modules.signin import extract_latest_netflix_signin_code
from database import init_db, add_emails, remove_email, get_emails, block_user, unblock_user, is_blocked, update_gmail_credentials, get_gmail_credentials, get_all_users, get_blocked_users
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def start_health_server():
    server = HTTPServer(("", 8080), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

print("The Bot is now active...")

API_ID = "19274214"
API_HASH = "bf87adfbc2c24c66904f3c36f3c0af3a"
BOT_TOKEN = "7521862287:AAEnZbQv72I6ATVkSWNpBrfQQKBBn7a3ju8"
ADMIN_ID = "2104057670"

app = Client("netflix_reset_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

init_db()

@app.on_message(filters.command("start"))
async def start_command(client, message):
    sender_id = message.from_user.id
    base_welcome = (
        "**🌟 Welcome to Netflix Reset Bot 🌟**\n\n"
        "We provide a **professional and efficient** service to help you manage your Netflix account.\n"
        "Retrieve password reset links and sign-in codes with ease!\n\n"
        "✨ **User Commands:**\n"
        "- `/reset <email>` - Get your password reset link\n"
        "- `/signin <email>` - Get your sign-in code\n"
        "- `/mymails` - View your whitelisted emails\n\n"
        "📝 **Note:** All links and codes are valid for emails received within the last hour.\n"
        "Contact our admin to get whitelisted and start using the bot!"
    )
    
    if sender_id == ADMIN_ID:
        admin_commands = (
            "\n\n🔧 **Admin Commands:**\n"
            "- `/add <user_id> email1 email2 ...` - Add emails to a user\n"
            "- `/remove <user_id> <email>` - Remove an email from a user\n"
            "- `/block <user_id>` - Block a user\n"
            "- `/unblock <user_id>` - Unblock a user\n"
            "- `/check <user_id>` - Check user's whitelisted emails\n"
            "- `/stats` - View bot statistics\n"
            "- `/gmail <email>:<app_password>` - Update Gmail credentials"
        )
        welcome_text = base_welcome + admin_commands
    else:
        welcome_text = base_welcome
        
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
        await message.reply_text("**Error:** Invalid user ID.", parse_mode=ParseMode.MARKDOWN)
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

@app.on_message(filters.command("remove") & filters.user(ADMIN_ID))
async def remove_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/remove <user_id> <email>`", parse_mode=ParseMode.MARKDOWN)
        return

    parts = command_parts[1].split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("**Error:** Use: `/remove <user_id> <email>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        user_id = int(parts[0].strip())
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID.", parse_mode=ParseMode.MARKDOWN)
        return

    target_email = parts[1].strip()
    if remove_email(user_id, target_email):
        email_list = "\n".join([f"- `{email}`" for email in get_emails(user_id)])
        response_text = f"**Success:** Removed `{target_email}` from User ID `{user_id}`.\nRemaining emails:\n{email_list}" if email_list else f"**Success:** Removed `{target_email}` from User ID `{user_id}`. No emails remain."
        await message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text(f"**Error:** Email not found in User ID `{user_id}`'s whitelist.", parse_mode=ParseMode.MARKDOWN)

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

@app.on_message(filters.command("check") & filters.user(ADMIN_ID))
async def check_command(client, message):
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply_text("**Error:** Use: `/check <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        user_id = int(command_parts[1].strip())
    except ValueError:
        await message.reply_text("**Error:** Invalid user ID.", parse_mode=ParseMode.MARKDOWN)
        return

    emails = get_emails(user_id)
    if not emails:
        await message.reply_text(f"**Info:** User ID `{user_id}` has no whitelisted emails.", parse_mode=ParseMode.MARKDOWN)
        return

    email_list = "\n".join([f"- `{email}`" for email in emails])
    response_text = (
        f"**Whitelisted Emails for User ID `{user_id}`:**\n"
        f"{email_list}"
    )
    await message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_command(client, message):
    total_users = len(get_all_users())
    blocked_users = len(get_blocked_users())
    whitelisted_users = len([user for user in get_all_users() if get_emails(user)])

    stats_text = (
        "**📊 Bot Statistics 📊**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"✅ **Whitelisted Users:** `{whitelisted_users}`\n"
        f"🚫 **Blocked Users:** `{blocked_users}`\n"
        f"📧 **Active Users (not blocked):** `{total_users - blocked_users}`"
    )
    await message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

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
    
    # Check if the sender is the admin
    if sender_id != ADMIN_ID:
        # For non-admin users, check if the email is whitelisted
        emails = get_emails(sender_id)
        if not emails or target_email not in emails:
            await message.reply_text("**Error:** Email not in your whitelist or you’re not authorized.", parse_mode=ParseMode.MARKDOWN)
            return

    # If the sender is admin, they can bypass the whitelist check
    gmail_email, gmail_app_password = get_gmail_credentials()
    sending_msg = await message.reply_text("**Sending...** Processing your request.", parse_mode=ParseMode.MARKDOWN)
    reset_link, error_message = extract_latest_netflix_reset_link(gmail_email, gmail_app_password, target_email)

    if reset_link:
        response_text = (
            f"**Success!** Reset link for `{target_email}`:\n\n"
            "**Click below to reset your password.**"
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
        moving = await message.reply_text("**Error:** You are blocked from using this bot.", parse_mode=ParseMode.MARKDOWN)
        return

    target_email = command_parts[1].strip()
    
    # Check if the sender is the admin
    if sender_id != ADMIN_ID:
        # For non-admin users, check if the email is whitelisted
        emails = get_emails(sender_id)
        if not emails or target_email not in emails:
            await message.reply_text("**Error:** Email not in your whitelist or you’re not authorized.", parse_mode=ParseMode.MARKDOWN)
            return

    # If the sender is admin, they can bypass the whitelist check
    gmail_email, gmail_app_password = get_gmail_credentials()
    sending_msg = await message.reply_text("**Sending...** Processing your request.", parse_mode=ParseMode.MARKDOWN)
    signin_code, error_message = extract_latest_netflix_signin_code(gmail_email, gmail_app_password, target_email)

    if signin_code:
        response_text = (
            f"**Success!** Sign-in code for `{target_email}`:\n\n"
            f"**Code:** `{signin_code}`\n"
            "__Use this code to sign in to Netflix.__"
        )
        await sending_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        response_text = f"**Error:** {error_message}"
        await sending_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)

print("The Bot is now active...")
app.run()
