FROM python:3.11-slim

WORKDIR /app

# system deps (safe)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# copy app
COPY . .

# REQUIRED for Render
ENV PYTHONUNBUFFERED=1

# IMPORTANT: use $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

