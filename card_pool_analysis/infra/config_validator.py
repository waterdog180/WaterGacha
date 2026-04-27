"""
配置校验模块（原子化架构 · 彻底重构版）
零兼容、零回退、零技术债
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path

# ===================== 卡池配置（pool.yaml）：纯机制 =====================
class CardTypeConfig(BaseModel):
    """稀有度基础配置（仅ID+基础概率）"""
    id: str
    base_prob: float = Field(ge=0.0, le=1.0)

class SoftPityConfig(BaseModel):
    """软保底原子组件"""
    enabled: bool = False
    threshold: int = Field(ge=0, default=70)
    increment: float = Field(ge=0.0, default=0.05)

class HardPityConfig(BaseModel):
    """硬保底原子组件"""
    enabled: bool = False
    threshold: int = Field(ge=0, default=90)

class UPJudgeConfig(BaseModel):
    """UP判定原子组件"""
    enabled: bool = False
    target_rarity: str = "SSR"
    up_prob: float = Field(ge=0.0, le=1.0, default=0.5)
    up_items: List[str] = []
    selected_up: Optional[str] = None

class PityGuaranteeConfig(BaseModel):
    """大保底原子组件"""
    enabled: bool = False

class FatePointConfig(BaseModel):
    """定轨值原子组件"""
    enabled: bool = False
    max_point: int = Field(ge=0, default=2)

class PoolConfig(BaseModel):
    """卡池配置（pool.yaml）：纯机制，无实验参数"""
    game_type: str
    strategy: str = "atomic_mechanism"
    card_types: List[CardTypeConfig]
    soft_pity: SoftPityConfig = SoftPityConfig()
    hard_pity: HardPityConfig = HardPityConfig()
    up_judge: UPJudgeConfig = UPJudgeConfig()
    pity_guarantee: PityGuaranteeConfig = PityGuaranteeConfig()
    fate_point: FatePointConfig = FatePointConfig()

    @field_validator("card_types")
    def check_total_prob(cls, v):
        total = sum(c.base_prob for c in v)
        if not (0 < total <= 1.0):
            raise ValueError(f"卡池总概率必须在 (0,1]，当前：{total}")
        return v

# ===================== 实验配置（run.yaml）：纯流程 =====================
class GlobalConfig(BaseModel):
    experiment_name: str
    random_seed: int = Field(ge=0, default=42)

class SimulationConfig(BaseModel):
    rounds: int = Field(ge=1, default=5000)
    draws_per_round: int = Field(ge=1, default=200)

class DataGenerationConfig(BaseModel):
    output_dir: str = "./experiments"
    chunk_size: int = Field(ge=1000, default=100000)

class VisualizationConfig(BaseModel):
    enabled: bool = True
    dpi: int = 300
    figsize: List[int] = [12, 8]
    style: str = "seaborn-v0_8"

class DataAnalysisConfig(BaseModel):
    target_rarity: str = "SSR"
    enabled: List[str] = ["basic_stats", "distribution"]
    visualization: VisualizationConfig = VisualizationConfig()

class RunConfig(BaseModel):
    """实验配置（run.yaml）：纯流程，无机制参数"""
    global_config: GlobalConfig
    simulation: SimulationConfig
    data_generation: DataGenerationConfig
    data_analysis: DataAnalysisConfig

# ===================== 合并配置（内部使用） =====================
class MergedConfig(BaseModel):
    """合并后的完整配置（内部使用，对外透明）"""
    game_type: str
    strategy: str
    global_config: GlobalConfig
    simulation: SimulationConfig
    data_generation: DataGenerationConfig
    data_analysis: DataAnalysisConfig
    mechanism: PoolConfig

    model_config = {"extra": "forbid"}

# ===================== 对外加载函数（双config分离） =====================
def load_config(pool_path: str | Path, run_path: str | Path) -> Dict[str, Any]:
    """
    加载并合并双配置（零兼容、零回退）
    Args:
        pool_path: 卡池配置文件路径
        run_path: 实验配置文件路径
    Returns:
        合并后的完整配置字典
    """
    try:
        with open(pool_path, "r", encoding="utf-8") as f:
            pool_raw = yaml.safe_load(f)
        pool_cfg = PoolConfig(**pool_raw)
        
        with open(run_path, "r", encoding="utf-8") as f:
            run_raw = yaml.safe_load(f)
        run_cfg = RunConfig(**run_raw)

        merged = MergedConfig(
            game_type=pool_cfg.game_type,
            strategy=pool_cfg.strategy,
            global_config=run_cfg.global_config,
            simulation=run_cfg.simulation,
            data_generation=run_cfg.data_generation,
            data_analysis=run_cfg.data_analysis,
            mechanism=pool_cfg
        )
        return merged.model_dump()

    except Exception as e:
        raise ValueError(f"配置加载失败：\n{e}") from e