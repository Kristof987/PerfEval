# ---- base ----
FROM python:3.11-slim

# Ne írjon .pyc-t, logok azonnal jelenjenek meg
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# (opcionális, de gyakran hasznos) build csomagok
# Ha nincs olyan pip csomagod, ami natív fordítást igényel, ezt ki is veheted.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Requirements külön rétegben a gyorsabb build miatt
COPY infrastructure/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Projekt fájlok
COPY . /app

# Streamlit port
EXPOSE 8501

# Streamlit szerver config (konténerben kell a 0.0.0.0)
CMD ["streamlit", "run", "src/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
