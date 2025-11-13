#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart3D等级库复制程序 - MVP版本
核心功能：基于PCMCD格式分析的智能材料和尺寸标准替换
"""

import pandas as pd
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# 添加当前目录到sys.path
sys.path.insert(0, str(Path(__file__).parent))

from pcmcd_analyzer import PCMCDAnalyzer
from intelligent_replacer import IntelligentReplacer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)


class Smart3DGradeCopy:
    """Smart3D等级库复制主程序"""

    def __init__(self, config_path: str):
        """
        初始化

        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.analyzer = None
        self.replacer = None
        self.pcmcd_df = None

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info(f"成功加载配置文件: {config_path}")
            return config
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            sys.exit(1)

    def step1_analyze_pcmcd_format(self):
        """步骤1: 分析PCMCD表格式"""
        logging.info("\n" + "="*80)
        logging.info("步骤1: 分析PCMCD表格式")
        logging.info("="*80)

        pcmcd_file = self.config.get('pcmcd_file')
        analyze_rows = self.config.get('pcmcd_analysis', {}).get('analyze_rows', 622)

        # 创建分析器
        self.analyzer = PCMCDAnalyzer(pcmcd_file)

        # 运行分析
        format_rules = self.analyzer.run_full_analysis(num_rows=analyze_rows)

        logging.info(f"✓ 格式分析完成，发现 {len(format_rules)} 种管件类型")

    def step2_load_pcmcd_data(self):
        """步骤2: 加载PCMCD数据"""
        logging.info("\n" + "="*80)
        logging.info("步骤2: 加载PCMCD数据")
        logging.info("="*80)

        if self.analyzer is None:
            logging.error("请先运行step1_analyze_pcmcd_format")
            return

        self.pcmcd_df = self.analyzer.df
        logging.info(f"✓ 加载PCMCD数据: {len(self.pcmcd_df)} 行")

    def step3_apply_intelligent_replacement(self):
        """步骤3: 应用智能替换"""
        logging.info("\n" + "="*80)
        logging.info("步骤3: 应用智能材料和尺寸标准替换")
        logging.info("="*80)

        if self.pcmcd_df is None:
            logging.error("请先运行step2_load_pcmcd_data")
            return

        # 创建替换器
        format_rules_file = self.config.get('format_rules_file', 'format_rules.json')
        self.replacer = IntelligentReplacer(format_rules_file)

        # 获取映射规则
        material_mapping = self.config.get('material_replacements', {})
        size_mapping = self.config.get('size_standard_replacements', {})

        logging.info(f"材料标准映射规则: {len(material_mapping)} 条")
        for old, new in material_mapping.items():
            logging.info(f"  {old} → {new}")

        logging.info(f"尺寸标准映射规则: {len(size_mapping)} 条")
        for old, new in size_mapping.items():
            logging.info(f"  {old} → {new}")

        # 备份原始数据
        original_pcmcd_df = self.pcmcd_df.copy()

        # 执行替换
        target_spec = self.config.get('target_grade', '')
        self.pcmcd_df = self.replacer.batch_replace_pcmcd(
            self.pcmcd_df,
            target_spec,
            material_mapping,
            size_mapping
        )

        # 验证替换结果
        logging.info("\n验证替换结果...")
        verification_stats = self.replacer.verify_replacements(
            original_pcmcd_df,
            self.pcmcd_df,
            material_mapping
        )

        # 显示替换摘要
        summary = self.replacer.get_replacement_summary()
        logging.info(f"\n替换摘要:")
        logging.info(f"  总替换次数: {summary['total_replacements']}")
        logging.info(f"  材料替换: {summary['material_replacements']}")
        logging.info(f"  尺寸替换: {summary['size_replacements']}")

        if summary['by_shortcode']:
            logging.info(f"  按管件类型统计:")
            for shortcode, count in sorted(summary['by_shortcode'].items(), key=lambda x: x[1], reverse=True)[:10]:
                logging.info(f"    {shortcode}: {count} 次")

        logging.info(f"✓ 智能替换完成")

    def step4_export_results(self):
        """步骤4: 导出结果"""
        logging.info("\n" + "="*80)
        logging.info("步骤4: 导出结果")
        logging.info("="*80)

        if self.pcmcd_df is None:
            logging.error("没有可导出的数据")
            return

        output_file = self.config.get('output_file', 'output/PCMCD_modified.xlsx')

        # 创建输出目录
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 导出Excel
        logging.info(f"导出修改后的PCMCD表到: {output_file}")

        # 恢复原始Excel格式（添加导航列和表头行）
        export_df = self.pcmcd_df.copy()

        # 简单导出（实际应用中需要恢复完整的Excel格式）
        export_df.to_excel(output_file, sheet_name='PipingCommodityMatlControlData', index=False)

        logging.info(f"✓ 导出完成")

        # 生成操作报告
        report_file = output_path.parent / 'replacement_report.txt'
        self.generate_report(str(report_file))

    def generate_report(self, report_file: str):
        """生成替换操作报告"""
        if self.replacer is None:
            return

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("Smart3D等级库复制 - 替换操作报告\n")
            f.write("="*80 + "\n\n")

            # 配置信息
            f.write("配置信息:\n")
            f.write(f"  源等级: {self.config.get('source_grade', 'N/A')}\n")
            f.write(f"  目标等级: {self.config.get('target_grade', 'N/A')}\n")
            f.write(f"  PCMCD文件: {self.config.get('pcmcd_file', 'N/A')}\n")
            f.write("\n")

            # 替换规则
            f.write("材料标准替换规则:\n")
            for old, new in self.config.get('material_replacements', {}).items():
                f.write(f"  {old} → {new}\n")
            f.write("\n")

            f.write("尺寸标准替换规则:\n")
            for old, new in self.config.get('size_standard_replacements', {}).items():
                f.write(f"  {old} → {new}\n")
            f.write("\n")

            # 替换摘要
            summary = self.replacer.get_replacement_summary()
            f.write("替换摘要:\n")
            f.write(f"  总替换次数: {summary['total_replacements']}\n")
            f.write(f"  材料替换: {summary['material_replacements']}\n")
            f.write(f"  尺寸替换: {summary['size_replacements']}\n")
            f.write("\n")

            # 详细日志
            f.write("详细替换日志:\n")
            f.write("-"*80 + "\n")
            for i, log in enumerate(self.replacer.replacement_log[:100], 1):  # 只显示前100条
                f.write(f"{i}. [{log['shortcode']}] 位置{log['position']}: "
                       f"{log['old']} → {log['new']} ({log['type']})\n")

            if len(self.replacer.replacement_log) > 100:
                f.write(f"... (还有 {len(self.replacer.replacement_log) - 100} 条记录)\n")

        logging.info(f"替换报告已生成: {report_file}")

    def run(self):
        """运行完整流程"""
        logging.info("\n" + "="*80)
        logging.info("Smart3D等级库复制程序 - MVP版本")
        logging.info("="*80)
        logging.info(f"核心功能: 基于PCMCD格式分析的智能替换\n")

        try:
            # 运行所有步骤
            self.step1_analyze_pcmcd_format()
            self.step2_load_pcmcd_data()
            self.step3_apply_intelligent_replacement()
            self.step4_export_results()

            logging.info("\n" + "="*80)
            logging.info("✓ 程序执行完成")
            logging.info("="*80 + "\n")

        except Exception as e:
            logging.error(f"程序执行出错: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python smart3d_grade_copy.py <配置文件路径>")
        print("示例: python smart3d_grade_copy.py config.json")
        sys.exit(1)

    config_path = sys.argv[1]
    program = Smart3DGradeCopy(config_path)
    program.run()


if __name__ == "__main__":
    main()
