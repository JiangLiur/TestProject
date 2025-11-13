#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart3D等级库复制程序 - 完整版
包含等级复制、壁厚修改、SHORTCODE精确匹配和智能材料替换
"""

import pandas as pd
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# 添加当前目录到sys.path
sys.path.insert(0, str(Path(__file__).parent))

from pcmcd_analyzer_v2 import PCMCDAnalyzerV2
from intelligent_replacer import IntelligentReplacer
from grade_copier import GradeCopier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)


class Smart3DGradeCopyFull:
    """Smart3D等级库复制主程序 - 完整版"""

    def __init__(self, config_path: str):
        """
        初始化

        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.analyzer = None
        self.replacer = None
        self.copier = None
        self.pcmcd_df = None

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info(f"✓ 成功加载配置文件: {config_path}")
            return config
        except Exception as e:
            logging.error(f"✗ 加载配置文件失败: {e}")
            sys.exit(1)

    def step1_copy_grade_tables(self):
        """步骤1: 复制等级库相关表"""
        logging.info("\n" + "="*80)
        logging.info("步骤1: 复制等级库相关表")
        logging.info("="*80)

        source_grade = self.config.get('source_grade')
        target_grade = self.config.get('target_grade')
        spec_rule_file = self.config.get('spec_rule_file')
        schedule_mappings = self.config.get('schedule_mappings', [])

        if not all([source_grade, target_grade, spec_rule_file]):
            logging.error("配置文件缺少必要字段: source_grade, target_grade, spec_rule_file")
            return

        # 创建复制器
        self.copier = GradeCopier()
        self.copier.source_grade = source_grade
        self.copier.target_grade = target_grade

        # 复制 PipingMaterialsClassData（等级基本信息）
        self.copier.copy_piping_materials_class(
            spec_rule_file,
            source_grade,
            target_grade
        )

        # 复制 PipingCommodityFilter（管件类型过滤器）并应用壁厚映射
        self.copier.copy_piping_commodity_filter(
            spec_rule_file,
            source_grade,
            target_grade,
            schedule_mappings
        )

        logging.info(f"\n✓ 等级库表复制完成")

    def step2_analyze_pcmcd_format(self):
        """步骤2: 分析PCMCD表格式（使用SHORTCODE精确匹配）"""
        logging.info("\n" + "="*80)
        logging.info("步骤2: 分析PCMCD表格式（使用SHORTCODE精确匹配）")
        logging.info("="*80)

        pcmcd_file = self.config.get('pcmcd_file')
        spec_rule_file = self.config.get('spec_rule_file')
        analyze_rows = self.config.get('pcmcd_analysis', {}).get('analyze_rows', 622)

        # 创建分析器（V2版本，使用SHORTCODE）
        self.analyzer = PCMCDAnalyzerV2(pcmcd_file, spec_rule_file)

        # 运行分析
        format_rules = self.analyzer.run_full_analysis(num_rows=analyze_rows)

        logging.info(f"\n✓ 格式分析完成，发现 {len(format_rules)} 种管件类型（SHORTCODE）")

    def step3_load_pcmcd_data(self):
        """步骤3: 加载PCMCD数据"""
        logging.info("\n" + "="*80)
        logging.info("步骤3: 加载PCMCD数据")
        logging.info("="*80)

        if self.analyzer is None:
            logging.error("请先运行步骤2: 分析PCMCD表格式")
            return

        self.pcmcd_df = self.analyzer.df
        logging.info(f"✓ 加载PCMCD数据: {len(self.pcmcd_df)} 行")

    def step4_apply_intelligent_replacement(self):
        """步骤4: 应用智能替换"""
        logging.info("\n" + "="*80)
        logging.info("步骤4: 应用智能材料和尺寸标准替换")
        logging.info("="*80)

        if self.pcmcd_df is None:
            logging.error("请先运行步骤3: 加载PCMCD数据")
            return

        # 创建替换器，传入commodity_mapping以支持真实SHORTCODE匹配
        format_rules_file = self.config.get('format_rules_file', 'format_rules.json')
        commodity_mapping = self.analyzer.commodity_code_to_shortcode if self.analyzer else {}
        self.replacer = IntelligentReplacer(format_rules_file, commodity_mapping)

        # 获取映射规则
        material_mapping = self.config.get('material_replacements', {})
        size_mapping = self.config.get('size_standard_replacements', {})

        if not material_mapping and not size_mapping:
            logging.warning("未配置材料或尺寸标准映射规则")
            return

        logging.info(f"材料标准映射规则: {len(material_mapping)} 条")
        for old, new in list(material_mapping.items())[:5]:  # 只显示前5条
            logging.info(f"  {old} → {new}")
        if len(material_mapping) > 5:
            logging.info(f"  ... 还有 {len(material_mapping) - 5} 条")

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
            logging.info(f"  按管件类型统计（前10名）:")
            for shortcode, count in sorted(summary['by_shortcode'].items(), key=lambda x: x[1], reverse=True)[:10]:
                logging.info(f"    {shortcode}: {count} 次")

        logging.info(f"\n✓ 智能替换完成")

    def step5_export_results(self):
        """步骤5: 导出结果"""
        logging.info("\n" + "="*80)
        logging.info("步骤5: 导出结果")
        logging.info("="*80)

        output_dir = self.config.get('output_dir', 'output')
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 导出等级库相关表
        if self.copier and self.copier.tables:
            logging.info("导出等级库相关表...")
            self.copier.export_tables(output_dir)

            # 生成等级复制报告
            grade_report_file = output_path / 'grade_copy_report.txt'
            self.copier.generate_copy_report(str(grade_report_file))

        # 导出PCMCD表
        if self.pcmcd_df is not None:
            pcmcd_output_file = output_path / 'CatalogDataExtractor_PCMCD.xlsx'
            logging.info(f"导出修改后的PCMCD表: {pcmcd_output_file}")

            self.pcmcd_df.to_excel(
                pcmcd_output_file,
                sheet_name='PipingCommodityMatlControlData',
                index=False
            )

        # 生成替换操作报告
        if self.replacer:
            replacement_report_file = output_path / 'replacement_report.txt'
            self.generate_replacement_report(str(replacement_report_file))

        # 生成完整操作报告
        full_report_file = output_path / 'full_operation_report.txt'
        self.generate_full_report(str(full_report_file))

        logging.info(f"\n✓ 所有结果已导出到: {output_dir}")

    def generate_replacement_report(self, report_file: str):
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
            f.write(f"  目标等级: {self.config.get('target_grade', 'N/A')}\n\n")

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
            f.write(f"  尺寸替换: {summary['size_replacements']}\n\n")

            # 按管件类型统计
            if summary['by_shortcode']:
                f.write("按管件类型统计:\n")
                for shortcode, count in sorted(summary['by_shortcode'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {shortcode}: {count} 次\n")
                f.write("\n")

            # 详细日志
            f.write("详细替换日志（前100条）:\n")
            f.write("-"*80 + "\n")
            for i, log in enumerate(self.replacer.replacement_log[:100], 1):
                f.write(f"{i}. [{log['shortcode']}] 位置{log['position']}: "
                       f"{log['old']} → {log['new']} ({log['type']})\n")

            if len(self.replacer.replacement_log) > 100:
                f.write(f"... (还有 {len(self.replacer.replacement_log) - 100} 条记录)\n")

        logging.info(f"替换报告已生成: {report_file}")

    def generate_full_report(self, report_file: str):
        """生成完整操作报告"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("Smart3D等级库复制 - 完整操作报告\n")
            f.write("="*80 + "\n\n")

            f.write("程序版本: 完整版 v1.0\n")
            f.write("执行时间: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")

            # 配置信息
            f.write("配置信息:\n")
            f.write(f"  源等级: {self.config.get('source_grade')}\n")
            f.write(f"  目标等级: {self.config.get('target_grade')}\n")
            f.write(f"  PCMCD文件: {self.config.get('pcmcd_file')}\n")
            f.write(f"  规格规则文件: {self.config.get('spec_rule_file')}\n\n")

            # 等级复制统计
            f.write("步骤1: 等级库表复制\n")
            if self.copier and self.copier.tables:
                for table_name, df in self.copier.tables.items():
                    f.write(f"  {table_name}: {len(df)} 行\n")
            f.write("\n")

            # 壁厚修改统计
            schedule_mappings = self.config.get('schedule_mappings', [])
            if schedule_mappings:
                f.write("步骤1b: 壁厚修改\n")
                for mapping in schedule_mappings:
                    f.write(f"  {mapping.get('pipe_size')}: "
                           f"{mapping.get('old_schedule')} → {mapping.get('new_schedule')}\n")
                f.write("\n")

            # PCMCD格式分析统计
            f.write("步骤2: PCMCD格式分析\n")
            f.write(f"  分析行数: {self.config.get('pcmcd_analysis', {}).get('analyze_rows', 622)}\n")
            if self.analyzer and self.analyzer.format_rules:
                f.write(f"  发现管件类型: {len(self.analyzer.format_rules)} 种\n")
            f.write("\n")

            # 智能替换统计
            f.write("步骤4: 智能材料和尺寸标准替换\n")
            if self.replacer:
                summary = self.replacer.get_replacement_summary()
                f.write(f"  总替换次数: {summary['total_replacements']}\n")
                f.write(f"  材料替换: {summary['material_replacements']}\n")
                f.write(f"  尺寸替换: {summary['size_replacements']}\n")
            f.write("\n")

            # 输出文件清单
            output_dir = self.config.get('output_dir', 'output')
            f.write("输出文件:\n")
            f.write(f"  等级库表: {output_dir}/CatalogDataExtractor_PipingSpecRuleData.xlsx\n")
            f.write(f"  PCMCD表: {output_dir}/CatalogDataExtractor_PCMCD.xlsx\n")
            f.write(f"  等级复制报告: {output_dir}/grade_copy_report.txt\n")
            f.write(f"  替换操作报告: {output_dir}/replacement_report.txt\n")
            f.write(f"  完整操作报告: {output_dir}/full_operation_report.txt\n")

        logging.info(f"完整操作报告已生成: {report_file}")

    def run(self):
        """运行完整流程"""
        logging.info("\n" + "="*80)
        logging.info("Smart3D等级库复制程序 - 完整版 v1.0")
        logging.info("="*80)
        logging.info("功能: 等级复制 + 壁厚修改 + SHORTCODE匹配 + 智能替换\n")

        try:
            # 运行所有步骤
            self.step1_copy_grade_tables()
            self.step2_analyze_pcmcd_format()
            self.step3_load_pcmcd_data()
            self.step4_apply_intelligent_replacement()
            self.step5_export_results()

            logging.info("\n" + "="*80)
            logging.info("✓ 程序执行完成！")
            logging.info("="*80)
            logging.info(f"输出目录: {self.config.get('output_dir', 'output')}")
            logging.info("="*80 + "\n")

        except Exception as e:
            logging.error(f"\n✗ 程序执行出错: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python smart3d_grade_copy_full.py <配置文件路径>")
        print("示例: python smart3d_grade_copy_full.py config_full.json")
        sys.exit(1)

    config_path = sys.argv[1]
    program = Smart3DGradeCopyFull(config_path)
    program.run()


if __name__ == "__main__":
    main()
