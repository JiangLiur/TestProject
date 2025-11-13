#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据结构分析脚本 - 快速查看Excel表格结构
"""

import pandas as pd
import sys

def analyze_excel_structure(file_path, sheet_name, header_row=2):
    """分析Excel文件结构"""
    print(f"\n{'='*80}")
    print(f"分析: {file_path} - {sheet_name}")
    print(f"{'='*80}\n")

    try:
        # 读取Excel，指定表头行
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)

        # 去除首列如果是导航列
        if df.columns[0].startswith('!'):
            df = df.iloc[:, 1:]

        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n列名列表:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print(f"\n前5行数据预览:")
        print(df.head(5).to_string(max_colwidth=50))

        # 检查关键字段
        key_fields = ['SHORTCODE', 'SPECNAME', 'LONGMATERIALDESCRIPTION',
                     'SHORTMATERIALDESCRIPTION', 'PipeSizeString', 'Schedule_FormulaText',
                     'CONTRACTORCOMMODITYCODE', 'INDUSTRYCOMMODITYCODE']

        existing_keys = [k for k in key_fields if k in df.columns]
        if existing_keys:
            print(f"\n✓ 关键字段存在: {existing_keys}")

        # 检查SPECNAME唯一值
        if 'SPECNAME' in df.columns:
            specs = df['SPECNAME'].unique()
            print(f"\n等级列表 (SPECNAME): {len(specs)} 个")
            print(f"前10个等级: {list(specs[:10])}")

        # 检查SHORTCODE唯一值
        if 'SHORTCODE' in df.columns:
            shortcodes = df['SHORTCODE'].unique()
            print(f"\n管件类型 (SHORTCODE): {len(shortcodes)} 个")
            print(f"所有管件类型: {list(shortcodes[:20])}")

        print(f"\n{'-'*80}\n")

        return df

    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("开始分析 Smart3D 等级库数据结构")
    print("="*80)

    # 分析PCMCD表（最重要）
    print("\n\n【核心表1：PCMCD表 - 管件材料和尺寸描述】")
    pcmcd_df = analyze_excel_structure(
        'files/CatalogDataExtractor_PCMCD.xlsx',
        'PipingCommodityMatlControlData',
        header_row=2
    )

    # 分析PipingCommodityFilter表
    print("\n\n【核心表2：PipingCommodityFilter - 管件类型过滤器】")
    filter_df = analyze_excel_structure(
        'files/CatalogDataExtractor_PipingSpecRuleData.xlsx',
        'PipingCommodityFilter',
        header_row=2
    )

    # 分析PipingMaterialsClassData表
    print("\n\n【核心表3：PipingMaterialsClassData - 等级基本信息】")
    materials_df = analyze_excel_structure(
        'files/CatalogDataExtractor_PipingSpecRuleData.xlsx',
        'PipingMaterialsClassData',
        header_row=2
    )

    print("\n" + "="*80)
    print("分析完成")
    print("="*80)
