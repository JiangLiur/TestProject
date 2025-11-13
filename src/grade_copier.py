#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
等级库复制模块
负责复制和修改 Smart3D 等级库相关表
"""

import pandas as pd
import logging
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


class GradeCopier:
    """等级库复制器"""

    def __init__(self):
        self.tables = {}
        self.source_grade = None
        self.target_grade = None

    def load_excel_table(
        self,
        file_path: str,
        sheet_name: str,
        header_row: int = 3,
        skip_start_row: bool = True
    ) -> pd.DataFrame:
        """
        加载Excel表格

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称
            header_row: 表头行索引
            skip_start_row: 是否跳过Start行

        Returns:
            DataFrame
        """
        logging.info(f"加载表: {sheet_name}")

        try:
            # 读取Excel
            skiprows = [header_row + 1] if skip_start_row else None
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header_row,
                skiprows=skiprows
            )
        except FileNotFoundError:
            logging.error(f"文件不存在: {file_path}")
            raise
        except ValueError as e:
            logging.error(f"工作表 '{sheet_name}' 不存在: {e}")
            raise
        except Exception as e:
            logging.error(f"读取Excel文件失败: {e}")
            raise

        # 删除导航列
        if len(df.columns) > 0 and str(df.columns[0]).startswith('!'):
            df = df.iloc[:, 1:]

        logging.info(f"  加载了 {len(df)} 行数据")
        return df

    def copy_piping_materials_class(
        self,
        file_path: str,
        source_grade: str,
        target_grade: str
    ) -> pd.DataFrame:
        """
        复制 PipingMaterialsClassData 表（等级基本信息）

        Args:
            file_path: Excel文件路径
            source_grade: 源等级名称
            target_grade: 目标等级名称

        Returns:
            包含新等级的DataFrame
        """
        logging.info(f"\n复制等级基本信息: {source_grade} → {target_grade}")

        # 加载表
        df = self.load_excel_table(
            file_path,
            'PipingMaterialsClassData'
        )

        # 查找源等级
        source_rows = df[df['SPECNAME'] == source_grade]

        if len(source_rows) == 0:
            logging.warning(f"未找到源等级: {source_grade}")
            return df

        logging.info(f"  找到源等级记录: {len(source_rows)} 条")

        # 检查目标等级是否已存在
        existing_target = df[df['SPECNAME'] == target_grade]
        if len(existing_target) > 0:
            logging.warning(f"  目标等级已存在，将跳过复制: {target_grade}")
            return df

        # 复制并修改等级名称
        new_rows = source_rows.copy()
        new_rows['SPECNAME'] = target_grade

        # 合并到原表
        result_df = pd.concat([df, new_rows], ignore_index=True)

        logging.info(f"  ✓ 复制完成，新增 {len(new_rows)} 条记录")

        self.tables['PipingMaterialsClassData'] = result_df
        return result_df

    def copy_piping_commodity_filter(
        self,
        file_path: str,
        source_grade: str,
        target_grade: str,
        schedule_mappings: Optional[List[Dict]] = None
    ) -> pd.DataFrame:
        """
        复制 PipingCommodityFilter 表（管件类型过滤器）

        Args:
            file_path: Excel文件路径
            source_grade: 源等级名称
            target_grade: 目标等级名称
            schedule_mappings: 壁厚映射配置列表

        Returns:
            包含新等级的DataFrame
        """
        logging.info(f"\n复制管件类型过滤器: {source_grade} → {target_grade}")

        # 加载表
        df = self.load_excel_table(
            file_path,
            'PipingCommodityFilter'
        )

        # 查找源等级
        source_rows = df[df['SPECNAME'] == source_grade]

        if len(source_rows) == 0:
            logging.warning(f"未找到源等级: {source_grade}")
            return df

        logging.info(f"  找到源等级记录: {len(source_rows)} 条")

        # 检查目标等级是否已存在
        existing_target = df[df['SPECNAME'] == target_grade]
        if len(existing_target) > 0:
            logging.warning(f"  目标等级已存在，将删除现有记录")
            df = df[df['SPECNAME'] != target_grade]

        # 复制并修改等级名称
        new_rows = source_rows.copy()
        new_rows['SPECNAME'] = target_grade

        # 如果有壁厚映射配置，应用壁厚修改
        if schedule_mappings:
            new_rows = self.apply_schedule_mappings(new_rows, schedule_mappings)

        # 合并到原表
        result_df = pd.concat([df, new_rows], ignore_index=True)

        logging.info(f"  ✓ 复制完成，新增 {len(new_rows)} 条记录")

        self.tables['PipingCommodityFilter'] = result_df
        return result_df

    def apply_schedule_mappings(
        self,
        df: pd.DataFrame,
        schedule_mappings: List[Dict]
    ) -> pd.DataFrame:
        """
        应用壁厚映射配置

        Args:
            df: DataFrame
            schedule_mappings: 壁厚映射配置列表
                [
                    {
                        "pipe_size": "DN50",
                        "old_schedule": "SCH40",
                        "new_schedule": "SCH80",
                        "shortcode": "Elbow"  # 可选
                    }
                ]

        Returns:
            修改后的DataFrame
        """
        if not schedule_mappings:
            return df

        logging.info(f"\n  应用壁厚映射配置: {len(schedule_mappings)} 条规则")

        modified_count = 0

        for mapping in schedule_mappings:
            pipe_size = mapping.get('pipe_size')
            old_schedule = mapping.get('old_schedule')
            new_schedule = mapping.get('new_schedule')
            shortcode = mapping.get('shortcode')  # 可选的管件类型

            if not all([pipe_size, old_schedule, new_schedule]):
                continue

            # 构建匹配条件
            conditions = (
                (df['FIRSTSIZEFROM'] == pipe_size) |
                (df['FIRSTSIZETO'] == pipe_size)
            )

            # 如果指定了SHORTCODE，添加到匹配条件
            if shortcode:
                conditions = conditions & (df['SHORTCODE'] == shortcode)

            # 找到匹配的行
            matched_rows = df[conditions]

            if len(matched_rows) == 0:
                logging.debug(f"    未找到匹配记录: pipe_size={pipe_size}, shortcode={shortcode}")
                continue

            # 修改壁厚
            row_modified_count = 0
            for idx in matched_rows.index:
                first_schedule = df.at[idx, 'FIRSTSIZESCHEDULE']
                second_schedule = df.at[idx, 'SECONDSIZESCHEDULE']

                # 修改第一尺寸壁厚
                if pd.notna(first_schedule):
                    if first_schedule == old_schedule:
                        df.at[idx, 'FIRSTSIZESCHEDULE'] = new_schedule
                        modified_count += 1
                        row_modified_count += 1
                    else:
                        logging.debug(f"      行{idx}: FIRSTSIZESCHEDULE={first_schedule} (期望{old_schedule}), 跳过")

                # 修改第二尺寸壁厚
                if pd.notna(second_schedule):
                    if second_schedule == old_schedule:
                        df.at[idx, 'SECONDSIZESCHEDULE'] = new_schedule
                        modified_count += 1
                        row_modified_count += 1
                    else:
                        logging.debug(f"      行{idx}: SECONDSIZESCHEDULE={second_schedule} (期望{old_schedule}), 跳过")

            shortcode_info = f" (SHORTCODE={shortcode})" if shortcode else ""
            logging.info(f"    {pipe_size}: {old_schedule} → {new_schedule}{shortcode_info}, 匹配{len(matched_rows)}条, 修改{row_modified_count}处")

        logging.info(f"  ✓ 壁厚修改完成，共修改 {modified_count} 处")

        return df

    def copy_pcmcd_table(
        self,
        file_path: str,
        source_grade: str,
        target_grade: str
    ) -> pd.DataFrame:
        """
        复制 PCMCD 表（管件材料和尺寸描述）

        注意：PCMCD表没有SPECNAME字段，这里只是为了保持接口一致性

        Args:
            file_path: Excel文件路径
            source_grade: 源等级名称（未使用）
            target_grade: 目标等级名称（未使用）

        Returns:
            DataFrame
        """
        logging.info(f"\n加载 PCMCD 表")

        # 加载表
        df = self.load_excel_table(
            file_path,
            'PipingCommodityMatlControlData'
        )

        logging.info(f"  加载了 {len(df)} 条记录")
        logging.info(f"  注意: PCMCD表不区分等级，将对所有记录应用智能替换")

        self.tables['PCMCD'] = df
        return df

    def export_tables(
        self,
        output_dir: str,
        base_filename: str = 'CatalogDataExtractor'
    ):
        """
        导出所有修改后的表到Excel文件

        Args:
            output_dir: 输出目录
            base_filename: 基础文件名
        """
        logging.info(f"\n导出修改后的表到: {output_dir}")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 导出 PipingSpecRuleData (包含 PipingCommodityFilter 和 PipingMaterialsClassData)
        if 'PipingCommodityFilter' in self.tables or 'PipingMaterialsClassData' in self.tables:
            spec_rule_file = output_path / f'{base_filename}_PipingSpecRuleData.xlsx'
            logging.info(f"  导出: {spec_rule_file.name}")

            with pd.ExcelWriter(spec_rule_file, engine='openpyxl') as writer:
                if 'PipingCommodityFilter' in self.tables:
                    self.tables['PipingCommodityFilter'].to_excel(
                        writer,
                        sheet_name='PipingCommodityFilter',
                        index=False
                    )

                if 'PipingMaterialsClassData' in self.tables:
                    self.tables['PipingMaterialsClassData'].to_excel(
                        writer,
                        sheet_name='PipingMaterialsClassData',
                        index=False
                    )

        # 导出 PCMCD
        if 'PCMCD' in self.tables:
            pcmcd_file = output_path / f'{base_filename}_PCMCD.xlsx'
            logging.info(f"  导出: {pcmcd_file.name}")

            self.tables['PCMCD'].to_excel(
                pcmcd_file,
                sheet_name='PipingCommodityMatlControlData',
                index=False
            )

        logging.info(f"  ✓ 导出完成")

    def generate_copy_report(self, output_file: str):
        """
        生成等级复制报告

        Args:
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("等级库复制报告\n")
            f.write("="*80 + "\n\n")

            f.write(f"源等级: {self.source_grade}\n")
            f.write(f"目标等级: {self.target_grade}\n\n")

            f.write("已处理的表:\n")
            for table_name, df in self.tables.items():
                f.write(f"  - {table_name}: {len(df)} 行\n")

            f.write("\n")

        logging.info(f"等级复制报告已生成: {output_file}")


def main():
    """主函数 - 用于测试"""
    print("\n" + "="*80)
    print("等级库复制模块测试")
    print("="*80 + "\n")

    # 创建复制器
    copier = GradeCopier()

    # 测试复制 PipingMaterialsClassData
    df1 = copier.copy_piping_materials_class(
        'files/CatalogDataExtractor_PipingSpecRuleData.xlsx',
        '1C0031',
        'TEST001'
    )

    print(f"\nPipingMaterialsClassData 表行数: {len(df1)}")

    # 测试复制 PipingCommodityFilter
    schedule_mappings = [
        {
            "pipe_size": 1.0,
            "old_schedule": "MATCH",
            "new_schedule": "SCH80"
        }
    ]

    df2 = copier.copy_piping_commodity_filter(
        'files/CatalogDataExtractor_PipingSpecRuleData.xlsx',
        '1C0031',
        'TEST001',
        schedule_mappings
    )

    print(f"PipingCommodityFilter 表行数: {len(df2)}")

    print("\n测试完成！")


if __name__ == "__main__":
    main()
