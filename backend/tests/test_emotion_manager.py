"""EmotionManager 单元测试（无 LLM 依赖）"""

import pytest
from emotion_manager import EmotionManager, EMOTIONS, EMOTION_MODIFIERS


class TestEmotionManager:
    """EmotionManager 核心功能测试"""

    def test_default_emotion_is_neutral(self, emotion_manager):
        """新 NPC 默认 neutral，标签 平静"""
        emotion = emotion_manager.get_emotion("程码")
        assert emotion == "neutral"
        assert emotion_manager.get_emotion_label(emotion) == "平静"

    def test_set_and_get_emotion(self, emotion_manager):
        """set_emotion 后 get_emotion 一致"""
        result = emotion_manager.set_emotion("程码", "happy")
        assert result == "happy"
        assert emotion_manager.get_emotion("程码") == "happy"
        assert emotion_manager.get_emotion_label("happy") == "开心"

    def test_invalid_emotion_normalized_to_neutral(self, emotion_manager):
        """非法 emotion 归一化为 neutral"""
        result = emotion_manager.set_emotion("程码", "invalid_emotion")
        assert result == "neutral"
        assert emotion_manager.get_emotion("程码") == "neutral"
        assert emotion_manager.get_emotion_label("neutral") == "平静"

    def test_all_valid_emotions_set_get(self, emotion_manager):
        """所有合法 emotion 都能正常 set/get"""
        for key in EMOTIONS:
            result = emotion_manager.set_emotion("测试NPC", key)
            assert result == key
            assert emotion_manager.get_emotion("测试NPC") == key

    def test_emotion_modifier_non_empty(self, emotion_manager):
        """各合法 emotion 的 modifier 非空且互不相同"""
        modifiers = set()
        for key in EMOTIONS:
            modifier = emotion_manager.get_emotion_modifier(key)
            assert modifier, f"{key} 的 modifier 不应为空"
            modifiers.add(modifier)
        assert len(modifiers) == len(EMOTIONS), "所有 modifier 应互不相同"

    def test_emotion_modifier_keywords(self, emotion_manager):
        """特定情绪 modifier 包含预期关键词"""
        assert "轻快" in emotion_manager.get_emotion_modifier("happy")
        assert "低沉" in emotion_manager.get_emotion_modifier("sad")
        assert "冷淡" in emotion_manager.get_emotion_modifier("angry")
        assert "热情" in emotion_manager.get_emotion_modifier("excited")
        assert "平和" in emotion_manager.get_emotion_modifier("neutral")

    def test_emotion_context_non_empty(self, emotion_manager):
        """get_emotion_context 返回非空且包含情绪标签"""
        context = emotion_manager.get_emotion_context("happy")
        assert "开心" in context
        assert "轻快" in context

    def test_get_all_emotions_structure(self, emotion_manager_with_data):
        """get_all_emotions 返回正确结构"""
        result = emotion_manager_with_data.get_all_emotions()
        assert "程码" in result
        assert result["程码"]["emotion"] == "happy"
        assert result["程码"]["emotion_label"] == "开心"
        assert "modifier" in result["程码"]
        assert "林案" in result
        assert result["林案"]["emotion"] == "sad"
        assert "苏绘" in result
        assert result["苏绘"]["emotion"] == "excited"

    def test_multiple_players(self, emotion_manager):
        """不同 player_id 的情绪独立"""
        emotion_manager.set_emotion("程码", "happy", "player1")
        emotion_manager.set_emotion("程码", "angry", "player2")
        assert emotion_manager.get_emotion("程码", "player1") == "happy"
        assert emotion_manager.get_emotion("程码", "player2") == "angry"

    def test_get_emotion_label_invalid_defaults_neutral(self, emotion_manager):
        """非法 emotion key 的标签回退到 平静"""
        assert emotion_manager.get_emotion_label("not_exist") == "平静"
