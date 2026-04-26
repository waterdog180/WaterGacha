"""
独立运行可视化脚本
仅读取数据和分析结果，生成可视化
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
    parser = argparse.ArgumentParser(description="生成可视化")
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
    analysis_path = exp_dir / "analysis.json"
    plots_dir = exp_dir / "plots"
    
    print("=" * 60)
    print("抽卡模拟分析项目 - 独立可视化脚本")
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

        # 读取分析结果
        logger.info("读取分析结果...")
        import json
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_results = json.load(f)

        # 生成可视化
        logger.info("生成可视化...")
        analysis = Analysis(config, exp_dir, plots_dir)
        
        # 手动调用可视化方法
        two_d_results = analysis_results["analyses"].get("two_dimensional")
        cl_results = analysis_results["analyses"].get("consecutive_lose")
        ci_results = analysis_results["analyses"].get("confidence_interval")
        wfp_results = analysis_results["analyses"].get("weapon_fate_point")
        
        if "distribution" in config["data_analysis"]["enabled"]:
            analysis._visualize_1d(df, analysis_results)
        if two_d_results:
            analysis._visualize_2d(two_d_results)
        if cl_results:
            analysis._visualize_consecutive_lose(cl_results)
        if ci_results:
            analysis._visualize_confidence_interval(ci_results)
        if wfp_results:
            analysis._visualize_weapon_fate_point(wfp_results)

        # 打印结果
        print("\n" + "=" * 60)
        print("可视化完成")
        print("=" * 60)
        print(f"可视化图片: {plots_dir}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"可视化失败: {str(e)}", exc_info=True)
        print(f"\n❌ 可视化失败: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()