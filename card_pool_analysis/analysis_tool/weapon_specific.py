"""
武器池专属分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def weapon_fate_point(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """
    武器池定轨值分析
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
    
    Returns:
        定轨值分析结果
    """
    target_df = df[df["rarity"] == target_rarity]
    up_df = target_df[target_df["is_up"] == True]
    
    fate_points = up_df["fate_point"].fillna(0).tolist()
    fate_point_triggered = up_df["fate_point_triggered"].fillna(False).tolist()
    
    fate_point_triggered_count = sum(fate_point_triggered)
    fate_point_triggered_rate = fate_point_triggered_count / len(up_df)
    mean_fate_point = float(np.mean(fate_points))
    fate_point_dist = pd.Series(fate_points).value_counts(normalize=True).sort_index()
    
    return {
        "fate_point_triggered_rate": float(fate_point_triggered_rate),
        "mean_fate_point": float(mean_fate_point),
        "fate_point_distribution": fate_point_dist.to_dict(),
        "fate_point_consume_distribution": fate_point_dist.to_dict()
    }