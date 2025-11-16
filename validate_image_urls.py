#!/usr/bin/env python3
import csv, requests, sys
CSV = "students.csv"
URL_FIELD = "image_url"
ID_FIELDS = ["student_id","roll_no","id","s_no","roll"]

def find_id_field(headers):
    for f in ID_FIELDS:
        if f in headers:
            return f
    return None

bad = []
ok = []
with open(CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    id_field = find_id_field(reader.fieldnames)
    if id_field is None:
        print("No id column found in CSV. Headers:", reader.fieldnames); sys.exit(1)
    if URL_FIELD not in reader.fieldnames:
        print(f"CSV missing '{URL_FIELD}' column. Add it."); sys.exit(1)
    for row in reader:
        sid = row[id_field].strip()
        url = row[URL_FIELD].strip()
        if not url:
            bad.append((sid, "empty")); continue
        try:
            r = requests.head(url, allow_redirects=True, timeout=10)
            ctype = r.headers.get("Content-Type","")
            if r.status_code == 200 and ("image" in ctype):
                ok.append((sid, url))
            else:
                bad.append((sid, url, r.status_code, ctype))
        except Exception as e:
            bad.append((sid, url, str(e)))
print("\nOK urls:", len(ok))
for a in ok[:50]:
    print(" OK:", a[0], a[1])
print("\nBad urls:", len(bad))
for b in bad[:50]:
    print(" BAD:", b)
