"""
路径工具类模块
统一管理所有实验目录、文件路径，避免硬编码文件名
"""
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from .constants import (
    EXPERIMENT_DIR_FORMAT,
    TIMESTAMP_FORMAT,
    DEFAULT_EXPERIMENTS_BASE_DIR,
    DATA_FILENAME,
    META_FILENAME,
    LOG_FILENAME,
    ANALYSIS_FILENAME,
    PLOTS_DIRNAME
)

logger = logging.getLogger(__name__)


class PathManager:
    """
    路径管理器类
    统一管理实验目录、数据文件、元数据、日志、分析结果、图表路径
    """
    
    def __init__(
        self,
        base_dir: Path | str = DEFAULT_EXPERIMENTS_BASE_DIR,
        experiment_name: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        """
        初始化路径管理器
        
        Args:
            base_dir: 实验根目录
            experiment_name: 实验名称（可选，用于创建新实验）
            timestamp: 时间戳（可选，用于创建新实验，不提供则自动生成）
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果提供了实验名称，创建新实验目录
        if experiment_name:
            self.timestamp = timestamp or datetime.now().strftime(TIMESTAMP_FORMAT)
            self.experiment_name = experiment_name
            self.experiment_dir = self.base_dir / EXPERIMENT_DIR_FORMAT.format(
                timestamp=self.timestamp,
                experiment_name=experiment_name
            )
            self._create_experiment_dir()
        else:
            # 未提供实验名称，用于加载已有实验
            self.experiment_dir = None
            self.timestamp = None
            self.experiment_name = None
    
    def _create_experiment_dir(self) -> None:
        """创建实验目录和子目录"""
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"实验目录已创建: {self.experiment_dir}")
    
    def load_existing(self, experiment_dir: Path | str) -> "PathManager":
        """
        加载已有实验目录
        
        Args:
            experiment_dir: 已有实验目录路径
        
        Returns:
            路径管理器实例（支持链式调用）
        """
        self.experiment_dir = Path(experiment_dir)
        if not self.experiment_dir.exists():
            raise FileNotFoundError(f"实验目录不存在: {self.experiment_dir}")
        
        # 从目录名解析时间戳和实验名称
        dir_name = self.experiment_dir.name
        if "_" in dir_name and len(dir_name) >= 15:  # 20260426_123456_name
            self.timestamp = dir_name[:15]
            self.experiment_name = dir_name[16:]
        else:
            self.timestamp = None
            self.experiment_name = dir_name
        
        logger.info(f"已加载实验目录: {self.experiment_dir}")
        return self
    
    @property
    def data_path(self) -> Path:
        """数据文件路径"""
        if not self.experiment_dir:
            raise ValueError("未设置实验目录，请先创建或加载实验")
        return self.experiment_dir / DATA_FILENAME
    
    @property
    def meta_path(self) -> Path:
        """元数据文件路径"""
        if not self.experiment_dir:
            raise ValueError("未设置实验目录，请先创建或加载实验")
        return self.experiment_dir / META_FILENAME
    
    @property
    def log_path(self) -> Path:
        """日志文件路径"""
        if not self.experiment_dir:
            raise ValueError("未设置实验目录，请先创建或加载实验")
        return self.experiment_dir / LOG_FILENAME
    
    @property
    def analysis_path(self) -> Path:
        """分析结果文件路径"""
        if not self.experiment_dir:
            raise ValueError("未设置实验目录，请先创建或加载实验")
        return self.experiment_dir / ANALYSIS_FILENAME
    
    @property
    def plots_dir(self) -> Path:
        """可视化图片目录路径"""
        if not self.experiment_dir:
            raise ValueError("未设置实验目录，请先创建或加载实验")
        return self.experiment_dir / PLOTS_DIRNAME
    
    def get_plot_path(self, plot_name: str) -> Path:
        """
        获取可视化图片文件路径
        
        Args:
            plot_name: 图片名称（不含扩展名）
        
        Returns:
            图片文件路径
        """
        if not plot_name.endswith(".png"):
            plot_name = f"{plot_name}.png"
        return self.plots_dir / plot_name
    
    def __str__(self) -> str:
        if self.experiment_dir:
            return f"PathManager(experiment_dir={self.experiment_dir})"
        return "PathManager(uninitialized)"
    
    def __repr__(self) -> str:
        return self.__str__()