"""
概率论命题分析模块
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def consecutive_lose(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """连续歪的概率分布"""
    target_df = df[df["rarity"] == target_rarity]
    sim_groups = target_df.groupby("sim_id")
    consecutive_lose_counts = []
    
    for _, group in sim_groups:
        small_pity_results = group[group["guarantee_triggered"] == False]["is_up"].values
        current_lose = 0
        for is_up in small_pity_results:
            if not is_up:
                current_lose += 1
            else:
                if current_lose > 0:
                    consecutive_lose_counts.append(current_lose)
                current_lose = 0
        if current_lose > 0:
            consecutive_lose_counts.append(current_lose)
    
    counts = pd.Series(consecutive_lose_counts).value_counts(normalize=True).sort_index()
    return {
        "max_consecutive_lose": int(counts.index.max()),
        "distribution": counts.to_dict(),
        "prob_2_consecutive_lose": float(counts.get(2, 0)),
        "prob_3_consecutive_lose": float(counts.get(3, 0)),
        "prob_4_consecutive_lose": float(counts.get(4, 0)),
        "prob_5_consecutive_lose": float(counts.get(5, 0))
    }


def conditional_expectation(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """条件期望分析"""
    target_df = df[df["rarity"] == target_rarity]
    first_draws = target_df.groupby("sim_id")["pull_id"].min()
    
    m_values = [30, 50, 70, 80]
    conditional_expectations = {}
    
    for m in m_values:
        filtered = first_draws[first_draws > m]
        conditional_expectations[f"E[X|X>{m}]"] = float(filtered.mean() - m)
    
    return conditional_expectations


def confidence_interval(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """置信区间分析"""
    target_df = df[df["rarity"] == target_rarity]
    first_draws = target_df.groupby("sim_id")["pull_id"].min()
    n = len(first_draws)
    mean = first_draws.mean()
    std = first_draws.std()
    
    ci_95_lower = mean - 1.96 * (std / np.sqrt(n))
    ci_95_upper = mean + 1.96 * (std / np.sqrt(n))
    ci_99_lower = mean - 2.576 * (std / np.sqrt(n))
    ci_99_upper = mean + 2.576 * (std / np.sqrt(n))
    
    return {
        "sample_size": n,
        "mean": float(mean),
        "std": float(std),
        "ci_95": [float(ci_95_lower), float(ci_95_upper)],
        "ci_99": [float(ci_99_lower), float(ci_99_upper)]
    }


def guarantee_trigger_distribution(df: pd.DataFrame, target_rarity: str) -> Dict[str, Any]:
    """大保底触发次数分布"""
    target_df = df[df["rarity"] == target_rarity]
    sim_groups = target_df.groupby("sim_id")
    guarantee_trigger_counts = []
    
    for _, group in sim_groups:
        guarantee_trigger_counts.append(len(group[group["guarantee_triggered"] == True]))
    
    counts = pd.Series(guarantee_trigger_counts).value_counts(normalize=True).sort_index()
    return {
        "mean_guarantee_triggers": float(np.mean(guarantee_trigger_counts)),
        "distribution": counts.to_dict()
    }