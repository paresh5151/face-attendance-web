FROM ghcr.io/paresh5151/face-attendance:latest

WORKDIR /app
COPY . /app

# Try python3 binaries (safer if 'python' is not on PATH).
RUN python3 -m pip install --upgrade pip || true \
 && python3 -m pip install --no-cache-dir gunicorn flask numpy || true

ENV PORT=10000
CMD ["bash", "-lc", "python3 -m gunicorn app:app --bind 0.0.0.0:$PORT --timeout 200 --workers 2"]
