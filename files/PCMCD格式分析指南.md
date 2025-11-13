# PCMCD格式分析指南

## 目标

通过分析PCMCD表前622行的SHORTMATERIALDESCRIPTION和LONGMATERIALDESCRIPTION字段，识别材料标准和尺寸标准在描述文本中的位置规律，实现基于位置的智能替换。

## PCMCD表结构

### 关键字段
```
PCMCD表 (前622行)
├── SHORTCODE                    # 管件类型代码（如"Elbow", "Tee"）
├── SHORTMATERIALDESCRIPTION     # 短材料描述
└── LONGMATERIALDESCRIPTION      # 长材料描述（重点分析）
```

## 描述格式分析方法

### 典型格式示例

#### 示例1: 弯头（Elbow）
```
LONGMATERIALDESCRIPTION:
"Elbow, 90°, ASTM A234 WPB, Butt Weld, SCH40, ASME B16.9"

格式分解：
位置0: "Elbow"           → 管件类型
位置1: "90°"             → 角度规格
位置2: "ASTM A234 WPB"   → 材料标准 ★
位置3: "Butt Weld"       → 连接方式
位置4: "SCH40"           → 尺寸标准（壁厚） ★
位置5: "ASME B16.9"      → 标准规范
```

#### 示例2: 三通（Tee）
```
LONGMATERIALDESCRIPTION:
"Tee, Reducing, ASTM A234 WPB, Butt Weld, SCH40, ASME B16.9"

格式分解：
位置0: "Tee"             → 管件类型
位置1: "Reducing"        → 类型说明
位置2: "ASTM A234 WPB"   → 材料标准 ★
位置3: "Butt Weld"       → 连接方式
位置4: "SCH40"           → 尺寸标准（壁厚） ★
位置5: "ASME B16.9"      → 标准规范
```

#### 示例3: 法兰（Flange）
```
LONGMATERIALDESCRIPTION:
"Flange, Weld Neck, Class 150, ASTM A105, RF, ASME B16.5"

格式分解：
位置0: "Flange"          → 管件类型
位置1: "Weld Neck"       → 法兰类型
位置2: "Class 150"       → 压力等级（尺寸标准） ★
位置3: "ASTM A105"       → 材料标准 ★
位置4: "RF"              → 密封面类型
位置5: "ASME B16.5"      → 标准规范
```

### 关键观察

1. **逗号分隔**：所有描述都用逗号分隔不同属性
2. **管件类型在首位**：第一个元素总是管件类型
3. **材料标准特征**：
   - 包含标准代码：ASTM, ASME, DIN, JIS, GB等
   - 后跟材料牌号：A105, A234 WPB, A350 LF2等
   - 通常在描述的中间位置（位置2-4）
4. **尺寸标准特征**：
   - 壁厚类：SCH40, SCH80, STD, XS, XXS
   - 压力等级类：Class 150, Class 300, PN16等
   - 通常在材料标准之后（位置3-5）

## 自动分析算法

### 步骤1: 位置统计分析

```python
def analyze_pcmcd_format(pcmcd_df, num_rows=622):
    """
    分析PCMCD表的格式规律
    
    参数:
        pcmcd_df: PCMCD表的DataFrame
        num_rows: 分析的行数（默认622）
    
    返回:
        format_rules: 每种管件类型的格式规则字典
    """
    format_stats = {}
    
    # 只分析前num_rows行
    for index, row in pcmcd_df.head(num_rows).iterrows():
        shortcode = row.get('SHORTCODE', '')
        long_desc = row.get('LONGMATERIALDESCRIPTION', '')
        
        if pd.isna(long_desc) or not long_desc.strip():
            continue
        
        # 按逗号分割
        parts = [p.strip() for p in long_desc.split(',')]
        
        # 初始化统计
        if shortcode not in format_stats:
            format_stats[shortcode] = {
                'count': 0,
                'material_positions': [],
                'size_positions': [],
                'examples': []
            }
        
        format_stats[shortcode]['count'] += 1
        format_stats[shortcode]['examples'].append(long_desc)
        
        # 查找材料标准位置
        for i, part in enumerate(parts):
            # 材料标准特征
            if re.search(r'\b(ASTM|ASME|DIN|JIS|GB)\s+[A-Z0-9\s]+', part):
                format_stats[shortcode]['material_positions'].append(i)
            
            # 尺寸标准特征
            if re.search(r'\b(SCH\s*\d+|STD|XS|XXS|Class\s+\d+|PN\s*\d+)', part):
                format_stats[shortcode]['size_positions'].append(i)
    
    return format_stats
```

### 步骤2: 提取主流位置

```python
def extract_dominant_positions(format_stats):
    """
    从统计数据中提取每种管件的主流位置
    
    参数:
        format_stats: 步骤1的统计结果
    
    返回:
        format_rules: 简化的格式规则
    """
    from collections import Counter
    
    format_rules = {}
    
    for shortcode, stats in format_stats.items():
        # 统计最常见的位置
        material_counter = Counter(stats['material_positions'])
        size_counter = Counter(stats['size_positions'])
        
        # 获取出现频率最高的位置
        material_pos = material_counter.most_common(1)[0][0] if material_counter else None
        size_pos = size_counter.most_common(1)[0][0] if size_counter else None
        
        format_rules[shortcode] = {
            'material_position': material_pos,
            'size_position': size_pos,
            'confidence': {
                'material': material_counter[material_pos] / stats['count'] if material_pos else 0,
                'size': size_counter[size_pos] / stats['count'] if size_pos else 0
            },
            'sample_count': stats['count'],
            'example': stats['examples'][0] if stats['examples'] else None
        }
    
    return format_rules
```

### 步骤3: 生成格式报告

```python
def generate_format_report(format_rules, output_file='format_analysis_report.txt'):
    """
    生成格式分析报告
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PCMCD表格式分析报告\n")
        f.write("=" * 80 + "\n\n")
        
        for shortcode, rule in sorted(format_rules.items()):
            f.write(f"\n【{shortcode}】\n")
            f.write(f"  样本数量: {rule['sample_count']}\n")
            f.write(f"  材料标准位置: {rule['material_position']} (置信度: {rule['confidence']['material']:.1%})\n")
            f.write(f"  尺寸标准位置: {rule['size_position']} (置信度: {rule['confidence']['size']:.1%})\n")
            f.write(f"  示例: {rule['example']}\n")
            f.write("-" * 80 + "\n")
    
    print(f"格式分析报告已生成: {output_file}")
```

## 实际应用：智能替换

### 替换函数

```python
def intelligent_replace(description, shortcode, format_rules, material_mapping, size_mapping):
    """
    基于位置规则进行智能替换
    
    参数:
        description: 原始描述文本
        shortcode: 管件类型代码
        format_rules: 格式规则字典
        material_mapping: 材料标准映射 {'ASTM A234 WPB': 'ASTM A420 WPL6'}
        size_mapping: 尺寸标准映射 {'SCH40': 'SCH80'}
    
    返回:
        new_description: 替换后的描述文本
    """
    if not description or pd.isna(description):
        return description
    
    # 获取格式规则
    if shortcode not in format_rules:
        logging.warning(f"未找到{shortcode}的格式规则，使用模糊替换")
        return fuzzy_replace(description, material_mapping, size_mapping)
    
    rule = format_rules[shortcode]
    parts = [p.strip() for p in description.split(',')]
    
    # 替换材料标准
    mat_pos = rule['material_position']
    if mat_pos is not None and mat_pos < len(parts):
        for old_mat, new_mat in material_mapping.items():
            if old_mat in parts[mat_pos]:
                parts[mat_pos] = parts[mat_pos].replace(old_mat, new_mat)
                logging.info(f"位置{mat_pos}替换材料: {old_mat} → {new_mat}")
                break
    
    # 替换尺寸标准
    size_pos = rule['size_position']
    if size_pos is not None and size_pos < len(parts):
        for old_size, new_size in size_mapping.items():
            if old_size in parts[size_pos]:
                parts[size_pos] = parts[size_pos].replace(old_size, new_size)
                logging.info(f"位置{size_pos}替换尺寸: {old_size} → {new_size}")
                break
    
    return ', '.join(parts)
```

### 模糊替换（备用方案）

```python
def fuzzy_replace(description, material_mapping, size_mapping):
    """
    当无法确定位置时使用的模糊替换
    使用正则表达式确保只替换标准格式的文本
    """
    result = description
    
    # 材料标准替换（带边界检查）
    for old_mat, new_mat in material_mapping.items():
        # 确保是完整的材料标准，不是部分匹配
        pattern = r'\b' + re.escape(old_mat) + r'\b'
        result = re.sub(pattern, new_mat, result)
    
    # 尺寸标准替换
    for old_size, new_size in size_mapping.items():
        pattern = r'\b' + re.escape(old_size) + r'\b'
        result = re.sub(pattern, new_size, result)
    
    return result
```

## 验证方法

### 验证1: 位置准确性验证

```python
def verify_position_accuracy(pcmcd_df, format_rules, num_samples=100):
    """
    验证位置规则的准确性
    """
    results = []
    
    for shortcode, rule in format_rules.items():
        samples = pcmcd_df[pcmcd_df['SHORTCODE'] == shortcode].head(num_samples)
        
        correct_material = 0
        correct_size = 0
        
        for _, row in samples.iterrows():
            desc = row['LONGMATERIALDESCRIPTION']
            if pd.isna(desc):
                continue
                
            parts = [p.strip() for p in desc.split(',')]
            
            # 检查材料位置
            mat_pos = rule['material_position']
            if mat_pos and mat_pos < len(parts):
                if re.search(r'ASTM|ASME|DIN', parts[mat_pos]):
                    correct_material += 1
            
            # 检查尺寸位置
            size_pos = rule['size_position']
            if size_pos and size_pos < len(parts):
                if re.search(r'SCH|Class|PN', parts[size_pos]):
                    correct_size += 1
        
        results.append({
            'shortcode': shortcode,
            'samples': len(samples),
            'material_accuracy': correct_material / len(samples) if len(samples) > 0 else 0,
            'size_accuracy': correct_size / len(samples) if len(samples) > 0 else 0
        })
    
    return pd.DataFrame(results)
```

### 验证2: 替换结果验证

```python
def verify_replacement_results(original_df, modified_df, material_mapping):
    """
    验证替换是否完整且正确
    """
    issues = []
    
    # 检查旧材料是否还存在
    for old_mat in material_mapping.keys():
        old_count = modified_df['LONGMATERIALDESCRIPTION'].str.contains(
            old_mat, na=False
        ).sum()
        
        if old_count > 0:
            issues.append(f"警告: {old_mat} 仍有{old_count}处未替换")
    
    # 检查新材料是否正确出现
    for old_mat, new_mat in material_mapping.items():
        original_count = original_df['LONGMATERIALDESCRIPTION'].str.contains(
            old_mat, na=False
        ).sum()
        
        new_count = modified_df['LONGMATERIALDESCRIPTION'].str.contains(
            new_mat, na=False
        ).sum()
        
        if new_count < original_count:
            issues.append(f"警告: {new_mat} 出现次数({new_count})少于预期({original_count})")
    
    return issues
```

## 完整示例代码

```python
import pandas as pd
import re
import json
import logging
from collections import Counter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# 1. 读取PCMCD表
pcmcd_df = pd.read_excel('PipingSpecRuleData.xlsx', sheet_name='PCMCD')

# 2. 分析格式（前622行）
format_stats = analyze_pcmcd_format(pcmcd_df, num_rows=622)
format_rules = extract_dominant_positions(format_stats)

# 3. 生成报告
generate_format_report(format_rules)

# 4. 保存格式规则
with open('format_rules.json', 'w', encoding='utf-8') as f:
    json.dump(format_rules, f, indent=2, ensure_ascii=False)

# 5. 验证准确性
accuracy_df = verify_position_accuracy(pcmcd_df, format_rules)
print("\n位置准确性验证:")
print(accuracy_df)

# 6. 执行替换
material_mapping = {
    'ASTM A105': 'ASTM A350 LF2',
    'ASTM A234 WPB': 'ASTM A420 WPL6',
    'ASTM A216 WCB': 'ASTM A352 LCB'
}

size_mapping = {
    'SCH40': 'SCH80',
    'SCH STD': 'SCH 80'
}

# 复制数据框以便比较
pcmcd_modified = pcmcd_df.copy()

# 只处理目标等级的记录
target_grade = 'C1L02'
for index, row in pcmcd_modified.iterrows():
    if row['SPECNAME'] != target_grade:
        continue
    
    shortcode = row['SHORTCODE']
    
    # 替换长描述
    if pd.notna(row['LONGMATERIALDESCRIPTION']):
        new_desc = intelligent_replace(
            row['LONGMATERIALDESCRIPTION'],
            shortcode,
            format_rules,
            material_mapping,
            size_mapping
        )
        pcmcd_modified.at[index, 'LONGMATERIALDESCRIPTION'] = new_desc
    
    # 替换短描述
    if pd.notna(row['SHORTMATERIALDESCRIPTION']):
        new_short = intelligent_replace(
            row['SHORTMATERIALDESCRIPTION'],
            shortcode,
            format_rules,
            material_mapping,
            size_mapping
        )
        pcmcd_modified.at[index, 'SHORTMATERIALDESCRIPTION'] = new_short

# 7. 验证替换结果
issues = verify_replacement_results(pcmcd_df, pcmcd_modified, material_mapping)
if issues:
    print("\n发现以下问题:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✓ 所有替换验证通过")

# 8. 保存结果
pcmcd_modified.to_excel('PCMCD_modified.xlsx', index=False)
print("\n修改后的数据已保存: PCMCD_modified.xlsx")
```

## 注意事项

1. **格式变化**: 如果PCMCD表格式有变化，需重新分析
2. **特殊情况**: 某些管件可能有特殊格式，需要特殊处理
3. **验证必要**: 每次替换后都要进行全面验证
4. **备份数据**: 操作前务必备份原始数据

## 输出文件

运行完整流程后会生成以下文件：
1. `format_rules.json` - 格式规则JSON文件
2. `format_analysis_report.txt` - 格式分析文本报告
3. `PCMCD_modified.xlsx` - 修改后的PCMCD表

---

**文档版本**: 1.0  
**创建日期**: 2025-11-13  
**作者**: Claude AI
