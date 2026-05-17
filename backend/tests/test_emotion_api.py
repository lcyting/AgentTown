"""FastAPI TestClient 接口测试（无 LLM 依赖，使用 mock）"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import types

# Mock hello_agents 模块以避免导入真实 LLM 依赖
_mock_hello_agents = types.ModuleType("hello_agents")
_mock_hello_agents.SimpleAgent = type("SimpleAgent", (), {})
_mock_hello_agents.HelloAgentsLLM = type("HelloAgentsLLM", (), {})
_mock_hello_agents_memory = types.ModuleType("hello_agents.memory")
_mock_hello_agents_memory.MemoryManager = type("MemoryManager", (), {})
_mock_hello_agents_memory.MemoryConfig = type("MemoryConfig", (), {})
_mock_hello_agents_memory.MemoryItem = type("MemoryItem", (), {})
sys.modules["hello_agents"] = _mock_hello_agents
sys.modules["hello_agents.memory"] = _mock_hello_agents_memory

# Mock state_manager 同样需要在 import main 之前
_mock_state_manager = types.ModuleType("state_manager")
_mock_state_manager.get_state_manager = lambda *args, **kwargs: None
sys.modules["state_manager"] = _mock_state_manager

import pytest
from fastapi.testclient import TestClient


# 创建 mock NPCAgentManager
class MockNPCAgentManager:
    def __init__(self):
        self.emotion_manager = None
        self.relationship_manager = None
        self._npc_info = {
            "程码": {"name": "程码", "title": "Python工程师", "location": "工位区", "activity": "写代码", "available": True},
            "林案": {"name": "林案", "title": "产品经理", "location": "会议室", "activity": "整理需求", "available": True},
            "苏绘": {"name": "苏绘", "title": "UI设计师", "location": "休息区", "activity": "喝咖啡", "available": True},
        }

    def get_npc_info(self, npc_name):
        return self._npc_info.get(npc_name, {})

    def get_all_npcs(self):
        return list(self._npc_info.values())

    def chat(self, npc_name, message, player_id="player"):
        return {
            "message": f"{npc_name}: 测试回复 -> {message}",
            "emotion": "happy",
            "emotion_label": "开心",
        }

    def get_npc_emotion(self, npc_name, player_id="player"):
        return {
            "emotion": "excited",
            "emotion_label": "兴奋",
            "modifier": "热情高涨，表达积极，细节丰富",
        }

    def get_all_emotions(self, player_id="player"):
        return {
            "程码": {"emotion": "happy", "emotion_label": "开心", "modifier": "语气轻快..."},
            "林案": {"emotion": "sad", "emotion_label": "难过", "modifier": "语气低沉..."},
            "苏绘": {"emotion": "excited", "emotion_label": "兴奋", "modifier": "热情高涨..."},
        }

    def set_npc_emotion(self, npc_name, emotion, player_id="player"):
        pass


# 现在安全导入 main（hello_agents 已被 mock）
import main


@pytest.fixture
def mock_npc_mgr():
    return MockNPCAgentManager()


# Mock get_managers 绕过真实 Agent 初始化
@pytest.fixture(autouse=True)
def mock_managers(monkeypatch, mock_npc_mgr):
    """全局 mock: main.get_managers 返回 mock 实例"""
    def mock_get_managers():
        return mock_npc_mgr, None
    monkeypatch.setattr(main, "get_managers", mock_get_managers)


@pytest.fixture
def client():
    """FastAPI TestClient"""
    return TestClient(main.app)


class TestEmotionAPI:
    """情绪 REST API 测试"""

    def test_get_npc_emotion_success(self, client):
        """GET 单个 NPC 情绪成功"""
        response = client.get("/npcs/程码/emotion")
        assert response.status_code == 200
        data = response.json()
        assert data["npc_name"] == "程码"
        assert data["emotion"] == "excited"
        assert data["emotion_label"] == "兴奋"

    def test_get_npc_emotion_404(self, client):
        """不存在的 NPC 返回 404"""
        response = client.get("/npcs/不存在NPC/emotion")
        assert response.status_code == 404

    def test_get_all_emotions(self, client):
        """GET 全部 NPC 情绪"""
        response = client.get("/emotions")
        assert response.status_code == 200
        data = response.json()
        assert "emotions" in data
        assert "程码" in data["emotions"]
        assert data["emotions"]["程码"]["emotion"] == "happy"
        assert "林案" in data["emotions"]
        assert "苏绘" in data["emotions"]

    def test_put_npc_emotion_success(self, client):
        """PUT 设置情绪成功"""
        response = client.put("/npcs/程码/emotion?emotion=excited")
        assert response.status_code == 200
        data = response.json()
        assert data["npc_name"] == "程码"
        assert data["emotion"] == "excited"
        assert data["emotion_label"] == "兴奋"

    def test_put_npc_emotion_invalid(self, client):
        """PUT 非法情绪值返回 400"""
        response = client.put("/npcs/程码/emotion?emotion=invalid")
        assert response.status_code == 400

    def test_put_npc_emotion_404(self, client):
        """PUT 不存在 NPC 返回 404"""
        response = client.put("/npcs/不存在NPC/emotion?emotion=happy")
        assert response.status_code == 404

    def test_post_chat_returns_emotion(self, client):
        """POST /chat 响应含 emotion 和 emotion_label"""
        response = client.post("/chat", json={
            "npc_name": "程码",
            "message": "你好"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "emotion" in data
        assert data["emotion"] == "happy"
        assert "emotion_label" in data
        assert data["emotion_label"] == "开心"

    def test_post_chat_404(self, client):
        """POST /chat 不存在的 NPC 返回 404"""
        response = client.post("/chat", json={
            "npc_name": "不存在NPC",
            "message": "你好"
        })
        assert response.status_code == 404

    def test_root_lists_emotion_endpoints(self, client):
        """根路由列出情绪端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "npc_emotion" in data["endpoints"]
        assert "all_emotions" in data["endpoints"]
        assert "情绪系统" in data["features"]


class TestChatResponseModel:
    """ChatResponse 模型测试"""

    def test_chat_response_with_emotion(self):
        """ChatResponse 包含 emotion 字段"""
        from models import ChatResponse
        resp = ChatResponse(
            npc_name="程码",
            npc_title="Python工程师",
            message="测试消息",
            emotion="happy",
            emotion_label="开心",
            success=True
        )
        data = resp.model_dump()
        assert data["emotion"] == "happy"
        assert data["emotion_label"] == "开心"

    def test_chat_response_default_emotion(self):
        """ChatResponse emotion 默认值"""
        from models import ChatResponse
        resp = ChatResponse(
            npc_name="程码",
            npc_title="Python工程师",
            message="测试消息",
            success=True
        )
        data = resp.model_dump()
        assert data["emotion"] == "neutral"
        assert data["emotion_label"] == "平静"
