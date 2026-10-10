"""Read 'annons-id REGNR (...)' lines from an issue body and write regnr into index.html.

Only touches the `regnr` field of listings that already exist. Prints what it changed.
"""
import json
import os
import re
import sys

BODY = os.environ.get("ISSUE_BODY", "")
PATH = "index.html"
REG_RE = re.compile(r"^[A-Z]{3}\d{2}[A-Z0-9]$")

html = open(PATH, encoding="utf-8").read()
m = re.search(r'(<script type="application/json" id="listings">)(.*?)(</script>)', html, re.S)
if not m:
    sys.exit("listings block not found")
rows = json.loads(m.group(2))
by_id = {r["id"]: r for r in rows}

changed = []
for line in BODY.splitlines():
    parts = line.strip().split()
    if len(parts) < 2:
        continue
    ad_id, reg = parts[0], parts[1].upper()
    if ad_id in by_id and REG_RE.match(reg):
        if by_id[ad_id].get("regnr") != reg:
            by_id[ad_id]["regnr"] = reg
            changed.append(f"{reg} → {by_id[ad_id]['model']} {by_id[ad_id]['year']}, {by_id[ad_id]['city']}")

if changed:
    data = "\n[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n"
    html = html[: m.start(2)] + data + html[m.end(2):]
    open(PATH, "w", encoding="utf-8").write(html)

print("\n".join(changed))
