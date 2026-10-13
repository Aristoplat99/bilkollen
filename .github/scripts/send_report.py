"""Mail report.md to Axel and Vendela if Claude wrote mail_subject.txt.

Env: GMAIL_USER, GMAIL_APP_PASSWORD, MAIL_TO (comma-separated).
"""
import os
import smtplib
from email.message import EmailMessage

if not os.path.exists("mail_subject.txt") or not os.path.exists("report.md"):
    print("Inget mejl att skicka")
    raise SystemExit(0)

msg = EmailMessage()
msg["From"] = os.environ["GMAIL_USER"]
msg["To"] = os.environ["MAIL_TO"]
msg["Subject"] = open("mail_subject.txt", encoding="utf-8").read().strip()
msg.set_content(open("report.md", encoding="utf-8").read())

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
    s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
    s.send_message(msg)
print("Mejl skickat:", msg["Subject"])
