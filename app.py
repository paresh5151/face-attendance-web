import os
import pandas as pd
import face_recognition
import numpy as np
import cv2
from flask import Flask, request, jsonify, render_template
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWN_DIR = os.path.join(BASE_DIR, "known")
ENCODINGS_FILE = os.path.join(BASE_DIR, "encodings.npz")
UPLOAD_FILE = os.path.join(BASE_DIR, "class_photo.jpg")
ANNOTATED_FILE = os.path.join(BASE_DIR, "annotated_class_photo.jpg")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.csv")

# -----------------------------
# LOAD KNOWN ENCODINGS
# -----------------------------
def load_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        return [], []

    data = np.load(ENCODINGS_FILE, allow_pickle=True)
    return data["encodings"], list(data["student_ids"])

# -----------------------------
# BUILD ATTENDANCE FROM PHOTO
# -----------------------------
def build_attendance(photo_path):
    image = face_recognition.load_image_file(photo_path)
    face_locations = face_recognition.face_locations(image, model="hog")
    face_encodings = face_recognition.face_encodings(image, face_locations)

    known_enc, known_ids = load_encodings()

    attendance = []
    timestamp = datetime.now().isoformat()

    image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    for (top, right, bottom, left), enc in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_enc, enc, tolerance=0.48)
        student_id = "UNKNOWN"

        if True in matches:
            idx = matches.index(True)
            student_id = known_ids[idx]

        attendance.append({
            "student_id": student_id,
            "present": 1 if student_id != "UNKNOWN" else 0,
            "timestamp": timestamp
        })

        label = student_id
        cv2.rectangle(image_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(image_bgr, label, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imwrite(ANNOTATED_FILE, image_bgr)
    df = pd.DataFrame(attendance)
    df.to_csv(ATTENDANCE_FILE, index=False)

    return attendance

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

# Upload photo → Run attendance
@app.route("/api/upload", methods=["POST"])
def upload():
    if "photo" not in request.files:
        return jsonify({"error": "No file received"}), 400

    photo = request.files["photo"]
    photo.save(UPLOAD_FILE)

    results = build_attendance(UPLOAD_FILE)

    return jsonify({
        "message": "Attendance taken",
        "count": len(results),
        "annotated_image": "/annotated",
        "attendance_csv": "/attendance"
    })

@app.route("/annotated")
def get_annotated():
    if not os.path.exists(ANNOTATED_FILE):
        return "No annotated image yet"
    return open(ANNOTATED_FILE, "rb").read()

@app.route("/attendance")
def get_attendance():
    if not os.path.exists(ATTENDANCE_FILE):
        return "No attendance yet"
    return open(ATTENDANCE_FILE, "rb").read()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)