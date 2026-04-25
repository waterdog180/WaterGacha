"""
极简插件注册中心模块
仅支持显式导入+装饰器注册，无复杂自动发现
"""
from typing import Dict, Any, Callable, Tuple
import logging
import numpy as np
from .schemas import PoolState, DrawResult

logger = logging.getLogger(__name__)

# ========== 策略插件注册表 ==========
_MECHANISM_REGISTRY: Dict[str, Dict[str, Any]] = {}

# ========== 策略插件签名类型提示 ==========
MechanismFunc = Callable[
    [Dict[str, Any], np.random.Generator, PoolState, int, int, Tuple[int, int, int]],
    DrawResult
]


def register_mechanism(
    name: str,
    game: str,
    pool_type: str,
    description: str = ""
) -> Callable[[MechanismFunc], MechanismFunc]:
    """
    策略插件注册装饰器
    所有策略插件必须使用此装饰器注册
    
    Args:
        name: 策略名称（唯一标识）
        game: 游戏名称
        pool_type: 卡池类型（如"character"、"weapon"）
        description: 策略描述（可选）
    
    Returns:
        装饰后的策略函数
    """
    def decorator(func: MechanismFunc) -> MechanismFunc:
        if name in _MECHANISM_REGISTRY:
            logger.warning(f"策略 [{name}] 已存在，将被覆盖")
        _MECHANISM_REGISTRY[name] = {
            "func": func,
            "game": game,
            "pool_type": pool_type,
            "description": description
        }
        logger.info(f"策略 [{name}] 已注册（游戏：{game}，卡池类型：{pool_type}）")
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
        策略元数据（func、game、pool_type、description）
    
    Raises:
        ValueError: 策略不存在
    """
    if name not in _MECHANISM_REGISTRY:
        available = list(_MECHANISM_REGISTRY.keys())
        raise ValueError(f"未知策略 [{name}]，可用策略：{available}")
    return _MECHANISM_REGISTRY[name]


def list_mechanisms() -> Dict[str, Dict[str, Any]]:
    """
    列出所有已注册的策略
    
    Returns:
        所有策略的元数据字典
    """
    return _MECHANISM_REGISTRY.copy()