"""
UP大保底机制插件（原神角色池）
原神标准角色池机制：
- 基础概率：SSR 0.6%，SR 5.1%，R 94.3%
- 软保底：74抽后概率递增，90抽必出SSR
- UP大保底：小保底50%概率出UP，歪了之后下一次必出UP
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism


@register_mechanism(
    name="up_guarantee_genshin_character",
    game="genshin",
    pool_type="character",
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
    """
    原神角色池UP大保底机制实现
    
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
    up_config = config.get("up_config", {})
    target_rarity = up_config.get("target_rarity", "SSR")
    up_prob = up_config.get("up_prob", 0.5)
    card_types = {c["id"]: c for c in config["card_types"]}

    # 1. 计算实际概率
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

    # 2. 归一化+抽样
    ids = list(probs.keys())
    norm_probs = [probs[c] / sum(probs.values()) for c in ids]
    rarity = round_rng.choice(ids, p=norm_probs)
    
    # 保存当前保底计数（在更新之前！）
    current_pity_count = state.pity_count[rarity]

    # 3. 更新保底计数
    for card_id in card_types:
        state.pity_count[card_id] += 1
    state.pity_count[rarity] = 0

    # 4. UP判定
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