#!/usr/bin/env python3
"""
Fast attendance_from_photo.py
- Resize large images
- HOG face detection (fast)
- num_jitters=1 (fast) for encodings
- Vectorized L2 matching against known encodings
- Optional multiprocessing for encoding/matching
Produces:
 - annotated_class_photo.jpg
 - attendance.csv
 - review.json
"""

import os, sys, time, json
from pathlib import Path
import numpy as np
import cv2
import face_recognition
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- CONFIG ----------
MAX_WIDTH = int(os.environ.get("MAX_WIDTH", "800"))     # px, lower => faster
DETECTION_MODEL = os.environ.get("DETECTION_MODEL", "hog")  # "hog" or "cnn"
ENCODE_JITTERS = int(os.environ.get("ENCODE_JITTERS", "1"))
TOLERANCE = float(os.environ.get("TOLERANCE", "0.50"))  # lower => stricter
USE_MULTIPROC = os.environ.get("USE_MULTIPROC", "1") == "1"
KNOWN_FILE = Path("encodings.npz")   # must exist
OUT_ANNOTATED = Path("annotated_class_photo.jpg")
OUT_CSV = Path("attendance.csv")
OUT_REVIEW = Path("review.json")
# -----------------------------

def resize_max_width(bgr_image, max_width=MAX_WIDTH):
    h, w = bgr_image.shape[:2]
    if w <= max_width:
        return bgr_image, 1.0
    scale = max_width / float(w)
    new_h, new_w = int(h * scale), int(max_width)
    small = cv2.resize(bgr_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return small, scale

def load_known_encodings(fn=KNOWN_FILE):
    if not fn.exists():
        raise FileNotFoundError(f"{fn} not found. Run enroll.py to build encodings.")
    data = np.load(fn, allow_pickle=True)
    encs = data.get("encodings")  # shape (N, 128)
    ids = data.get("ids", data.get("student_ids", None))
    names = data.get("names", None)  # optional
    if encs is None or ids is None:
        raise ValueError("encodings.npz missing required keys 'encodings' and 'ids'")
    encs = np.asarray(encs, dtype=np.float32)
    ids = list(ids)
    names = list(names) if names is not None else [None]*len(ids)
    return encs, ids, names

def compute_face_encodings(rgb_small, face_locations, num_jitters=ENCODE_JITTERS):
    # face_recognition.face_encodings is not vectorized; we can parallelize per-face if desired
    if not USE_MULTIPROC or len(face_locations) <= 1:
        return face_recognition.face_encodings(rgb_small, face_locations, num_jitters=num_jitters)
    # ThreadPoolExecutor works well because face_recognition has C code that releases GIL
    encs = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(face_recognition.face_encodings, rgb_small, [loc], num_jitters) for loc in face_locations]
        for fut in as_completed(futures):
            e = fut.result()
            if len(e) > 0:
                encs.append(e[0])
            else:
                encs.append(None)
    # ensure order matches face_locations -> as_completed breaks order; reorder by original index
    # simpler: run serial if ordering matters (above parallel approach intended for speed with small images)
    return encs

def match_encoding_vectorized(face_encoding, known_encodings, tolerance=TOLERANCE):
    # compute L2 distances and return best index, best distance
    dists = np.linalg.norm(known_encodings - face_encoding, axis=1)
    best_idx = int(np.argmin(dists))
    best_dist = float(dists[best_idx])
    matched = best_dist <= tolerance
    return matched, best_idx, best_dist

def annotate_image(original_bgr, results):
    img = original_bgr.copy()
    for r in results:
        top, right, bottom, left = r["location"]
        label = r["label"]
        color = (0, 255, 0) if r["matched"] else (0, 0, 255)
        cv2.rectangle(img, (left, top), (right, bottom), color, 2)
        # label background
        text = label if label else "Unknown"
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (left, bottom - text_h - 8), (left + text_w + 8, bottom), color, -1)
        cv2.putText(img, text, (left + 4, bottom - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
    return img

def process_class_photo(image_path, out_annotated=OUT_ANNOTATED, tolerance=TOLERANCE, max_width=MAX_WIDTH):
    t0 = time.time()
    known_encodings, known_ids, known_names = load_known_encodings()
    # read and resize
    bgr = cv2.imread(str(image_path))
    if bgr is None:
        raise FileNotFoundError(image_path)
    small_bgr, scale = resize_max_width(bgr, max_width=max_width)
    rgb = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2RGB)

    # detect faces
    t_detect0 = time.time()
    locations = face_recognition.face_locations(rgb, model=DETECTION_MODEL)
    t_detect1 = time.time()

    # compute encodings
    t_enc0 = time.time()
    encs = face_recognition.face_encodings(rgb, locations, num_jitters=ENCODE_JITTERS)
    t_enc1 = time.time()

    results = []
    for i, enc in enumerate(encs):
        if enc is None:
            # skip
            continue
        matched, best_idx, best_dist = match_encoding_vectorized(enc, known_encodings, tolerance=tolerance)
        matched_id = known_ids[best_idx] if matched else None
        matched_name = known_names[best_idx] if matched else None
        # scale coords back to original image size
        top, right, bottom, left = locations[i]
        top = int(top / scale); right = int(right / scale); bottom = int(bottom / scale); left = int(left / scale)
        label = matched_name if (matched_name and matched) else (matched_id if matched else None)
        results.append({
            "matched": bool(matched),
            "id": matched_id,
            "name": matched_name,
            "distance": float(best_dist),
            "location": (top, right, bottom, left),
            "label": label
        })

    total = time.time() - t0
    print(f"Detected {len(locations)} faces — detect: {t_detect1 - t_detect0:.2f}s, enc: {t_enc1 - t_enc0:.2f}s, total: {total:.2f}s")

    # annotate full-size original
    annotated = annotate_image(bgr, results)
    cv2.imwrite(str(out_annotated), annotated)

    # write CSV
    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "name", "matched", "distance", "top", "right", "bottom", "left"])
        for r in results:
            tid = r["id"] if r["id"] is not None else ""
            tname = r["name"] if r["name"] is not None else ""
            writer.writerow([tid, tname, r["matched"], r["distance"], *r["location"]])

    # save review JSON
    with open(OUT_REVIEW, "w") as fh:
        json.dump({"processed": len(results), "faces_detected": len(locations), "results": results}, fh, indent=2)

    return {"annotated": str(out_annotated), "csv": str(OUT_CSV), "review": str(OUT_REVIEW)}

# ---------- CLI usage ----------
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("image", nargs="?", default="class_photo.jpg", help="Path to class photo")
    p.add_argument("--tolerance", type=float, default=TOLERANCE)
    p.add_argument("--max-width", type=int, default=MAX_WIDTH)
    p.add_argument("--detect-model", choices=["hog", "cnn"], default=DETECTION_MODEL)
    p.add_argument("--jitters", type=int, default=ENCODE_JITTERS)
    args = p.parse_args()

    # update runtime config
    TOLERANCE = args.tolerance
    MAX_WIDTH = args.max_width
    DETECTION_MODEL = args.detect_model
    ENCODE_JITTERS = args.jitters

    out = process_class_photo(args.image, tolerance=TOLERANCE, max_width=MAX_WIDTH)
    print("Done:", out)