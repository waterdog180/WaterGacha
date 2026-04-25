"""
唯一入口（规范版）
显式导入插件，确保它们被注册
"""
from pathlib import Path
import logging
from card_pool_analysis import load_config, Simulator, DataIO, Analysis
import plugins  # 显式导入插件包，确保所有插件被注册

# ========== 快速切换配置（仅改这两行） ==========
POOL_CONFIG = Path("configs/pool.yaml")
RUN_CONFIG = Path("configs/run.yaml")
# ==================================================

def setup_logging():
    """初始化日志系统（中文输出）"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("抽卡模拟分析项目（阶段2：插件化架构）")
    print("=" * 60)

    try:
        # 1. 加载配置
        logger.info("\n[1/4] 加载配置...")
        config = load_config(POOL_CONFIG, RUN_CONFIG)

        # 2. 运行模拟
        logger.info("\n[2/4] 运行模拟...")
        simulator = Simulator(config)
        result_generator = simulator.run()

        # 3. 保存数据+元数据+日志
        logger.info("\n[3/4] 保存数据...")
        data_io = DataIO(config)
        data_path, meta_path, log_path = data_io.write(result_generator)

        # 4. 运行分析+保存结果
        logger.info("\n[4/4] 运行分析...")
        df = data_io.read_data(data_path)
        analysis = Analysis(config)
        analysis_results = analysis.run(df)
        analysis_path = analysis.save(analysis_results, data_io.output_dir)

        # 打印关键结果
        print("\n" + "=" * 60)
        print("关键分析结果")
        print("=" * 60)
        if "basic_stats" in analysis_results["analyses"]:
            stats = analysis_results["analyses"]["basic_stats"]
            print(f"目标稀有度 [{config['data_analysis']['target_rarity']}] 平均抽卡次数: {stats['mean']:.1f}")
        if "conditional_prob" in analysis_results["analyses"]:
            cond = analysis_results["analyses"]["conditional_prob"]
            print(f"小保底歪率: {cond['small_pity_lose_rate']:.2%}")
        print("=" * 60)
        print(f"实验日志: {log_path}")
        print(f"数据文件: {data_path}")
        print(f"分析结果: {analysis_path}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"程序运行失败: {str(e)}", exc_info=True)
        print(f"\n❌ 程序运行失败: {str(e)}")
        print("详细错误信息请查看日志文件")
        exit(1)

if __name__ == "__main__":
    main()