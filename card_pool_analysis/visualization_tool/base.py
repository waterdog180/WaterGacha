"""
基础可视化模块
"""
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def visualize_1d(
    df: pd.DataFrame,
    target_rarity: str,
    plots_dir: Path,
    vis_dpi: int = 300,
    vis_figsize: tuple = (12, 8)
) -> None:
    """
    一维可视化
    
    Args:
        df: 抽卡数据DataFrame
        target_rarity: 目标稀有度
        plots_dir: 图片保存目录
        vis_dpi: 图片DPI
        vis_figsize: 图片尺寸
    """
    target_df = df[df["rarity"] == target_rarity]
    first_draws = target_df.groupby("sim_id")["pull_id"].min()
    
    # PMF
    fig, ax = plt.subplots(figsize=vis_figsize)
    pmf = first_draws.value_counts(normalize=True).sort_index()
    ax.bar(pmf.index, pmf.values, alpha=0.7, color="#1f77b4")
    ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
    ax.set_ylabel("Probability", fontsize=12)
    ax.set_title("Distribution of Pulls to First SSR (PMF)", fontsize=14)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "pmf.png", dpi=vis_dpi)
    plt.close()
    logger.info("PMF图已保存")
    
    # CDF
    fig, ax = plt.subplots(figsize=vis_figsize)
    cdf = pmf.cumsum()
    ax.plot(cdf.index, cdf.values, linewidth=2, color="#ff7f0e")
    ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
    ax.set_ylabel("Cumulative Probability", fontsize=12)
    ax.set_title("Cumulative Distribution of Pulls to First SSR (CDF)", fontsize=14)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "cdf.png", dpi=vis_dpi)
    plt.close()
    logger.info("CDF图已保存")
    
    # 收敛曲线
    if len(first_draws) > 100:
        fig, ax = plt.subplots(figsize=vis_figsize)
        means = []
        for i in range(100, len(first_draws) + 1, max(1, len(first_draws) // 100)):
            means.append(first_draws[:i].mean())
        ax.plot(range(100, len(first_draws) + 1, max(1, len(first_draws) // 100)), 
               means, linewidth=2, color="#2ca02c")
        ax.axhline(y=first_draws.mean(), color="red", linestyle="--", 
                  label=f"Final Expectation: {first_draws.mean():.1f}")
        ax.set_xlabel("Number of Simulation Rounds", fontsize=12)
        ax.set_ylabel("Expected Number of Pulls", fontsize=12)
        ax.set_title("Convergence of Expected Pulls with Simulation Rounds", fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(plots_dir / "convergence.png", dpi=vis_dpi)
        plt.close()
        logger.info("收敛曲线图已保存")