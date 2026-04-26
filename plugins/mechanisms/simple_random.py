"""
简单随机机制插件
无保底、无UP，纯随机抽卡（通用机制）
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism
from card_pool_analysis.infra import Game, PoolType, MechanismTag


@register_mechanism(
    name="simple_random",
    game=Game.GENERIC,
    pool_type=PoolType.SIMPLE,
    tags={MechanismTag.SIMPLE_RANDOM},
    description="无保底、无UP，纯随机抽卡（通用机制）"
)
def simple_random_mechanism(
    config: Dict[str, Any],
    round_rng: np.random.Generator,
    state: PoolState,
    sim_id: int,
    pull_id: int,
    seed_chain: Tuple[int, int, int]
) -> DrawResult:
    card_types = {c["id"]: c for c in config["card_types"]}
    ids = list(card_types.keys())
    probs = [card_types[c]["base_prob"] for c in ids]
    norm_probs = [p / sum(probs) for p in probs]
    rarity = round_rng.choice(ids, p=norm_probs)
    
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