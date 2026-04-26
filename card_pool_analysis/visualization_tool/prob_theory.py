"""
概率论命题可视化模块
"""
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def visualize_prob_theory(
    analyses: Dict[str, Any],
    plots_dir: Path,
    vis_dpi: int = 300,
    vis_figsize: tuple = (12, 8)
) -> None:
    """
    概率论命题可视化
    
    Args:
        analyses: 所有分析结果
        plots_dir: 图片保存目录
        vis_dpi: 图片DPI
        vis_figsize: 图片尺寸
    """
    # 连续歪概率分布
    if "consecutive_lose" in analyses:
        cl_results = analyses["consecutive_lose"]
        dist = cl_results["distribution"]
        max_lose = cl_results["max_consecutive_lose"]
        
        fig, ax = plt.subplots(figsize=vis_figsize)
        ax.bar(dist.keys(), dist.values(), alpha=0.7, color="#d62728")
        ax.set_xlabel("Number of Consecutive Small Pity Loses", fontsize=12)
        ax.set_ylabel("Probability", fontsize=12)
        ax.set_title("Distribution of Consecutive Small Pity Loses", fontsize=14)
        ax.set_xlim(0, min(max_lose + 1, 10))
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(plots_dir / "consecutive_lose.png", dpi=vis_dpi)
        plt.close()
        logger.info("连续歪概率分布图已保存")
    
    # 置信区间
    if "confidence_interval" in analyses:
        ci_results = analyses["confidence_interval"]
        mean = ci_results["mean"]
        ci_95 = ci_results["ci_95"]
        ci_99 = ci_results["ci_99"]
        
        fig, ax = plt.subplots(figsize=vis_figsize)
        ax.bar(["95% CI", "99% CI"], [mean, mean], yerr=[[mean - ci_95[0], mean - ci_99[0]], 
                                                          [ci_95[1] - mean, ci_99[1] - mean]],
               capsize=10, alpha=0.7, color=["#1f77b4", "#ff7f0e"])
        ax.set_ylabel("Expected Number of Pulls", fontsize=12)
        ax.set_title("Confidence Intervals of Expected Pulls", fontsize=14)
        ax.grid(alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(plots_dir / "confidence_interval.png", dpi=vis_dpi)
        plt.close()
        logger.info("置信区间图已保存")