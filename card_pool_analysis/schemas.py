"""
统一数据结构模块
所有插件和核心模块共享的数据结构
"""
from typing import Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class PoolState:
    """
    卡池状态数据结构
    所有策略插件共享的状态
    """
    pity_count: Dict[str, int] = field(default_factory=dict)
    guarantee_active: bool = False
    extended: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DrawResult:
    """
    抽卡结果数据结构
    所有策略插件必须返回的统一格式
    """
    sim_id: int
    pull_id: int
    rarity: str
    base_prob: float
    actual_prob: float
    pity_triggered: bool
    is_up: bool
    guarantee_triggered: bool
    pity_count: int
    seed_chain: Tuple[int, int, int]
    extended: Dict[str, Any] = field(default_factory=dict)