"""
抽卡模拟分析项目（阶段2：插件化架构）
"""
from .schemas import PoolState, DrawResult
from .registry import register_mechanism, get_mechanism, get_mechanism_metadata, list_mechanisms
from .core import load_config, Simulator
from .data import DataGenerator, DataIO
from .analysis import Analysis

__all__ = [
    "PoolState", "DrawResult",
    "register_mechanism", "get_mechanism", "get_mechanism_metadata", "list_mechanisms",
    "load_config", "Simulator",
    "DataGenerator", "DataIO",
    "Analysis"
]