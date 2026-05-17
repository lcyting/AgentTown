"""批量NPC对话生成器"""

import json
from datetime import datetime
from typing import Dict, Optional

from hello_agents import HelloAgentsLLM
from agents import NPC_ROLES, npc_names_for_scene
from npc_config_loader import get_ambient_dialogues

class NPCBatchGenerator:
    """批量生成NPC对话的生成器
    
    核心思路: 一次LLM调用生成所有NPC的对话,降低API成本和延迟
    """
    
    def __init__(self):
        """初始化批量生成器"""
        print("🎨 正在初始化批量对话生成器...")
        
        try:
            self.llm = HelloAgentsLLM()
            self.enabled = True
            print("✅ 批量生成器初始化成功")
        except Exception as e:
            print(f"❌ 批量生成器初始化失败: {e}")
            print("⚠️  将使用预设对话模式")
            self.llm = None
            self.enabled = False
        
        self.npc_configs = NPC_ROLES
        self.preset_dialogues = get_ambient_dialogues()
        self._validate_ambient_dialogues()

    def _validate_ambient_dialogues(self) -> None:
        all_names = set(NPC_ROLES.keys())
        for period, dialogues in self.preset_dialogues.items():
            missing = all_names - set(dialogues.keys())
            if missing:
                print(
                    f"⚠️  ambient_dialogues.{period} 缺少 NPC: "
                    + ", ".join(sorted(missing))
                )
    
    def generate_batch_dialogues(
        self, context: Optional[str] = None, scene_id: Optional[str] = None
    ) -> Dict[str, str]:
        """批量生成 NPC 对话
        
        Args:
            context: 场景上下文(如"上午工作时间"、"午餐时间"等)
            scene_id: 若指定则仅生成该场景 NPC 的台词
        
        Returns:
            Dict[str, str]: NPC名称到对话内容的映射
        """
        if not self.enabled or self.llm is None:
            return self._get_preset_dialogues(scene_id=scene_id)
        
        try:
            prompt = self._build_batch_prompt(context, scene_id=scene_id)
            response = self.llm.invoke([
                {"role": "system", "content": "你是一个游戏NPC对话生成器,擅长创作自然真实的小镇场景对话。"},
                {"role": "user", "content": prompt}
            ])

            dialogues = self._parse_response(response, scene_id=scene_id)

            if dialogues:
                print(f"✅ 批量生成成功: {len(dialogues)}个NPC对话")
                return dialogues
            else:
                print("⚠️  解析失败,使用预设对话")
                return self._get_preset_dialogues(scene_id=scene_id)

        except Exception as e:
            print(f"❌ 批量生成失败: {e}")
            return self._get_preset_dialogues(scene_id=scene_id)
    
    def _npc_subset(self, scene_id: Optional[str] = None) -> Dict[str, dict]:
        names = npc_names_for_scene(scene_id)
        return {name: self.npc_configs[name] for name in names}

    def _build_batch_prompt(
        self, context: Optional[str] = None, scene_id: Optional[str] = None
    ) -> str:
        """构建批量生成提示词"""
        if context is None:
            context = self._get_current_context()

        subset = self._npc_subset(scene_id)
        npc_descriptions = []
        for name, cfg in subset.items():
            world = cfg.get("world_name", "赛博小镇")
            desc = (
                f"- {name}({cfg['title']}, {world}): "
                f"在{cfg['location']}{cfg['activity']},性格{cfg['personality']}"
            )
            npc_descriptions.append(desc)
        
        npc_desc_text = "\n".join(npc_descriptions)
        names = list(subset.keys())
        example_line = ", ".join(f'"{n}": "..."' for n in names)
        scene_hint = f"（仅包含场景 {scene_id} 的角色）" if scene_id else "（全部场景角色）"
        
        prompt = f"""请为赛博小镇的{len(names)}个NPC生成当前的对话或行为描述{scene_hint}。

【场景】{context}

【NPC信息】
{npc_desc_text}

【生成要求】
1. 每个NPC生成1句话(20-40字)
2. 内容要符合角色设定、当前活动、所在场所和场景氛围
3. 可以是自言自语、工作状态描述、或简单的思考
4. 要自然真实
5. 可以体现一些个性化特点和情绪
6. **必须严格按照JSON格式返回**

【输出格式】(严格遵守)
{{{example_line}}}

请生成(只返回JSON,不要其他内容):
"""
        return prompt
    
    def _parse_response(
        self, response: str, scene_id: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """解析LLM响应"""
        expected = set(npc_names_for_scene(scene_id))
        try:
            dialogues = json.loads(response)
            if isinstance(dialogues, dict) and expected.issubset(set(dialogues.keys())):
                return {k: dialogues[k] for k in expected}
            print(f"⚠️  JSON格式不正确: {dialogues}")
            return None
                
        except json.JSONDecodeError:
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = response[start:end]
                    dialogues = json.loads(json_str)
                    
                    if isinstance(dialogues, dict) and expected.issubset(set(dialogues.keys())):
                        return {k: dialogues[k] for k in expected}
            except Exception:
                pass
            
            print(f"⚠️  无法解析响应: {response[:100]}...")
            return None
    
    def _get_current_context(self) -> str:
        """根据当前时间推断场景上下文"""
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            return "清晨时分,小镇陆续热闹起来,居民准备开始新的一天"
        elif 9 <= hour < 12:
            return "上午时分,办公室、咖啡厅与图书馆各自忙碌而有序"
        elif 12 <= hour < 14:
            return "午餐时间,大家在休息放松,聊聊天或者看看手机"
        elif 14 <= hour < 17:
            return "下午时分,继续推进各自的工作与爱好"
        elif 17 <= hour < 19:
            return "傍晚时分,准备收尾今天的工作,整理明天的计划"
        else:
            return "夜晚时分,小镇安静下来,偶尔还有人在加班或夜读"
    
    def _get_preset_dialogues(self, scene_id: Optional[str] = None) -> Dict[str, str]:
        """获取预设对话(根据时间)，可按场景过滤"""
        hour = datetime.now().hour
        
        if 6 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 14:
            period = "noon"
        elif 14 <= hour < 18:
            period = "afternoon"
        else:
            period = "evening"
        
        period_dialogues = self.preset_dialogues.get(period) or self.preset_dialogues.get(
            "morning", {}
        )
        names = npc_names_for_scene(scene_id)
        result = {}
        for name in names:
            if name in period_dialogues:
                result[name] = period_dialogues[name]
            else:
                print(f"⚠️  {name} 在 ambient_dialogues.{period} 中无预设台词，已跳过")
        return result

# 全局单例
_batch_generator = None

def get_batch_generator() -> NPCBatchGenerator:
    """获取批量生成器单例"""
    global _batch_generator
    if _batch_generator is None:
        _batch_generator = NPCBatchGenerator()
    return _batch_generator
