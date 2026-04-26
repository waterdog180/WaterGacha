"""
分析模块（实验文件夹隔离版）
使用实验独立的图片目录，避免覆盖
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
        """
        🔥 修改：新增exp_dir和plots_dir参数，从DataIO获取
        Args:
            config: 合并后的配置字典
            exp_dir: 实验独立文件夹路径
            plots_dir: 实验独立的图片目录路径
        """
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
        
        # 获取策略元数据，用于兼容性检查
        self.strategy_name = config["strategy"]
        try:
            self.strategy_meta = get_mechanism_metadata(self.strategy_name)
            self.pool_type = self.strategy_meta["pool_type"]
        except Exception as e:
            logger.warning(f"无法获取策略元数据: {str(e)}，兼容性检查可能失效")
            self.strategy_meta = {}
            self.pool_type = "unknown"
        
        if self.vis_enabled:
            plt.style.use(self.vis_style)
        
        logger.info(f"分析器初始化完成：目标稀有度={self.target}，启用分析={self.enabled}")
        logger.info(f"策略元数据：游戏={self.strategy_meta.get('game', 'unknown')}，卡池类型={self.pool_type}")
        if self.vis_enabled:
            logger.info(f"可视化已启用：保存目录={self.plots_dir}")

    def _basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            logger.warning(f"未找到目标稀有度 [{self.target}] 的记录")
            return {}
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
        if len(target_df) == 0:
            return {}
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        pmf = first_draws.value_counts(normalize=True).sort_index()
        return {"pmf": pmf.to_dict(), "cdf": pmf.cumsum().to_dict()}

    def _conditional_prob(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        条件概率分析（概念区分版）
        - small_pity_lose_rate: 仅小保底状态下的歪率（玩家最常用）
        - total_up_rate: 所有SSR中UP的占比
        """
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        # 1. 总UP率：所有SSR中UP的占比
        total_up = len(target_df[target_df["is_up"] == True])
        total_ssr = len(target_df)
        total_up_rate = total_up / total_ssr
        
        # 2. 小保底歪率：仅小保底状态下的歪率（玩家最常用）
        small_pity_df = target_df[target_df["guarantee_triggered"] == False]
        if len(small_pity_df) > 0:
            small_pity_lose = len(small_pity_df[small_pity_df["is_up"] == False])
            small_pity_lose_rate = small_pity_lose / len(small_pity_df)
            small_pity_up_rate = 1 - small_pity_lose_rate
        else:
            small_pity_lose_rate = 0.0
            small_pity_up_rate = 0.0
        
        # 3. 大保底触发率：所有SSR中大保底的占比
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
        """
        二维随机变量分析
        - 联合分布：(首次抽到SSR的抽卡次数, 抽到时的保底计数)
        - 边缘分布：抽卡次数的边缘分布、保底计数的边缘分布
        - 条件分布：给定抽卡次数时的保底计数分布
        """
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        # 获取首次抽到SSR的记录
        first_target = target_df.groupby("sim_id").first().reset_index()
        x = first_target["pull_id"].values  # 首次抽卡次数
        y = first_target["pity_count"].values  # 抽到时的保底计数
        
        # 1. 联合分布（使用histogram2d高效计算）
        max_x = min(int(x.max()), 100)
        max_y = min(int(y.max()), 100)
        bins = (max_x, max_y)
        joint, x_edges, y_edges = np.histogram2d(x, y, bins=bins, density=True)
        
        # 2. 边缘分布
        marginal_x = joint.sum(axis=1)
        marginal_y = joint.sum(axis=0)
        
        # 3. 条件分布：P(Y | X=50)、P(Y | X=70)、P(Y | X=90)
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

    # ========== 阶段1.5 新增：核心概率论命题分析 ==========
    def _consecutive_lose(self, df: pd.DataFrame) -> Dict[str, Any]:
        """连续歪的概率分布：连续n次小保底歪的概率"""
        logger.info("正在执行分析: consecutive_lose")
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        # 按模拟ID分组，获取每个模拟的UP/歪序列
        sim_groups = target_df.groupby("sim_id")
        consecutive_lose_counts = []
        
        for _, group in sim_groups:
            # 只考虑小保底的结果
            small_pity_results = group[group["guarantee_triggered"] == False]["is_up"].values
            # 统计连续歪的次数
            current_lose = 0
            for is_up in small_pity_results:
                if not is_up:
                    current_lose += 1
                else:
                    if current_lose > 0:
                        consecutive_lose_counts.append(current_lose)
                    current_lose = 0
            # 处理最后一次连续歪
            if current_lose > 0:
                consecutive_lose_counts.append(current_lose)
        
        if not consecutive_lose_counts:
            return {}
        
        # 计算分布
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
        """条件期望分析：已知已抽m次没出SSR，还需抽多少次"""
        logger.info("正在执行分析: conditional_expectation")
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        
        # 计算不同m值的条件期望
        m_values = [30, 50, 70, 80]
        conditional_expectations = {}
        
        for m in m_values:
            # 筛选已抽m次没出SSR的模拟
            filtered = first_draws[first_draws > m]
            if len(filtered) > 0:
                # 条件期望：E[X | X > m] = (E[X] - Σ_{i=1}^m i·P(X=i)) / P(X > m)
                # 简化计算：直接用filtered的均值
                conditional_expectations[f"E[X|X>{m}]"] = float(filtered.mean() - m)
            else:
                conditional_expectations[f"E[X|X>{m}]"] = 0.0
        
        return conditional_expectations

    def _confidence_interval(self, df: pd.DataFrame) -> Dict[str, Any]:
        """蒙特卡洛模拟的置信区间：量化模拟结果的误差范围"""
        logger.info("正在执行分析: confidence_interval")
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        n = len(first_draws)
        mean = first_draws.mean()
        std = first_draws.std()
        
        # 95%置信区间：均值 ± 1.96×(标准差/√n)
        ci_95_lower = mean - 1.96 * (std / np.sqrt(n))
        ci_95_upper = mean + 1.96 * (std / np.sqrt(n))
        
        # 99%置信区间：均值 ± 2.576×(标准差/√n)
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
        """大保底触发次数的分布：n轮模拟中触发大保底的次数"""
        logger.info("正在执行分析: guarantee_trigger_distribution")
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return {}
        
        # 按模拟ID分组，统计每轮触发大保底的次数
        sim_groups = target_df.groupby("sim_id")
        guarantee_trigger_counts = []
        
        for _, group in sim_groups:
            guarantee_trigger_counts.append(len(group[group["guarantee_triggered"] == True]))
        
        # 计算分布
        counts = pd.Series(guarantee_trigger_counts).value_counts(normalize=True).sort_index()
        return {
            "mean_guarantee_triggers": float(np.mean(guarantee_trigger_counts)),
            "distribution": counts.to_dict()
        }

    # ========== 可视化方法（全英文） ==========
    def _visualize_1d(self, df: pd.DataFrame, analysis_results: Dict[str, Any]):
        """一维可视化：PMF、CDF、收敛曲线（全英文）"""
        target_df = df[df["rarity"] == self.target]
        if len(target_df) == 0:
            return
        
        first_draws = target_df.groupby("sim_id")["pull_id"].min()
        
        # 1. PMF柱状图
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
        
        # 2. CDF折线图
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
        
        # 3. 收敛曲线：期望随模拟轮数的变化
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
        """二维可视化：联合分布热力图、边缘分布直方图、条件分布折线图（全英文）"""
        if not two_d_results:
            return
        
        joint = np.array(two_d_results["joint_distribution"])
        x_edges = np.array(two_d_results["x_edges"])
        y_edges = np.array(two_d_results["y_edges"])
        marginal_x = np.array(two_d_results["marginal_x"])
        marginal_y = np.array(two_d_results["marginal_y"])
        conditional_dists = two_d_results["conditional_dists"]
        
        # 1. 联合分布热力图
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
        
        # 2. 边缘分布直方图
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
        
        # 3. 条件分布折线图
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

    # ========== 阶段1.5 新增：核心概率论命题可视化 ==========
    def _visualize_consecutive_lose(self, cl_results: Dict[str, Any]):
        """连续歪的概率分布可视化（全英文）"""
        if not cl_results or "distribution" not in cl_results:
            return
        
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
        """置信区间可视化（全英文）"""
        if not ci_results:
            return
        
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

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        """运行所有启用的分析"""
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
            else:
                logger.warning(f"未知分析方法: {name}，已跳过")
        
        # 可视化
        if self.vis_enabled:
            logger.info("开始可视化...")
            if "distribution" in self.enabled:
                self._visualize_1d(df, results)
            if "two_dimensional" in self.enabled and two_d_results:
                self._visualize_2d(two_d_results)
            if "consecutive_lose" in self.enabled and cl_results:
                self._visualize_consecutive_lose(cl_results)
            if "confidence_interval" in self.enabled and ci_results:
                self._visualize_confidence_interval(ci_results)
        
        logger.info("分析完成")
        return results

    def save(self, results: Dict[str, Any]) -> Path:
        """🔥 修改：分析结果保存在实验独立文件夹中"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.exp_dir / "analysis.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"分析结果已保存到: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"分析结果保存失败: {str(e)}", exc_info=True)
            raise