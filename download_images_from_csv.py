#!/usr/bin/env python3
import csv, os, sys, requests
from urllib.parse import urlparse
from time import sleep

CSV = "students.csv"
KNOWN_DIR = "known"
URL_FIELD = "image_url"
ID_FIELD_CANDIDATES = ["student_id", "id", "roll_no", "roll", "s_no"]

os.makedirs(KNOWN_DIR, exist_ok=True)

with open(CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    id_field = None
    for cand in ID_FIELD_CANDIDATES:
        if cand in reader.fieldnames:
            id_field = cand; break
    if id_field is None:
        print("CSV missing id column. Found fields:", reader.fieldnames); sys.exit(1)
    if URL_FIELD not in reader.fieldnames:
        print(f"CSV missing required column '{URL_FIELD}'."); sys.exit(1)
    counts = {}; failed = []; total = 0
    for row in reader:
        total += 1
        sid = row[id_field].strip()
        url = row[URL_FIELD].strip()
        if not sid or not url:
            print(f"[skip] {sid} {('no url' if not url else '')}"); continue
        counts.setdefault(sid, 0)
        idx = counts[sid] + 1
        parsed = urlparse(url)
        _, ext = os.path.splitext(parsed.path)
        if ext.lower() not in (".jpg", ".jpeg", ".png"): ext = ".jpg"
        out_name = f"{sid}_{idx}{ext}"
        out_path = os.path.join(KNOWN_DIR, out_name)
        try:
            print(f"Downloading {sid} <- {url} -> {out_name}")
            resp = requests.get(url, timeout=20); resp.raise_for_status()
            with open(out_path, "wb") as w: w.write(resp.content)
            counts[sid] = idx
            sleep(0.15)
        except Exception as e:
            print(f"[error] {sid} {url} => {e}")
            failed.append((sid, url, str(e)))
print("\nSummary:")
print(" Total CSV rows processed:", total)
print(" Students with images downloaded:", len([k for k,v in counts.items() if v>0]))
if failed:
    print(" Failed downloads:", len(failed))
    for sid,url,err in failed[:20]:
        print("  -", sid, url, err)
else:
    print(" No download failures.")
