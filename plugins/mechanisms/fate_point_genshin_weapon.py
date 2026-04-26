"""
定轨值机制插件（原神武器池）
原神标准武器池机制
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism
from card_pool_analysis.infra import Game, PoolType, MechanismTag


@register_mechanism(
    name="fate_point_genshin_weapon",
    game=Game.GENSHIN,
    pool_type=PoolType.WEAPON,
    tags={
        MechanismTag.SOFT_PITY,
        MechanismTag.HARD_PITY,
        MechanismTag.UP_GUARANTEE,
        MechanismTag.FATE_POINT,
        MechanismTag.DOUBLE_UP
    },
    description="原神标准武器池定轨值机制"
)
def fate_point_genshin_weapon_mechanism(
    config: Dict[str, Any],
    round_rng: np.random.Generator,
    state: PoolState,
    sim_id: int,
    pull_id: int,
    seed_chain: Tuple[int, int, int]
) -> DrawResult:
    weapon_config = config.get("weapon_config", {})
    target_rarity = weapon_config.get("target_rarity", "SSR")
    up_weapons = weapon_config.get("up_weapons", ["Weapon1", "Weapon2"])
    selected_up = weapon_config.get("selected_up", up_weapons[0])
    up_prob = weapon_config.get("up_prob", 0.75)
    card_types = {c["id"]: c for c in config["card_types"]}

    if "fate_point" not in state.extended:
        state.extended["fate_point"] = 0
    if "selected_up" not in state.extended:
        state.extended["selected_up"] = selected_up

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

    is_up = False
    guarantee_triggered = False
    fate_point_triggered = False
    current_fate_point = state.extended["fate_point"]
    selected_weapon = None

    if rarity == target_rarity:
        is_up_candidate = round_rng.random() < up_prob
        
        if current_fate_point >= 2:
            is_up = True
            guarantee_triggered = False
            fate_point_triggered = True
            selected_weapon = state.extended["selected_up"]
            state.extended["fate_point"] = 0
        elif is_up_candidate:
            is_up = True
            if round_rng.random() < 0.5:
                selected_weapon = up_weapons[0]
            else:
                selected_weapon = up_weapons[1]
            
            if selected_weapon == state.extended["selected_up"]:
                state.extended["fate_point"] = 0
            else:
                state.extended["fate_point"] += 1
        else:
            is_up = False
            state.extended["fate_point"] += 1

    extended = {
        "fate_point": current_fate_point,
        "fate_point_triggered": fate_point_triggered,
        "selected_weapon": selected_weapon,
        "selected_up": state.extended["selected_up"]
    }

    return DrawResult(
        sim_id=sim_id, pull_id=pull_id, rarity=rarity,
        base_prob=card_types[rarity]["base_prob"],
        actual_prob=probs[rarity],
        pity_triggered=pity_triggered[rarity],
        is_up=is_up, guarantee_triggered=guarantee_triggered,
        pity_count=current_pity_count,
        seed_chain=seed_chain,
        extended=extended
    )