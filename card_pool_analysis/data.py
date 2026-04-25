"""
数据模块（微调版）
仅调整导入，其他功能保持不变
"""
from pathlib import Path
from typing import Generator, List, Dict, Any
import json
import logging
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from .schemas import DrawResult  # 仅调整导入

logger = logging.getLogger(__name__)

# ========== 极简数据生成器 ==========
class DataGenerator:
    @staticmethod
    def to_dataframe(results: List[DrawResult]) -> pd.DataFrame:
        records = []
        for r in results:
            record = {
                "sim_id": r.sim_id, "pull_id": r.pull_id, "rarity": r.rarity,
                "base_prob": r.base_prob, "actual_prob": r.actual_prob,
                "pity_triggered": r.pity_triggered, "is_up": r.is_up,
                "guarantee_triggered": r.guarantee_triggered,
                "pity_count": r.pity_count,
                "global_seed": r.seed_chain[0], "round_seed": r.seed_chain[1],
                "pull_seed": r.seed_chain[2]
            }
            if r.extended:
                record.update(r.extended)
            records.append(record)
        return pd.DataFrame(records)

# ========== 极简数据持久化（数据+元数据分离） ==========
class DataIO:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config["data_generation"]["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = config["data_generation"].get("chunk_size", 100000)
        logger.info(f"数据持久化初始化：分块大小={self.chunk_size}")

    def _get_git_hash(self) -> str | None:
        try:
            import subprocess
            return subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=Path(__file__).parent.parent,
                text=True
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _generate_paths(self) -> tuple[Path, Path, Path]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_name = self.config["global"]["experiment_name"]
        return (
            self.output_dir / f"{timestamp}_{exp_name}.parquet",
            self.output_dir / f"{timestamp}_{exp_name}_meta.json",
            self.output_dir / f"{timestamp}_{exp_name}.log"
        )

    def write(self, result_generator: Generator[DrawResult, None, None]) -> tuple[Path, Path, Path]:
        data_path, meta_path, log_path = self._generate_paths()
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)
        logger.info(f"实验日志已保存到: {log_path}")

        try:
            meta = {
                "timestamp": datetime.now().isoformat(),
                "experiment_name": self.config["global"]["experiment_name"],
                "git_hash": self._get_git_hash(),
                "config": self.config
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            logger.info(f"元数据已保存到: {meta_path}")

            chunk: List[DrawResult] = []
            writer = None
            total_written = 0

            for result in result_generator:
                chunk.append(result)
                if len(chunk) >= self.chunk_size:
                    df = DataGenerator.to_dataframe(chunk)
                    table = pa.Table.from_pandas(df, preserve_index=False)
                    if not writer:
                        writer = pq.ParquetWriter(data_path, table.schema, compression="snappy")
                    writer.write_table(table)
                    total_written += len(chunk)
                    logger.info(f"已写入 {total_written} 条记录")
                    chunk = []

            if chunk:
                df = DataGenerator.to_dataframe(chunk)
                table = pa.Table.from_pandas(df, preserve_index=False)
                if not writer:
                    writer = pq.ParquetWriter(data_path, table.schema, compression="snappy")
                writer.write_table(table)
                total_written += len(chunk)

            if writer:
                writer.close()

            logger.info(f"数据写入完成，共 {total_written} 条记录")
            logger.info(f"数据文件已保存到: {data_path}")
            return data_path, meta_path, log_path

        except Exception as e:
            logger.error(f"数据写入失败: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def read_data(data_path: Path) -> pd.DataFrame:
        try:
            logger.info(f"正在读取数据: {data_path}")
            return pd.read_parquet(data_path, engine="pyarrow")
        except Exception as e:
            logger.error(f"数据读取失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"数据文件损坏或不存在: {data_path}") from e

    @staticmethod
    def read_meta(meta_path: Path) -> Dict[str, Any]:
        try:
            logger.info(f"正在读取元数据: {meta_path}")
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"元数据读取失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"元数据文件损坏或不存在: {meta_path}") from e