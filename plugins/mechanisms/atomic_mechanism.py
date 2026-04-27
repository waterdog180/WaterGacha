"""
原子化抽卡机制插件（核心 · 彻底修复版）
支持全组件插拔、消融实验、自由组合
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism
from card_pool_analysis.infra import Game, PoolType, MechanismTag, StateEx, EXTENDED_KEYS

@register_mechanism(
    name="atomic_mechanism",
    game=Game.GENERIC,
    pool_type=PoolType.SIMPLE,
    tags={MechanismTag.SIMPLE_RANDOM},
    description="原子化抽卡机制：全组件插拔、消融实验、自由组合"
)
def atomic_mechanism(
    config: Dict[str, Any],
    round_rng: np.random.Generator,
    state: PoolState,
    sim_id: int,
    pull_id: int,
    seed_chain: Tuple[int, int, int]
) -> DrawResult:
    """
    原子化抽卡逻辑：按配置中启用的原子组件依次执行
    """
    mech = config["mechanism"]
    rarity_list = mech["card_types"]
    soft = mech["soft_pity"]
    hard = mech["hard_pity"]
    up = mech["up_judge"]
    pity_gte = mech["pity_guarantee"]
    fate = mech["fate_point"]

    # 0. 递增所有稀有度的保底计数
    for cfg in rarity_list:
        state.pity_count[cfg["id"]] = state.pity_count.get(cfg["id"], 0) + 1

    # 1. 原子：计算实际概率（基础+软保底+硬保底）
    prob_list = []
    trigger_list = []
    for cfg in rarity_list:
        card_id = cfg["id"]
        pity = state.pity_count.get(card_id, 0)
        base = cfg["base_prob"]

        # 硬保底（最高优先级）
        if hard["enabled"] and pity >= hard["threshold"]:
            prob_list.append(1.0)
            trigger_list.append(True)
        # 软保底
        elif soft["enabled"] and pity >= soft["threshold"]:
            prob = base + soft["increment"] * (pity - soft["threshold"])
            prob_list.append(min(prob, 1.0))
            trigger_list.append(True)
        # 基础概率
        else:
            prob_list.append(base)
            trigger_list.append(False)

    norm_prob = np.array(prob_list) / sum(prob_list)

    # 2. 原子：抽中稀有度
    idx = round_rng.choice(len(rarity_list), p=norm_prob)
    rarity = rarity_list[idx]["id"]
    # 🔥 核心修复：先保存当前保底计数，再重置（彻底修正逻辑）
    current_pity_count = state.pity_count.get(rarity, 0)
    state.pity_count[rarity] = 0

    # 3. 原子：UP/大保底/定轨判定
    is_up = False
    guarantee_triggered = False
    ext = {}

    if up["enabled"] and rarity == up["target_rarity"]:
        # 大保底：歪过 → 必中UP
        if pity_gte["enabled"] and StateEx.get(state, EXTENDED_KEYS["GUARANTEE_ACTIVE"], False):
            is_up = True
            guarantee_triggered = True
            StateEx.set(state, EXTENDED_KEYS["GUARANTEE_ACTIVE"], False)
        else:
            is_up = round_rng.random() < up["up_prob"]
            if pity_gte["enabled"] and not is_up:
                StateEx.set(state, EXTENDED_KEYS["GUARANTEE_ACTIVE"], True)

        # 定轨值（武器专属）
        if fate["enabled"] and is_up:
            point = StateEx.increment(state, EXTENDED_KEYS["FATE_POINT"])
            if point >= fate["max_point"]:
                fate_trigger = True
                StateEx.set(state, EXTENDED_KEYS["FATE_POINT"], 0)
            else:
                fate_trigger = False
            ext["fate_point"] = point
            ext["fate_point_triggered"] = fate_trigger

    # 4. 返回结果
    return DrawResult(
        sim_id=sim_id, pull_id=pull_id, rarity=rarity,
        base_prob=rarity_list[idx]["base_prob"],
        actual_prob=prob_list[idx],
        pity_triggered=trigger_list[idx],
        is_up=is_up, guarantee_triggered=guarantee_triggered,
        pity_count=current_pity_count,  # 使用修复后的正确值
        seed_chain=seed_chain,
        extended=ext
    )