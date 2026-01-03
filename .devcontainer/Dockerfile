# Imagem base Python leve
FROM mcr.microsoft.com/devcontainers/python:3.11
WORKDIR /workspace

# Evita avisos de frontend durante instalações apt
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências básicas do sistema (git, curl, etc.)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Atualizar pip
RUN pip install --upgrade pip
COPY requirements.txt /tmp/pip-tmp/

RUN pip3 install --no-cache-dir -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# Definir diretório de trabalho
