"""Read Blocket saved-search alerts from Gmail over IMAP and write the listings
that are not yet in index.html to new_listings.json.

Env: GMAIL_USER, GMAIL_APP_PASSWORD, DAYS (default 2).
"""
import datetime as dt
import email
import imaplib
import json
import os
import re

USER = os.environ["GMAIL_USER"]
PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
DAYS = int(os.environ.get("DAYS", "2"))


def existing_ids():
    html = open("index.html", encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="listings">(.*?)</script>', html, re.S)
    return {r["id"] for r in json.loads(m.group(1))}


def plain_text(msg):
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            raw = part.get_payload(decode=True) or b""
            return raw.decode(part.get_content_charset() or "utf-8", "replace")
    return ""


# Block: title / "year · mil · details" / "Seller, City price kr" / ... / Mer information: URL
BLOCK = re.compile(
    r"^(?P<title>[^\n]+)\n"
    r"(?P<year>\d{4})\s*·\s*(?P<mil>[\d\s ]+)\s*mil\s*·\s*(?P<details>[^\n]*)\n"
    r"(?P<seller>[^,\n]+),\s*(?P<city>.+?)\s+(?P<price>[\d\s ]+)\s*kr\s*\n"
    r"(?:.*\n)*?\s*Mer information:\s*https://www\.blocket\.se/(?P<id>\d+)",
    re.M,
)


def parse(text, received):
    out = []
    for m in BLOCK.finditer(text):
        num = lambda s: int(re.sub(r"\D", "", s))
        out.append({
            "id": m["id"],
            "title": m["title"].strip(" ,"),
            "year": int(m["year"]),
            "mil": num(m["mil"]),
            "details": m["details"].strip(),
            "seller": m["seller"].strip(),
            "city": m["city"].strip(),
            "price": num(m["price"]),
            "url": f"https://www.blocket.se/{m['id']}",
            "received": received,
        })
    return out


def main():
    have = existing_ids()
    since = (dt.date.today() - dt.timedelta(days=DAYS)).strftime("%d-%b-%Y")
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(USER, PASSWORD)
    imap.select('"[Gmail]/All Mail"', readonly=True)
    _, data = imap.search(None, f'(FROM "blocket@blocket.se" SINCE {since})')
    found = {}
    for num in data[0].split():
        _, msg_data = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = str(email.header.make_header(email.header.decode_header(msg.get("Subject", ""))))
        if "bevakning" not in subject:
            continue
        received = email.utils.parsedate_to_datetime(msg["Date"]).date().isoformat()
        for item in parse(plain_text(msg), received):
            if item["id"] not in have:
                found[item["id"]] = item
    imap.logout()
    new = list(found.values())
    json.dump(new, open("new_listings.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(new)} nya annonser")


if __name__ == "__main__":
    main()
