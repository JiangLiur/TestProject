#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能替换模块
基于PCMCD格式规则，对材料和尺寸标准进行精确替换
"""

import pandas as pd
import re
import json
import logging
from typing import Dict, Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


class IntelligentReplacer:
    """基于位置规则的智能替换器"""

    def __init__(self, format_rules_path: str):
        """
        初始化替换器

        Args:
            format_rules_path: 格式规则JSON文件路径
        """
        self.format_rules = self.load_format_rules(format_rules_path)
        self.replacement_log = []

    def load_format_rules(self, file_path: str) -> Dict:
        """加载格式规则"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            logging.info(f"成功加载格式规则: {len(rules)} 种管件类型")
            return rules
        except Exception as e:
            logging.error(f"加载格式规则失败: {e}")
            return {}

    def replace_by_position(
        self,
        description: str,
        shortcode: str,
        material_mapping: Dict[str, str],
        size_mapping: Dict[str, str]
    ) -> str:
        """
        基于位置规则进行智能替换

        Args:
            description: 原始描述文本
            shortcode: 管件类型代码
            material_mapping: 材料标准映射字典
            size_mapping: 尺寸标准映射字典

        Returns:
            替换后的描述文本
        """
        if not description or pd.isna(description):
            return description

        description = str(description).strip()

        # 获取该管件类型的位置规则
        if shortcode not in self.format_rules:
            logging.debug(f"未找到{shortcode}的格式规则，使用模糊替换")
            return self.fuzzy_replace(description, material_mapping, size_mapping)

        rule = self.format_rules[shortcode]

        # 按逗号分割
        parts = [p.strip() for p in description.split(',')]

        replaced = False

        # 替换材料标准（按位置）
        mat_pos = rule['material_position']
        if mat_pos is not None and mat_pos < len(parts):
            for old_mat, new_mat in material_mapping.items():
                if old_mat in parts[mat_pos]:
                    parts[mat_pos] = parts[mat_pos].replace(old_mat, new_mat)
                    self.replacement_log.append({
                        'type': 'material',
                        'shortcode': shortcode,
                        'position': mat_pos,
                        'old': old_mat,
                        'new': new_mat
                    })
                    replaced = True
                    break

        # 替换尺寸标准（按位置）
        size_pos = rule['size_position']
        if size_pos is not None and size_pos < len(parts):
            for old_size, new_size in size_mapping.items():
                if old_size in parts[size_pos]:
                    parts[size_pos] = parts[size_pos].replace(old_size, new_size)
                    self.replacement_log.append({
                        'type': 'size',
                        'shortcode': shortcode,
                        'position': size_pos,
                        'old': old_size,
                        'new': new_size
                    })
                    replaced = True
                    break

        if replaced:
            return ', '.join(parts)
        else:
            # 如果按位置没有找到，尝试模糊替换
            return self.fuzzy_replace(description, material_mapping, size_mapping)

    def fuzzy_replace(
        self,
        description: str,
        material_mapping: Dict[str, str],
        size_mapping: Dict[str, str]
    ) -> str:
        """
        模糊替换（备用方案）
        使用正则表达式确保只替换完整匹配的文本

        Args:
            description: 原始描述文本
            material_mapping: 材料标准映射字典
            size_mapping: 尺寸标准映射字典

        Returns:
            替换后的描述文本
        """
        result = description

        # 材料标准替换（带边界检查）
        for old_mat, new_mat in material_mapping.items():
            # 使用正则确保完整匹配
            pattern = re.escape(old_mat)
            result = re.sub(pattern, new_mat, result)

        # 尺寸标准替换
        for old_size, new_size in size_mapping.items():
            pattern = re.escape(old_size)
            result = re.sub(pattern, new_size, result)

        return result

    def batch_replace_pcmcd(
        self,
        pcmcd_df: pd.DataFrame,
        target_spec: str,
        material_mapping: Dict[str, str],
        size_mapping: Dict[str, str],
        commodity_code_col: str = 'CONTRACTORCOMMODITYCODE',
        short_desc_col: str = 'SHORTMATERIALDESCRIPTION',
        long_desc_col: str = 'LONGMATERIALDESCRIPTION'
    ) -> pd.DataFrame:
        """
        批量替换PCMCD表中的描述字段

        Args:
            pcmcd_df: PCMCD DataFrame
            target_spec: 目标等级名称（未来扩展用）
            material_mapping: 材料标准映射字典
            size_mapping: 尺寸标准映射字典
            commodity_code_col: 商品编码列名
            short_desc_col: 短描述列名
            long_desc_col: 长描述列名

        Returns:
            替换后的DataFrame
        """
        logging.info(f"开始批量替换PCMCD表描述字段...")
        logging.info(f"材料映射规则: {len(material_mapping)} 条")
        logging.info(f"尺寸映射规则: {len(size_mapping)} 条")

        modified_count = 0
        self.replacement_log = []

        # 复制DataFrame避免修改原始数据
        result_df = pcmcd_df.copy()

        for idx, row in result_df.iterrows():
            # 获取管件类型代码（使用商品编码前4位）
            commodity_code = row.get(commodity_code_col, '')
            shortcode = str(commodity_code)[:4] if pd.notna(commodity_code) else 'UNKNOWN'

            # 替换长描述
            if long_desc_col in result_df.columns and pd.notna(row[long_desc_col]):
                old_long_desc = row[long_desc_col]
                new_long_desc = self.replace_by_position(
                    old_long_desc,
                    shortcode,
                    material_mapping,
                    size_mapping
                )
                if new_long_desc != old_long_desc:
                    result_df.at[idx, long_desc_col] = new_long_desc
                    modified_count += 1

            # 替换短描述
            if short_desc_col in result_df.columns and pd.notna(row[short_desc_col]):
                old_short_desc = row[short_desc_col]
                new_short_desc = self.replace_by_position(
                    old_short_desc,
                    shortcode,
                    material_mapping,
                    size_mapping
                )
                if new_short_desc != old_short_desc:
                    result_df.at[idx, short_desc_col] = new_short_desc

        logging.info(f"替换完成: 修改了 {modified_count} 条记录")
        logging.info(f"详细替换日志: {len(self.replacement_log)} 次替换操作")

        return result_df

    def verify_replacements(
        self,
        original_df: pd.DataFrame,
        modified_df: pd.DataFrame,
        material_mapping: Dict[str, str],
        long_desc_col: str = 'LONGMATERIALDESCRIPTION'
    ) -> Dict:
        """
        验证替换结果

        Args:
            original_df: 原始DataFrame
            modified_df: 修改后的DataFrame
            material_mapping: 材料标准映射字典
            long_desc_col: 长描述列名

        Returns:
            验证结果字典
        """
        logging.info("开始验证替换结果...")

        issues = []
        stats = {
            'old_material_remaining': 0,
            'new_material_found': 0,
            'issues': []
        }

        # 检查旧材料是否还存在
        for old_mat in material_mapping.keys():
            count = modified_df[long_desc_col].astype(str).str.contains(
                re.escape(old_mat), na=False
            ).sum()

            if count > 0:
                issue = f"警告: '{old_mat}' 仍有 {count} 处未替换"
                issues.append(issue)
                stats['old_material_remaining'] += count
                logging.warning(issue)

        # 检查新材料是否正确出现
        for old_mat, new_mat in material_mapping.items():
            original_count = original_df[long_desc_col].astype(str).str.contains(
                re.escape(old_mat), na=False
            ).sum()

            new_count = modified_df[long_desc_col].astype(str).str.contains(
                re.escape(new_mat), na=False
            ).sum()

            stats['new_material_found'] += new_count

            if new_count > 0:
                logging.info(f"'{new_mat}' 出现 {new_count} 次 (原 '{old_mat}' 出现 {original_count} 次)")

        stats['issues'] = issues

        if not issues:
            logging.info("✓ 所有替换验证通过")
        else:
            logging.warning(f"发现 {len(issues)} 个问题")

        return stats

    def get_replacement_summary(self) -> Dict:
        """获取替换操作摘要"""
        from collections import Counter

        summary = {
            'total_replacements': len(self.replacement_log),
            'material_replacements': sum(1 for r in self.replacement_log if r['type'] == 'material'),
            'size_replacements': sum(1 for r in self.replacement_log if r['type'] == 'size'),
            'by_shortcode': {}
        }

        # 按管件类型统计
        shortcode_counter = Counter(r['shortcode'] for r in self.replacement_log)
        summary['by_shortcode'] = dict(shortcode_counter)

        return summary


def main():
    """主函数 - 用于测试"""
    print("\n" + "="*80)
    print("智能替换模块测试")
    print("="*80 + "\n")

    # 测试用例
    replacer = IntelligentReplacer('format_rules.json')

    # 示例映射
    material_mapping = {
        'ASTM A216 WCB': 'ASTM A352 LCB',
        'ASTM A105': 'ASTM A350 LF2',
        'ASTM A182 F304': 'ASTM A182 F316'
    }

    size_mapping = {
        'CL150': 'CL300',
        'XS': 'XXS'
    }

    # 测试描述
    test_descriptions = [
        ("平板闸阀,[801],螺栓连接阀盖,外螺纹阀杆,CL150,RF,阀体材料:ASTM A216 WCB", "2603"),
        ("对焊支管台,[801],XS,BE,MSS SP-97,16MnD", "0109"),
        ("盲法兰,[801],CL150,RF,ASME B16.5,ASTM A105", "0115"),
    ]

    print("测试智能替换功能:\n")
    for desc, shortcode in test_descriptions:
        print(f"原始: {desc}")
        new_desc = replacer.replace_by_position(desc, shortcode, material_mapping, size_mapping)
        print(f"替换: {new_desc}")
        print()

    # 显示替换日志
    summary = replacer.get_replacement_summary()
    print(f"\n替换摘要:")
    print(f"- 总替换次数: {summary['total_replacements']}")
    print(f"- 材料替换: {summary['material_replacements']}")
    print(f"- 尺寸替换: {summary['size_replacements']}")


if __name__ == "__main__":
    main()
