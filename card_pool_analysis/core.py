"""
核心模块（简化版）
仅保留配置加载、Simulator（策略从注册表获取）
"""
from pathlib import Path
from typing import Dict, Any, Generator
import yaml
import logging
import numpy as np
from .schemas import PoolState, DrawResult
from .registry import get_mechanism

logger = logging.getLogger(__name__)


def load_config(pool_path: Path, run_path: Path) -> Dict[str, Any]:
    """
    加载配置，明确区分卡池参数和实验参数
    
    Args:
        pool_path: 卡池配置文件路径
        run_path: 实验配置文件路径
    
    Returns:
        合并后的配置字典
    
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: 配置文件格式错误
        KeyError: 配置缺失必填项
    """
    try:
        logger.info(f"正在加载卡池配置: {pool_path}")
        with open(pool_path, 'r', encoding='utf-8') as f:
            pool = yaml.safe_load(f)
        logger.info(f"正在加载实验配置: {run_path}")
        with open(run_path, 'r', encoding='utf-8') as f:
            run = yaml.safe_load(f)
        
        # 合并配置并明确优先级：run > pool
        config = {**pool, **run}
        
        # 检查必填项
        required_pool = ["strategy", "card_types"]
        required_run = ["global", "simulation", "data_generation", "data_analysis"]
        for field in required_pool:
            if field not in pool:
                raise KeyError(f"卡池配置缺失必填项: {field}")
        for field in required_run:
            if field not in run:
                raise KeyError(f"实验配置缺失必填项: {field}")
        
        # 提取模拟次数参数
        config["simulation_rounds"] = run["simulation"]["rounds"]
        config["draws_per_round"] = run["simulation"]["draws_per_round"]
        
        logger.info("配置加载成功")
        return config
    
    except FileNotFoundError as e:
        logger.error(f"配置文件不存在: {e.filename}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"配置文件格式错误: {str(e)}")
        raise
    except KeyError as e:
        logger.error(f"配置缺失必填项: {str(e)}")
        raise


class Simulator:
    """
    模拟器类（简化版）
    策略从插件注册表获取，无硬编码
    """
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模拟器
        
        Args:
            config: 合并后的配置字典
        """
        self.config = config
        self.global_seed = config["global"]["random_seed"]
        self.rng = np.random.Generator(np.random.PCG64(self.global_seed))
        self.card_types = {c["id"]: c for c in config["card_types"]}
        self.strategy_name = config["strategy"]
        self.strategy_func = get_mechanism(self.strategy_name)
        self.simulation_rounds = config["simulation_rounds"]
        self.draws_per_round = config["draws_per_round"]
        
        # 预生成所有轮种子，提升模拟速度
        self.round_seeds = self.rng.integers(0, 2**32 - 1, size=self.simulation_rounds)
        logger.info(f"模拟器初始化完成：策略={self.strategy_name}，{self.simulation_rounds} 轮，每轮 {self.draws_per_round} 抽")
        logger.info(f"全局随机种子: {self.global_seed}")

    def _init_state(self) -> PoolState:
        """
        初始化卡池状态
        
        Returns:
            初始化后的卡池状态
        """
        return PoolState(
            pity_count={c["id"]: 0 for c in self.config["card_types"]},
            guarantee_active=False
        )

    def run(self) -> Generator[DrawResult, None, None]:
        """
        运行模拟，生成器模式，每10%打印一次进度
        
        Yields:
            抽卡结果
        """
        progress_step = max(1, self.simulation_rounds // 10)
        logger.info("开始模拟...")
        
        for sim_id in range(self.simulation_rounds):
            # 使用预生成的轮种子
            round_seed = self.round_seeds[sim_id]
            round_rng = np.random.Generator(np.random.PCG64(round_seed))
            state = self._init_state()

            for pull_id in range(1, self.draws_per_round + 1):
                pull_seed = round_rng.integers(0, 2**32 - 1)
                seed_chain = (self.global_seed, round_seed, pull_seed)

                # 从插件注册表获取策略并执行
                yield self.strategy_func(
                    self.config, round_rng, state, sim_id, pull_id, seed_chain
                )

            # 打印进度
            if (sim_id + 1) % progress_step == 0:
                progress = (sim_id + 1) / self.simulation_rounds * 100
                logger.info(f"模拟进度: {sim_id + 1}/{self.simulation_rounds} ({progress:.0f}%)")

        logger.info("模拟完成")