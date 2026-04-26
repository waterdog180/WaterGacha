"""
条件概率分析模块
"""
import pandas as pd
from typing import Dict, Any


def conditional_probability(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """
    条件概率分析
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
    
    Returns:
        条件概率分析结果
    """
    target_df = df[df["rarity"] == target_rarity]
    
    total_up = len(target_df[target_df["is_up"] == True])
    total_ssr = len(target_df)
    total_up_rate = total_up / total_ssr
    
    small_pity_df = target_df[target_df["guarantee_triggered"] == False]
    small_pity_lose = len(small_pity_df[small_pity_df["is_up"] == False])
    small_pity_lose_rate = small_pity_lose / len(small_pity_df)
    small_pity_up_rate = 1 - small_pity_lose_rate
    
    guarantee_triggered = len(target_df[target_df["guarantee_triggered"] == True])
    guarantee_triggered_rate = guarantee_triggered / total_ssr
    
    return {
        "total_up_rate": float(total_up_rate),
        "total_lose_rate": float(1 - total_up_rate),
        "small_pity_lose_rate": float(small_pity_lose_rate),
        "small_pity_up_rate": float(small_pity_up_rate),
        "guarantee_triggered_rate": float(guarantee_triggered_rate)
    }