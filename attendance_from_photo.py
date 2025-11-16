#!/usr/bin/env python3
import face_recognition
import numpy as np
import cv2
import os
import pandas as pd
import json
from datetime import datetime
from collections import defaultdict

ENC_FILE = "encodings.npz"
PHOTO_PATH = "class_photo.jpg"
OUTPUT_CSV = "attendance.csv"
ANNOTATED = "annotated_class_photo.jpg"
REVIEW = "review.json"
TOLERANCE = 0.50  # adjust if needed

if not os.path.exists(ENC_FILE):
    raise SystemExit("❌ encodings.npz not found. Run enroll.py first (or downloader + enroll).")

data = np.load(ENC_FILE, allow_pickle=True)
known_encodings = list(data["encodings"])
known_ids = [str(x) for x in list(data["ids"])]

def base_id(kid):
    parts = kid.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return kid

known_base_ids = [base_id(k) for k in known_ids]
base_to_indices = defaultdict(list)
for i, b in enumerate(known_base_ids):
    base_to_indices[b].append(i)

if not os.path.exists(PHOTO_PATH):
    raise SystemExit(f"❌ {PHOTO_PATH} not found. Place your class photo as {PHOTO_PATH}")

photo = face_recognition.load_image_file(PHOTO_PATH)
print("📸 Detecting faces...")
face_locations = face_recognition.face_locations(photo, model="hog")
face_encodings = face_recognition.face_encodings(photo, face_locations)
print(f"👀 Found {len(face_encodings)} faces")

attendance_records = []
recognized_base_ids = set()

for loc, enc in zip(face_locations, face_encodings):
    distances = face_recognition.face_distance(known_encodings, enc)
    if len(distances) == 0:
        match_label = "Unknown"; conf = 0.0
    else:
        best_idx = np.argmin(distances)
        best_dist = float(distances[best_idx])
        if best_dist <= TOLERANCE:
            matched_full_id = known_ids[best_idx]
            matched_base = base_id(matched_full_id)
            match_label = matched_base
            conf = max(0.0, min(1.0, 1.0 - best_dist))
            recognized_base_ids.add(matched_base)
        else:
            match_label = "Unknown"; conf = 0.0
    top, right, bottom, left = loc
    attendance_records.append({
        "student_id": match_label,
        "confidence": conf,
        "bbox": [int(left), int(top), int(right), int(bottom)]
    })

unique_base_ids = sorted(set(known_base_ids))
timestamp = datetime.now().isoformat()
rows = []
for sid in unique_base_ids:
    rows.append({
        "student_id": sid,
        "present": 1 if sid in recognized_base_ids else 0,
        "timestamp": timestamp
    })

pd.DataFrame(rows).to_csv(OUTPUT_CSV, index=False)
print(f"✅ Attendance saved → {OUTPUT_CSV}")

img = cv2.cvtColor(photo, cv2.COLOR_RGB2BGR)
for rec in attendance_records:
    left, top, right, bottom = rec["bbox"]
    label = rec["student_id"]
    cv2.rectangle(img, (left, top), (right, bottom), (0,255,0), 2)
    cv2.putText(img, label, (left, top - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

cv2.imwrite(ANNOTATED, img)
print(f"🖼️ Annotated image saved → {ANNOTATED}")

with open(REVIEW, "w") as f:
    json.dump({"photo": PHOTO_PATH, "detections": attendance_records}, f)
print(f"📄 Review JSON saved → {REVIEW}")
