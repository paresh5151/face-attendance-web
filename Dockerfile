# Use micromamba base image and install prebuilt packages from conda-forge
FROM mambaorg/micromamba:1.4.2

# Create environment and install runtime deps (prebuilt dlib/opencv from conda-forge)
RUN micromamba create -y -n faceenv -c conda-forge \
    python=3.9 \
    numpy \
    pandas \
    pillow \
    opencv=4.10.0 \
    dlib=19.24.2 \
    face_recognition=1.3.0 \
    requests \
  && micromamba clean --all --yes

SHELL ["micromamba", "run", "-n", "faceenv", "/bin/bash", "-lc"]

WORKDIR /app
COPY . /app

# ensure encodings and known are accessible at runtime (encodings.npz already in repo)
RUN mkdir -p /mnt/data/face-attendance || true

# remove caches to slim image
RUN rm -rf /root/.cache/pip /root/.cache/micromamba || true

EXPOSE 5000

CMD ["micromamba", "run", "-n", "faceenv", "gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "180"]
