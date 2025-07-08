
import imaplib
import email
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

IMAP_HOST = 'mail.blackcat-it.com.au'
IMAP_PORT = 993
SMTP_HOST = 'mail.blackcat-it.com.au'
SMTP_PORT = 587
USERNAME = 'agentzero@teamcollins.net'
PASSWORD = 'redacted'

# Returns a list of unread email IDs in INBOX
def check_inbox():
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(USERNAME, PASSWORD)
    mail.select('INBOX')
    status, data = mail.search(None, 'UNSEEN')
    mail.logout()
    if status == 'OK':
        return [eid.decode() for eid in data[0].split()]
    else:
        return []

# Returns a dict with sender, subject, and body for a given email ID
def read_email(email_id):
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(USERNAME, PASSWORD)
    mail.select('INBOX')
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    result = {}
    if status == 'OK':
        msg = email.message_from_bytes(msg_data[0][1])
        result['from'] = msg['From']
        result['subject'] = msg['Subject']
        if msg.is_multipart():
            body = ''
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body += part.get_payload(decode=True).decode(errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode(errors='ignore')
        result['body'] = body
    mail.logout()
    return result

# Sends an email via SMTP
def reply_email(to_address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = formataddr(("Dan 'Agent0' Case", USERNAME))
    msg['To'] = to_address
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(USERNAME, PASSWORD)
        server.sendmail(USERNAME, [to_address], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

if __name__ == '__main__':
    # Example usage of the email helper functions
    print("--- Running Email Helper Examples ---")

    # 1. Check for emails
    print("\n1. Checking inbox for unread emails...")
    unread_email_ids = check_inbox()

    if unread_email_ids:
        print(f"Found {len(unread_email_ids)} unread email(s).")

        # 2. Read and reply to each unread email
        for email_id in unread_email_ids:
            print(f"\n--- Processing email with ID: {email_id} ---")
            print(f"2. Reading email with ID: {email_id}")
            email_details = read_email(email_id)

            if email_details:
                print("Email content:")
                print(f"  From: {email_details['from']}")
                print(f"  Subject: {email_details['subject']}")
                print(f"  Body: {email_details['body'][:100].strip()}...")

                # 3. Reply to the email
                recipient_email = email.utils.parseaddr(email_details['from'])[1]
                if recipient_email:
                    reply_subject = f"Re: {email_details['subject']}"
                    reply_body = (
                        "Hello,\n\n"
                        "This is an automated response to acknowledge receipt of your email.\n\n"
                        "Thank you,\n"
                        "Agent0"
                    )
                    print(f"\n3. Replying to {recipient_email}...")
                    success = reply_email(recipient_email, reply_subject, reply_body)
                    if success:
                        print("Reply sent successfully.")
                    else:
                        print("Failed to send reply.")
                else:
                    print("\nCould not extract recipient email address. Cannot reply.")
            else:
                print(f"Could not read email with ID: {email_id}")
    else:
        print("No unread emails found in the inbox.")

    print("\n--- Email Helper Examples Finished ---")
