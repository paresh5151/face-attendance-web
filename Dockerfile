FROM ghcr.io/paresh5151/face-attendance:latest

WORKDIR /app
COPY . /app

# Use python -m pip (safer if pip binary isn't on PATH in base image)
# upgrade pip then install only lightweight runtime deps (no rebuilding dlib/opencv)
RUN python -m pip install --upgrade pip || true \
 && python -m pip install --no-cache-dir gunicorn flask numpy || true

ENV PORT=10000
# Use python -m gunicorn to avoid depending on a shell wrapper binary
CMD ["bash", "-lc", "python -m gunicorn app:app --bind 0.0.0.0:$PORT --timeout 200 --workers 2"]
