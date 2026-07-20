FROM python:3.12-slim
WORKDIR /app
COPY exporter.py /app/exporter.py
USER 65534:65534
ENTRYPOINT ["python3", "/app/exporter.py"]
