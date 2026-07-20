FROM python:3.14-slim

LABEL org.opencontainers.image.title="bitcoin-fn-prometheus-exporter"
LABEL org.opencontainers.image.description="Prometheus exporter for Bitcoin Core full nodes"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]