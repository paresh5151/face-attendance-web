FROM ghcr.io/curtimus/face-recognition:latest

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=10000
CMD ["bash", "-lc", "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 200 --workers 2"]
