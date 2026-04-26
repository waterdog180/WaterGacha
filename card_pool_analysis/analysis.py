"""
分析管理模块（彻底重构版）
仅负责识别触发、数据分发、日志输出
"""
from pathlib import Path
from typing import Dict, Any
import json
import logging
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

from .registry import get_mechanism_metadata
from .infra import MechanismTag
from .analysis_tool import (
    basic_stats,
    distribution_analysis,
    conditional_probability,
    multivariate_analysis,
    consecutive_lose,
    conditional_expectation,
    confidence_interval,
    guarantee_trigger_distribution,
    weapon_fate_point
)
from .visualization_tool import (
    visualize_1d,
    visualize_2d,
    visualize_prob_theory,
    visualize_weapon_specific
)

logger = logging.getLogger(__name__)


class Analysis:
    def __init__(self, config: Dict[str, Any], exp_dir: Path, plots_dir: Path):
        self.config = config
        self.exp_dir = exp_dir
        self.plots_dir = plots_dir
        self.target = config["data_analysis"].get("target_rarity", "SSR")
        self.enabled = config["data_analysis"].get("enabled", [
            "basic_stats", "distribution", "conditional_prob", "two_dimensional"
        ])
        self.vis_config = config["data_analysis"].get("visualization", {})
        self.vis_enabled = self.vis_config.get("enabled", False)
        self.vis_dpi = self.vis_config.get("dpi", 300)
        self.vis_figsize = tuple(self.vis_config.get("figsize", [12, 8]))
        self.vis_style = self.vis_config.get("style", "seaborn-v0_8")
        
        self.strategy_name = config["strategy"]
        self.strategy_meta = get_mechanism_metadata(self.strategy_name)
        
        if self.vis_enabled:
            plt.style.use(self.vis_style)
        
        logger.info(f"分析器初始化完成：目标稀有度={self.target}，启用分析={self.enabled}")
        logger.info(f"策略标签: {self.strategy_meta['tag_strings']}")
        if self.vis_enabled:
            logger.info(f"可视化已启用：保存目录={self.plots_dir}")

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        logger.info("开始分析...")
        
        strategy_meta_serializable = {
            "name": self.strategy_meta["name"],
            "game": self.strategy_meta["game"].value,
            "pool_type": self.strategy_meta["pool_type"].value,
            "tag_strings": list(self.strategy_meta["tag_strings"]),
            "description": self.strategy_meta["description"]
        }
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "experiment_name": self.config["global"]["experiment_name"],
            "target_rarity": self.target,
            "strategy_metadata": strategy_meta_serializable,
            "analyses": {}
        }
        
        analysis_map = {
            "basic_stats": basic_stats,
            "distribution": distribution_analysis,
            "conditional_prob": conditional_probability,
            "two_dimensional": multivariate_analysis,
            "consecutive_lose": consecutive_lose,
            "conditional_expectation": conditional_expectation,
            "confidence_interval": confidence_interval,
            "guarantee_trigger_distribution": guarantee_trigger_distribution,
            "weapon_fate_point": weapon_fate_point
        }
        
        for name in self.enabled:
            if name in analysis_map:
                logger.info(f"正在执行分析: {name}")
                results["analyses"][name] = analysis_map[name](df, self.target)
        
        if self.vis_enabled:
            logger.info("开始可视化...")
            if "distribution" in self.enabled:
                visualize_1d(df, self.target, self.plots_dir, self.vis_dpi, self.vis_figsize)
            if "two_dimensional" in self.enabled and "two_dimensional" in results["analyses"]:
                visualize_2d(results["analyses"]["two_dimensional"], self.plots_dir, self.vis_dpi, self.vis_figsize)
            if "consecutive_lose" in self.enabled and "consecutive_lose" in results["analyses"]:
                visualize_prob_theory(results["analyses"], self.plots_dir, self.vis_dpi, self.vis_figsize)
            if "weapon_fate_point" in self.enabled and "weapon_fate_point" in results["analyses"]:
                visualize_weapon_specific(results["analyses"]["weapon_fate_point"], self.plots_dir, self.vis_dpi, self.vis_figsize)
        
        logger.info("分析完成")
        return results

    def save(self, results: Dict[str, Any]) -> Path:
        file_path = self.exp_dir / "analysis.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"分析结果已保存到: {file_path}")
        return file_path