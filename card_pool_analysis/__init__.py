"""
抽卡模拟分析项目（前置加固版）
"""
from .schemas import PoolState, DrawResult
from .registry import register_mechanism, get_mechanism, get_mechanism_metadata, list_mechanisms
from .infra import (
    Rarity,
    Game,
    PoolType,
    MechanismTag,
    PathManager,
    parse_tags,
    tags_to_strings
)
from .core import load_config, Simulator
from .data import DataGenerator, DataIO
from .analysis import Analysis

__all__ = [
    # 数据结构
    "PoolState",
    "DrawResult",
    # 枚举
    "Rarity",
    "Game",
    "PoolType",
    "MechanismTag",
    # 注册中心
    "register_mechanism",
    "get_mechanism",
    "get_mechanism_metadata",
    "list_mechanisms",
    # 核心工具
    "PathManager",
    "parse_tags",
    "tags_to_strings",
    # 核心类
    "load_config",
    "Simulator",
    "DataGenerator",
    "DataIO",
    "Analysis"
]