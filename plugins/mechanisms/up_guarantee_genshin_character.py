"""
UP大保底机制插件（原神角色池）
原神标准角色池机制
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism
from card_pool_analysis.infra import Game, PoolType, MechanismTag


@register_mechanism(
    name="up_guarantee_genshin_character",
    game=Game.GENSHIN,
    pool_type=PoolType.CHARACTER,
    tags={
        MechanismTag.SOFT_PITY,
        MechanismTag.HARD_PITY,
        MechanismTag.UP_GUARANTEE,
        MechanismTag.SINGLE_UP
    },
    description="原神标准角色池UP大保底机制"
)
def up_guarantee_genshin_character_mechanism(
    config: Dict[str, Any],
    round_rng: np.random.Generator,
    state: PoolState,
    sim_id: int,
    pull_id: int,
    seed_chain: Tuple[int, int, int]
) -> DrawResult:
    up_config = config.get("up_config", {})
    target_rarity = up_config.get("target_rarity", "SSR")
    up_prob = up_config.get("up_prob", 0.5)
    card_types = {c["id"]: c for c in config["card_types"]}

    probs, pity_triggered = {}, {}
    for card_id, card in card_types.items():
        pity = state.pity_count[card_id]
        base = card["base_prob"]
        threshold = card.get("pity_threshold", 10**9)
        hard = card.get("hard_pity", 10**9)
        incr = card.get("pity_increment", 0.0)

        if pity >= hard:
            probs[card_id], pity_triggered[card_id] = 1.0, True
        elif pity >= threshold:
            probs[card_id] = min(base + incr * (pity - threshold), 1.0)
            pity_triggered[card_id] = True
        else:
            probs[card_id], pity_triggered[card_id] = base, False

    ids = list(probs.keys())
    norm_probs = [probs[c] / sum(probs.values()) for c in ids]
    rarity = round_rng.choice(ids, p=norm_probs)
    
    current_pity_count = state.pity_count[rarity]

    for card_id in card_types:
        state.pity_count[card_id] += 1
    state.pity_count[rarity] = 0

    is_up, guarantee_triggered = False, False
    if rarity == target_rarity:
        if state.guarantee_active:
            is_up, guarantee_triggered = True, True
            state.guarantee_active = False
        else:
            is_up = round_rng.random() < up_prob
            if not is_up:
                state.guarantee_active = True

    return DrawResult(
        sim_id=sim_id, pull_id=pull_id, rarity=rarity,
        base_prob=card_types[rarity]["base_prob"],
        actual_prob=probs[rarity],
        pity_triggered=pity_triggered[rarity],
        is_up=is_up, guarantee_triggered=guarantee_triggered,
        pity_count=current_pity_count,
        seed_chain=seed_chain
    )