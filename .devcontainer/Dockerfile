FROM mcr.microsoft.com/devcontainers/python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

# --- MUDANÇA AQUI ---
# Instalamos libgl1 (para corrigir o erro libGL.so.1)
# Instalamos tesseract-ocr (para ler PDFs escaneados antigos)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-por \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*
# Nota: 'tesseract-ocr-por' adiciona suporte ao idioma Português!
# --------------------

RUN pip install --upgrade pip

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp