# ── Stage 1: Apache POI fat JAR fordítása ───────────────────────────────────
FROM maven:3.9-eclipse-temurin-17-alpine AS jar-builder

WORKDIR /build

# pom.xml és Java forrás átmásolása (jobb cache rétegek miatt külön lépésben)
COPY src/integrations/excel/java/pom.xml ./pom.xml
COPY src/integrations/excel/java/src     ./src

# Függőségek letöltése (elkülönített réteg → gyorsabb újraépítés)
RUN mvn dependency:go-offline -q

# Fat JAR buildlelése
RUN mvn package -q -DskipTests

# ── Stage 2: Python alkalmazás ──────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Java futtatókörnyezet (JRE) a JAR meghívásához + build eszközök
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-jre-headless \
  && rm -rf /var/lib/apt/lists/*

COPY infrastructure/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app

# A fat JAR-t /app/lib/-be másoljuk – ez KÍVÜL van a ./src:/app/src volume-mount-on,
# tehát futás közben sem fedik el
COPY --from=jar-builder /build/target/excel-writer-1.0.0.jar /app/lib/excel-writer-1.0.0.jar

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
