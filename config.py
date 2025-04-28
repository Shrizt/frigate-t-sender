
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import os
import sys
import time

from typing import List, Dict, Any, Type
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    ConfigDict,
#    ValidationInfo,    
)
from pydantic.fields import PydanticUndefined
#import yaml
#from pathlib import Path
from io import StringIO

from logger import ulog

yaml = YAML()
yaml.width = 120
yaml.default_flow_style = False


class EngineConfig(BaseModel):
    retry_count: int = Field(
        default=5,
        gt=0,
        le=10,  # Max 10 retries
        description="Max retries to restart engine on errors happened in one retry window (1-10)"
    )
    retry_delay: int = Field(
        default=5,
        gt=0,
        le=300,  # Max 5 minutes
        description="Delay between retries (1-300s)"
    )
    retry_window: int = Field(
        default=60,
        gt=0,
        le=1440,  # Max 24 hours
        description="Retry counting window (1-1440 minutes)"
    )

class FrigateConfig(BaseModel):
    frigate_api: HttpUrl = Field('http://localhost:5000', description="API endpoint URL")
    event_zone: str = Field(
        'zone1',
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",  # Alphanumeric + underscores
        description="Zone raising event name (1-50 chars, a-z0-9_)"
    )
    camera_whitelist: List[str] = Field(
        default=["cam1", "cam2"],
        min_items=1,
        max_items=20,
        description="1-20 cameras raising events"
    )
    min_event_interval: int = Field(
        default=10,
        gt=0,
        le=3600,  # Max 1 hour
        description="Minimum event interval to send (1-3600s)"
    )

class MQTTConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    mqtt_broker: str = Field('localhost', min_length=1)
    mqtt_port: int = Field(1883, gt=0, le=65535)
    mqtt_keepalive: int = Field(60, gt=0)
    mqtt_topic: str = Field("frigate/events", min_length=1, description="MQTT topic to subscribe")

class StorageConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    clip_duration: int = Field(8, gt=0, description="Duration (minutes) of video clips to cut to")

class TelegramConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    bot_token: str = Field('telegram_bot_token', min_length=1)
    chat_id: str = Field('your_chat_id', min_length=1)
    mute_durations: Dict[str, int] = Field(
        default={"short": 300, "long": 3600},
        description="Mute duration presets in seconds"
    )

    @field_validator('mute_durations')
    @classmethod
    def validate_mute_durations(cls, v: Dict[str, int]) -> Dict[str, int]:
        if not all(isinstance(x, int) for x in v.values()):
            raise ValueError("All mute durations must be integers")
        if any(v < 0 for v in v.values()):
            raise ValueError("Mute durations cannot be negative")
        return v

class AppConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    engine: EngineConfig
    frigate: FrigateConfig
    mqtt: MQTTConfig
    storage: StorageConfig
    telegram: TelegramConfig


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load and validate configuration from YAML file using ruamel.yaml"""
    if not os.path.exists(config_path):
        ulog.error(f"Config not found at {config_path}, creating from default...")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        write_default_config(config_path)
        ulog.info(f"Default config created at {config_path}, please update settings and restart. Exiting...")
        time.sleep(1)
        sys.exit(10)
    try:
        with open(config_path, 'r') as f:
            raw_config = yaml.load(f)
        return AppConfig.model_validate(raw_config)
    except Exception as e:
        raise ValueError(f"Configuration error in '{config_path}': {str(e)}") from e

def generate_default_config(model: Type[BaseModel]) -> str:
    """
    Generate YAML with default values from Pydantic model.
    Field descriptions are added as comments above each key.
    """
    def build_config_map(model_type: Type[BaseModel]) -> CommentedMap:
        result = CommentedMap()
        for field_name, field_info in model_type.model_fields.items():
            annotation = field_info.annotation

            # Field description as comment
            desc = field_info.description or ""
            if desc:
                result.yaml_set_comment_before_after_key(
                    key=field_name,
                    before=f"# {desc}"
                )

            # Handle nested models
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                nested = build_config_map(annotation)
                result[field_name] = nested
            else:
                if field_info.default is not PydanticUndefined:
                    value = field_info.default
                elif field_info.default_factory is not None:
                    value = field_info.default_factory()
                elif field_info.is_required():
                    value = ""  # Leave required fields empty
                else:
                    value = None

                result[field_name] = value

        return result

    config_map = build_config_map(model)
    stream = StringIO()
    yaml.dump(config_map, stream)
    return stream.getvalue()

def write_default_config(output_path: str = "config_default.yaml"):
    """Write default configuration to YAML file"""
    header = """# Auto-generated configuration template\n\n"""
    
    with open(output_path, 'w') as f:
        f.write(header)
        f.write(generate_default_config(AppConfig))


# Singleton configuration instance
# config2 = load_config(CONFIG_FILE)