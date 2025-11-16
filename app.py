# app.py — lazy-import friendly + health + admin enroll
import os
from flask import Flask, request, jsonify, render_template, send_file
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use persistent dir if set (Render persistent disk)
PERSISTENT_DIR = os.environ.get("PERSISTENT_DIR", None)
if PERSISTENT_DIR:
    os.makedirs(PERSISTENT_DIR, exist_ok=True)

# Paths (fallback to repo-local)
KNOWN_DIR = os.path.join(PERSISTENT_DIR or BASE_DIR, "known")
ENC_FILE = os.path.join(PERSISTENT_DIR or BASE_DIR, "encodings.npz")
UPLOAD_PHOTO = os.path.join(PERSISTENT_DIR or BASE_DIR, "class_photo.jpg")
ANNOTATED = os.path.join(PERSISTENT_DIR or BASE_DIR, "annotated_class_photo.jpg")
ATT_CSV = os.path.join(PERSISTENT_DIR or BASE_DIR, "attendance.csv")
STUD_CSV = os.path.join(PERSISTENT_DIR or BASE_DIR, "students.csv")

TOLERANCE = float(os.environ.get("TOLERANCE", 0.50))

app = Flask(__name__, static_folder="static", template_folder="templates")

# ---------- Utility: lazy import heavy libs ----------
def load_face_libs():
    """
    Import heavy ML libs only when needed. Raises ImportError if missing.
    """
    import numpy as np
    import cv2
    import face_recognition
    return np, cv2, face_recognition

def load_encodings():
    import numpy as _np
    if not os.path.exists(ENC_FILE):
        return [], []
    data = _np.load(ENC_FILE, allow_pickle=True)
    # Accept either key names
    encs = data.get("encodings", None)
    ids = data.get("ids", None) or data.get("student_ids", None)
    if encs is None:
        return [], []
    return list(encs), list(ids)

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "env": bool(os.environ.get("PERSISTENT_DIR"))})

@app.route("/api/upload", methods=["POST"])
def upload_and_run():
    # save uploaded file
    f = request.files.get("photo")
    if not f:
        return jsonify({"error": "no file"}), 400
    f.save(UPLOAD_PHOTO)

    # run recognition (lazy import)
    try:
        np, cv2, fr = load_face_libs()
    except Exception as e:
        return jsonify({"error": "missing ML libs", "detail": str(e)}), 500

    # load encodings
    known_encs, known_ids = load_encodings()
    if not known_encs:
        return jsonify({"error": "no encodings found; run enroll.py first"}), 400

    # load and optionally downscale image for speed
    img = cv2.imread(UPLOAD_PHOTO)
    if img is None:
        return jsonify({"error": "uploaded image unreadable"}), 400
    h, w = img.shape[:2]
    MAX_W = int(os.environ.get("MAX_IMAGE_WIDTH", 1200))
    if w > MAX_W:
        scale = MAX_W / float(w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locs = fr.face_locations(rgb, model="hog")
    face_encs = fr.face_encodings(rgb, face_locs)

    records = []
    recognized = set()
    for loc, enc in zip(face_locs, face_encs):
        dists = fr.face_distance(known_encs, enc)
        best_idx = int(np.argmin(dists))
        best_dist = float(dists[best_idx]) if len(dists)>0 else 1.0
        if best_dist <= TOLERANCE:
            sid = known_ids[best_idx]
            recognized.add(sid)
            label = sid
        else:
            label = "Unknown"
        top, right, bottom, left = loc
        records.append({"student_id": label, "confidence": 1.0-best_dist if best_dist<1 else 0.0, "bbox":[int(left),int(top),int(right),int(bottom)], "dist": best_dist})

        # draw on image
        cv2.rectangle(img, (left, top), (right, bottom), (0,255,0), 2)
        cv2.putText(img, label, (left, max(top-6,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    # save annotated and attendance csv
    cv2.imwrite(ANNOTATED, img)
    # Build attendance rows (use known ids so we have full list)
    rows = []
    for sid in sorted([os.path.splitext(x)[0].rsplit("_",1)[0] for x in os.listdir(KNOWN_DIR) if not x.startswith(".")]):
        rows.append({"student_id": sid, "present": 1 if sid in recognized else 0, "timestamp": datetime.now().isoformat()})
    import json, csv
    with open(ATT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["student_id","present","timestamp"])
        writer.writeheader()
        writer.writerows(rows)

    # save review json
    with open(os.path.join(PERSISTENT_DIR or BASE_DIR, "review.json"), "w") as fh:
        json.dump({"detections": records}, fh)

    return jsonify({"ok": True, "detections": records, "attendance_csv": os.path.basename(ATT_CSV), "annotated_image": os.path.basename(ANNOTATED)})

# ---------- Admin endpoint to run enroll.py safely (protected by ADMIN_TOKEN) ----------
@app.route("/api/admin/enroll", methods=["POST"])
def admin_enroll():
    token = request.headers.get("X-ADMIN-TOKEN") or request.args.get("token")
    if token != os.environ.get("ADMIN_TOKEN"):
        return jsonify({"error":"unauthorized"}), 403

    # run enroll.py as script (so it executes in current container)
    try:
        # import enroll module if it exposes a function, otherwise run as script
        import subprocess, sys, shlex
        rv = subprocess.run([sys.executable, os.path.join(BASE_DIR, "enroll.py")], capture_output=True, text=True, cwd=BASE_DIR, timeout=300)
        return jsonify({"ok": True, "stdout": rv.stdout, "stderr": rv.stderr, "retcode": rv.returncode})
    except Exception as e:
        return jsonify({"error":"enroll failed", "detail": str(e)}), 500

# ---------- Serve files ----------
@app.route("/annotated")
def serve_annotated():
    if os.path.exists(ANNOTATED):
        return send_file(ANNOTATED)
    return "No annotated image", 404

@app.route("/attendance")
def serve_attendance():
    if os.path.exists(ATT_CSV):
        return send_file(ATT_CSV)
    return "No attendance yet", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)