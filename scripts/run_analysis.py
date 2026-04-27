"""
独立运行分析脚本
仅读取数据，运行分析，保存结果
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from card_pool_analysis import DataIO, Analysis


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
    parser = argparse.ArgumentParser(description="运行分析")
    parser.add_argument(
        "--exp-dir", 
        type=Path, 
        required=True,
        help="实验独立文件夹路径"
    )
    args = parser.parse_args()
    
    exp_dir = args.exp_dir
    data_path = exp_dir / "data.parquet"
    meta_path = exp_dir / "meta.json"
    plots_dir = exp_dir / "plots"
    
    print("=" * 60)
    print("抽卡模拟分析项目 - 独立分析脚本")
    print("=" * 60)

    try:
        # 读取元数据获取配置
        logger.info("读取元数据...")
        meta = DataIO.read_meta(meta_path)
        config = meta["config"]
        
        # 确保plots目录存在
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取数据
        logger.info("读取数据...")
        df = DataIO.read_data(data_path)
        
        # 运行分析
        logger.info("运行分析...")
        analysis = Analysis(config, exp_dir, plots_dir)
        analysis_results = analysis.run(df)
        analysis_path = analysis.save(analysis_results)

        # 打印结果
        print("\n" + "=" * 60)
        print("分析完成")
        print("=" * 60)
        print(f"分析结果: {analysis_path}")
        print(f"可视化图片: {plots_dir}")
        print("=" * 60)
    except Exception as e:
        logger.error(f"分析失败: {str(e)}", exc_info=True)
        print(f"\n❌ 分析失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()