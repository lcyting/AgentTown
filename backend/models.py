"""数据模型定义"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    """单个NPC对话请求"""
    npc_name: str = Field(..., description="NPC名称")
    message: str = Field(..., description="玩家消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "npc_name": "程码",
                "message": "你好,你在做什么?"
            }
        }

class ChatResponse(BaseModel):
    """单个NPC对话响应"""
    npc_name: str = Field(..., description="NPC名称")
    npc_title: str = Field(..., description="NPC职位")
    message: str = Field(..., description="NPC回复")
    emotion: Optional[str] = Field(default="neutral", description="情绪key (happy/sad/angry/excited/neutral)")
    emotion_label: Optional[str] = Field(default="平静", description="情绪中文标签")
    affinity: Optional[float] = Field(default=50.0, description="好感度数值 (0-100)")
    affinity_level: Optional[str] = Field(default="友好", description="好感度等级")
    affinity_change: Optional[float] = Field(default=0.0, description="本轮好感度变化")
    success: bool = Field(default=True, description="是否成功")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="时间戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "npc_name": "程码",
                "npc_title": "Python工程师",
                "message": "你好!我正在写代码,调试一个多智能体系统的bug。",
                "emotion": "happy",
                "emotion_label": "开心",
                "success": True
            }
        }

class NPCInfo(BaseModel):
    """NPC信息"""
    name: str = Field(..., description="NPC名称")
    title: str = Field(..., description="NPC职位")
    location: str = Field(..., description="NPC位置")
    activity: str = Field(..., description="当前活动")
    scene_id: str = Field(default="office", description="所属场景ID")
    interaction_hint: Optional[str] = Field(default=None, description="交互提示文案")
    available: bool = Field(default=True, description="是否可对话")

class NPCStatusResponse(BaseModel):
    """NPC状态响应"""
    dialogues: Dict[str, str] = Field(..., description="NPC当前对话内容")
    last_update: Optional[datetime] = Field(None, description="上次更新时间")
    next_update_in: int = Field(..., description="下次更新倒计时(秒)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dialogues": {
                    "程码": "终于把这个bug修复了,测试通过!",
                    "林案": "下周的产品评审会需要准备一下资料。",
                    "苏绘": "这个界面的配色方案还需要优化一下。"
                },
                "last_update": "2024-01-15T10:30:00",
                "next_update_in": 25
            }
        }

class NPCListResponse(BaseModel):
    """NPC列表响应"""
    npcs: List[NPCInfo] = Field(..., description="NPC列表")
    total: int = Field(..., description="NPC总数")

