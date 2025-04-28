FROM python:3-alpine

# Install ffmpeg + dependencies
#RUN apt-get update && \
#    apt-get install -y ffmpeg && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

# Install Python-req
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY main.py globals.py config.py logger.py /app/

WORKDIR /app

# Volumes for config and cache
VOLUME ["/config", "/cache"]

# HEALTHCHECK: todo
#HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD curl -f http://localhost:1883 || exit 1

# run with console output uncached
CMD ["python", "-u", "main.py"]
