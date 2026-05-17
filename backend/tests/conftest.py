"""共享 fixture 和 mock 配置"""

import sys
import os
import pytest

# 确保 backend 目录在 Python path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from emotion_manager import EmotionManager


@pytest.fixture
def emotion_manager():
    """干净的 EmotionManager 实例"""
    return EmotionManager()


@pytest.fixture
def emotion_manager_with_data():
    """预填充一些情绪数据的 EmotionManager"""
    mgr = EmotionManager()
    mgr.set_emotion("程码", "happy")
    mgr.set_emotion("林案", "sad")
    mgr.set_emotion("苏绘", "excited")
    return mgr
