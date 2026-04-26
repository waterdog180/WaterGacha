"""
分析模块（阶段4：简化版）
移除过度异常处理，保证数据结构一致性
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from .registry import get_mechanism_metadata

logger = logging.getLogger(__name__)

# ========== 极简分析器（所有逻辑集中） ==========
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
        
        # 获取策略元数据
        self.strategy_name = config["strategy"]
        self.strategy_meta = get_mechanism_metadata(self.strategy_name)
        self.pool_type = self.strategy_meta["pool_type"]
        
        if self.vis_enabled:
            plt.style.use(self.vis_style)
        
        logger.info(f"分析器初始化完成：目标稀有度={self.target}，启用分析={self.enabled}")
        logger.info(f"策略元数据：游戏={self.strategy_meta['game']}，卡池类型={self.pool_type}")
        if self.vis_enabled:
            logger.info(f"可视化已启用：保存目录={self.plots_dir}")

    def _basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        return {
            "mean": float(first_draws.mean()),
            "variance": float(first_draws.var()),
            "std": float(first_draws.std()),
            "median": float(first_draws.median()),
            "min": int(first_draws.min()),
            "max": int(first_draws.max())
        }

    def _distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        pmf = first_draws.value_counts(normalize=True).sort_index()
        return {"pmf": pmf.to_dict(), "cdf": pmf.cumsum().to_dict()}

    def _conditional_prob(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        
        # 1. 总UP率
        total_up = len(target_df[target_df["is_up"] == True])
        total_ssr = len(target_df)
        total_up_rate = total_up / total_ssr
        
        # 2. 小保底歪率
        small_pity_df = target_df[target_df["guarantee_triggered"] == False]
        small_pity_lose = len(small_pity_df[small_pity_df["is_up"] == False])
        small_pity_lose_rate = small_pity_lose / len(small_pity_df)
        small_pity_up_rate = 1 - small_pity_lose_rate
        
        # 3. 大保底触发率
        guarantee_triggered = len(target_df[target_df["guarantee_triggered"] == True])
        guarantee_triggered_rate = guarantee_triggered / total_ssr
        
        return {
            "total_up_rate": float(total_up_rate),
            "total_lose_rate": float(1 - total_up_rate),
            "small_pity_lose_rate": float(small_pity_lose_rate),
            "small_pity_up_rate": float(small_pity_up_rate),
            "guarantee_triggered_rate": float(guarantee_triggered_rate)
        }

    def _two_dimensional(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
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

    def _consecutive_lose(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
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

    def _conditional_expectation(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        
        m_values = [30, 50, 70, 80]
        conditional_expectations = {}
        
        for m in m_values:
            filtered = first_draws[first_draws > m]
            conditional_expectations[f"E[X|X>{m}]"] = float(filtered.mean() - m)
        
        return conditional_expectations

    def _confidence_interval(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
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

    def _guarantee_trigger_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        sim_groups = target_df.groupby("sim_id")
        guarantee_trigger_counts = []
        
        for _, group in sim_groups:
            guarantee_trigger_counts.append(len(group[group["guarantee_triggered"] == True]))
        
        counts = pd.Series(guarantee_trigger_counts).value_counts(normalize=True).sort_index()
        return {
            "mean_guarantee_triggers": float(np.mean(guarantee_trigger_counts)),
            "distribution": counts.to_dict()
        }

    def _weapon_fate_point(self, df: pd.DataFrame) -> Dict[str, Any]:
        if self.pool_type != "weapon":
            return {}
        
        target_df = df[df["rarity"] == self.target]
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

    # ========== 可视化方法（全英文） ==========
    def _visualize_1d(self, df: pd.DataFrame, analysis_results: Dict[str, Any]):
        target_df = df[df["rarity"] == self.target]
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        
        # PMF
        fig, ax = plt.subplots(figsize=self.vis_figsize)
        pmf = first_draws.value_counts(normalize=True).sort_index()
        ax.bar(pmf.index, pmf.values, alpha=0.7, color="#1f77b4")
        ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
        ax.set_ylabel("Probability", fontsize=12)
        ax.set_title("Distribution of Pulls to First SSR (PMF)", fontsize=14)
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / "pmf.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("PMF图已保存")
        
        # CDF
        fig, ax = plt.subplots(figsize=self.vis_figsize)
        cdf = pmf.cumsum()
        ax.plot(cdf.index, cdf.values, linewidth=2, color="#ff7f0e")
        ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
        ax.set_ylabel("Cumulative Probability", fontsize=12)
        ax.set_title("Cumulative Distribution of Pulls to First SSR (CDF)", fontsize=14)
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / "cdf.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("CDF图已保存")
        
        # 收敛曲线
        if len(first_draws) > 100:
            fig, ax = plt.subplots(figsize=self.vis_figsize)
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
            plt.savefig(self.plots_dir / "convergence.png", dpi=self.vis_dpi)
            plt.close()
            logger.info("收敛曲线图已保存")

    def _visualize_2d(self, two_d_results: Dict[str, Any]):
        joint = np.array(two_d_results["joint_distribution"])
        x_edges = np.array(two_d_results["x_edges"])
        y_edges = np.array(two_d_results["y_edges"])
        marginal_x = np.array(two_d_results["marginal_x"])
        marginal_y = np.array(two_d_results["marginal_y"])
        conditional_dists = two_d_results["conditional_dists"]
        
        # 联合分布热力图
        fig, ax = plt.subplots(figsize=self.vis_figsize)
        im = ax.imshow(joint.T, origin="lower", aspect="auto", 
                      extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]],
                      cmap="viridis")
        ax.set_xlabel("Number of Pulls to First SSR", fontsize=12)
        ax.set_ylabel("Pity Count at First SSR", fontsize=12)
        ax.set_title("Joint Distribution Heatmap: Pulls vs Pity Count", fontsize=14)
        plt.colorbar(im, ax=ax, label="Probability Density")
        plt.tight_layout()
        plt.savefig(self.plots_dir / "joint_distribution.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("联合分布热力图已保存")
        
        # 边缘分布直方图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(self.vis_figsize[0] * 1.5, self.vis_figsize[1]))
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
        plt.savefig(self.plots_dir / "marginal_distributions.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("边缘分布直方图已保存")
        
        # 条件分布折线图
        fig, ax = plt.subplots(figsize=self.vis_figsize)
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
        plt.savefig(self.plots_dir / "conditional_distribution.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("条件分布折线图已保存")

    def _visualize_consecutive_lose(self, cl_results: Dict[str, Any]):
        dist = cl_results["distribution"]
        max_lose = cl_results["max_consecutive_lose"]
        
        fig, ax = plt.subplots(figsize=self.vis_figsize)
        ax.bar(dist.keys(), dist.values(), alpha=0.7, color="#d62728")
        ax.set_xlabel("Number of Consecutive Small Pity Loses", fontsize=12)
        ax.set_ylabel("Probability", fontsize=12)
        ax.set_title("Distribution of Consecutive Small Pity Loses", fontsize=14)
        ax.set_xlim(0, min(max_lose + 1, 10))
        ax.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / "consecutive_lose.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("连续歪概率分布图已保存")

    def _visualize_confidence_interval(self, ci_results: Dict[str, Any]):
        mean = ci_results["mean"]
        ci_95 = ci_results["ci_95"]
        ci_99 = ci_results["ci_99"]
        
        fig, ax = plt.subplots(figsize=self.vis_figsize)
        ax.bar(["95% CI", "99% CI"], [mean, mean], yerr=[[mean - ci_95[0], mean - ci_99[0]], 
                                                          [ci_95[1] - mean, ci_99[1] - mean]],
               capsize=10, alpha=0.7, color=["#1f77b4", "#ff7f0e"])
        ax.set_ylabel("Expected Number of Pulls", fontsize=12)
        ax.set_title("Confidence Intervals of Expected Pulls", fontsize=14)
        ax.grid(alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(self.plots_dir / "confidence_interval.png", dpi=self.vis_dpi)
        plt.close()
        logger.info("置信区间图已保存")

    def _visualize_weapon_fate_point(self, wfp_results: Dict[str, Any]):
        # 定轨值分布直方图
        if "fate_point_distribution" in wfp_results:
            dist = wfp_results["fate_point_distribution"]
            fig, ax = plt.subplots(figsize=self.vis_figsize)
            ax.bar(dist.keys(), dist.values(), alpha=0.7, color="#9467bd")
            ax.set_xlabel("Fate Point When Pulling UP Weapon", fontsize=12)
            ax.set_ylabel("Probability", fontsize=12)
            ax.set_title("Distribution of Fate Points When Pulling UP Weapon", fontsize=14)
            ax.set_xlim(-0.5, 2.5)
            ax.set_xticks([0, 1, 2])
            ax.grid(alpha=0.3, axis="y")
            plt.tight_layout()
            plt.savefig(self.plots_dir / "weapon_fate_point_distribution.png", dpi=self.vis_dpi)
            plt.close()
            logger.info("定轨值分布直方图已保存")
        
        # 定轨消耗分布饼图
        if "fate_point_consume_distribution" in wfp_results:
            dist = wfp_results["fate_point_consume_distribution"]
            labels = [f"Fate Point {k}" for k in dist.keys()]
            sizes = list(dist.values())
            colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
            
            fig, ax = plt.subplots(figsize=self.vis_figsize)
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                               autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title("Distribution of Fate Points When Pulling UP Weapon", fontsize=14)
            plt.tight_layout()
            plt.savefig(self.plots_dir / "weapon_fate_point_pie.png", dpi=self.vis_dpi)
            plt.close()
            logger.info("定轨消耗分布饼图已保存")

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        logger.info("开始分析...")
        results = {
            "timestamp": datetime.now().isoformat(),
            "experiment_name": self.config["global"]["experiment_name"],
            "target_rarity": self.target,
            "strategy_metadata": {
                k: v for k, v in self.strategy_meta.items() if k != "func"
            },
            "analyses": {}
        }
        
        two_d_results = None
        cl_results = None
        ci_results = None
        wfp_results = None
        
        for name in self.enabled:
            method = getattr(self, f"_{name}", None)
            if method:
                logger.info(f"正在执行分析: {name}")
                results["analyses"][name] = method(df)
                if name == "two_dimensional":
                    two_d_results = results["analyses"][name]
                if name == "consecutive_lose":
                    cl_results = results["analyses"][name]
                if name == "confidence_interval":
                    ci_results = results["analyses"][name]
                if name == "weapon_fate_point":
                    wfp_results = results["analyses"][name]
        
        if self.vis_enabled:
            logger.info("开始可视化...")
            if "distribution" in self.enabled:
                self._visualize_1d(df, results)
            if two_d_results:
                self._visualize_2d(two_d_results)
            if cl_results:
                self._visualize_consecutive_lose(cl_results)
            if ci_results:
                self._visualize_confidence_interval(ci_results)
            if wfp_results:
                self._visualize_weapon_fate_point(wfp_results)
        
        logger.info("分析完成")
        return results

    def save(self, results: Dict[str, Any]) -> Path:
        file_path = self.exp_dir / "analysis.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"分析结果已保存到: {file_path}")
        return file_path