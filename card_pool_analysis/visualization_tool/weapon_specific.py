"""
武器池专属可视化模块
"""
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def visualize_weapon_specific(
    wfp_results: Dict[str, Any],
    plots_dir: Path,
    vis_dpi: int = 300,
    vis_figsize: tuple = (12, 8)
) -> None:
    """
    武器池专属可视化
    
    Args:
        wfp_results: 武器池定轨值分析结果
        plots_dir: 图片保存目录
        vis_dpi: 图片DPI
        vis_figsize: 图片尺寸
    """
    # 定轨值分布直方图
    if "fate_point_distribution" in wfp_results:
        dist = wfp_results["fate_point_distribution"]
        fig, ax = plt.subplots(figsize=vis_figsize)
        ax.bar(dist.keys(), dist.values(), alpha=0.7, color="#9467bd")
        ax.set_xlabel("Fate Point When Pulling UP Weapon", fontsize=12)
        ax.set_ylabel("Probability", fontsize=12)
        ax.set_title("Distribution of Fate Points When Pulling UP Weapon", fontsize=14)
        ax.set_xlim(-0.5, 2.5)
        ax.set_xticks([0, 1, 2])
        ax.grid(alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(plots_dir / "weapon_fate_point_distribution.png", dpi=vis_dpi)
        plt.close()
        logger.info("定轨值分布直方图已保存")
    
    # 定轨消耗分布饼图
    if "fate_point_consume_distribution" in wfp_results:
        dist = wfp_results["fate_point_consume_distribution"]
        labels = [f"Fate Point {k}" for k in dist.keys()]
        sizes = list(dist.values())
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        
        fig, ax = plt.subplots(figsize=vis_figsize)
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                           autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title("Distribution of Fate Points When Pulling UP Weapon", fontsize=14)
        plt.tight_layout()
        plt.savefig(plots_dir / "weapon_fate_point_pie.png", dpi=vis_dpi)
        plt.close()
        logger.info("定轨消耗分布饼图已保存")