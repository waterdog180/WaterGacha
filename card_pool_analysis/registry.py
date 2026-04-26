"""
插件注册中心模块（彻底重构版）
支持机制标签体系，实现自动路由专属分析
"""
from typing import Dict, Any, Callable, Set
import logging
import numpy as np
from .schemas import PoolState, DrawResult
from .infra import MechanismTag, Game, PoolType, tags_to_strings, parse_tags

logger = logging.getLogger(__name__)

# ========== 策略插件注册表 ==========
_MECHANISM_REGISTRY: Dict[str, Dict[str, Any]] = {}

# ========== 策略插件签名类型提示 ==========
MechanismFunc = Callable[
    [Dict[str, Any], np.random.Generator, PoolState, int, int, tuple[int, int, int]],
    DrawResult
]

def register_mechanism(
    name: str,
    game: Game,
    pool_type: PoolType,
    tags: Set[MechanismTag],
    description: str = ""
) -> Callable[[MechanismFunc], MechanismFunc]:
    def decorator(func: MechanismFunc) -> MechanismFunc:
        if name in _MECHANISM_REGISTRY:
            logger.warning(f"策略 [{name}] 已存在，将被覆盖")
        
        _MECHANISM_REGISTRY[name] = {
            "name": name,  # 🔥 修复：在元数据中也保存 name 字段
            "func": func,
            "game": game,
            "pool_type": pool_type,
            "tags": tags,
            "tag_strings": tags_to_strings(tags),
            "description": description
        }
        
        logger.info(
            f"策略 [{name}] 已注册 "
            f"(游戏: {game.value}, 卡池: {pool_type.value}, "
            f"标签: {[t.value for t in tags]})"
        )
        return func
    return decorator

def get_mechanism(name: str) -> MechanismFunc:
    """
    从注册表获取策略函数
    
    Args:
        name: 策略名称
    
    Returns:
        策略函数
    
    Raises:
        ValueError: 策略不存在
    """
    if name not in _MECHANISM_REGISTRY:
        available = list(_MECHANISM_REGISTRY.keys())
        raise ValueError(f"未知策略 [{name}]，可用策略：{available}")
    return _MECHANISM_REGISTRY[name]["func"]


def get_mechanism_metadata(name: str) -> Dict[str, Any]:
    """
    从注册表获取策略元数据
    
    Args:
        name: 策略名称
    
    Returns:
        策略元数据
    
    Raises:
        ValueError: 策略不存在
    """
    if name not in _MECHANISM_REGISTRY:
        available = list(_MECHANISM_REGISTRY.keys())
        raise ValueError(f"未知策略 [{name}]，可用策略：{available}")
    return _MECHANISM_REGISTRY[name].copy()


def has_tag(name: str, tag: MechanismTag) -> bool:
    """
    检查策略是否包含指定标签
    
    Args:
        name: 策略名称
        tag: 机制标签
    
    Returns:
        是否包含标签
    """
    if name not in _MECHANISM_REGISTRY:
        return False
    return tag in _MECHANISM_REGISTRY[name]["tags"]


def list_mechanisms() -> Dict[str, Dict[str, Any]]:
    """
    列出所有已注册的策略
    
    Returns:
        所有策略的元数据字典
    """
    return {k: v.copy() for k, v in _MECHANISM_REGISTRY.items()}