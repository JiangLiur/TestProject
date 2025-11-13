#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCMCD格式分析模块 V2 - 改进的SHORTCODE匹配
通过关联 PipingCommodityFilter 表获取精确的 SHORTCODE
"""

import pandas as pd
import re
import json
import logging
from collections import Counter
from typing import Dict, List, Tuple, Optional

from pcmcd_analyzer import PCMCDAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


class PCMCDAnalyzerV2(PCMCDAnalyzer):
    """PCMCD表格式分析器 V2 - 改进的SHORTCODE匹配"""

    def __init__(
        self,
        pcmcd_excel_path: str,
        spec_rule_excel_path: str,
        pcmcd_sheet_name: str = 'PipingCommodityMatlControlData',
        filter_sheet_name: str = 'PipingCommodityFilter'
    ):
        """
        初始化分析器

        Args:
            pcmcd_excel_path: PCMCD Excel文件路径
            spec_rule_excel_path: PipingSpecRuleData Excel文件路径
            pcmcd_sheet_name: PCMCD工作表名称
            filter_sheet_name: PipingCommodityFilter工作表名称
        """
        super().__init__(pcmcd_excel_path, pcmcd_sheet_name)
        self.spec_rule_excel_path = spec_rule_excel_path
        self.filter_sheet_name = filter_sheet_name
        self.commodity_filter_df = None
        self.commodity_code_to_shortcode = {}

    def load_commodity_filter(self) -> pd.DataFrame:
        """加载 PipingCommodityFilter 表"""
        logging.info(f"加载 PipingCommodityFilter 表...")

        # 读取Excel，表头在第4行（索引3）
        df = pd.read_excel(
            self.spec_rule_excel_path,
            sheet_name=self.filter_sheet_name,
            header=3,
            skiprows=[4]  # 跳过"Start"行
        )

        # 删除导航列
        if str(df.columns[0]).startswith('!'):
            df = df.iloc[:, 1:]

        logging.info(f"成功加载 {len(df)} 行数据")
        self.commodity_filter_df = df
        return df

    def build_commodity_code_mapping(self):
        """
        构建商品编码到SHORTCODE的映射

        从 PipingCommodityFilter 表中，通过 COMMODITYCODE 关联到 SHORTCODE
        """
        if self.commodity_filter_df is None:
            self.load_commodity_filter()

        logging.info("构建商品编码到SHORTCODE的映射...")

        mapping = {}
        for _, row in self.commodity_filter_df.iterrows():
            commodity_code = row.get('COMMODITYCODE', '')
            shortcode = row.get('SHORTCODE', '')

            if pd.notna(commodity_code) and pd.notna(shortcode):
                # 商品编码可能有多个SHORTCODE，取第一个
                if commodity_code not in mapping:
                    mapping[str(commodity_code)] = str(shortcode)

        self.commodity_code_to_shortcode = mapping
        logging.info(f"构建了 {len(mapping)} 个映射关系")

        return mapping

    def get_shortcode_from_commodity_code(self, commodity_code: str) -> Optional[str]:
        """
        从商品编码获取SHORTCODE

        Args:
            commodity_code: 商品编码 (CONTRACTORCOMMODITYCODE)

        Returns:
            SHORTCODE 或 None
        """
        if not commodity_code or pd.isna(commodity_code):
            return None

        # 首先尝试直接匹配完整编码
        if commodity_code in self.commodity_code_to_shortcode:
            return self.commodity_code_to_shortcode[commodity_code]

        # 如果没有找到，尝试前缀匹配（商品编码的前几位）
        commodity_code_str = str(commodity_code)
        for length in [24, 20, 16, 12, 8, 4]:  # 逐步缩短长度尝试匹配
            prefix = commodity_code_str[:length]
            if prefix in self.commodity_code_to_shortcode:
                return self.commodity_code_to_shortcode[prefix]

        return None

    def analyze_format(self, num_rows: int = 622) -> Dict:
        """
        分析PCMCD表前N行的描述格式（使用改进的SHORTCODE匹配）

        Args:
            num_rows: 分析的行数，默认622行

        Returns:
            格式统计字典
        """
        if self.df is None:
            self.load_data()

        if not self.commodity_code_to_shortcode:
            self.build_commodity_code_mapping()

        logging.info(f"开始分析前 {num_rows} 行的格式规律（使用SHORTCODE精确匹配）...")

        format_stats = {}
        analyzed_count = 0
        unknown_count = 0

        # 遍历前num_rows行
        for idx, row in self.df.head(num_rows).iterrows():
            # 获取商品编码
            commodity_code = row.get('CONTRACTORCOMMODITYCODE', '')

            # 通过商品编码获取SHORTCODE
            shortcode = self.get_shortcode_from_commodity_code(commodity_code)

            if not shortcode:
                shortcode = 'UNKNOWN'
                unknown_count += 1

            # 获取描述字段
            long_desc = row.get('LONGMATERIALDESCRIPTION', '')

            if pd.isna(long_desc) or not str(long_desc).strip():
                continue

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
        logging.info(f"发现 {len(format_stats)} 种管件类型（SHORTCODE）")
        if unknown_count > 0:
            logging.warning(f"有 {unknown_count} 行无法识别SHORTCODE")

        return format_stats


def main():
    """主函数 - 用于测试"""
    print("\n" + "="*80)
    print("PCMCD格式分析工具 V2 - 改进的SHORTCODE匹配")
    print("="*80 + "\n")

    # 创建分析器
    analyzer = PCMCDAnalyzerV2(
        'files/CatalogDataExtractor_PCMCD.xlsx',
        'files/CatalogDataExtractor_PipingSpecRuleData.xlsx'
    )

    # 运行完整分析
    format_rules = analyzer.run_full_analysis(num_rows=622)

    print("\n分析完成！")
    print(f"- 格式规则: format_rules.json")
    print(f"- 分析报告: format_analysis_report.txt")
    print(f"- 发现 {len(format_rules)} 种管件类型（使用SHORTCODE）\n")


if __name__ == "__main__":
    main()
