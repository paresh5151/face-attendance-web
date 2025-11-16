FROM ghcr.io/paresh5151/face-attendance:latest

WORKDIR /app
COPY . /app

# install only tiny runtime deps (no dlib/opencv)
RUN pip install --no-cache-dir -r requirements.txt || true

ENV PORT=10000
CMD ["bash", "-lc", "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 200 --workers 2"]
