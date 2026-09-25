# Optional local tile + processing image. Web map is still `npm run dev` in web/.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY processing /app/processing
RUN pip install --no-cache-dir -e /app/processing

WORKDIR /data
ENTRYPOINT ["siret3"]
CMD ["--help"]
