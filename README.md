# Frigate Telegram Sender

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

**Default: `config.yaml`** - will be created on first run if not exist (config_default.yaml is included to project)

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
export FTS_CONFIG_PATH=./config/config.yaml
export FTS_CACHE_DIR=./cache
python main.py
```

---

## 🤖 Telegram Commands

- `/muteshort` – mute notifications for short duration
- `/mutelong` – mute for longer period
* not yet implemented - will send silent messages if muted

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
