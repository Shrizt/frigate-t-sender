FROM python:3-alpine

# Установим ffmpeg и необходимые зависимости
#RUN apt-get update && \
#    apt-get install -y ffmpeg && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

# Установим Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем скриптs
COPY main.py globals.py config.py config_default.yaml /app/

WORKDIR /app

# Объявляем volume для конфигурации и кэша
VOLUME ["/config", "/cache"]

# HEALTHCHECK: проверяет, что контейнер жив, раз в 30 сек
#HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD curl -f http://localhost:1883 || exit 1

# Запуск скрипта
CMD ["python", "main.py"]
