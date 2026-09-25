FROM python:3.12-slim
WORKDIR /app
COPY processing /app/processing
RUN pip install --no-cache-dir -e /app/processing
WORKDIR /data
ENTRYPOINT ["siret3"]
CMD ["--help"]
