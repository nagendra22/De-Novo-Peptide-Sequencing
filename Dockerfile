FROM nvcr.io/nvidia/pytorch:26.04-py3

RUN apt-get update && apt-get install -y --no-install-recommends \
        libxrender1 libxext6 libsm6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install casanovo

WORKDIR /data