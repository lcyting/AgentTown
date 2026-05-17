"""NPC Agent系统 - 支持记忆功能"""

import os

from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.memory import MemoryManager, MemoryConfig, MemoryItem
from typing import Dict, List, Optional
from datetime import datetime
from relationship_manager import RelationshipManager
from emotion_manager import EmotionManager
from logger import (
    log_dialogue_start, log_affinity, log_memory_retrieval,
    log_generating_response, log_npc_response, log_analyzing_affinity,
    log_affinity_change, log_memory_saved, log_dialogue_end, log_info,
    log_emotion, log_emotion_change
)

# NPC角色配置
NPC_ROLES = {
    "程码": {
        "scene_id": "office",
        "world_name": "赛博小镇办公室",
        "title": "Python工程师",
        "location": "工位区",
        "activity": "写代码",
        "interaction_hint": "按 E 交互",
        "personality": "技术宅,喜欢讨论算法和框架",
        "expertise": "多智能体系统、HelloAgents框架、Python开发、代码优化",
        "style": "简洁专业,喜欢用技术术语,偶尔吐槽bug",
        "hobbies": "看技术博客、刷LeetCode、研究新框架",
    },
    "林案": {
        "scene_id": "office",
        "world_name": "赛博小镇办公室",
        "title": "产品经理",
        "location": "会议室",
        "activity": "整理需求",
        "interaction_hint": "按 E 交互",
        "personality": "外向健谈,善于沟通协调",
        "expertise": "需求分析、产品规划、用户体验、项目管理",
        "style": "友好热情,善于引导对话,喜欢用比喻",
        "hobbies": "看产品分析、研究竞品、思考用户需求",
    },
    "苏绘": {
        "scene_id": "office",
        "world_name": "赛博小镇办公室",
        "title": "UI设计师",
        "location": "休息区",
        "activity": "喝咖啡",
        "interaction_hint": "按 E 交互",
        "personality": "细腻敏感,注重美感",
        "expertise": "界面设计、交互设计、视觉呈现、用户体验",
        "style": "优雅简洁,喜欢用艺术化的表达,追求完美",
        "hobbies": "看设计作品、逛Dribbble、品咖啡",
    },
    "小林": {
        "scene_id": "cafe",
        "world_name": "赛博小镇咖啡厅",
        "title": "咖啡师",
        "location": "吧台",
        "activity": "手冲咖啡",
        "interaction_hint": "按 E 点一杯咖啡",
        "personality": "温和细致,对咖啡有执念",
        "expertise": "手冲咖啡、拉花、咖啡豆品鉴、轻食搭配",
        "style": "轻声细语,喜欢用香气和口感形容,偶尔推荐今日特调",
        "hobbies": "研究新豆种、逛咖啡展、记录萃取参数",
    },
    "陈读": {
        "scene_id": "library",
        "world_name": "赛博小镇图书馆",
        "title": "图书管理员",
        "location": "服务台",
        "activity": "整理书架",
        "interaction_hint": "按 E 借阅咨询",
        "personality": "安静博学,乐于荐书",
        "expertise": "图书分类、阅读推荐、资料检索、小镇文史",
        "style": "沉稳克制,爱引用书中句子,说话有条理",
        "hobbies": "阅读科幻与心理学、编写导读卡片、维护小镇档案",
    },
}


def npc_names_for_scene(scene_id: Optional[str] = None) -> List[str]:
    """按场景筛选 NPC 名称；scene_id 为空时返回全部。"""
    if not scene_id:
        return list(NPC_ROLES.keys())
    return [
        name
        for name, role in NPC_ROLES.items()
        if role.get("scene_id", "office") == scene_id
    ]


def create_system_prompt(name: str, role: Dict[str, str]) -> str:
    """创建NPC的系统提示词"""
    world_name = role.get("world_name", "赛博小镇")
    return f"""你是{world_name}的{role['title']}{name}。

【角色设定】
- 职位: {role['title']}
- 性格: {role['personality']}
- 专长: {role['expertise']}
- 说话风格: {role['style']}
- 爱好: {role['hobbies']}
- 当前位置: {role['location']}
- 当前活动: {role['activity']}

【行为准则】
1. 保持角色一致性,用第一人称"我"回答
2. 回复简洁自然,控制在30-50字以内
3. 可以适当提及你的工作内容和兴趣爱好
4. 对玩家友好,但保持专业和真实感
5. 如果问题超出专长,可以推荐其他同事
6. 偶尔展现一些个性化的小习惯或口头禅

【对话示例】
玩家: "你好,你是做什么的?"
{name}: "你好!我是{role['title']},主要负责{role['expertise'].split('、')[0]}。最近在忙{role['activity']},挺有意思的。"

玩家: "最近在做什么项目?"
{name}: "最近在做一个多智能体系统的项目,用HelloAgents框架。你对这个感兴趣吗?"

【重要】
- 不要说"我是AI"或"我是语言模型"
- 要像真实的小镇居民一样自然对话
- 可以表达情绪(开心、疲惫、兴奋等)
- 回复要有人情味,不要太机械
"""

class NPCAgentManager:
    """NPC Agent管理器 - 支持记忆功能"""

    def __init__(self):
        """初始化所有NPC Agent"""
        print("🤖 正在初始化NPC Agent系统...")

        try:
            self.llm = HelloAgentsLLM()
            print("✅ LLM初始化成功")
        except Exception as e:
            print(f"❌ LLM初始化失败: {e}")
            print("⚠️  将使用模拟模式运行")
            self.llm = None

        self.agents: Dict[str, SimpleAgent] = {}
        self.memories: Dict[str, MemoryManager] = {}  # ⭐ NPC记忆管理器
        self.relationship_manager: Optional[RelationshipManager] = None  # ⭐ 好感度管理器
        self.emotion_manager: Optional[EmotionManager] = None  # ⭐ 情绪管理器

        # 初始化好感度和情绪管理器
        if self.llm:
            self.relationship_manager = RelationshipManager(self.llm)
            self.emotion_manager = EmotionManager()

        self._create_agents()
    
    def _create_agents(self):
        """创建所有NPC Agent和记忆系统"""
        for name, role in NPC_ROLES.items():
            self.agents[name] = None
            self.memories[name] = None

            try:
                if self.llm:
                    system_prompt = create_system_prompt(name, role)
                    self.agents[name] = SimpleAgent(
                        name=f"{name}-{role['title']}",
                        llm=self.llm,
                        system_prompt=system_prompt
                    )
            except Exception as e:
                print(f"❌ {name} Agent创建失败: {e}")
                continue

            try:
                self.memories[name] = self._create_memory_manager(name)
            except Exception as e:
                print(f"⚠️  {name} 记忆系统初始化失败: {e}")
                print(f"   {name} 仍可对话，但短期/长期记忆功能受限")

            if self.agents[name] is not None:
                memory_hint = "记忆系统已启用" if self.memories[name] else "仅对话（无记忆）"
                print(f"✅ {name}({role['title']}) Agent创建成功 ({memory_hint})")

    def _memory_config(self, memory_dir: str) -> MemoryConfig:
        """记忆系统通用配置"""
        return MemoryConfig(
            storage_path=memory_dir,
            working_memory_capacity=10,
            working_memory_tokens=2000,
            episodic_memory_capacity=100,
            enable_forgetting=True,
            forgetting_threshold=0.3,
        )

    def _create_memory_manager(self, npc_name: str) -> MemoryManager:
        """为NPC创建记忆管理器（Qdrant 不可用时回退为仅工作记忆）"""
        memory_dir = os.path.join(os.path.dirname(__file__), 'memory_data', npc_name)
        os.makedirs(memory_dir, exist_ok=True)
        memory_config = self._memory_config(memory_dir)

        try:
            memory_manager = MemoryManager(
                config=memory_config,
                user_id=npc_name,
                enable_working=True,
                enable_episodic=True,
                enable_semantic=False,
                enable_perceptual=False,
            )
            print(f"  💾 {npc_name} 记忆: 工作记忆 + 情景记忆 (Qdrant)")
            return memory_manager
        except Exception as episodic_error:
            print(f"  ⚠️  {npc_name} 情景记忆不可用 ({episodic_error})，回退为仅工作记忆")
            memory_manager = MemoryManager(
                config=memory_config,
                user_id=npc_name,
                enable_working=True,
                enable_episodic=False,
                enable_semantic=False,
                enable_perceptual=False,
            )
            print(f"  💾 {npc_name} 记忆: 仅工作记忆 (SQLite, {memory_dir})")
            return memory_manager
    
    def chat(self, npc_name: str, message: str, player_id: str = "player") -> Dict:
        """与指定NPC对话 (支持记忆功能、好感度系统和情绪系统)
        
        Returns:
            {"message": str, "emotion": str, "emotion_label": str}
        """
        if npc_name not in self.agents:
            return {
                "message": f"错误: NPC '{npc_name}' 不存在",
                "emotion": "neutral",
                "emotion_label": "平静",
                "affinity": 50.0,
                "affinity_level": "友好",
                "affinity_change": 0.0,
            }

        agent = self.agents[npc_name]
        memory_manager = self.memories.get(npc_name)

        if agent is None:
            # 模拟模式回复
            role = NPC_ROLES[npc_name]
            sim_affinity = 50.0
            sim_level = "友好"
            if self.relationship_manager:
                sim_affinity = self.relationship_manager.get_affinity(npc_name, player_id)
                sim_level = self.relationship_manager.get_affinity_level(sim_affinity)
            return {
                "message": f"你好!我是{npc_name},一名{role['title']}。(当前为模拟模式,请配置API_KEY以启用AI对话)",
                "emotion": "neutral",
                "emotion_label": "平静",
                "affinity": sim_affinity,
                "affinity_level": sim_level,
                "affinity_change": 0.0,
            }

        try:
            # 记录对话开始 ⭐ 使用日志系统
            log_dialogue_start(npc_name, message)

            # ⭐ 1. 获取当前好感度
            affinity_context = ""
            if self.relationship_manager:
                affinity = self.relationship_manager.get_affinity(npc_name, player_id)
                affinity_level = self.relationship_manager.get_affinity_level(affinity)
                affinity_modifier = self.relationship_manager.get_affinity_modifier(affinity)

                affinity_context = f"""【当前关系】
你与玩家的关系: {affinity_level} (好感度: {affinity:.0f}/100)
【对话风格】{affinity_modifier}

"""
                log_affinity(npc_name, affinity, affinity_level)

            # ⭐ 1.5 获取当前情绪并构建情绪上下文
            emotion_context = ""
            current_emotion = "neutral"
            if self.emotion_manager:
                current_emotion = self.emotion_manager.get_emotion(npc_name, player_id)
                emotion_context = self.emotion_manager.get_emotion_context(current_emotion) + "\n\n"
                emotion_label = self.emotion_manager.get_emotion_label(current_emotion)
                log_emotion(npc_name, current_emotion, emotion_label)

            # ⭐ 2. 检索相关记忆
            relevant_memories = []
            if memory_manager:
                relevant_memories = memory_manager.retrieve_memories(
                    query=message,
                    memory_types=["working", "episodic"],
                    limit=5,
                    min_importance=0.3  # 只检索重要性>=0.3的记忆
                )
                log_memory_retrieval(npc_name, len(relevant_memories), relevant_memories)

            # ⭐ 3. 构建增强的提示词 (包含好感度、情绪和记忆上下文)
            memory_context = self._build_memory_context(relevant_memories)

            enhanced_message = affinity_context + emotion_context
            if memory_context:
                enhanced_message += f"{memory_context}\n\n"
            enhanced_message += f"【当前对话】\n玩家: {message}"

            # ⭐ 4. 调用Agent生成回复
            log_generating_response()
            response = agent.run(enhanced_message)
            log_npc_response(npc_name, response)

            # ⭐ 5. 分析并更新好感度和情绪
            log_analyzing_affinity()
            if self.relationship_manager:
                affinity_result = self.relationship_manager.analyze_and_update_affinity(
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id,
                    current_emotion=current_emotion
                )

                # 记录好感度变化详情 ⭐ 使用日志系统
                log_affinity_change(affinity_result)

                # ⭐ 更新情绪
                if self.emotion_manager and "emotion" in affinity_result:
                    new_emotion = self.emotion_manager.set_emotion(
                        npc_name, affinity_result["emotion"], player_id
                    )
                    if affinity_result.get("emotion_changed"):
                        old_label = self.emotion_manager.get_emotion_label(current_emotion)
                        new_label = self.emotion_manager.get_emotion_label(new_emotion)
                        log_emotion_change(npc_name, current_emotion, new_emotion, old_label, new_label)
            else:
                affinity_result = {"changed": False, "affinity": 50.0, "emotion": "neutral", "emotion_label": "平静"}

            # 提取最终情绪信息
            final_emotion = affinity_result.get("emotion", current_emotion)
            final_emotion_label = affinity_result.get("emotion_label", "平静")

            # 提取好感度信息（对话后最新值）
            if self.relationship_manager:
                final_affinity = self.relationship_manager.get_affinity(npc_name, player_id)
                final_affinity_level = self.relationship_manager.get_affinity_level(final_affinity)
            else:
                final_affinity = float(affinity_result.get("affinity", 50.0))
                final_affinity_level = "友好"
            affinity_change = 0.0
            if affinity_result.get("changed"):
                affinity_change = float(affinity_result.get("change_amount", 0))

            # ⭐ 6. 保存对话到记忆 (包含好感度和情绪信息)
            if memory_manager:
                self._save_conversation_to_memory(
                    memory_manager=memory_manager,
                    npc_name=npc_name,
                    player_message=message,
                    npc_response=response,
                    player_id=player_id,
                    affinity_info=affinity_result
                )
                log_memory_saved(npc_name)

            # 记录对话结束 ⭐ 使用日志系统
            log_dialogue_end()

            return {
                "message": response,
                "emotion": final_emotion,
                "emotion_label": final_emotion_label,
                "affinity": final_affinity,
                "affinity_level": final_affinity_level,
                "affinity_change": affinity_change,
            }

        except Exception as e:
            print(f"❌ {npc_name}对话失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "message": f"抱歉,我现在有点忙,等会儿再聊吧。(错误: {str(e)})",
                "emotion": "neutral",
                "emotion_label": "平静",
                "affinity": 50.0,
                "affinity_level": "友好",
                "affinity_change": 0.0,
            }
    
    def _build_memory_context(self, memories: List[MemoryItem]) -> str:
        """构建记忆上下文"""
        if not memories:
            return ""

        context_parts = ["【之前的对话记忆】"]
        for memory in memories:
            # 格式化时间
            time_str = memory.timestamp.strftime("%H:%M")
            # 添加记忆内容
            context_parts.append(f"[{time_str}] {memory.content}")

        context_parts.append("")  # 空行分隔
        return "\n".join(context_parts)

    def _save_conversation_to_memory(
        self,
        memory_manager: MemoryManager,
        npc_name: str,
        player_message: str,
        npc_response: str,
        player_id: str,
        affinity_info: Optional[Dict] = None
    ):
        """保存对话到记忆系统 (包含好感度和情绪信息)"""
        current_time = datetime.now()

        # 获取好感度信息
        affinity = affinity_info.get("new_affinity", affinity_info.get("affinity", 50.0)) if affinity_info else 50.0
        affinity_change = affinity_info.get("change_amount", 0) if affinity_info else 0
        sentiment = affinity_info.get("sentiment", "neutral") if affinity_info else "neutral"
        emotion = affinity_info.get("emotion", "neutral") if affinity_info else "neutral"
        emotion_label = affinity_info.get("emotion_label", "平静") if affinity_info else "平静"

        # 保存玩家消息
        memory_manager.add_memory(
            content=f"玩家说: {player_message}",
            memory_type="working",  # 先存入工作记忆
            importance=0.5,  # 中等重要性
            metadata={
                "speaker": "player",
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  # ⭐ 记录当时的好感度
                "affinity_change": affinity_change,  # ⭐ 记录好感度变化
                "sentiment": sentiment,  # ⭐ 记录情感倾向
                "emotion": emotion,  # ⭐ 记录情绪
                "emotion_label": emotion_label,  # ⭐ 记录情绪标签
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        # 保存NPC回复
        memory_manager.add_memory(
            content=f"我说: {npc_response}",
            memory_type="working",  # 先存入工作记忆
            importance=0.6,  # 稍高重要性
            metadata={
                "speaker": npc_name,
                "player_id": player_id,
                "session_id": player_id,
                "timestamp": current_time.isoformat(),
                "affinity": affinity,  # ⭐ 记录当时的好感度
                "sentiment": sentiment,  # ⭐ 记录情感倾向
                "emotion": emotion,  # ⭐ 记录情绪
                "emotion_label": emotion_label,  # ⭐ 记录情绪标签
                "context": {
                    "interaction_type": "dialogue",
                    "npc_name": npc_name
                }
            }
        )

        print(f"  💾 对话已保存到{npc_name}的记忆中")

    def get_npc_info(self, npc_name: str) -> Dict[str, str]:
        """获取NPC信息"""
        if npc_name not in NPC_ROLES:
            return {}

        role = NPC_ROLES[npc_name]
        return {
            "name": npc_name,
            "title": role["title"],
            "location": role["location"],
            "activity": role["activity"],
            "scene_id": role.get("scene_id", "office"),
            "interaction_hint": role.get("interaction_hint"),
            "world_name": role.get("world_name"),
            "available": self.agents.get(npc_name) is not None
        }
    
    def get_all_npcs(self, scene_id: Optional[str] = None) -> list:
        """获取 NPC 信息列表，可按 scene_id 过滤"""
        names = npc_names_for_scene(scene_id)
        return [self.get_npc_info(name) for name in names]

    def get_dialogue_history(
        self, npc_name: str, player_id: str = "player", limit: int = 30
    ) -> List[Dict]:
        """获取与玩家的对话历史（按时间正序，用于 UI 展示）"""
        if npc_name not in self.memories:
            return []

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            return []

        dialogue_items = []
        for memory_type in ("working", "episodic"):
            memory_instance = memory_manager.memory_types.get(memory_type)
            if not memory_instance or not hasattr(memory_instance, "get_all"):
                continue
            for memory in memory_instance.get_all():
                meta = memory.metadata or {}
                ctx = meta.get("context") or {}
                if ctx.get("interaction_type") != "dialogue":
                    continue
                if meta.get("player_id") not in (None, player_id):
                    continue
                dialogue_items.append(memory)

        dialogue_items.sort(key=lambda m: m.timestamp)

        history = []
        for memory in dialogue_items[-limit:]:
            meta = memory.metadata or {}
            speaker = meta.get("speaker", "")
            content = memory.content
            role = "player"
            text = content

            if content.startswith("玩家说: "):
                text = content[len("玩家说: "):]
                role = "player"
            elif content.startswith("我说: "):
                text = content[len("我说: "):]
                role = "npc"
            elif speaker == "player":
                role = "player"
                if content.startswith("玩家:"):
                    text = content.split(":", 1)[-1].strip()
            else:
                role = "npc"
                if speaker == npc_name and content.startswith(f"{npc_name}:"):
                    text = content.split(":", 1)[-1].strip()

            history.append(
                {
                    "role": role,
                    "content": text,
                    "timestamp": memory.timestamp.isoformat(),
                    "emotion": meta.get("emotion"),
                    "emotion_label": meta.get("emotion_label"),
                }
            )

        return history

    def get_npc_memories(self, npc_name: str, player_id: str = "player", limit: int = 10) -> List[Dict]:
        """获取NPC的记忆列表 (用于调试和展示)"""
        if npc_name not in self.memories:
            return []

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            return []

        try:
            # 检索所有记忆
            memories = memory_manager.retrieve_memories(
                query="",  # 空查询返回所有记忆
                memory_types=["working", "episodic"],
                limit=limit
            )

            # 转换为字典格式
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "id": memory.id,
                    "content": memory.content,
                    "type": memory.memory_type,
                    "importance": memory.importance,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata
                })

            return memory_list

        except Exception as e:
            print(f"❌ 获取{npc_name}记忆失败: {e}")
            return []

    def clear_npc_memory(self, npc_name: str, memory_type: Optional[str] = None):
        """清空NPC的记忆 (用于测试)"""
        if npc_name not in self.memories:
            print(f"❌ NPC '{npc_name}' 不存在")
            return

        memory_manager = self.memories[npc_name]
        if not memory_manager:
            print(f"❌ {npc_name}没有记忆系统")
            return

        try:
            if memory_type:
                # 清空指定类型的记忆
                memory_manager.clear_memory_type(memory_type)
                print(f"✅ 已清空{npc_name}的{memory_type}记忆")
            else:
                # 清空所有记忆
                for mem_type in ["working", "episodic"]:
                    try:
                        memory_manager.clear_memory_type(mem_type)
                    except:
                        pass
                print(f"✅ 已清空{npc_name}的所有记忆")

        except Exception as e:
            print(f"❌ 清空{npc_name}记忆失败: {e}")

    def get_npc_affinity(self, npc_name: str, player_id: str = "player") -> Dict:
        """获取NPC对玩家的好感度信息

        Args:
            npc_name: NPC名称
            player_id: 玩家ID

        Returns:
            好感度信息字典
        """
        if not self.relationship_manager:
            return {
                "affinity": 50.0,
                "level": "熟悉",
                "modifier": "礼貌友善,正常交流,保持专业"
            }

        affinity = self.relationship_manager.get_affinity(npc_name, player_id)
        level = self.relationship_manager.get_affinity_level(affinity)
        modifier = self.relationship_manager.get_affinity_modifier(affinity)

        return {
            "affinity": affinity,
            "level": level,
            "modifier": modifier
        }

    def get_all_affinities(self, player_id: str = "player") -> Dict[str, Dict]:
        """获取所有NPC的好感度信息

        Args:
            player_id: 玩家ID

        Returns:
            所有NPC的好感度信息
        """
        if not self.relationship_manager:
            return {}

        return self.relationship_manager.get_all_affinities(player_id)

    def set_npc_affinity(self, npc_name: str, affinity: float, player_id: str = "player"):
        """设置NPC对玩家的好感度 (用于测试)

        Args:
            npc_name: NPC名称
            affinity: 好感度值 (0-100)
            player_id: 玩家ID
        """
        if not self.relationship_manager:
            print("❌ 好感度系统未初始化")
            return

        self.relationship_manager.set_affinity(npc_name, affinity, player_id)
        level = self.relationship_manager.get_affinity_level(affinity)
        print(f"✅ 已设置{npc_name}对玩家的好感度: {affinity:.1f} ({level})")

    def get_npc_emotion(self, npc_name: str, player_id: str = "player") -> Dict:
        """获取NPC对玩家的情绪信息

        Args:
            npc_name: NPC名称
            player_id: 玩家ID

        Returns:
            情绪信息字典
        """
        if not self.emotion_manager:
            return {
                "emotion": "neutral",
                "emotion_label": "平静",
                "modifier": "平和专业，按角色人设正常交流"
            }

        emotion = self.emotion_manager.get_emotion(npc_name, player_id)
        label = self.emotion_manager.get_emotion_label(emotion)
        modifier = self.emotion_manager.get_emotion_modifier(emotion)

        return {
            "emotion": emotion,
            "emotion_label": label,
            "modifier": modifier
        }

    def get_all_emotions(self, player_id: str = "player") -> Dict[str, Dict]:
        """获取所有NPC的情绪信息

        Args:
            player_id: 玩家ID

        Returns:
            所有NPC的情绪信息
        """
        if not self.emotion_manager:
            return {}

        return self.emotion_manager.get_all_emotions(player_id)

    def set_npc_emotion(self, npc_name: str, emotion: str, player_id: str = "player"):
        """设置NPC情绪 (用于测试)

        Args:
            npc_name: NPC名称
            emotion: 情绪key (happy/sad/angry/excited/neutral)
            player_id: 玩家ID
        """
        if not self.emotion_manager:
            print("❌ 情绪系统未初始化")
            return

        normalized = self.emotion_manager.set_emotion(npc_name, emotion, player_id)
        label = self.emotion_manager.get_emotion_label(normalized)
        print(f"✅ 已设置{npc_name}的情绪: {label}")

# 全局单例
_npc_manager = None

def get_npc_manager() -> NPCAgentManager:
    """获取NPC管理器单例"""
    global _npc_manager
    if _npc_manager is None:
        _npc_manager = NPCAgentManager()
    return _npc_manager

