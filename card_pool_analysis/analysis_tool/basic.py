"""
基础统计分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def basic_stats(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """
    基础统计分析
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
    
    Returns:
        基础统计结果
    """
    target_df = df[df["rarity"] == target_rarity]
    first_draws = target_df.groupby("sim_id")["pull_id"].min()
    return {
        "mean": float(first_draws.mean()),
        "variance": float(first_draws.var()),
        "std": float(first_draws.std()),
        "median": float(first_draws.median()),
        "min": int(first_draws.min()),
        "max": int(first_draws.max())
    }