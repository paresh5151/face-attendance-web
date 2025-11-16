# Use conda image to get prebuilt dlib/opencv from conda-forge
FROM continuumio/miniconda3:23.5.0

WORKDIR /app

# Use conda-forge and create env with python + prebuilt packages
RUN conda config --append channels conda-forge && \
    conda create -n faceenv python=3.9 -y && \
    /bin/bash -lc "conda activate faceenv && conda install -y -c conda-forge \
      dlib=19.24.2 \
      opencv=4.10.0 \
      numpy \
      pandas \
      pillow \
      requests" && \
    # pip-install lighter extras (Flask + gunicorn)
    /bin/bash -lc "conda activate faceenv && pip install --no-cache-dir flask flask-cors gunicorn face_recognition==1.3.0"

# Make conda env available on PATH
ENV PATH /opt/conda/envs/faceenv/bin:$PATH

# Copy app code
COPY . /app

# Ensure known dir exists
RUN mkdir -p /app/known

EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "120"]
