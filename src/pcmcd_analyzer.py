#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCMCD格式分析模块
通过分析PCMCD表中的LONGMATERIALDESCRIPTION字段，识别材料标准和尺寸标准在文本中的位置规律
"""

import pandas as pd
import re
import json
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

class PCMCDAnalyzer:
    """PCMCD表格式分析器"""

    def __init__(self, excel_path: str, sheet_name: str = 'PipingCommodityMatlControlData'):
        """
        初始化分析器

        Args:
            excel_path: Excel文件路径
            sheet_name: 工作表名称
        """
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.df = None
        self.format_rules = {}

    def load_data(self) -> pd.DataFrame:
        """加载PCMCD表数据"""
        logging.info(f"加载Excel文件: {self.excel_path}")

        try:
            # 读取Excel，表头在第4行（索引3）
            df = pd.read_excel(
                self.excel_path,
                sheet_name=self.sheet_name,
                header=3,  # 第4行是表头
                skiprows=[4]  # 跳过"Start"行
            )
        except FileNotFoundError:
            logging.error(f"文件不存在: {self.excel_path}")
            raise
        except ValueError as e:
            logging.error(f"工作表 '{self.sheet_name}' 不存在: {e}")
            raise
        except Exception as e:
            logging.error(f"读取Excel文件失败: {e}")
            raise

        # 删除导航列
        if len(df.columns) > 0 and str(df.columns[0]).startswith('!'):
            df = df.iloc[:, 1:]

        logging.info(f"成功加载 {len(df)} 行数据")
        self.df = df
        return df

    def analyze_format(self, num_rows: int = 622) -> Dict:
        """
        分析PCMCD表前N行的描述格式

        Args:
            num_rows: 分析的行数，默认622行

        Returns:
            格式统计字典
        """
        if self.df is None:
            self.load_data()

        logging.info(f"开始分析前 {num_rows} 行的格式规律...")

        format_stats = {}
        analyzed_count = 0

        # 遍历前num_rows行
        for idx, row in self.df.head(num_rows).iterrows():
            # 获取管件编码作为类型标识（CONTRACTORCOMMODITYCODE的前几位）
            commodity_code = row.get('CONTRACTORCOMMODITYCODE', '')

            # 获取描述字段
            long_desc = row.get('LONGMATERIALDESCRIPTION', '')
            short_desc = row.get('SHORTMATERIALDESCRIPTION', '')

            if pd.isna(long_desc) or not str(long_desc).strip():
                continue

            # 识别管件类型（从商品编码推断）
            # 这里简单使用商品编码的前几位作为类型标识
            shortcode = str(commodity_code)[:4] if pd.notna(commodity_code) else 'UNKNOWN'

            # 按逗号分割描述
            long_desc_str = str(long_desc)
            parts = [p.strip() for p in long_desc_str.split(',')]

            if len(parts) < 2:  # 描述太短，跳过
                continue

            # 初始化统计
            if shortcode not in format_stats:
                format_stats[shortcode] = {
                    'count': 0,
                    'material_positions': [],
                    'size_positions': [],
                    'examples': []
                }

            format_stats[shortcode]['count'] += 1
            if len(format_stats[shortcode]['examples']) < 3:  # 只保存前3个示例
                format_stats[shortcode]['examples'].append(long_desc_str)

            # 识别材料标准位置
            for i, part in enumerate(parts):
                # 材料标准特征：包含标准代码 + 材料牌号
                if re.search(r'\b(ASTM|ASME|GB|DIN|JIS|EN|ISO)\s+[A-Z0-9]+', part, re.IGNORECASE):
                    # 排除只包含标准规范的（如"ASME B16.9"）
                    if not re.search(r'B\d+\.\d+', part):
                        format_stats[shortcode]['material_positions'].append(i)

            # 识别尺寸标准位置
            for i, part in enumerate(parts):
                # 尺寸标准特征：壁厚标识或压力等级
                if re.search(r'\b(SCH\s*\d+|STD|XS|XXS|Class\s+\d+|PN\s*\d+|\d+LB|\[\d+\])', part, re.IGNORECASE):
                    format_stats[shortcode]['size_positions'].append(i)

            analyzed_count += 1

        logging.info(f"分析完成: 成功分析 {analyzed_count} 行数据")
        logging.info(f"发现 {len(format_stats)} 种管件类型")

        return format_stats

    def extract_dominant_positions(self, format_stats: Dict) -> Dict:
        """
        从统计数据中提取每种管件的主流位置

        Args:
            format_stats: 格式统计字典

        Returns:
            简化的格式规则字典
        """
        logging.info("提取主流位置规则...")

        format_rules = {}

        for shortcode, stats in format_stats.items():
            # 统计最常见的位置
            material_counter = Counter(stats['material_positions'])
            size_counter = Counter(stats['size_positions'])

            # 获取出现频率最高的位置
            material_pos = material_counter.most_common(1)[0][0] if material_counter else None
            material_count = material_counter.most_common(1)[0][1] if material_counter else 0

            size_pos = size_counter.most_common(1)[0][0] if size_counter else None
            size_count = size_counter.most_common(1)[0][1] if size_counter else 0

            # 计算置信度
            total_count = stats['count']
            material_confidence = material_count / total_count if total_count > 0 else 0
            size_confidence = size_count / total_count if total_count > 0 else 0

            format_rules[shortcode] = {
                'material_position': material_pos,
                'size_position': size_pos,
                'confidence': {
                    'material': material_confidence,
                    'size': size_confidence
                },
                'sample_count': total_count,
                'example': stats['examples'][0] if stats['examples'] else None
            }

        self.format_rules = format_rules
        logging.info(f"生成 {len(format_rules)} 个格式规则")

        return format_rules

    def generate_report(self, output_file: str = 'format_analysis_report.txt') -> None:
        """
        生成格式分析报告

        Args:
            output_file: 输出文件路径
        """
        if not self.format_rules:
            logging.warning("格式规则为空，请先运行analyze_format和extract_dominant_positions")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PCMCD表格式分析报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"分析数据源: {self.excel_path}\n")
            f.write(f"工作表: {self.sheet_name}\n")
            f.write(f"管件类型数量: {len(self.format_rules)}\n\n")

            # 按样本数量排序
            sorted_rules = sorted(
                self.format_rules.items(),
                key=lambda x: x[1]['sample_count'],
                reverse=True
            )

            for shortcode, rule in sorted_rules:
                f.write(f"\n【{shortcode}】\n")
                f.write(f"  样本数量: {rule['sample_count']}\n")
                f.write(f"  材料标准位置: {rule['material_position']} "
                       f"(置信度: {rule['confidence']['material']:.1%})\n")
                f.write(f"  尺寸标准位置: {rule['size_position']} "
                       f"(置信度: {rule['confidence']['size']:.1%})\n")

                if rule['example']:
                    f.write(f"  示例: {rule['example'][:100]}")
                    if len(rule['example']) > 100:
                        f.write("...")
                    f.write("\n")
                f.write("-" * 80 + "\n")

        logging.info(f"格式分析报告已生成: {output_file}")

    def save_format_rules(self, output_file: str = 'format_rules.json') -> None:
        """
        保存格式规则到JSON文件

        Args:
            output_file: 输出文件路径
        """
        if not self.format_rules:
            logging.warning("格式规则为空，请先运行analyze_format和extract_dominant_positions")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.format_rules, f, indent=2, ensure_ascii=False)

        logging.info(f"格式规则已保存: {output_file}")

    def run_full_analysis(self, num_rows: int = 622) -> Dict:
        """
        运行完整分析流程

        Args:
            num_rows: 分析的行数

        Returns:
            格式规则字典
        """
        # 1. 加载数据
        self.load_data()

        # 2. 分析格式
        format_stats = self.analyze_format(num_rows)

        # 3. 提取主流位置
        format_rules = self.extract_dominant_positions(format_stats)

        # 4. 生成报告
        self.generate_report()

        # 5. 保存规则
        self.save_format_rules()

        return format_rules


def main():
    """主函数 - 用于测试"""
    print("\n" + "="*80)
    print("PCMCD格式分析工具")
    print("="*80 + "\n")

    # 创建分析器
    analyzer = PCMCDAnalyzer('files/CatalogDataExtractor_PCMCD.xlsx')

    # 运行完整分析
    format_rules = analyzer.run_full_analysis(num_rows=622)

    print("\n分析完成！")
    print(f"- 格式规则: format_rules.json")
    print(f"- 分析报告: format_analysis_report.txt")
    print(f"- 发现 {len(format_rules)} 种管件类型\n")


if __name__ == "__main__":
    main()
