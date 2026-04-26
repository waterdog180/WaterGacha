"""
全局常量与枚举模块
统一管理所有硬编码字符串、数值、标签，避免隐性bug
"""
from enum import Enum, auto
from typing import Set


# ========== 枚举定义 ==========
class Rarity(Enum):
    """稀有度枚举"""
    SSR = "SSR"
    SR = "SR"
    R = "R"


class Game(Enum):
    """游戏枚举"""
    GENERIC = "generic"
    GENSHIN = "genshin"
    ZZZ = "zzz"
    HSR = "hsr"
    ARKNIGHTS = "arknights"


class PoolType(Enum):
    """卡池类型枚举"""
    SIMPLE = "simple"
    CHARACTER = "character"
    WEAPON = "weapon"
    LIGHTCONE = "lightcone"
    PERMANENT = "permanent"


class MechanismTag(Enum):
    """机制能力标签枚举（用于自动路由专属分析）"""
    SIMPLE_RANDOM = auto()
    SOFT_PITY = auto()
    HARD_PITY = auto()
    UP_GUARANTEE = auto()
    FATE_POINT = auto()
    DOUBLE_UP = auto()
    SINGLE_UP = auto()


# ========== 全局常量定义 ==========
# 文件命名常量
DEFAULT_POOL_CONFIG_FILENAME = "pool.yaml"
DEFAULT_RUN_CONFIG_FILENAME = "run.yaml"
DATA_FILENAME = "data.parquet"
META_FILENAME = "meta.json"
LOG_FILENAME = "log.txt"
ANALYSIS_FILENAME = "analysis.json"
PLOTS_DIRNAME = "plots"

# 实验目录命名格式
EXPERIMENT_DIR_FORMAT = "{timestamp}_{experiment_name}"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# 默认配置路径
DEFAULT_POOL_CONFIG_PATH = "configs/pool.yaml"
DEFAULT_RUN_CONFIG_PATH = "configs/run.yaml"
DEFAULT_EXPERIMENTS_BASE_DIR = "experiments"

# 可视化常量
DEFAULT_VIS_DPI = 300
DEFAULT_VIS_FIGSIZE = (12, 8)
DEFAULT_VIS_STYLE = "seaborn-v0_8"

# 数据生成常量
DEFAULT_CHUNK_SIZE = 100000
DEFAULT_SIMULATION_ROUNDS = 5000
DEFAULT_DRAWS_PER_ROUND = 200

# 机制标签映射（用于兼容旧代码的字符串标签）
TAG_STRING_MAPPING = {
    "simple_random": MechanismTag.SIMPLE_RANDOM,
    "soft_pity": MechanismTag.SOFT_PITY,
    "hard_pity": MechanismTag.HARD_PITY,
    "up_guarantee": MechanismTag.UP_GUARANTEE,
    "fate_point": MechanismTag.FATE_POINT,
    "double_up": MechanismTag.DOUBLE_UP,
    "single_up": MechanismTag.SINGLE_UP
}


# ========== 工具函数 ==========
def parse_tags(tag_strings: Set[str]) -> Set[MechanismTag]:
    """
    将字符串标签集合转换为枚举标签集合
    
    Args:
        tag_strings: 字符串标签集合
    
    Returns:
        枚举标签集合
    """
    tags = set()
    for tag_str in tag_strings:
        if tag_str in TAG_STRING_MAPPING:
            tags.add(TAG_STRING_MAPPING[tag_str])
    return tags


def tags_to_strings(tags: Set[MechanismTag]) -> Set[str]:
    """
    将枚举标签集合转换为字符串标签集合
    
    Args:
        tags: 枚举标签集合
    
    Returns:
        字符串标签集合
    """
    string_mapping = {v: k for k, v in TAG_STRING_MAPPING.items()}
    return {string_mapping[tag] for tag in tags if tag in string_mapping}