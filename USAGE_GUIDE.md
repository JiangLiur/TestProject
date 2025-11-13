# Smart3D等级库复制程序 - 详细使用指南

## 📋 使用前准备

### 1. 确认环境

您的环境已经准备好，无需额外安装！

```bash
# 确认Python和依赖包已安装
python3 --version   # 应该显示 Python 3.x
pip list | grep pandas    # 应该显示 pandas
pip list | grep openpyxl  # 应该显示 openpyxl
```

### 2. 准备数据文件

您需要两个 Excel 文件（已经在 `files/` 目录中）：

✅ `files/CatalogDataExtractor_PCMCD.xlsx` - PCMCD数据表
✅ `files/CatalogDataExtractor_PipingSpecRuleData.xlsx` - 规格规则数据表

这两个文件是从 Smart3D 导出的原始数据。

## 🎯 使用步骤（完整版）

### 步骤1: 创建配置文件

根据您的实际需求创建配置文件。我帮您准备一个模板：

```bash
# 复制示例配置文件
cp config_full.json my_project_config.json
```

### 步骤2: 编辑配置文件

打开 `my_project_config.json`，按照您的需求修改：

```json
{
  "source_grade": "1C0031",        // ← 改成您的源等级名称
  "target_grade": "1C0032",        // ← 改成您的目标等级名称

  "pcmcd_file": "files/CatalogDataExtractor_PCMCD.xlsx",
  "spec_rule_file": "files/CatalogDataExtractor_PipingSpecRuleData.xlsx",
  "output_dir": "output_my_project",  // ← 改成您想要的输出目录名

  "pcmcd_analysis": {
    "analyze_rows": 622,
    "export_format_rules": true
  },

  "schedule_mappings": [
    // 如果需要修改壁厚，在这里配置
    // 如果不需要，可以留空数组 []
    {
      "pipe_size": 0.75,              // 管径
      "old_schedule": "MATCH",         // 旧壁厚
      "new_schedule": "SCH80",         // 新壁厚
      "shortcode": "45 Degree Direction Change"  // 管件类型（可选）
    }
  ],

  "material_replacements": {
    // 在这里配置材料标准替换规则
    // 格式：旧材料标准: 新材料标准
    "ASTM A216 WCB": "ASTM A352 LCB",
    "ASTM A105": "ASTM A350 LF2",
    "ASTM A182 F304": "ASTM A182 F316"
  },

  "size_standard_replacements": {
    // 在这里配置尺寸标准替换规则
    // 格式：旧尺寸标准: 新尺寸标准
    "SCH40": "SCH80",
    "XS": "XXS",
    "CL150": "CL300"
  }
}
```

### 步骤3: 运行程序

```bash
# 运行完整版程序
python3 src/smart3d_grade_copy_full.py my_project_config.json
```

程序会自动执行以下操作：
1. ✅ 复制等级库表（PipingMaterialsClassData、PipingCommodityFilter）
2. ✅ 应用壁厚修改配置
3. ✅ 分析PCMCD表格式（使用SHORTCODE精确匹配）
4. ✅ 执行智能材料和尺寸标准替换
5. ✅ 导出所有结果文件

### 步骤4: 查看结果

```bash
# 查看输出目录
ls output_my_project/

# 您会看到以下文件：
# CatalogDataExtractor_PipingSpecRuleData.xlsx  - 修改后的等级库表
# CatalogDataExtractor_PCMCD.xlsx               - 修改后的PCMCD表
# grade_copy_report.txt                         - 等级复制报告
# replacement_report.txt                        - 替换操作报告
# full_operation_report.txt                     - 完整操作报告

# 查看完整操作报告
cat output_my_project/full_operation_report.txt
```

## 📝 配置文件详解

### 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `source_grade` | 源等级名称 | "1C0031" |
| `target_grade` | 目标等级名称 | "1C0032" |
| `pcmcd_file` | PCMCD文件路径 | "files/CatalogDataExtractor_PCMCD.xlsx" |
| `spec_rule_file` | 规格规则文件路径 | "files/CatalogDataExtractor_PipingSpecRuleData.xlsx" |

### 可选字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `output_dir` | 输出目录 | "output_full" |
| `format_rules_file` | 格式规则文件 | "format_rules.json" |
| `schedule_mappings` | 壁厚映射配置 | [] （空数组）|
| `material_replacements` | 材料标准映射 | {} （空对象）|
| `size_standard_replacements` | 尺寸标准映射 | {} （空对象）|

## 🔧 配置示例

### 示例1: 只复制等级库，不修改材料和壁厚

```json
{
  "source_grade": "1C0031",
  "target_grade": "1C0033",

  "pcmcd_file": "files/CatalogDataExtractor_PCMCD.xlsx",
  "spec_rule_file": "files/CatalogDataExtractor_PipingSpecRuleData.xlsx",
  "output_dir": "output_copy_only",

  "pcmcd_analysis": {
    "analyze_rows": 622,
    "export_format_rules": true
  },

  "schedule_mappings": [],              // 不修改壁厚
  "material_replacements": {},          // 不替换材料
  "size_standard_replacements": {}      // 不替换尺寸标准
}
```

### 示例2: 复制并修改壁厚（不修改材料）

```json
{
  "source_grade": "1C0031",
  "target_grade": "1C0034",

  "pcmcd_file": "files/CatalogDataExtractor_PCMCD.xlsx",
  "spec_rule_file": "files/CatalogDataExtractor_PipingSpecRuleData.xlsx",
  "output_dir": "output_schedule_change",

  "schedule_mappings": [
    {
      "pipe_size": 0.75,
      "old_schedule": "MATCH",
      "new_schedule": "SCH80"
    },
    {
      "pipe_size": 1.0,
      "old_schedule": "MATCH",
      "new_schedule": "SCH80"
    },
    {
      "pipe_size": 1.5,
      "old_schedule": "SCH40",
      "new_schedule": "SCH80"
    }
  ],

  "material_replacements": {},
  "size_standard_replacements": {}
}
```

### 示例3: 完整配置（复制+壁厚+材料替换）

```json
{
  "source_grade": "1C0031",
  "target_grade": "1C0035",

  "pcmcd_file": "files/CatalogDataExtractor_PCMCD.xlsx",
  "spec_rule_file": "files/CatalogDataExtractor_PipingSpecRuleData.xlsx",
  "output_dir": "output_complete",

  "schedule_mappings": [
    {
      "pipe_size": 0.75,
      "old_schedule": "MATCH",
      "new_schedule": "SCH80",
      "shortcode": "45 Degree Direction Change"
    }
  ],

  "material_replacements": {
    "ASTM A216 WCB": "ASTM A352 LCB",
    "ASTM A105": "ASTM A350 LF2"
  },

  "size_standard_replacements": {
    "SCH40": "SCH80",
    "CL150": "CL300"
  }
}
```

## 🎯 如何填写配置

### 1. 如何确定源等级名称？

查看您的 Excel 文件：

```bash
# 方法1: 在 PipingSpecRuleData Excel 中查看
# 打开: files/CatalogDataExtractor_PipingSpecRuleData.xlsx
# 工作表: PipingMaterialsClassData
# 列名: SPECNAME
# 找到您想复制的等级名称，如 "1C0031"
```

或者运行一个简单的查询脚本：

```bash
python3 -c "
import pandas as pd
df = pd.read_excel('files/CatalogDataExtractor_PipingSpecRuleData.xlsx',
                   sheet_name='PipingMaterialsClassData',
                   header=3, skiprows=[4])
if '!BacktoIndex' in df.columns[0]:
    df = df.iloc[:, 1:]
print('可用的等级列表:')
print(df['SPECNAME'].unique())
"
```

### 2. 如何配置壁厚映射？

**基本格式**：
```json
{
  "pipe_size": 管径数值,
  "old_schedule": "旧壁厚",
  "new_schedule": "新壁厚",
  "shortcode": "管件类型"  // 可选
}
```

**常见壁厚值**：
- `"MATCH"` - 匹配源等级的壁厚
- `"SCH40"`, `"SCH80"`, `"SCH160"` - 标准壁厚
- `"STD"`, `"XS"`, `"XXS"` - 标准/加强/双倍加强

**管径示例**：
- `0.75` - 3/4英寸
- `1.0` - 1英寸
- `1.5` - 1.5英寸
- `2.0` - 2英寸

### 3. 如何配置材料替换？

在PCMCD表中查找您需要替换的材料标准：

```json
"material_replacements": {
  "旧材料标准": "新材料标准",
  "ASTM A216 WCB": "ASTM A352 LCB",     // 碳钢 → 低温碳钢
  "ASTM A105": "ASTM A350 LF2",         // 锻钢 → 低温锻钢
  "ASTM A182 F304": "ASTM A182 F316",   // 304不锈钢 → 316不锈钢
  "ASTM A234 WPB": "ASTM A420 WPL6"     // 碳钢管件 → 低温钢管件
}
```

**提示**：材料标准会在正确的位置进行精确替换，不会误替换描述中其他位置的相同文字。

### 4. 如何配置尺寸标准替换？

```json
"size_standard_replacements": {
  "旧尺寸标准": "新尺寸标准",
  "SCH40": "SCH80",           // 壁厚等级
  "SCH STD": "SCH 80",        // 注意格式差异
  "XS": "XXS",                // 加强 → 双倍加强
  "CL150": "CL300",           // 压力等级
  "PN16": "PN25"              // 公称压力
}
```

## ⚠️ 重要注意事项

### 1. 备份原始数据

**在运行程序前，请备份您的原始 Excel 文件！**

```bash
# 创建备份
cp files/CatalogDataExtractor_PCMCD.xlsx files/CatalogDataExtractor_PCMCD.xlsx.backup
cp files/CatalogDataExtractor_PipingSpecRuleData.xlsx files/CatalogDataExtractor_PipingSpecRuleData.xlsx.backup
```

### 2. 检查目标等级是否已存在

如果目标等级已存在，程序会：
- 对于 `PipingMaterialsClassData`：跳过复制
- 对于 `PipingCommodityFilter`：删除现有记录后重新复制

### 3. PCMCD表的特殊性

PCMCD表**不区分等级**，所以材料和尺寸标准替换会应用到**整个表**，不仅仅是目标等级。

如果您只想修改特定等级的材料，请：
1. 先导出该等级相关的PCMCD记录
2. 单独处理
3. 再导入回Smart3D

### 4. 验证结果

运行完成后，务必检查：
```bash
# 查看完整操作报告
cat output_my_project/full_operation_report.txt

# 查看替换报告
cat output_my_project/replacement_report.txt

# 特别注意警告信息
grep "WARNING" output_my_project/*.txt
```

## 🐛 常见问题

### Q1: 找不到源等级

**错误信息**：
```
未找到源等级: XXX
```

**解决方法**：
1. 检查配置文件中的 `source_grade` 是否拼写正确
2. 检查Excel文件中是否真的存在这个等级
3. 运行上面的查询脚本查看所有可用等级

### Q2: 程序运行很慢

**原因**：
- PCMCD表数据量大（3000+行）
- 格式分析需要遍历622行

**正常时间**：
- 完整版：5-8秒
- MVP版：2-3秒

### Q3: 替换后发现旧材料还存在

查看警告信息：
```
WARNING: 警告: 'ASTM A105' 仍有 83 处未替换
```

**可能原因**：
1. 该材料不在标准位置（程序无法识别格式）
2. 描述格式特殊

**解决方法**：
查看 `format_analysis_report.txt`，找到未替换的管件类型，检查其格式规则。

### Q4: 如何只运行MVP版（只修改PCMCD）？

```bash
# 使用MVP版配置和程序
python3 src/smart3d_grade_copy.py config_example.json
```

## 📊 执行日志示例

正常执行时，您会看到类似的日志：

```
================================================================================
Smart3D等级库复制程序 - 完整版 v1.0
================================================================================
功能: 等级复制 + 壁厚修改 + SHORTCODE匹配 + 智能替换

步骤1: 复制等级库相关表
  复制等级基本信息: 1C0031 → 1C0032
    ✓ 复制完成，新增 1 条记录
  复制管件类型过滤器: 1C0031 → 1C0032
    应用壁厚映射配置: 2 条规则
    0.75: MATCH → SCH80 (SHORTCODE=45 Degree Direction Change)
    ✓ 复制完成，新增 1 条记录
  ✓ 等级库表复制完成

步骤2: 分析PCMCD表格式（使用SHORTCODE精确匹配）
  构建商品编码到SHORTCODE的映射: 1065 个映射关系
  分析前 622 行数据
  发现 26 种管件类型（SHORTCODE）
  ✓ 格式分析完成

步骤3: 加载PCMCD数据
  ✓ 加载 3386 行数据

步骤4: 应用智能材料和尺寸标准替换
  材料标准映射规则: 5 条
  尺寸标准映射规则: 4 条
  修改了 1037 条记录
  ✓ 智能替换完成

步骤5: 导出结果
  ✓ 所有结果已导出到: output_my_project

✓ 程序执行完成！
```

## 📋 快速检查清单

运行程序前，请确认：

- [ ] 已备份原始Excel文件
- [ ] 已确认源等级名称存在
- [ ] 已确认目标等级名称（如果存在会被覆盖）
- [ ] 已正确配置壁厚映射（如果需要）
- [ ] 已正确配置材料替换（如果需要）
- [ ] 已正确配置尺寸标准替换（如果需要）
- [ ] 输出目录名称已设置

运行程序后，请检查：

- [ ] 查看 `full_operation_report.txt`
- [ ] 检查是否有WARNING信息
- [ ] 验证等级复制记录数是否正确
- [ ] 抽查几个管件的材料替换是否正确
- [ ] 在Smart3D中测试导入（推荐）

## 🎯 推荐工作流程

### 第一次使用（测试）

1. **小范围测试**
   ```bash
   # 复制一个测试等级
   python3 src/smart3d_grade_copy_full.py config_test.json
   ```

2. **验证结果**
   - 检查输出文件
   - 在Smart3D测试环境中导入
   - 验证功能是否正常

3. **正式使用**
   - 使用实际的源等级和目标等级
   - 配置完整的映射规则
   - 在生产环境中导入

### 批量处理

如果需要创建多个等级：

```bash
# 方法1: 多次运行（推荐）
python3 src/smart3d_grade_copy_full.py config_grade1.json
python3 src/smart3d_grade_copy_full.py config_grade2.json
python3 src/smart3d_grade_copy_full.py config_grade3.json

# 方法2: 写一个简单的批处理脚本
for config in config_*.json; do
    python3 src/smart3d_grade_copy_full.py "$config"
done
```

## 📞 需要帮助？

如果遇到问题：

1. **查看日志** - 程序会输出详细的执行日志
2. **查看报告** - 检查生成的各种报告文件
3. **查看文档** - README_FULL.md 有详细说明
4. **检查配置** - 确认配置文件格式正确

---

**祝您使用愉快！** 🎉

如有任何疑问，请随时提问。
