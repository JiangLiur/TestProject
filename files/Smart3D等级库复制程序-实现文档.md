# Smart3D等级库复制程序 - 完整实现文档 (修订版)

## 项目概述

本程序用于在Smart3D中复制现有等级库（如C1L01）并修改其中的壁厚和材料标准，生成新的等级库（如C1L02）。

## 核心功能

### 1. 复制等级库
- 复制源等级（如C1L01）的所有相关数据到新等级（如C1L02）
- 包括管道规格、管件、阀门等所有组件

### 2. 壁厚修改
- 根据配置文件，将指定管径的壁厚从旧值修改为新值
- 例如：DN50从SCH40改为SCH80

### 3. 材料标准智能替换（重要改进）
- **基于位置的智能替换策略**
- 通过分析PCMCD表中的材料描述格式，确定材料标准和尺寸标准的位置
- 按位置进行精确替换，而非简单的字符串查找替换

## 数据结构和关键字段

### 涉及的Excel表单

1. **PipingMaterialsSpec** - 等级基本信息
2. **PipingSpecRuleData** - 规格规则数据
3. **PipingSpecPart** - 具体管件零件数据
4. **PipingCommodityFilter** - 管件类型过滤器
5. **PCMCD表** - 管件材料和尺寸描述（关键表）

### 关键字段说明

#### 等级标识字段
- `Specname` / `SPECNAME`: 等级名称（如"C1L01"）
- 在所有表中作为主要过滤条件

#### 壁厚相关字段
- `PipeSizeString` / `PIPESIZESTRING`: 管径规格（如"DN50"）
- `NominalPipeSize`: 公称管径
- `Schedule_FormulaText`: 壁厚等级（如"SCH40", "SCH80"）

#### 材料描述字段（重点）
- `SHORTMATERIALDESCRIPTION`: 短材料描述
- `LONGMATERIALDESCRIPTION`: 长材料描述
- **这两个字段包含材料标准和尺寸标准信息**

#### SHORTCODE对应字段
- `PipingCommodityFilter`表中的`SHORTCODE`字段
- 与Part表中的`PipingComponentShortCode`字段对应
- 用于精确匹配管件类型（如弯头、三通等）

## 四个关键改进点

### 改进1: SHORTCODE列对应
**问题**: 只用PipeSizeString和Schedule无法精确定位Part表记录

**解决方案**: 
```
在PipingSpecRuleData的NominalPipeSizeAliasFilter子表中添加SHORTCODE列
- 弯头对应: "Elbow"
- 三通对应: "Tee" 
- 管帽对应: "Cap"
```

**实现逻辑**:
```python
# 定位Part表时的匹配条件
match_conditions = {
    'SPECNAME': new_grade,
    'PipeSizeString': pipe_size,
    'Schedule_FormulaText': old_schedule,  # 用旧壁厚
    'PipingComponentShortCode': shortcode   # 新增条件
}
```

### 改进2: 基于位置的智能材料替换（重大改进）

**原理说明**:

PCMCD表中的材料描述遵循固定格式，例如：
```
LONGMATERIALDESCRIPTION格式示例：
"Elbow, 90°, ASTM A234 WPB, Butt Weld, SCH40, ASME B16.9"
  ^管件类型  ^材料标准         ^连接方式  ^尺寸标准  ^尺寸标准规范

格式规律：
[管件类型], [规格信息], [材料标准], [连接方式], [尺寸标准], [标准规范]
```

**位置识别策略**:

通过分析PCMCD表前622行数据，可以发现：

1. **材料标准位置规律**：
   - 通常在管件类型后的第2-3个位置
   - 以"ASTM"、"ASME"等标准代码开头
   - 后跟材料牌号（如"A234 WPB"、"A105"）

2. **尺寸标准位置规律**：
   - 通常在描述后半部分
   - 包含"SCH"、"STD"、"XS"等壁厚标识
   - 或包含"Class"、"Pressure Rating"等压力等级

**实现方法**:

```python
def parse_material_description_format(pcmcd_table):
    """
    分析PCMCD表前622行，提取材料描述格式规律
    
    返回：每种管件类型的描述格式模板
    {
        'Elbow': {
            'material_position': 2,  # 材料标准在第几个逗号后
            'size_position': 4,      # 尺寸标准在第几个逗号后
            'material_pattern': r'ASTM\s+[A-Z0-9\s]+',  # 材料匹配正则
            'size_pattern': r'SCH\d+|STD|XS|XXS'        # 尺寸匹配正则
        },
        'Tee': {...},
        'Reducer': {...},
        ...
    }
    """
    format_rules = {}
    
    # 遍历PCMCD表前622行
    for index, row in pcmcd_table.head(622).iterrows():
        shortcode = row['SHORTCODE']
        long_desc = row['LONGMATERIALDESCRIPTION']
        
        if pd.isna(long_desc):
            continue
            
        # 按逗号分割描述
        parts = [p.strip() for p in long_desc.split(',')]
        
        # 识别材料标准位置
        material_pos = None
        for i, part in enumerate(parts):
            if re.search(r'ASTM|ASME|DIN|JIS|GB', part):
                material_pos = i
                break
        
        # 识别尺寸标准位置
        size_pos = None
        for i, part in enumerate(parts):
            if re.search(r'SCH|STD|XS|XXS|Class|Pressure', part):
                size_pos = i
                break
        
        # 记录格式规则
        if shortcode not in format_rules:
            format_rules[shortcode] = {
                'material_position': material_pos,
                'size_position': size_pos,
                'examples': []
            }
        
        format_rules[shortcode]['examples'].append(long_desc)
    
    return format_rules
```

**替换实现**:

```python
def replace_material_by_position(description, format_rule, material_mapping, size_mapping):
    """
    基于位置规则替换材料和尺寸标准
    
    参数:
        description: 原始描述文本
        format_rule: 该管件类型的格式规则
        material_mapping: 材料标准映射 {'ASTM A234 WPB': 'ASTM A420 WPL6'}
        size_mapping: 尺寸标准映射 {'SCH40': 'SCH80'}
    """
    parts = [p.strip() for p in description.split(',')]
    
    # 替换材料标准
    if format_rule['material_position'] is not None:
        mat_pos = format_rule['material_position']
        if mat_pos < len(parts):
            old_material = parts[mat_pos]
            # 查找匹配的材料映射
            for old_std, new_std in material_mapping.items():
                if old_std in old_material:
                    parts[mat_pos] = old_material.replace(old_std, new_std)
                    break
    
    # 替换尺寸标准
    if format_rule['size_position'] is not None:
        size_pos = format_rule['size_position']
        if size_pos < len(parts):
            old_size = parts[size_pos]
            # 查找匹配的尺寸映射
            for old_std, new_std in size_mapping.items():
                if old_std in old_size:
                    parts[size_pos] = old_size.replace(old_std, new_std)
                    break
    
    return ', '.join(parts)
```

**优势分析**:

1. **精确性高**：
   - 按位置替换，避免误替换描述中其他位置的相同文字
   - 例如："ASTM A105, Flanged, ASTM标准" 只替换第一个ASTM标准

2. **适应性强**：
   - 自动学习各种管件类型的描述格式
   - 支持不同长度和格式的描述文本

3. **可扩展**：
   - 容易添加新的管件类型
   - 支持自定义位置规则

### 改进3: 旧壁厚精确匹配
**问题**: 使用新壁厚查找Part表会找不到记录

**解决方案**: 
```
两步走策略
1. 用旧壁厚定位原有Part表记录
2. 修改Schedule_FormulaText为新壁厚
```

**关键代码逻辑**:
```python
# 第一步：用旧壁厚查找
old_parts = part_table[
    (part_table['SPECNAME'] == new_grade) &
    (part_table['PipeSizeString'] == 'DN50') &
    (part_table['Schedule_FormulaText'] == 'SCH40') &  # 旧壁厚
    (part_table['PipingComponentShortCode'] == 'Elbow')
]

# 第二步：修改为新壁厚
for index in old_parts.index:
    part_table.at[index, 'Schedule_FormulaText'] = 'SCH80'  # 新壁厚
```

### 改进4: 中文名称映射
**问题**: C1L01等级表用中文名称，但PipingCommodityFilter用英文SHORTCODE

**解决方案**: 
```
建立中英文对应表
- 弯头 → "Elbow"
- 三通 → "Tee"
- 异径管 → "Reducer"
- 管帽 → "Cap"
```

## 完整工作流程

### 步骤1: 分析PCMCD表格式
```python
# 读取PCMCD表
pcmcd_table = pd.read_excel('PipingSpecRuleData.xlsx', sheet_name='PCMCD')

# 分析前622行，提取格式规律
format_rules = parse_material_description_format(pcmcd_table.head(622))

# 保存格式规则供后续使用
with open('format_rules.json', 'w') as f:
    json.dump(format_rules, f, indent=2)
```

### 步骤2: 数据准备
1. 导出原始等级库Excel文件
2. 创建配置文件，定义壁厚映射和材料替换规则
3. 确认中文名称与SHORTCODE的对应关系

### 步骤3: 等级复制
```python
def copy_grade(source_grade, target_grade):
    """复制等级库"""
    # 复制所有相关表的记录
    tables = ['PipingMaterialsSpec', 'PipingSpecRuleData', 
              'PipingSpecPart', 'PCMCD']
    
    for table_name in tables:
        table = read_table(table_name)
        source_records = table[table['SPECNAME'] == source_grade]
        
        # 复制并修改等级名称
        new_records = source_records.copy()
        new_records['SPECNAME'] = target_grade
        
        # 追加到表中
        append_to_table(table_name, new_records)
```

### 步骤4: 壁厚修改
```python
for pipe_size, mapping in schedule_mappings.items():
    old_schedule = mapping['old']
    new_schedule = mapping['new']
    
    # 在NominalPipeSizeAliasFilter子表中查找
    filters = rule_data[
        (rule_data['SPECNAME'] == new_grade) &
        (rule_data['PipeSizeString'] == pipe_size)
    ]
    
    for filter_index in filters.index:
        # 获取对应的SHORTCODE
        shortcode = rule_data.at[filter_index, 'SHORTCODE']
        
        # 用旧壁厚+SHORTCODE定位Part表记录
        parts = part_table[
            (part_table['SPECNAME'] == new_grade) &
            (part_table['PipeSizeString'] == pipe_size) &
            (part_table['Schedule_FormulaText'] == old_schedule) &
            (part_table['PipingComponentShortCode'] == shortcode)
        ]
        
        # 修改为新壁厚
        for part_index in parts.index:
            part_table.at[part_index, 'Schedule_FormulaText'] = new_schedule
```

### 步骤5: 智能材料替换
```python
def intelligent_material_replacement(pcmcd_table, format_rules, material_mapping, size_mapping):
    """
    智能材料和尺寸标准替换
    """
    for index, row in pcmcd_table.iterrows():
        if row['SPECNAME'] != target_grade:
            continue
            
        shortcode = row['SHORTCODE']
        
        # 获取该管件类型的格式规则
        if shortcode not in format_rules:
            logging.warning(f"未找到{shortcode}的格式规则")
            continue
            
        format_rule = format_rules[shortcode]
        
        # 替换短描述
        if pd.notna(row['SHORTMATERIALDESCRIPTION']):
            new_short_desc = replace_material_by_position(
                row['SHORTMATERIALDESCRIPTION'],
                format_rule,
                material_mapping,
                size_mapping
            )
            pcmcd_table.at[index, 'SHORTMATERIALDESCRIPTION'] = new_short_desc
        
        # 替换长描述
        if pd.notna(row['LONGMATERIALDESCRIPTION']):
            new_long_desc = replace_material_by_position(
                row['LONGMATERIALDESCRIPTION'],
                format_rule,
                material_mapping,
                size_mapping
            )
            pcmcd_table.at[index, 'LONGMATERIALDESCRIPTION'] = new_long_desc
```

### 步骤6: 数据验证
```python
def validate_modifications():
    """验证修改结果"""
    
    # 1. 验证壁厚修改
    for pipe_size, mapping in schedule_mappings.items():
        old_count = count_records(pipe_size, mapping['old'])
        new_count = count_records(pipe_size, mapping['new'])
        assert old_count == 0, f"{pipe_size}仍有旧壁厚记录"
        assert new_count > 0, f"{pipe_size}新壁厚记录为空"
    
    # 2. 验证材料替换
    for old_mat, new_mat in material_mapping.items():
        old_mat_count = search_in_descriptions(old_mat)
        assert old_mat_count == 0, f"仍有{old_mat}未替换"
    
    # 3. 验证SHORTCODE匹配
    check_shortcode_consistency()
    
    # 4. 验证记录数量
    source_count = count_grade_records(source_grade)
    target_count = count_grade_records(target_grade)
    assert source_count == target_count, "记录数量不一致"
```

### 步骤7: 导出结果
1. 将修改后的数据写回Excel文件
2. 生成修改日志和报告
3. 导入Smart3D进行测试

## 配置文件格式

### config.json示例

```json
{
  "source_grade": "C1L01",
  "target_grade": "C1L02",
  
  "schedule_mappings": [
    {
      "pipe_size": "DN50",
      "old_schedule": "SCH40",
      "new_schedule": "SCH80"
    },
    {
      "pipe_size": "DN80",
      "old_schedule": "SCH40",
      "new_schedule": "SCH80"
    }
  ],
  
  "material_replacements": {
    "ASTM A105": "ASTM A350 LF2",
    "ASTM A234 WPB": "ASTM A420 WPL6",
    "ASTM A216 WCB": "ASTM A352 LCB"
  },
  
  "size_standard_replacements": {
    "SCH40": "SCH80",
    "SCH STD": "SCH 80"
  },
  
  "pcmcd_analysis": {
    "analyze_rows": 622,
    "export_format_rules": true,
    "format_rules_file": "format_rules.json"
  }
}
```

## 常见问题和注意事项

### Q1: 为什么需要分析PCMCD表格式？
**A**: 因为材料描述是自由文本，简单的字符串替换可能会误替换其他位置的文字。通过分析格式，可以精确定位材料标准和尺寸标准的位置。

### Q2: 如何处理格式不一致的描述？
**A**: 
1. 先分析主流格式（622行数据）
2. 对于特殊格式，使用正则表达式模糊匹配
3. 记录无法识别的格式，人工审核

### Q3: 材料替换会不会漏掉？
**A**: 基于位置的替换更精确，但需要：
1. 完整分析PCMCD表格式
2. 建立每种管件的格式规则
3. 验证阶段全文搜索确认

### Q4: 如何验证替换是否成功？
**A**: 
1. 统计修改前后的材料标准出现次数
2. 全文搜索旧材料标准，应为0
3. 抽查典型管件的描述文本
4. 在Smart3D中实际测试

## 技术实现要点

### Python库依赖
```python
import pandas as pd
import openpyxl
import json
import logging
import re
from typing import Dict, List, Tuple
```

### 关键数据操作
```python
# 1. 读取Excel文件
df = pd.read_excel('PipingSpecRuleData.xlsx', sheet_name='PCMCD')

# 2. 分析描述格式
format_rules = parse_material_description_format(df.head(622))

# 3. 基于位置替换
new_desc = replace_material_by_position(
    description, 
    format_rules['Elbow'],
    material_mapping,
    size_mapping
)

# 4. 批量修改
for index, row in df.iterrows():
    if row['SPECNAME'] == target_grade:
        df.at[index, 'LONGMATERIALDESCRIPTION'] = new_desc

# 5. 写回Excel
df.to_excel('output.xlsx', index=False)
```

## 项目交付清单

### 必需文件
1. ✅ Smart3D等级库复制程序-实现文档.md（本文档）
2. ✅ config.json（配置文件）
3. ✅ C1L01等级-输入数据模板.xlsx（壁厚和材料映射表）
4. ✅ 中文名称-SHORTCODE对应表.xlsx（命名对应关系）
5. ✅ format_rules.json（PCMCD格式规则，程序自动生成）
6. ✅ 原始Excel文件（PipingSpecRuleData.xlsx等）

### 参考文档
1. ✅ 关键改进说明.md
2. ✅ 快速参考卡.md
3. ✅ PCMCD格式分析指南.md（新增）
4. ✅ 材料替换验证报告模板.md（新增）

## 后续优化建议

1. **机器学习优化**: 使用ML算法自动识别描述格式
2. **批量处理**: 支持一次处理多个等级
3. **图形界面**: 开发GUI便于非技术人员使用
4. **自动验证**: 自动对比修改前后的差异
5. **回滚功能**: 支持撤销修改操作

---

**文档版本**: 3.0（基于位置的智能替换版）  
**最后更新**: 2025-11-13  
**作者**: Claude AI  
**重大改进**: 材料替换从简单字符串替换升级为基于位置的智能替换
