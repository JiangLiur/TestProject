#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查PCMCD表的实际数据
"""

import pandas as pd

# 读取PCMCD表 - 使用正确的方式
pcmcd_df = pd.read_excel(
    'files/CatalogDataExtractor_PCMCD.xlsx',
    sheet_name='PipingCommodityMatlControlData',
    header=2  # 第3行(索引2)是表头
)

# 过滤掉"Head"和"Start"行
pcmcd_df = pcmcd_df[~pcmcd_df.iloc[:, 0].isin(['Head', 'Start'])]

# 使用第一行作为列名
pcmcd_df.columns = pcmcd_df.iloc[0]
pcmcd_df = pcmcd_df[1:].reset_index(drop=True)

# 删除导航列
first_col = str(pcmcd_df.columns[0])
if first_col.startswith('!'):
    pcmcd_df = pcmcd_df.iloc[:, 1:]

print("="*80)
print("PCMCD表数据分析")
print("="*80)
print(f"\n总行数: {len(pcmcd_df)}")
print(f"总列数: {len(pcmcd_df.columns)}")

print(f"\n前10个列名:")
for i, col in enumerate(list(pcmcd_df.columns)[:10], 1):
    print(f"  {i}. {col}")

print(f"\n前5行数据:")
print(pcmcd_df.head(5)[['CONTRACTORCOMMODITYCODE', 'SHORTMATERIALDESCRIPTION', 'LONGMATERIALDESCRIPTION']].to_string())

print(f"\n检查关键字段...")
key_fields = ['CONTRACTORCOMMODITYCODE', 'SHORTMATERIALDESCRIPTION', 'LONGMATERIALDESCRIPTION']
for field in key_fields:
    if field in pcmcd_df.columns:
        non_null = pcmcd_df[field].notna().sum()
        print(f"✓ {field}: {non_null}/{len(pcmcd_df)} 非空值")
    else:
        print(f"✗ {field}: 不存在")

# 查看长描述的样本
print(f"\n前10个LONGMATERIALDESCRIPTION样本:")
long_desc_samples = pcmcd_df['LONGMATERIALDESCRIPTION'].dropna().head(10)
for idx, desc in enumerate(long_desc_samples, 1):
    print(f"{idx}. {desc[:100] if len(str(desc)) > 100 else desc}")
