"""
定轨值机制插件（原神武器池）
原神标准武器池机制：
- 基础概率：SSR 0.7%，SR 6.0%，R 93.3%
- 软保底：63抽后概率递增，80抽必出SSR
- 双UP共享保底：两个UP武器共享保底计数
- 定轨值系统：每抽非定轨UP加1点，满2点必出定轨UP
"""
from typing import Dict, Any, Tuple
import numpy as np
from card_pool_analysis.schemas import PoolState, DrawResult
from card_pool_analysis.registry import register_mechanism


@register_mechanism(
    name="fate_point_genshin_weapon",
    game="genshin",
    pool_type="weapon",
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
    """
    原神武器池定轨值机制实现
    
    Args:
        config: 合并后的配置字典
        round_rng: 轮随机数生成器
        state: 当前卡池状态（包含extended字段中的定轨值）
        sim_id: 模拟ID
        pull_id: 抽卡ID
        seed_chain: 种子链（全局, 轮, 抽）
    
    Returns:
        抽卡结果
    """
    weapon_config = config.get("weapon_config", {})
    target_rarity = weapon_config.get("target_rarity", "SSR")
    up_weapons = weapon_config.get("up_weapons", ["Weapon1", "Weapon2"])
    selected_up = weapon_config.get("selected_up", up_weapons[0])  # 默认定轨第一个UP
    up_prob = weapon_config.get("up_prob", 0.75)  # 武器池UP率75%
    card_types = {c["id"]: c for c in config["card_types"]}

    # 初始化定轨值（在PoolState的extended字段中）
    if "fate_point" not in state.extended:
        state.extended["fate_point"] = 0
    if "selected_up" not in state.extended:
        state.extended["selected_up"] = selected_up

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

    # 4. UP判定+定轨逻辑
    is_up = False
    guarantee_triggered = False
    fate_point_triggered = False
    current_fate_point = state.extended["fate_point"]
    selected_weapon = None

    if rarity == target_rarity:
        # 武器池UP率75%
        is_up_candidate = round_rng.random() < up_prob
        
        # 定轨逻辑：满2点必出定轨UP
        if current_fate_point >= 2:
            is_up = True
            guarantee_triggered = False
            fate_point_triggered = True
            selected_weapon = state.extended["selected_up"]
            state.extended["fate_point"] = 0  # 清空定轨值
        elif is_up_candidate:
            is_up = True
            # 双UP随机选择
            if round_rng.random() < 0.5:
                selected_weapon = up_weapons[0]
            else:
                selected_weapon = up_weapons[1]
            
            # 检查是否是定轨UP
            if selected_weapon == state.extended["selected_up"]:
                state.extended["fate_point"] = 0  # 清空定轨值
            else:
                state.extended["fate_point"] += 1  # 非定轨UP，加1点
        else:
            # 歪了，加1点定轨值
            is_up = False
            state.extended["fate_point"] += 1

    # 保存定轨相关信息到extended字段
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