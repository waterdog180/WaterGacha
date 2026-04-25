"""
策略插件包
显式导入所有策略插件，确保它们被注册
"""
from .simple import simple_mechanism
from .genshin_character import genshin_character_mechanism

__all__ = ["simple_mechanism", "genshin_character_mechanism"]