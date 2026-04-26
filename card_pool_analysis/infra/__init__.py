"""
核心工具包
包含全局常量、枚举、路径工具等基础设施
"""
from .constants import (
    Rarity,
    Game,
    PoolType,
    MechanismTag,
    parse_tags,
    tags_to_strings,
    DEFAULT_POOL_CONFIG_FILENAME,
    DEFAULT_RUN_CONFIG_FILENAME,
    DATA_FILENAME,
    META_FILENAME,
    LOG_FILENAME,
    ANALYSIS_FILENAME,
    PLOTS_DIRNAME,
    DEFAULT_VIS_DPI,
    DEFAULT_VIS_FIGSIZE,
    DEFAULT_VIS_STYLE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_SIMULATION_ROUNDS,
    DEFAULT_DRAWS_PER_ROUND
)
from .paths import PathManager

__all__ = [
    # 枚举
    "Rarity",
    "Game",
    "PoolType",
    "MechanismTag",
    # 工具函数
    "parse_tags",
    "tags_to_strings",
    # 路径管理
    "PathManager",
    # 常量
    "DEFAULT_POOL_CONFIG_FILENAME",
    "DEFAULT_RUN_CONFIG_FILENAME",
    "DATA_FILENAME",
    "META_FILENAME",
    "LOG_FILENAME",
    "ANALYSIS_FILENAME",
    "PLOTS_DIRNAME",
    "DEFAULT_VIS_DPI",
    "DEFAULT_VIS_FIGSIZE",
    "DEFAULT_VIS_STYLE",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_SIMULATION_ROUNDS",
    "DEFAULT_DRAWS_PER_ROUND"
]