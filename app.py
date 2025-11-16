#!/usr/bin/env python3
from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os, uuid, time
from pathlib import Path
from werkzeug.utils import secure_filename
import traceback

# import the fast processor (reuse functions)
from attendance_from_photo import process_class_photo, MAX_WIDTH, TOLERANCE

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED = {"jpg", "jpeg", "png"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-key")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        f = request.files.get("photo")
        if not f or f.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)
        if not allowed_file(f.filename):
            flash("Allowed image types: jpg, jpeg, png", "error")
            return redirect(request.url)
        filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
        dest = UPLOAD_FOLDER / filename
        f.save(dest)
        try:
            start = time.time()
            out = process_class_photo(str(dest), tolerance=TOLERANCE, max_width=MAX_WIDTH)
            elapsed = time.time() - start
            flash(f"Processed in {elapsed:.2f}s", "success")
            return render_template("result.html", annotated=out["annotated"], csv=out["csv"], review=out["review"])
        except Exception as e:
            traceback.print_exc()
            flash(f"Processing error: {e}", "error")
            return redirect(request.url)
    return render_template("index.html")

@app.route("/annotated")
def annotated():
    return send_file("annotated_class_photo.jpg")

@app.route("/attendance.csv")
def attendance_csv():
    return send_file("attendance.csv")

if __name__ == "__main__":
    # run dev server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))