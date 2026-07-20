FROM fullstorydev/grpcurl:v1.9.3 AS grpcurl

FROM python:3.12-slim
WORKDIR /app
COPY --chmod=0755 --from=grpcurl /bin/grpcurl /usr/local/bin/grpcurl
COPY --chmod=0755 prober.py /app/prober.py
COPY --chmod=0644 service_info.proto /app/service_info.proto
USER 65534:65534
ENTRYPOINT ["python3", "/app/prober.py"]
