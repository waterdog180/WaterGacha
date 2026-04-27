"""
数据结构定义
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

@dataclass
class PoolState:
    """
    卡池状态（标准化扩展字段）
    """
    # 标准保底计数
    pity_count: Dict[str, int] = field(default_factory=dict)
    # 标准化扩展字段（由 StateEx 统一管理）
    extended: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """初始化安全保障"""
        self.pity_count = self.pity_count or {}
        self.extended = self.extended or {}

@dataclass
class DrawResult:
    """抽卡结果结构"""
    sim_id: int
    pull_id: int
    rarity: str
    base_prob: float
    actual_prob: float
    pity_triggered: bool
    is_up: bool
    guarantee_triggered: bool
    pity_count: int
    seed_chain: tuple[int, int, int]
    extended: Optional[Dict[str, Any]] = None