FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    THM_DATA_DIR=/data

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libx264-164 \
        tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY services /app/services

RUN mkdir -p /data/{music,video,assets,playlists,logs,state,uploads,research,covers}

ENTRYPOINT ["tini", "--"]
COPY run_services.sh /app/
RUN chmod +x /app/run_services.sh
EXPOSE 8000
CMD ["/app/run_services.sh"]
