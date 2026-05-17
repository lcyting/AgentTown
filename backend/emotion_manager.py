"""NPC情绪管理系统"""

from typing import Dict, Optional


# 情绪枚举与中文标签
EMOTIONS = {
    "happy": "开心",
    "sad": "难过",
    "angry": "生气",
    "excited": "兴奋",
    "neutral": "平静",
}

# 情绪 → 风格修饰词（注入对话 prompt）
EMOTION_MODIFIERS = {
    "happy": "语气轻快，愿意多分享专业/私人信息，主动延伸话题",
    "excited": "热情高涨，表达积极，细节丰富",
    "neutral": "平和专业，按角色人设正常交流",
    "sad": "语气低沉，回答偏短，不太主动展开",
    "angry": "语气生硬，冷淡疏离，拒绝深入交流，回答简短",
}


class EmotionManager:
    """NPC情绪管理器

    职责:
    - 管理 NPC 对玩家的情绪状态（happy / sad / angry / excited / neutral）
    - 提供情绪修饰词用于注入对话 prompt
    - 不负责单独调用 LLM（与好感度分析合并）
    - 内存态存储，重启归零
    """

    def __init__(self):
        # 存储格式: {npc_name: {player_id: emotion_key}}
        self.emotion_states: Dict[str, Dict[str, str]] = {}
        print("😊 情绪管理系统已初始化")

    def get_emotion(self, npc_name: str, player_id: str = "player") -> str:
        """获取 NPC 当前情绪

        Args:
            npc_name: NPC 名称
            player_id: 玩家 ID

        Returns:
            情绪 key（happy/sad/angry/excited/neutral），默认 neutral
        """
        if npc_name not in self.emotion_states:
            self.emotion_states[npc_name] = {}

        if player_id not in self.emotion_states[npc_name]:
            self.emotion_states[npc_name][player_id] = "neutral"

        return self.emotion_states[npc_name][player_id]

    def get_emotion_label(self, emotion: str) -> str:
        """获取情绪的中文标签

        Args:
            emotion: 情绪 key

        Returns:
            中文标签（如 "开心"）
        """
        return EMOTIONS.get(emotion, EMOTIONS["neutral"])

    def set_emotion(
        self, npc_name: str, emotion: str, player_id: str = "player"
    ) -> str:
        """设置 NPC 情绪

        Args:
            npc_name: NPC 名称
            emotion: 情绪 key（非法值归一化为 neutral）
            player_id: 玩家 ID

        Returns:
            归一化后的情绪 key
        """
        if npc_name not in self.emotion_states:
            self.emotion_states[npc_name] = {}

        # 非法情绪归一化为 neutral
        normalized = emotion if emotion in EMOTIONS else "neutral"
        self.emotion_states[npc_name][player_id] = normalized
        return normalized

    def get_emotion_modifier(self, emotion: str) -> str:
        """获取情绪对应的风格修饰词

        Args:
            emotion: 情绪 key

        Returns:
            风格修饰文案
        """
        return EMOTION_MODIFIERS.get(emotion, EMOTION_MODIFIERS["neutral"])

    def get_emotion_context(self, emotion: str) -> str:
        """构建注入 prompt 的情绪上下文文本

        Args:
            emotion: 情绪 key

        Returns:
            格式化的情绪上下文（可直接拼入 enhanced_message）
        """
        label = self.get_emotion_label(emotion)
        modifier = self.get_emotion_modifier(emotion)
        return f"""【当前情绪】
你现在的情绪: {label}
【情绪表现】{modifier}"""

    def get_all_emotions(self, player_id: str = "player") -> Dict[str, Dict]:
        """获取所有 NPC 的情绪信息

        Args:
            player_id: 玩家 ID

        Returns:
            {npc_name: {emotion, emotion_label, modifier}}
        """
        result = {}
        for npc_name in self.emotion_states:
            emotion = self.get_emotion(npc_name, player_id)
            result[npc_name] = {
                "emotion": emotion,
                "emotion_label": self.get_emotion_label(emotion),
                "modifier": self.get_emotion_modifier(emotion),
            }
        return result
