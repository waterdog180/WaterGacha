"""
二维可视化模块
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def visualize_2d(
    two_d_results: Dict[str, Any],
    plots_dir: Path,
    vis_dpi: int = 300,
    vis_figsize: tuple = (12, 8)
) -> None:
    """
    二维可视化
    
    Args:
        two_d_results: 二维分析结果
        plots_dir: 图片保存目录
        vis_dpi: 图片DPI
        vis_figsize: 图片尺寸
    """
    joint = np.array(two_d_results["joint_distribution"])
    x_edges = np.array(two_d_results["x_edges"])
    y_edges = np.array(two_d_results["y_edges"])
    marginal_x = np.array(two_d_results["marginal_x"])
    marginal_y = np.array(two_d_results["marginal_y"])
    conditional_dists = two_d_results["conditional_dists"]
    
    # 联合分布热力图
    fig, ax = plt.subplots(figsize=vis_figsize)
    im = ax.imshow(joint.T, origin="lower", aspect="auto", 
                  extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
                  cmap="viridis")
    ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
    ax.set_ylabel("Pity Count at First SSR", fontsize=12)
    ax.set_title("Joint Distribution Heatmap: Pulls vs Pity Count", fontsize=14)
    plt.colorbar(im, ax=ax, label="Probability Density")
    plt.tight_layout()
    plt.savefig(plots_dir / "joint_distribution.png", dpi=vis_dpi)
    plt.close()
    logger.info("联合分布热力图已保存")
    
    # 边缘分布直方图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(vis_figsize[0] * 1.5, vis_figsize[1]))
    ax1.bar(x_edges[:-1], marginal_x, width=np.diff(x_edges), alpha=0.7, color="#1f77b4")
    ax1.set_xlabel("Number of Pulls to First SSR", fontsize=12)
    ax1.set_ylabel("Probability Density", fontsize=12)
    ax1.set_title("Marginal Distribution of Pulls", fontsize=14)
    ax1.grid(alpha=0.3)
    
    ax2.bar(y_edges[:-1], marginal_y, width=np.diff(y_edges), alpha=0.7, color="#ff7f0e")
    ax2.set_xlabel("Pity Count at First SSR", fontsize=12)
    ax2.set_ylabel("Probability Density", fontsize=12)
    ax2.set_title("Marginal Distribution of Pity Count", fontsize=14)
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plots_dir / "marginal_distributions.png", dpi=vis_dpi)
    plt.close()
    logger.info("边缘分布直方图已保存")
    
    # 条件分布折线图
    fig, ax = plt.subplots(figsize=vis_figsize)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for i, (x_target, cond_y) in enumerate(conditional_dists.items()):
        ax.plot(y_edges[:-1], cond_y, linewidth=2, color=colors[i], 
               label=f"Pulls={x_target.split('_')[-1]}")
    ax.set_xlabel("Pity Count", fontsize=12)
    ax.set_ylabel("Conditional Probability Density", fontsize=12)
    ax.set_title("Conditional Distribution of Pity Count Given Pulls", fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "conditional_distribution.png", dpi=vis_dpi)
    plt.close()
    logger.info("条件分布折线图已保存")