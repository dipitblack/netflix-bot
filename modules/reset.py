import imaplib
import email
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

def extract_latest_netflix_reset_link(gmail_email, gmail_app_password, target_email):
    mail = None
    try:
        imap_server = "imap.gmail.com"
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(gmail_email, gmail_app_password)
        mail.select("inbox")

        result, data = mail.search(None, '(FROM "info@account.netflix.com" SUBJECT "reset")')
        email_ids = data[0].split()

        if not email_ids:
            return None, "No Netflix reset emails found in the archives."

        email_ids = email_ids[::-1]

        for email_id in email_ids:
            try:
                result, msg_data = mail.fetch(email_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                to_field = msg.get("To", "").strip()
                if target_email.lower() in to_field.lower():
                    date_str = msg.get("Date")
                    if date_str:
                        email_date = parsedate_to_datetime(date_str)
                        current_time = datetime.now(email_date.tzinfo)
                        if current_time - email_date > timedelta(hours=1):
                            return None, f"The reset link for {target_email} has expired (over 1 hour old). Please request a new one."

                    email_body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/html" and "attachment" not in content_disposition:
                                email_body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                            elif content_type == "text/plain" and not email_body:
                                email_body = part.get_payload(decode=True).decode(errors="ignore")

                    if not email_body:
                        continue

                    soup = BeautifulSoup(email_body, "html.parser")
                    for link in soup.find_all("a", href=True):
                        if "netflix.com/password" in link["href"]:
                            return link["href"], None

                    return None, f"No reset link found in the email to {target_email}."

            except imaplib.IMAP4.error:
                continue

        return None, f"No reset emails found addressed to {target_email}."

    except imaplib.IMAP4.error as e:
        return None, f"IMAP Error: {str(e)}. Unable to connect to the server."
    except Exception as e:
        return None, f"General Error: {str(e)}. An unexpected issue occurred."
    finally:
        if mail:
            try:
                mail.logout()
            except:
                pass
