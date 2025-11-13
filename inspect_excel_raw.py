#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原始Excel数据检查
"""

import pandas as pd

print("="*80)
print("原始Excel数据检查 - PCMCD表")
print("="*80)

# 读取前20行，不指定表头
pcmcd_raw = pd.read_excel(
    'files/CatalogDataExtractor_PCMCD.xlsx',
    sheet_name='PipingCommodityMatlControlData',
    header=None,
    nrows=20
)

print(f"\n前20行原始数据:\n")
for idx, row in pcmcd_raw.iterrows():
    print(f"行{idx}: {list(row[:10])}")  # 只显示前10列

print("\n" + "="*80)
print("查找表头行...")
print("="*80)

# 查找包含"LONGMATERIALDESCRIPTION"的行
for idx, row in pcmcd_raw.iterrows():
    row_str = ' '.join([str(x) for x in row if pd.notna(x)])
    if 'LONG'in row_str.upper() or 'DESCRIPTION' in row_str.upper():
        print(f"\n找到可能的表头行 (索引{idx}):")
        print(f"前15列: {list(row[:15])}")
        break
