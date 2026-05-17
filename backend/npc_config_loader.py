"""NPC 配置 YAML 加载与校验"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from emotion_manager import EMOTIONS

VALID_TIME_SLOTS = ("morning", "noon", "afternoon", "evening")
DEFAULT_CONFIG_PATH = Path(__file__).parent / "npc_config" / "npcs.yaml"
_config_path_override: Optional[Path] = None


class NPCBaselines(BaseModel):
    emotion: str = "neutral"
    affinity: float = Field(default=50.0, ge=0.0, le=100.0)

    @field_validator("emotion")
    @classmethod
    def normalize_emotion(cls, value: str) -> str:
        if value not in EMOTIONS:
            return "neutral"
        return value


class InitialMemoryItem(BaseModel):
    content: str
    type: Literal["working", "episodic"] = "episodic"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class NPCRoleConfig(BaseModel):
    scene_id: str
    world_name: str
    title: str
    location: str
    activity: str
    interaction_hint: str = "按 E 交互"
    personality: str
    expertise: str
    style: str
    hobbies: str
    baselines: NPCBaselines = Field(default_factory=NPCBaselines)
    initial_memories: List[InitialMemoryItem] = Field(default_factory=list)


class NPCConfigFile(BaseModel):
    version: int = 1
    npcs: Dict[str, NPCRoleConfig]
    ambient_dialogues: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    @field_validator("ambient_dialogues")
    @classmethod
    def validate_time_slots(cls, value: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        for slot in value:
            if slot not in VALID_TIME_SLOTS:
                raise ValueError(
                    f"ambient_dialogues 时段 '{slot}' 无效，"
                    f"允许: {', '.join(VALID_TIME_SLOTS)}"
                )
        return value


def _resolve_config_path() -> Path:
    if _config_path_override is not None:
        return _config_path_override
    env_path = os.environ.get("NPC_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_CONFIG_PATH


def load_npc_config(path: Optional[os.PathLike] = None) -> NPCConfigFile:
    """加载并校验 NPC 配置文件。失败时抛出 ValueError（含中文说明）。"""
    config_path = Path(path) if path else _resolve_config_path()
    if not config_path.is_file():
        raise ValueError(f"NPC 配置文件不存在: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"NPC 配置文件 YAML 语法错误 ({config_path}): {e}") from e

    if not isinstance(raw, dict):
        raise ValueError(f"NPC 配置文件根节点必须是对象: {config_path}")

    try:
        return NPCConfigFile.model_validate(raw)
    except ValidationError as e:
        errors = []
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errors.append(f"  - {loc}: {err['msg']}")
        raise ValueError(
            f"NPC 配置文件校验失败 ({config_path}):\n" + "\n".join(errors)
        ) from e


@lru_cache(maxsize=1)
def get_npc_config() -> NPCConfigFile:
    return load_npc_config(_resolve_config_path())


def reload_npc_config(path: Optional[os.PathLike] = None) -> NPCConfigFile:
    global _config_path_override
    get_npc_config.cache_clear()
    if path is not None:
        _config_path_override = Path(path)
    else:
        _config_path_override = None
    return get_npc_config()


def reset_npc_config_cache() -> None:
    global _config_path_override
    _config_path_override = None
    get_npc_config.cache_clear()


def get_npc_roles() -> Dict[str, Dict[str, str]]:
    roles = {}
    for name, cfg in get_npc_config().npcs.items():
        roles[name] = {
            "scene_id": cfg.scene_id,
            "world_name": cfg.world_name,
            "title": cfg.title,
            "location": cfg.location,
            "activity": cfg.activity,
            "interaction_hint": cfg.interaction_hint,
            "personality": cfg.personality,
            "expertise": cfg.expertise,
            "style": cfg.style,
            "hobbies": cfg.hobbies,
        }
    return roles


def get_baselines() -> Dict[str, Dict[str, object]]:
    return {
        name: {
            "emotion": cfg.baselines.emotion,
            "affinity": cfg.baselines.affinity,
        }
        for name, cfg in get_npc_config().npcs.items()
    }


def get_initial_memories() -> Dict[str, List[InitialMemoryItem]]:
    return {
        name: list(cfg.initial_memories)
        for name, cfg in get_npc_config().npcs.items()
    }


def get_ambient_dialogues() -> Dict[str, Dict[str, str]]:
    return dict(get_npc_config().ambient_dialogues)


def get_default_emotions() -> Dict[str, str]:
    return {name: b["emotion"] for name, b in get_baselines().items()}


def get_default_affinities() -> Dict[str, float]:
    return {name: float(b["affinity"]) for name, b in get_baselines().items()}
