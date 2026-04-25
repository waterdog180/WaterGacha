"""
简单随机策略插件
无保底、无UP，纯随机抽卡
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism


@register_mechanism(
    name="simple",
    game="generic",
    pool_type="simple",
    description="无保底、无UP，纯随机抽卡"
)
def simple_mechanism(
    config: Dict[str, Any],
    round_rng: np.random.Generator,
    state: PoolState,
    sim_id: int,
    pull_id: int,
    seed_chain: Tuple[int, int, int]
) -> DrawResult:
    """
    简单随机策略实现
    
    Args:
        config: 合并后的配置字典
        round_rng: 轮随机数生成器
        state: 当前卡池状态
        sim_id: 模拟ID
        pull_id: 抽卡ID
        seed_chain: 种子链（全局, 轮, 抽）
    
    Returns:
        抽卡结果
    """
    card_types = {c["id"]: c for c in config["card_types"]}
    ids = list(card_types.keys())
    probs = [card_types[c]["base_prob"] for c in ids]
    norm_probs = [p / sum(probs) for p in probs]
    rarity = round_rng.choice(ids, p=norm_probs)
    
    # 更新保底计数（虽然简单策略不用，但保持统一接口）
    for card_id in card_types:
        state.pity_count[card_id] += 1
    current_pity_count = state.pity_count[rarity]
    state.pity_count[rarity] = 0
    
    return DrawResult(
        sim_id=sim_id, pull_id=pull_id, rarity=rarity,
        base_prob=card_types[rarity]["base_prob"],
        actual_prob=card_types[rarity]["base_prob"],
        pity_triggered=False, is_up=False, guarantee_triggered=False,
        pity_count=current_pity_count,
        seed_chain=seed_chain
    )