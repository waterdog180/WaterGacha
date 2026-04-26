"""
分布分析模块
"""
import pandas as pd
from typing import Dict, Any


def distribution_analysis(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """
    分布分析
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
    
    Returns:
        分布分析结果
    """
    target_df = df[df["rarity"] == target_rarity]
    first_draws = target_df.groupby("sim_id")["pull_id"].min()
    pmf = first_draws.value_counts(normalize=True).sort_index()
    return {
        "pmf": pmf.to_dict(),
        "cdf": pmf.cumsum().to_dict()
    }