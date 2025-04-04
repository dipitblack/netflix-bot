import sqlite3
import json

def init_db():
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist 
                 (user_id INTEGER PRIMARY KEY, emails TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS blocked_users 
                 (user_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gmail_credentials 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, app_password TEXT)''')
    # Insert default Gmail credentials if table is empty
    c.execute("INSERT OR IGNORE INTO gmail_credentials (email, app_password) VALUES (?, ?)", 
              ("mdnehal0911@gmail.com", "tlxv hyjj ylro kclo"))
    conn.commit()
    conn.close()

def add_emails(user_id, emails):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT emails FROM whitelist WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        existing_emails = json.loads(result[0])
        updated_emails = list(set(existing_emails + emails))
        c.execute("UPDATE whitelist SET emails = ? WHERE user_id = ?", (json.dumps(updated_emails), user_id))
    else:
        c.execute("INSERT INTO whitelist (user_id, emails) VALUES (?, ?)", (user_id, json.dumps(emails)))
    conn.commit()
    conn.close()

def remove_email(user_id, email):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT emails FROM whitelist WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        emails = json.loads(result[0])
        if email in emails:
            emails.remove(email)
            if emails:
                c.execute("UPDATE whitelist SET emails = ? WHERE user_id = ?", (json.dumps(emails), user_id))
            else:
                c.execute("DELETE FROM whitelist WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def get_emails(user_id):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT emails FROM whitelist WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return json.loads(result[0]) if result else []

def block_user(user_id):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unblock_user(user_id):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_blocked(user_id):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM blocked_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def update_gmail_credentials(email, app_password):
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO gmail_credentials (email, app_password) VALUES (?, ?)", (email, app_password))
    conn.commit()
    conn.close()

def get_gmail_credentials():
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT email, app_password FROM gmail_credentials ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result if result else ("mdnehal0911@gmail.com", "tlxv hyjj ylro kclo")

def get_all_users():
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id FROM whitelist")
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]

def get_blocked_users():
    conn = sqlite3.connect("netflix_bot.db")
    c = conn.cursor()
    c.execute("SELECT user_id FROM blocked_users")
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]
