import imaplib
import email
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import re
import socket

def extract_latest_netflix_signin_code(gmail_email, gmail_app_password, target_email):
    mail = None
    try:
        socket.setdefaulttimeout(10)
        imap_server = "imap.gmail.com"

        try:
            mail = imaplib.IMAP4_SSL(imap_server, 993)
        except (socket.timeout, ConnectionError) as e:
            return None, f"Connection Error: Failed to connect to {imap_server}. {str(e)}"

        try:
            mail.login(gmail_email, gmail_app_password)
        except imaplib.IMAP4.error as e:
            return None, f"Login Error: Failed to authenticate with Gmail. {str(e)}"

        try:
            mail.select("inbox", readonly=True)
        except imaplib.IMAP4.error as e:
            return None, f"IMAP Error: Failed to select inbox. {str(e)}"

        since_date = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
        search_query = f'FROM "info@account.netflix.com" SUBJECT "sign-in code" SINCE {since_date}'
        
        try:
            result, data = mail.search(None, search_query)
            if result != "OK":
                return None, f"IMAP Error: Failed to search for emails. {result}"
            email_ids = data[0].split()
        except imaplib.IMAP4.error as e:
            return None, f"IMAP Error: Failed to search emails. {str(e)}"

        if not email_ids:
            return None, "No recent Netflix sign-in code emails found (within the last hour)."

        email_ids = email_ids[::-1]

        for email_id in email_ids:
            try:
                result, msg_data = mail.fetch(email_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                to_field = msg.get("To", "").strip()
                if target_email.lower() not in to_field.lower():
                    continue

                date_str = msg.get("Date")
                if date_str:
                    email_date = parsedate_to_datetime(date_str)
                    current_time = datetime.now(email_date.tzinfo)
                    if current_time - email_date > timedelta(minutes=15):
                        return None, f"The sign-in code for {target_email} has expired (over 15 minutes old). Please request a new one."

                email_body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            email_body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    email_body = msg.get_payload(decode=True).decode(errors="ignore")

                if not email_body:
                    continue

                code_match = re.search(r'\b\d{4}\b', email_body)
                if code_match:
                    return code_match.group(0), None
                return None, f"No sign-in code found in the email to {target_email}."

            except imaplib.IMAP4.error:
                continue

        return None, f"No recent sign-in code emails found addressed to {target_email} (within the last 15 minutes)."

    except imaplib.IMAP4.error as e:
        return None, f"IMAP Error: {str(e)}. Unable to connect to the server."
    except Exception as e:
        return None, f"General Error: {str(e)}. An unexpected issue occurred."
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except:
                pass
