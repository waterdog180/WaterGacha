"""
策略插件包
显式导入所有策略插件，确保它们被注册
"""
from .simple_random import simple_random_mechanism
from .up_guarantee_genshin_character import up_guarantee_genshin_character_mechanism
from .fate_point_genshin_weapon import fate_point_genshin_weapon_mechanism

__all__ = [
    "simple_random_mechanism",
    "up_guarantee_genshin_character_mechanism",
    "fate_point_genshin_weapon_mechanism"
]