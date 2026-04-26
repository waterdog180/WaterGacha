"""
分析逻辑包
按概率论与统计学分类管理
"""
from .basic import basic_stats
from .distribution import distribution_analysis
from .conditional import conditional_probability
from .multivariate import multivariate_analysis
from .prob_theory import (
    consecutive_lose,
    conditional_expectation,
    confidence_interval,
    guarantee_trigger_distribution
)
from .weapon_specific import weapon_fate_point

__all__ = [
    "basic_stats",
    "distribution_analysis",
    "conditional_probability",
    "multivariate_analysis",
    "consecutive_lose",
    "conditional_expectation",
    "confidence_interval",
    "guarantee_trigger_distribution",
    "weapon_fate_point"
]