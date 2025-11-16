#!/usr/bin/env python3
import csv, os, sys
CSV = "students.csv"
KNOWN_DIR = "known"
ID_FIELD_CANDIDATES = ["student_id", "id", "roll_no", "roll", "s_no"]

if not os.path.exists(CSV):
    print("CSV not found:", CSV); sys.exit(1)
if not os.path.exists(KNOWN_DIR):
    print("known/ folder not found. Run downloader first."); sys.exit(1)

ids = []
with open(CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    id_field = None
    for c in ID_FIELD_CANDIDATES:
        if c in reader.fieldnames:
            id_field = c; break
    if id_field is None:
        print("CSV missing id column. Found fields:", reader.fieldnames); sys.exit(1)
    for r in reader:
        ids.append(r[id_field].strip())

files = [os.path.splitext(x)[0] for x in os.listdir(KNOWN_DIR) if x.lower().endswith(('.jpg','.jpeg','.png'))]
base_ids = set()
for f in files:
    parts = f.rsplit("_",1)
    if len(parts)==2 and parts[1].isdigit():
        base_ids.add(parts[0])
    else:
        base_ids.add(f)

have = [i for i in ids if i in base_ids]
missing = [i for i in ids if i not in base_ids]

print("Total students in CSV:", len(ids))
print("Students with images in known/:", len(have))
print("Missing images:", len(missing))
if missing:
    print("\\nMissing sample (first 50):")
    print("\\n".join(missing[:50]))
else:
    print("\\nAll students have at least one image in known/")
