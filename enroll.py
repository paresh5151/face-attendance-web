#!/usr/bin/env python3
import os
import face_recognition
import numpy as np

KNOWN_DIR = "known"
ENC_FILE = "encodings.npz"

encodings = []
ids = []

if not os.path.exists(KNOWN_DIR):
    raise SystemExit("known/ folder not found. Create it or run downloader first.")

for fname in sorted(os.listdir(KNOWN_DIR)):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    path = os.path.join(KNOWN_DIR, fname)
    print("Processing:", fname)
    image = face_recognition.load_image_file(path)
    faces = face_recognition.face_encodings(image)
    if len(faces) == 0:
        print(" ⚠️ No face detected in", fname)
        continue
    encodings.append(faces[0])
    ids.append(os.path.splitext(fname)[0])

if len(encodings) == 0:
    raise SystemExit("❌ No valid faces found in known/ folder!")

np.savez(ENC_FILE, encodings=np.array(encodings), ids=np.array(ids))
print(f"✅ Saved {len(encodings)} encodings to {ENC_FILE}")
