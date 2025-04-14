import os
import time
import yaml
import shutil
from globals import SCRIPT_DIR

def ensure_default_config(path):
    default_path = os.path.join(SCRIPT_DIR, "config_default.yaml")  # Путь к шаблону
    if not os.path.exists(path):
        print(f"Config not found at {path}, creating from default: {default_path}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copyfile(default_path, path)
        print(f"Default config created at {path}, please update settings and restart container. Sleeping 120 sec...")
        time.sleep(120)

def load_config(path):    
    ensure_default_config(path)
    with open(path, "r") as f:
        print(f"Config load from {path}, script started...")
        return yaml.safe_load(f)
    
