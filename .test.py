import os
from globals import CONFIG_FILE, CONFIG_DEFAULT_FILE, CONFIG_PATH
from config import write_default_config, load_config

write_default_config(os.path.join(CONFIG_PATH, "config2_default.yaml"))

cfg = load_config(os.path.join(CONFIG_PATH, "config2_default.yaml"))
print(cfg)