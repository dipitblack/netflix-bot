# Netflix Reset Bot

A Telegram bot to retrieve Netflix password reset links and sign-in codes from Gmail with persistent whitelist storage.

## Features
- `/start` - Welcome message with instructions.
- `/add <user_id> email1 email2 ...` - Whitelist a user (admin only).
- `/remove <email>` - Remove an email from your whitelist.
- `/mymails` - View your whitelisted emails.
- `/reset <email>` - Get the latest Netflix reset link.
- `/signin <email>` - Get the latest Netflix sign-in code.
- `/block <user_id>` - Block a user (admin only).
- `/unblock <user_id>` - Unblock a user (admin only).
- `/gmail <email>:<app_password>` - Update Gmail credentials (admin only).
