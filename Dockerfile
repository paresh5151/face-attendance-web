# Dockerfile (place at project root)
FROM python:3.9-slim

# Install system dependencies required for dlib + OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    git \
    wget \
    curl \
    unzip \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first (for Docker cache)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /app/requirements.txt

# Copy the rest of the app
COPY . /app

# Ensure known directory exists
RUN mkdir -p /app/known

# Expose port 5000
EXPOSE 5000

# Start using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "120"]