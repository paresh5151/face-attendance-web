FROM mambaorg/micromamba:1.4.2

RUN micromamba create -y -n faceenv -c conda-forge python=3.9 \
    dlib=19.24.2 \
    face_recognition \
    opencv \
    numpy \
    pandas \
    pillow \
    requests \
    && micromamba clean --all --yes

SHELL ["micromamba", "run", "-n", "faceenv", "/bin/bash", "-c"]

WORKDIR /app

COPY . /app

RUN python - <<'PY'
import sys
print("Python binary:", sys.executable)
import numpy, dlib, face_recognition, cv2, pandas
print("IMPORT OK")
PY

EXPOSE 5000

CMD ["micromamba", "run", "-n", "faceenv", "gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "180"]
