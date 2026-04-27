"""
策略插件包（原子化架构 · 彻底重构版）
只保留原子化机制
"""
from .atomic_mechanism import atomic_mechanism
__all__ = ["atomic_mechanism"]