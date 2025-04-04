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

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

app = Client("netflix_reset_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

init_db()

def is_authorized(user_id, target_email=None):
    """Check if user is authorized to access the email"""
    if user_id == ADMIN_ID:
        return True  # Owner is always authorized
    if is_blocked(user_id):
        return False
    if not target_email:
        return bool(get_emails(user_id))
    return target_email in get_emails(user_id)

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
        "📝 **Note:** All links and codes are valid for emails received within the last hour."
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
    try:
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            raise ValueError("Invalid format")
            
        user_id = int(command_parts[1])
        emails = [email.strip() for email in command_parts[2].split() if '@' in email]
        
        if not emails:
            raise ValueError("No valid emails provided")
            
        add_emails(user_id, emails)
        email_list = "\n".join([f"- `{email}`" for email in get_emails(user_id)])
        
        await message.reply_text(
            f"✅ Successfully added emails for user {user_id}:\n{email_list}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await message.reply_text(
            f"❌ Error: {str(e)}\nUsage: `/add <user_id> email1 email2 ...`",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("remove") & filters.user(ADMIN_ID))
async def remove_command(client, message):
    try:
        command_parts = message.text.split(maxsplit=2)
        if len(command_parts) < 3:
            raise ValueError("Invalid format")
            
        user_id = int(command_parts[1])
        target_email = command_parts[2].strip()
        
        if not remove_email(user_id, target_email):
            raise ValueError("Email not found for this user")
            
        remaining_emails = get_emails(user_id)
        response = f"✅ Removed `{target_email}` from user {user_id}"
        
        if remaining_emails:
            email_list = "\n".join([f"- `{email}`" for email in remaining_emails])
            response += f"\nRemaining emails:\n{email_list}"
        else:
            response += "\nNo emails remaining for this user"
            
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply_text(
            f"❌ Error: {str(e)}\nUsage: `/remove <user_id> <email>`",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("mymails"))
async def mymails_command(client, message):
    sender_id = message.from_user.id
    
    if not is_authorized(sender_id):
        await message.reply_text("❌ You are not authorized to use this command", parse_mode=ParseMode.MARKDOWN)
        return
        
    emails = get_emails(sender_id)
    
    if not emails and sender_id != ADMIN_ID:
        await message.reply_text("ℹ️ You don't have any whitelisted emails. Contact admin.", parse_mode=ParseMode.MARKDOWN)
        return
        
    email_list = "\n".join([f"- `{email}`" for email in emails]) if emails else "- No emails (owner has full access)"
    await message.reply_text(
        f"📧 Your authorized emails (User ID: `{sender_id}`):\n{email_list}",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.command(["block", "unblock", "check"]) & filters.user(ADMIN_ID))
async def admin_management_commands(client, message):
    try:
        command = message.command[0]
        user_id = int(message.command[1])
        
        if command == "block":
            block_user(user_id)
            action = "blocked"
        elif command == "unblock":
            unblock_user(user_id)
            action = "unblocked"
        else:  # check command
            emails = get_emails(user_id)
            email_list = "\n".join([f"- `{email}`" for email in emails]) if emails else "- No emails"
            await message.reply_text(
                f"📋 Whitelisted emails for user {user_id}:\n{email_list}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        await message.reply_text(f"✅ User {user_id} has been {action}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await message.reply_text(
            f"❌ Error: {str(e)}\nUsage: `/{message.command[0]} <user_id>`",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats_command(client, message):
    users = get_all_users()
    blocked = get_blocked_users()
    
    stats = (
        "📊 **Bot Statistics**\n\n"
        f"👥 Total users: `{len(users)}`\n"
        f"🚫 Blocked users: `{len(blocked)}`\n"
        f"✅ Active users: `{len(users) - len(blocked)}`\n\n"
        "🔍 Use `/check <user_id>` to view specific user details"
    )
    
    await message.reply_text(stats, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("gmail") & filters.user(ADMIN_ID))
async def gmail_command(client, message):
    try:
        credentials = message.text.split(maxsplit=1)[1].strip()
        if ':' not in credentials:
            raise ValueError("Invalid format")
            
        email, password = credentials.split(':', 1)
        update_gmail_credentials(email.strip(), password.strip())
        
        await message.reply_text(
            f"✅ Gmail credentials updated to: `{email}`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await message.reply_text(
            f"❌ Error: {str(e)}\nUsage: `/gmail <email>:<app_password>`",
            parse_mode=ParseMode.MARKDOWN
        )

async def process_email_request(client, message, command_type):
    sender_id = message.from_user.id
    
    if not is_authorized(sender_id):
        await message.reply_text("❌ You are not authorized to use this bot", parse_mode=ParseMode.MARKDOWN)
        return
        
    try:
        target_email = message.text.split(maxsplit=1)[1].strip()
        
        # For non-admin users, verify the email is in their whitelist
        if sender_id != ADMIN_ID and target_email not in get_emails(sender_id):
            await message.reply_text("❌ This email is not in your whitelist", parse_mode=ParseMode.MARKDOWN)
            return
            
        gmail_email, gmail_app_password = get_gmail_credentials()
        processing_msg = await message.reply_text("⏳ Processing your request...", parse_mode=ParseMode.MARKDOWN)
        
        if command_type == "reset":
            result, error = extract_latest_netflix_reset_link(gmail_email, gmail_app_password, target_email)
            if result:
                buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Reset Password", url=result)]])
                await processing_msg.edit_text(
                    f"✅ Password reset link for `{target_email}`",
                    reply_markup=buttons,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await processing_msg.edit_text(f"❌ {error}", parse_mode=ParseMode.MARKDOWN)
        else:  # signin
            result, error = extract_latest_netflix_signin_code(gmail_email, gmail_app_password, target_email)
            if result:
                await processing_msg.edit_text(
                    f"✅ Sign-in code for `{target_email}`:\n\n"
                    f"**Code:** `{result}`\n"
                    "This code is valid for 15 minutes",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await processing_msg.edit_text(f"❌ {error}", parse_mode=ParseMode.MARKDOWN)
    except IndexError:
        await message.reply_text(
            f"❌ Usage: `/{command_type} <email>`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await message.reply_text(
            f"❌ An error occurred: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

@app.on_message(filters.command("reset"))
async def reset_command(client, message):
    await process_email_request(client, message, "reset")

@app.on_message(filters.command("signin"))
async def signin_command(client, message):
    await process_email_request(client, message, "signin")

print("Bot is running...")
app.run()
