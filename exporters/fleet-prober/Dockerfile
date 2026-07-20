FROM python:3.12-slim
WORKDIR /app
COPY prober.py /app/prober.py
USER 65534:65534
ENTRYPOINT ["python3", "/app/prober.py"]
