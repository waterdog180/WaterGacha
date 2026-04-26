"""
二维分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def multivariate_analysis(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """
    二维分析
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
    
    Returns:
        二维分析结果
    """
    target_df = df[df["rarity"] == target_rarity]
    first_target = target_df.groupby("sim_id").first().reset_index()
    x = first_target["pull_id"].values
    y = first_target["pity_count"].values
    
    max_x = min(int(x.max()), 100)
    max_y = min(int(y.max()), 100)
    bins = (max_x, max_y)
    joint, x_edges, y_edges = np.histogram2d(x, y, bins=bins, density=True)
    
    marginal_x = joint.sum(axis=1)
    marginal_y = joint.sum(axis=0)
    
    conditional_dists = {}
    for x_target in [50, 70, 90]:
        x_idx = np.digitize(x_target, x_edges) - 1
        if 0 <= x_idx < joint.shape[0] and marginal_x[x_idx] > 0:
            conditional_y = joint[x_idx, :] / marginal_x[x_idx]
        else:
            conditional_y = np.zeros(joint.shape[1])
        conditional_dists[f"y_given_x_{x_target}"] = conditional_y.tolist()
    
    return {
        "joint_distribution": joint.tolist(),
        "x_edges": x_edges.tolist(),
        "y_edges": y_edges.tolist(),
        "marginal_x": marginal_x.tolist(),
        "marginal_y": marginal_y.tolist(),
        "conditional_dists": conditional_dists
    }