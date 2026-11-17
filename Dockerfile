# Imagem do painel. O mesmo jeito de subir dos irmãos da família Cenários.
FROM python:3.13-slim

WORKDIR /app

# curl → healthcheck · libgomp1 → DuckDB usa OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Do lock, não do requirements.txt: dois builds do mesmo commit sobem as
# mesmas versões. O lock aponta para o wheel do cenarios-core em `vendor/`.
COPY requirements.lock.txt .
COPY vendor/ vendor/
RUN pip install --no-cache-dir -r requirements.lock.txt

COPY app.py .
COPY src/ src/
COPY .streamlit/ .streamlit/
COPY geo/ geo/
COPY assets/ assets/
# data/ vem do volume do compose (somente leitura)

ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8501/cenarios/demografico/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
