# Claude Skills 开源项目详细指南

## 目录
1. [什么是 Claude Skills](#什么是-claude-skills)
2. [Skill Seeker - 文档转技能工具](#skill-seeker---文档转技能工具)
3. [Anthropic 官方技能库](#anthropic-官方技能库)
4. [Superpowers - 核心技能库](#superpowers---核心技能库)
5. [Awesome Claude Skills 精选列表](#awesome-claude-skills-精选列表)
6. [其他开源项目](#其他开源项目)
7. [如何创建自己的技能](#如何创建自己的技能)

---

## 什么是 Claude Skills

Claude Skills 是扩展 Claude 功能的模块化能力系统。Skills 通过包含指令、脚本和资源的组织化文件夹来工作，本质上非常简单：一个技能就是一个告诉模型如何做某事的 Markdown 文件，可选地附带额外的文档和预编写的脚本。

### 主要特点
- **轻量级**：每个技能只使用 30-50 tokens，直到被加载
- **自动激活**：Claude 会根据请求上下文自动决定使用相应的技能
- **模块化**：每个技能都是独立的，易于分享和安装
- **适用范围**：Pro、Max、Team 和 Enterprise 用户可用（Free 用户不支持）

---

## Skill Seeker - 文档转技能工具

**项目地址**: https://github.com/yusufkaraaslan/Skill_Seekers

### 项目简介
Skill Seeker 是一个强大的工具，可以将**任何**文档网站转换为 Claude 技能。在 20-40 分钟内为任何框架、API 或工具生成全面的 Claude 技能。

### 核心功能
- ✅ 通用爬虫：支持任何文档网站
- ✅ AI 增强：智能分类和代码语言检测
- ✅ MCP Server 支持：与 Claude Code 集成
- ✅ 大规模文档支持：可处理 10K-40K+ 页面
- ✅ 8个预设配置：Godot、React、Vue、Django、FastAPI 等
- ✅ 断点续传功能
- ✅ 并行爬取和缓存系统
- ✅ 96个测试，100% 通过率
- ✅ 使用 Claude Code Max 本地增强，无 API 成本

### 安装步骤

#### 前置要求
- Python 3.10 或更高版本
- Git
- 15-30 分钟（首次设置）

#### 详细安装步骤

**步骤 1: 克隆仓库**
```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
```

**步骤 2: 运行一次性设置**
```bash
./setup_mcp.sh
```

这个脚本会：
- 创建虚拟环境
- 安装所有依赖
- 配置 MCP Server
- 设置 Claude Code 集成

### 使用方法

#### 方法 1: 自然语言集成（推荐）

设置完成后，可以在 Claude Code 中直接使用自然语言：

```
"列出所有可用的配置文件"
"为 [框架名] 文档生成配置"
"使用配置文件爬取文档"
"打包技能"
```

#### 方法 2: 命令行使用

**使用预设配置：**
```bash
# Godot 文档
python3 doc_scraper.py --config configs/godot.json

# React 文档
python3 doc_scraper.py --config configs/react.json

# Django 文档
python3 doc_scraper.py --config configs/django.json
```

**创建自定义配置：**
```bash
# 创建新配置
python3 doc_scraper.py --create-config my_framework

# 使用自定义配置
python3 doc_scraper.py --config configs/my_framework.json
```

### 工作流程

1. **选择或创建配置** - 使用预设配置或创建自定义配置
2. **爬取文档** - 工具会自动爬取并处理文档
3. **AI 增强** - 使用 Claude Code 本地增强内容
4. **打包技能** - 生成可安装的技能包
5. **安装使用** - 在 Claude Code 中安装并使用

### 预设配置列表
- Godot Engine
- React
- Vue.js
- Django
- FastAPI
- 等等...

---

## Anthropic 官方技能库

**项目地址**: https://github.com/anthropics/skills

### 项目简介
Anthropic 官方公开的技能仓库，包含示例技能和文档技能，采用 Apache 2.0 开源许可。

### 安装方法

#### 在 Claude Code 中安装

**安装文档技能包：**
```bash
/plugin install document-skills@anthropic-agent-skills
```

**安装示例技能包：**
```bash
/plugin install example-skills@anthropic-agent-skills
```

#### 手动安装

将技能文件夹复制到以下位置之一：
- `~/.claude/skills/` - 全局技能目录
- `.claude/skills/` - 项目级技能目录
- 插件的 `skills/` 子目录

### 可用技能

#### 示例技能（开源 - Apache 2.0）
- **algorithmic-art** - 算法艺术生成
- **canvas-design** - 画布设计工具
- **slack-gif-creator** - Slack GIF 创建器
- **artifacts-builder** - 构建工件
- **mcp-server** - MCP 服务器集成
- **webapp-testing** - Web 应用测试
- **brand-guidelines** - 品牌指南管理
- **internal-comms** - 内部沟通
- **skill-creator** - 技能创建助手
- **template-skill** - 技能模板

#### 文档技能（源码可用）
- **docx** - Word 文档处理
- **pdf** - PDF 文档处理
- **pptx** - PowerPoint 处理
- **xlsx** - Excel 表格处理

### 创建新技能

#### 基本结构

创建一个包含 `SKILL.md` 文件的文件夹：

```markdown
---
name: my-skill-name
description: 清晰描述此技能的功能和使用场景
---

# 我的技能名称

[在这里添加 Claude 激活此技能时要遵循的指令]

## 使用场景
- 场景 1
- 场景 2

## 示例
提供使用示例...
```

#### 使用 skill-creator 辅助创建

1. 在 Claude Code 中激活 skill-creator
2. Claude 会询问你的工作流程
3. 自动生成文件夹结构
4. 格式化 SKILL.md 文件
5. 打包所需资源

### 技能结构详解

```
my-skill/
├── SKILL.md          # 主要技能文件（必需）
├── README.md         # 技能文档（可选）
├── scripts/          # 辅助脚本（可选）
│   └── helper.py
└── resources/        # 资源文件（可选）
    └── template.json
```

---

## Superpowers - 核心技能库

**项目地址**: https://github.com/obra/superpowers

### 项目简介
由 Jesse Vincent 创建的 Claude Code 核心技能库，包含 20+ 个经过实战检验的技能，提供测试、调试和协作模式。

### 安装步骤

**步骤 1: 添加 marketplace**
```bash
/plugin marketplace add obra/superpowers-marketplace
```

**步骤 2: 安装插件**
```bash
/plugin install superpowers@superpowers-marketplace
```

**步骤 3: 重启 Claude Code**
重启后运行 `/help` 验证安装

### 核心功能

#### 可用命令
- `/brainstorm` - 头脑风暴
- `/write-plan` - 编写计划
- `/execute-plan` - 执行计划
- 以及更多测试和调试命令...

### 工作原理
- 技能文件存储在 `~/.claude/skills/` 中
- 核心非常轻量，拉取少于 2k tokens 的文档
- 根据需要运行 shell 脚本搜索相关内容

### 相关项目
- **superpowers-skills**: https://github.com/obra/superpowers-skills - 社区可编辑技能
- **superpowers-marketplace**: https://github.com/obra/superpowers-marketplace - 精选插件市场

---

## Awesome Claude Skills 精选列表

### travisvn/awesome-claude-skills
**项目地址**: https://github.com/travisvn/awesome-claude-skills

精选的 Claude Skills、资源和工具列表，特别关注 Claude Code 工作流程。

#### 特点
- 技术深度分析
- 常见问题解答
- 资源链接集合
- 使用技巧和最佳实践

### BehiSecc/awesome-claude-skills
**项目地址**: https://github.com/BehiSecc/awesome-claude-skills

社区精选的实用和实验性技能集合。

#### 包含的技能类型

**开发工作流**
- finishing-a-development-branch
- git-pushing
- skill-creator
- template-skill

**测试和调试**
- pypict-claude-skill（测试用例设计）
- root-cause-tracing

**数据处理**
- csv-data-summarizer-claude-skill
- content-research-writer

**媒体处理**
- article-extractor
- youtube-transcript
- video-downloader
- image-enhancer

**文档格式**
- claude-epub-skill

**安全工具**
- ffuf_claude_skill（安全模糊测试）

---

## 其他开源项目

### 1. simonw/claude-skills
**项目地址**: https://github.com/simonw/claude-skills

Simon Willison 整理的 Claude 代码解释器环境中 `/mnt/skills` 的内容。

### 2. abubakarsiddik31/claude-skills-collection
**项目地址**: https://github.com/abubakarsiddik31/claude-skills-collection

官方和社区构建的 Claude Skills 精选集合，包含用于生产力、创意、编码等的强大模块化功能。

### 3. alirezarezvani/claude-skills
**项目地址**: https://github.com/alirezarezvani/claude-skills

Claude Code 或 Claude AI 的综合技能集合。

### 4. Claude Skills Hub
**网址**: https://claudeskills.info/

发现和下载技能的在线平台。

---

## 如何创建自己的技能

### 方法 1: 使用 Template Skill

**步骤 1: 复制模板**
```bash
cp -r template-skill my-new-skill
cd my-new-skill
```

**步骤 2: 编辑 SKILL.md**
```markdown
---
name: my-new-skill
description: 你的技能描述
version: 1.0.0
author: 你的名字
---

# 我的新技能

## 用途
描述这个技能解决什么问题

## 使用方法
提供清晰的使用说明

## 示例
给出具体示例
```

**步骤 3: 添加脚本和资源**
```bash
mkdir scripts resources
# 添加你的辅助文件
```

**步骤 4: 测试技能**
```bash
cp -r my-new-skill ~/.claude/skills/
```

### 方法 2: 使用 skill-creator

在 Claude Code 中：
```
请帮我创建一个新技能，用于 [描述你的需求]
```

Claude 会：
1. 询问详细需求
2. 生成技能结构
3. 创建 SKILL.md
4. 添加必要的脚本
5. 打包技能

### 方法 3: 从零开始

**最小化技能结构：**

```markdown
---
name: hello-world
description: 简单的问候技能
---

# Hello World Skill

当用户请求问候时，使用友好的方式回复。

## 响应格式
- 包含表情符号
- 使用用户的名字（如果提供）
- 添加时间相关的问候（早上/下午/晚上）
```

### 技能开发最佳实践

1. **清晰的描述**
   - 准确描述技能的用途
   - 明确使用场景
   - 提供示例

2. **结构化指令**
   - 使用标题组织内容
   - 提供分步指导
   - 包含边界情况处理

3. **测试充分**
   - 在不同场景下测试
   - 验证与其他技能的兼容性
   - 确保错误处理

4. **文档完善**
   - 添加 README.md
   - 提供使用示例
   - 说明依赖关系

5. **版本控制**
   - 使用语义化版本号
   - 记录变更日志
   - 标记重大更改

---

## 技能安装位置

### 全局技能
```bash
~/.claude/skills/
```
所有 Claude Code 会话都可以使用

### 项目技能
```bash
/path/to/project/.claude/skills/
```
仅在特定项目中可用

### 插件技能
```bash
~/.claude/plugins/plugin-name/skills/
```
随插件一起安装

---

## 常见问题

### Q: 技能会消耗多少 tokens？
A: 每个技能只使用 30-50 tokens，直到它被激活。完整内容仅在 Claude 判断相关时才加载。

### Q: 如何查看已安装的技能？
A: 在 Claude Code 中运行 `/help` 或检查 `~/.claude/skills/` 目录。

### Q: 可以同时使用多个技能吗？
A: 可以，Claude 会自动加载所有相关的技能。

### Q: 如何分享我的技能？
A: 创建 Git 仓库并发布，或提交到 awesome-claude-skills 列表。

### Q: Skills 和 MCP 有什么区别？
A: Skills 更轻量，专注于指令和工作流程；MCP 提供工具和外部集成。

---

## 资源链接

### 官方资源
- [Claude Skills 官方文档](https://docs.claude.com/en/docs/claude-code/skills)
- [Anthropic Skills 博客](https://www.anthropic.com/news/skills)
- [Anthropic Academy](https://www.anthropic.com/academy)

### 社区资源
- [Simon Willison 的技能分析](https://simonwillison.net/2025/Oct/16/claude-skills/)
- [Jesse Vincent 的 Superpowers 博客](https://blog.fsck.com/2025/10/16/skills-for-claude/)

### GitHub 仓库汇总
- https://github.com/anthropics/skills
- https://github.com/yusufkaraaslan/Skill_Seekers
- https://github.com/obra/superpowers
- https://github.com/travisvn/awesome-claude-skills
- https://github.com/BehiSecc/awesome-claude-skills
- https://github.com/simonw/claude-skills
- https://github.com/abubakarsiddik31/claude-skills-collection
- https://github.com/alirezarezvani/claude-skills

---

## 总结

Claude Skills 生态系统正在快速发展，从官方的技能库到社区驱动的工具如 Skill Seeker，为用户提供了丰富的选择。无论你是想使用现有技能提高生产力，还是创建自己的技能来自动化工作流程，这个指南都应该能帮你快速入门。

开始探索这些开源项目，找到适合你需求的技能，或者创建并分享你自己的技能，为社区做出贡献！
