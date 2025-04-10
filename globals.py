import os

SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.getenv("FTS_CONFIG_PATH", SCRIPT_DIR)
CACHE_DIR = os.getenv("FTS_CACHE_DIR", os.path.join(SCRIPT_DIR, "cache"))
STATE_FILE = os.path.join(CACHE_DIR, "state.json")
LOG_FILE = os.path.join(CACHE_DIR, "fts.log")
CONFIG_FILE = os.path.join(CONFIG_PATH, "config.yaml")
