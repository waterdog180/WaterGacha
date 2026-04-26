"""
独立运行模拟脚本
仅运行模拟，保存数据到指定目录
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from card_pool_analysis import load_config, Simulator, DataIO
import plugins


def setup_logging():
    """初始化日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行抽卡模拟")
    parser.add_argument(
        "--pool-config", 
        type=Path, 
        default=Path("configs/pool.yaml"),
        help="卡池配置文件路径"
    )
    parser.add_argument(
        "--run-config", 
        type=Path, 
        default=Path("configs/run.yaml"),
        help="实验配置文件路径"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("抽卡模拟分析项目 - 独立模拟脚本")
    print("=" * 60)

    try:
        # 加载配置
        logger.info("加载配置...")
        config = load_config(args.pool_config, args.run_config)

        # 运行模拟
        logger.info("运行模拟...")
        simulator = Simulator(config)
        result_generator = simulator.run()

        # 保存数据
        logger.info("保存数据...")
        data_io = DataIO(config)
        data_path, meta_path, log_path = data_io.write(result_generator)

        # 打印结果
        print("\n" + "=" * 60)
        print("模拟完成")
        print("=" * 60)
        print(f"实验独立文件夹: {data_io.exp_dir}")
        print(f"实验日志: {log_path}")
        print(f"数据文件: {data_path}")
        print(f"元数据文件: {meta_path}")
        print("=" * 60)
        print("\n提示：使用以下命令运行分析：")
        print(f"python scripts/run_analysis.py --exp-dir {data_io.exp_dir}")

    except Exception as e:
        logger.error(f"模拟失败: {str(e)}", exc_info=True)
        print(f"\n❌ 模拟失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()