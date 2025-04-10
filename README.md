# Frigate Telegram Bot

A lightweight Python-based notification bot that listens to Frigate MQTT events and sends annotated alerts and video clips to Telegram.

---

## 🚀 Features

- Subscribes to Frigate MQTT events
- Filters by zone and camera
- Downloads event video and snapshot from Frigate API
- Sends alerts and video clips to Telegram
- Mute functionality with Telegram bot commands
- Dockerized for easy deployment

---

## 🧱 Project Structure

```
project-root/
├── main.py                # Main MQTT listener
├── config.py              # Config loader
├── telegram_utils.py      # Telegram messaging functions
├── frigate_utils.py       # Frigate API handlers
├── state.py               # Mute state storage
├── paths.py               # Centralized path constants
├── config_default.yaml    # Fallback config template
├── Dockerfile             # Container build script
├── docker-compose.yml     # Docker service runner
├── requirements.txt       # Python dependencies
├── config/                # Mounted config (volume)
└── cache/                 # Mounted storage (volume)
```

---

## ⚙️ Configuration

Create your config in `config/config.yaml` or let the bot auto-generate a default one.

**Example: `config.yaml`**

```yaml
frigate:
  mqtt_broker: "mqtt.local"
  mqtt_topic: "frigate/events"
  event_zone: "notify"
  camera_whitelist: ["front_door"]
  min_event_interval: 30

storage:
  clip_duration: 8

telegram:
  bot_token: "your_bot_token"
  chat_id: "your_chat_id"
  mute_durations:
    short: 300
    long: 3600

server:
  frigate_api: "http://frigate.local:5000/api/events"
```

---

## 🐳 Run with Docker

### 1. Build and start the service

```bash
docker-compose up --build -d
```

### 2. Folder mapping

- `config/` → stores `config.yaml`
- `cache/` → stores temp videos, logs, and state

### 3. Healthcheck

tbd

---

## 🛠 Development

### Run locally:

```bash
python main.py
```

### Override default paths via ENV:

```bash
export CONFIG_PATH=./config/config.yaml
export CACHE_DIR=./cache
python main.py
```

---

## 🤖 Telegram Commands

- `/muteshort` – mute notifications for short duration
- `/mutelong` – mute for longer period

---

## 📦 Building a New Release

```bash
docker build -t frigate-telegram-bot .
```

---

## 📄 License

MIT License — feel free to use, modify, and share.

---

## ❤️ Contributions

PRs and issues are welcome!
