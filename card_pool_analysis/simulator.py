"""
抽卡引擎（原子化架构 · 彻底重构版）
零兼容、零回退、零技术债
"""
from typing import Dict, Any
import numpy as np
from .infra import load_config, StateEx, EXTENDED_KEYS
from .registry import get_mechanism
from .schemas import PoolState

class Simulator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mech = config["mechanism"]
        self.sim_cfg = config["simulation"]
        self.rng = np.random.default_rng(config["global_config"]["random_seed"])
        self.mechanism_func = get_mechanism(config["strategy"])
        self.state = PoolState()
        StateEx.init_extended(self.state)

    def run_single_round(self, sim_id: int) -> list:
        results = []
        max_pulls = self.sim_cfg["draws_per_round"]
        for pull_id in range(1, max_pulls + 1):
            seed_tuple = (self.rng.integers(0, 10**9),) * 3
            res = self.mechanism_func(
                self.config, self.rng, self.state,
                sim_id, pull_id, seed_tuple
            )
            results.append(res)
        return results

    def run(self):
        for sim_id in range(1, self.sim_cfg["rounds"] + 1):
            yield from self.run_single_round(sim_id)