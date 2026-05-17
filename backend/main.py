"""赛博小镇 FastAPI 后端主程序"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

import sys

from config import settings
from models import (
    ChatRequest, ChatResponse, 
    NPCStatusResponse, NPCListResponse, NPCInfo
)
from agents import get_npc_manager
from state_manager import get_state_manager

def _check_memory_dependencies():
    """检查情景记忆（Qdrant）可选依赖"""
    try:
        import qdrant_client  # noqa: F401
    except ImportError:
        print("提示: 未检测到 qdrant-client，情景记忆将回退为仅工作记忆")
        print(f"  当前 Python: {sys.executable}")
        print("  安装: .\\venv\\Scripts\\python.exe -m pip install qdrant-client>=1.6.0")
        print("  推荐启动: .\\start.ps1")


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("\n" + "="*60)
    print("🎮 赛博小镇后端服务启动中...")
    print("="*60)
    
    # 验证配置
    settings.validate()
    _check_memory_dependencies()
    
    # 初始化NPC管理器
    npc_manager = get_npc_manager()
    
    # 初始化并启动状态管理器
    state_manager = get_state_manager(settings.NPC_UPDATE_INTERVAL)
    await state_manager.start()
    
    print("\n✅ 所有服务已启动!")
    print(f"📡 API地址: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时
    print("\n🛑 正在关闭服务...")
    await state_manager.stop()
    print("✅ 服务已关闭\n")

# 创建FastAPI应用
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="赛博小镇 - 基于HelloAgents的AI NPC对话系统",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取全局实例
npc_manager = None
state_manager = None

def get_managers():
    """获取管理器实例"""
    global npc_manager, state_manager
    if npc_manager is None:
        npc_manager = get_npc_manager()
    if state_manager is None:
        state_manager = get_state_manager()
    return npc_manager, state_manager

# ==================== API路由 ====================

@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "features": ["AI对话", "NPC记忆系统", "好感度系统", "情绪系统", "批量状态更新"],
        "endpoints": {
            "docs": "/docs",
            "chat": "/chat",
            "npcs": "/npcs",
            "npcs_status": "/npcs/status",
            "npc_memories": "/npcs/{npc_name}/memories",
            "npc_affinity": "/npcs/{npc_name}/affinity",
            "all_affinities": "/affinities",
            "npc_emotion": "/npcs/{npc_name}/emotion",
            "npc_dialogue_history": "/npcs/{npc_name}/dialogue-history",
            "all_emotions": "/emotions"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "now"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest):
    """与NPC对话接口
    
    玩家与指定NPC进行实时对话,使用独立的Agent处理
    """
    npc_mgr, _ = get_managers()
    
    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(request.npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{request.npc_name}' 不存在"
        )
    
    try:
        # 调用NPC Agent处理对话 (返回 dict with message, emotion, emotion_label)
        result = npc_mgr.chat(request.npc_name, request.message)
        
        return ChatResponse(
            npc_name=request.npc_name,
            npc_title=npc_info["title"],
            message=result["message"],
            emotion=result.get("emotion", "neutral"),
            emotion_label=result.get("emotion_label", "平静"),
            affinity=result.get("affinity", 50.0),
            affinity_level=result.get("affinity_level", "友好"),
            affinity_change=result.get("affinity_change", 0.0),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"对话处理失败: {str(e)}"
        )

@app.get("/npcs", response_model=NPCListResponse)
async def list_npcs(scene_id: str = None):
    """获取 NPC 列表，可选按 scene_id 过滤（office / cafe / library）"""
    npc_mgr, _ = get_managers()
    
    npcs_data = npc_mgr.get_all_npcs(scene_id=scene_id)
    npcs = [NPCInfo(**npc) for npc in npcs_data]
    
    return NPCListResponse(
        npcs=npcs,
        total=len(npcs)
    )

@app.get("/npcs/status", response_model=NPCStatusResponse)
async def get_npcs_status(scene_id: str = None):
    """获取 NPC 当前状态；可选 scene_id 仅返回该场景角色的头顶台词"""
    from agents import npc_names_for_scene

    _, state_mgr = get_managers()
    
    state = state_mgr.get_current_state()
    dialogues = state["dialogues"]
    if scene_id:
        allowed = set(npc_names_for_scene(scene_id))
        dialogues = {k: v for k, v in dialogues.items() if k in allowed}
    
    return NPCStatusResponse(
        dialogues=dialogues,
        last_update=state["last_update"],
        next_update_in=state["next_update_in"]
    )

@app.post("/npcs/status/refresh")
async def refresh_npcs_status():
    """强制刷新NPC状态
    
    立即触发一次批量对话生成
    """
    _, state_mgr = get_managers()
    
    await state_mgr.force_update()
    state = state_mgr.get_current_state()
    
    return {
        "message": "NPC状态已刷新",
        "dialogues": state["dialogues"]
    }

@app.get("/npcs/{npc_name}")
async def get_npc_info(npc_name: str):
    """获取指定NPC的详细信息"""
    npc_mgr, state_mgr = get_managers()

    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    # 添加当前对话
    current_dialogue = state_mgr.get_npc_dialogue(npc_name)
    npc_info["current_dialogue"] = current_dialogue

    return npc_info

@app.get("/npcs/{npc_name}/memories")
async def get_npc_memories(npc_name: str, limit: int = 10):
    """获取NPC的记忆列表

    Args:
        npc_name: NPC名称
        limit: 返回的记忆数量限制 (默认10条)

    Returns:
        NPC的记忆列表
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        memories = npc_mgr.get_npc_memories(npc_name, limit=limit)

        return {
            "npc_name": npc_name,
            "memories": memories,
            "total": len(memories)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取记忆失败: {str(e)}"
        )

@app.delete("/npcs/{npc_name}/memories")
async def clear_npc_memories(npc_name: str, memory_type: str = None):
    """清空NPC的记忆 (用于测试)

    Args:
        npc_name: NPC名称
        memory_type: 记忆类型 (working/episodic), 不指定则清空所有

    Returns:
        操作结果
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        npc_mgr.clear_npc_memory(npc_name, memory_type)

        return {
            "message": f"已清空{npc_name}的记忆",
            "npc_name": npc_name,
            "memory_type": memory_type or "all"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空记忆失败: {str(e)}"
        )

@app.get("/npcs/{npc_name}/affinity")
async def get_npc_affinity(npc_name: str, player_id: str = "player"):
    """获取NPC对玩家的好感度

    Args:
        npc_name: NPC名称
        player_id: 玩家ID (默认为"player")

    Returns:
        好感度信息
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)

        return {
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取好感度失败: {str(e)}"
        )

@app.get("/affinities")
async def get_all_affinities(player_id: str = "player"):
    """获取所有NPC对玩家的好感度

    Args:
        player_id: 玩家ID (默认为"player")

    Returns:
        所有NPC的好感度信息
    """
    npc_mgr, _ = get_managers()

    try:
        affinities = npc_mgr.get_all_affinities(player_id)

        return {
            "player_id": player_id,
            "affinities": affinities
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取好感度失败: {str(e)}"
        )

@app.put("/npcs/{npc_name}/affinity")
async def set_npc_affinity(npc_name: str, affinity: float, player_id: str = "player"):
    """设置NPC对玩家的好感度 (用于测试)

    Args:
        npc_name: NPC名称
        affinity: 好感度值 (0-100)
        player_id: 玩家ID (默认为"player")

    Returns:
        操作结果
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    # 验证好感度范围
    if affinity < 0 or affinity > 100:
        raise HTTPException(
            status_code=400,
            detail="好感度必须在0-100之间"
        )

    try:
        npc_mgr.set_npc_affinity(npc_name, affinity, player_id)
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)

        return {
            "message": f"已设置{npc_name}对玩家的好感度",
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"设置好感度失败: {str(e)}"
        )

@app.get("/npcs/{npc_name}/dialogue-history")
async def get_npc_dialogue_history(npc_name: str, player_id: str = "player", limit: int = 30):
    """获取与 NPC 的对话历史（按时间正序）"""
    npc_mgr, _ = get_managers()

    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        history = npc_mgr.get_dialogue_history(npc_name, player_id=player_id, limit=limit)
        return {
            "npc_name": npc_name,
            "player_id": player_id,
            "history": history,
            "total": len(history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取对话历史失败: {str(e)}"
        )

# ==================== 情绪 API ====================

@app.get("/npcs/{npc_name}/emotion")
async def get_npc_emotion(npc_name: str, player_id: str = "player"):
    """获取NPC对玩家的情绪

    Args:
        npc_name: NPC名称
        player_id: 玩家ID (默认为"player")

    Returns:
        情绪信息
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        emotion_info = npc_mgr.get_npc_emotion(npc_name, player_id)

        return {
            "npc_name": npc_name,
            "player_id": player_id,
            **emotion_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪失败: {str(e)}"
        )

@app.get("/emotions")
async def get_all_emotions(player_id: str = "player"):
    """获取所有NPC的情绪

    Args:
        player_id: 玩家ID (默认为"player")

    Returns:
        所有NPC的情绪信息
    """
    npc_mgr, _ = get_managers()

    try:
        emotions = npc_mgr.get_all_emotions(player_id)

        return {
            "player_id": player_id,
            "emotions": emotions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取情绪失败: {str(e)}"
        )

@app.put("/npcs/{npc_name}/emotion")
async def set_npc_emotion(npc_name: str, emotion: str, player_id: str = "player"):
    """设置NPC情绪 (用于测试)

    Args:
        npc_name: NPC名称
        emotion: 情绪key (happy/sad/angry/excited/neutral)
        player_id: 玩家ID (默认为"player")

    Returns:
        操作结果
    """
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    # 验证情绪值
    valid_emotions = ["happy", "sad", "angry", "excited", "neutral"]
    if emotion not in valid_emotions:
        raise HTTPException(
            status_code=400,
            detail=f"无效的情绪值: {emotion}。有效值: {', '.join(valid_emotions)}"
        )

    try:
        npc_mgr.set_npc_emotion(npc_name, emotion, player_id)
        emotion_info = npc_mgr.get_npc_emotion(npc_name, player_id)

        return {
            "message": f"已设置{npc_name}的情绪",
            "npc_name": npc_name,
            "player_id": player_id,
            **emotion_info
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"设置情绪失败: {str(e)}"
        )

# ==================== 主程序入口 ====================

if __name__ == "__main__":
    print("\n🚀 启动赛博小镇后端服务...")
    print(f"📍 监听地址: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 访问文档: http://localhost:{settings.API_PORT}/docs\n")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )

