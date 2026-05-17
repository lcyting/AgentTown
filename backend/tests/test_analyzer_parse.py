"""Analyzer JSON 解析回退测试（无 LLM 依赖）"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock hello_agents 模块以避免导入真实 LLM 依赖
import types
_mock_hello_agents = types.ModuleType("hello_agents")
_mock_hello_agents.SimpleAgent = type("SimpleAgent", (), {})
_mock_hello_agents.HelloAgentsLLM = type("HelloAgentsLLM", (), {})
_mock_hello_agents_memory = types.ModuleType("hello_agents.memory")
sys.modules["hello_agents"] = _mock_hello_agents
sys.modules["hello_agents.memory"] = _mock_hello_agents_memory

import pytest
from relationship_manager import RelationshipManager


class MockLLM:
    """Mock LLM for RelationshipManager init"""
    pass


@pytest.fixture
def rm():
    """创建可测 _parse_analysis 的 RelationshipManager（不依赖真实 LLM）"""
    llm = MockLLM()
    # 使用 __new__ 绕过 __init__ 中的 SimpleAgent 初始化
    obj = RelationshipManager.__new__(RelationshipManager)
    obj.llm = llm
    obj.affinity_scores = {}
    return obj


class TestParseAnalysis:
    """_parse_analysis JSON 解析测试"""

    def test_complete_json_with_emotion(self, rm):
        """标准 JSON 含 emotion 字段"""
        response = '{"should_change": true, "change_amount": 5, "reason": "友好", "sentiment": "positive", "emotion": "happy"}'
        result = rm._parse_analysis(response)
        assert result["should_change"] == True
        assert result["emotion"] == "happy"

    def test_json_with_markdown_wrapper(self, rm):
        """带 markdown 代码块包裹的 JSON 仍能提取"""
        response = '''```json
{"should_change": true, "change_amount": -8, "reason": "批评", "sentiment": "negative", "emotion": "angry"}
```'''
        result = rm._parse_analysis(response)
        assert result["should_change"] == True
        assert result["emotion"] == "angry"

    def test_json_missing_emotion_key(self, rm):
        """缺少 emotion 键不抛异常（直接 JSON 解析不含 emotion 键）"""
        response = '{"should_change": true, "change_amount": 3, "reason": "问候", "sentiment": "positive"}'
        result = rm._parse_analysis(response)
        assert result["should_change"] == True
        assert "emotion" not in result

    def test_regex_fallback_extracts_emotion(self, rm):
        """残缺 JSON 正则提取 emotion（部分引号正确）"""
        response = '分析结果："should_change": true, "change_amount": 5, "reason": "友好", "sentiment": "positive", "emotion": "excited"，还有更多文字。'
        result = rm._parse_analysis(response)
        assert result["should_change"] == True
        assert result["change_amount"] == 5
        assert result["emotion"] == "excited"

    def test_regex_fallback_no_emotion(self, rm):
        """残缺 JSON 正则无 emotion 时回退 neutral"""
        response = '分析结果："should_change": false, "change_amount": 0, "reason": "闲聊", "sentiment": "neutral"，没有emotion字段。'
        result = rm._parse_analysis(response)
        assert result["should_change"] == False
        assert result["emotion"] == "neutral"

    def test_complete_parse_failure_returns_defaults(self, rm):
        """完全无法解析返回默认值"""
        response = "这是一段完全无法解析的文本"
        result = rm._parse_analysis(response)
        assert result["should_change"] == False
        assert result["change_amount"] == 0
        assert result["emotion"] == "neutral"

    def test_emotion_excited(self, rm):
        """emotion: excited 解析"""
        response = '{"should_change": true, "change_amount": 8, "reason": "赞美", "sentiment": "positive", "emotion": "excited"}'
        result = rm._parse_analysis(response)
        assert result["emotion"] == "excited"

    def test_emotion_sad(self, rm):
        """emotion: sad 解析"""
        response = '{"should_change": true, "change_amount": -3, "reason": "失望", "sentiment": "negative", "emotion": "sad"}'
        result = rm._parse_analysis(response)
        assert result["emotion"] == "sad"

    def test_emotion_neutral(self, rm):
        """emotion: neutral 解析"""
        response = '{"should_change": false, "change_amount": 0, "reason": "闲聊", "sentiment": "neutral", "emotion": "neutral"}'
        result = rm._parse_analysis(response)
        assert result["emotion"] == "neutral"
