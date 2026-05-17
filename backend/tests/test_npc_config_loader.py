"""NPC YAML 配置加载测试"""

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

if "hello_agents" not in sys.modules:
    _mock_hello_agents = types.ModuleType("hello_agents")
    _mock_hello_agents.SimpleAgent = type("SimpleAgent", (), {})
    _mock_hello_agents.HelloAgentsLLM = type("HelloAgentsLLM", (), {})
    _mock_ha_memory = types.ModuleType("hello_agents.memory")
    _mock_ha_memory.MemoryManager = type("MemoryManager", (), {})
    _mock_ha_memory.MemoryConfig = type("MemoryConfig", (), {})
    _mock_ha_memory.MemoryItem = type("MemoryItem", (), {})
    sys.modules["hello_agents"] = _mock_hello_agents
    sys.modules["hello_agents.memory"] = _mock_ha_memory

from npc_config_loader import (
    get_default_affinities,
    get_default_emotions,
    get_npc_config,
    get_npc_roles,
    load_npc_config,
    reload_npc_config,
    reset_npc_config_cache,
)
from emotion_manager import EmotionManager

FIXTURES = Path(__file__).parent / "fixtures"
DEFAULT_YAML = Path(__file__).parent.parent / "npc_config" / "npcs.yaml"
MINIMAL_YAML = FIXTURES / "minimal_npcs.yaml"


@pytest.fixture(autouse=True)
def clear_config_cache():
    reset_npc_config_cache()
    yield
    reset_npc_config_cache()


class TestLoadNpcConfig:
    def test_load_default_config(self):
        config = load_npc_config(DEFAULT_YAML)
        assert config.version == 1
        assert "程码" in config.npcs

    def test_load_minimal_fixture(self):
        config = load_npc_config(MINIMAL_YAML)
        assert config.npcs["测试员"].baselines.affinity == 70


class TestGetters:
    def test_get_npc_roles_excludes_baselines(self):
        reload_npc_config(MINIMAL_YAML)
        roles = get_npc_roles()
        assert "baselines" not in roles["测试员"]

    def test_get_baselines_and_defaults(self):
        reload_npc_config(MINIMAL_YAML)
        assert get_default_emotions()["测试员"] == "happy"
        assert get_default_affinities()["测试员"] == 70.0


class TestManagerBaselines:
    def test_emotion_manager_uses_yaml_baseline(self):
        mgr = EmotionManager(default_emotions={"测试员": "excited"})
        assert mgr.get_emotion("测试员") == "excited"

    def test_relationship_manager_uses_yaml_baseline(self):
        from relationship_manager import RelationshipManager

        mgr = RelationshipManager.__new__(RelationshipManager)
        mgr.default_affinities = {"测试员": 75.0}
        mgr.affinity_scores = {}
        assert mgr.get_affinity("测试员") == 75.0


class TestMemorySeed:
    def test_seed_on_empty_memory(self):
        from agents import NPCAgentManager
        from npc_config_loader import InitialMemoryItem

        mgr = NPCAgentManager.__new__(NPCAgentManager)
        memory_manager = MagicMock()
        memory_manager.memory_types = {
            "working": MagicMock(get_all=MagicMock(return_value=[])),
            "episodic": MagicMock(get_all=MagicMock(return_value=[])),
        }
        items = [InitialMemoryItem(content="种子A", type="working", importance=0.5)]
        mgr._seed_initial_memories("测试员", memory_manager, items)
        assert memory_manager.add_memory.call_count == 1

    def test_skip_seed_when_memory_exists(self):
        from agents import NPCAgentManager
        from npc_config_loader import InitialMemoryItem

        mgr = NPCAgentManager.__new__(NPCAgentManager)
        memory_manager = MagicMock()
        memory_manager.memory_types = {
            "working": MagicMock(get_all=MagicMock(return_value=[object()])),
            "episodic": MagicMock(get_all=MagicMock(return_value=[])),
        }
        mgr._seed_initial_memories("测试员", memory_manager, [InitialMemoryItem(content="x")])
        memory_manager.add_memory.assert_not_called()
