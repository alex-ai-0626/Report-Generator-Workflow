---
name: report-generator
description: 从 Git、Todo/Issue 和用户内容文件收集项目进展，根据用户 prompt 自动生成结构化日报/周报/月报（HTML/PDF）；当用户需要"生成日报"、"生成本周周报"、"生成月报"或指定时间范围时使用
dependency:
  python:
    - requests==2.28.0
---

# 日报/周报/月报生成助手

## 任务目标

- 本 Skill 用于：根据用户 prompt 自动识别报告类型（日报/周报/月报），收集项目数据并生成结构化报告
- 能力包含：Prompt 解析、Git 提交分析、Todo/Issue 解析、用户内容提取、HTML/PDF 生成
- 触发条件：用户说"帮我生成今天的日报"、"生成本周周报"、"生成上月月报"、指定时间范围或表达报告需求

## 前置准备

### 依赖环境
- Python 3.8+
- Git 仓库（可选，非必须）
- PDF 转换工具（wkhtmltopdf/weasyprint/pyppeteer 三选一）

### 脚本依赖
| 脚本 | 用途 |
|------|------|
| date-range-resolver.py | 从用户 prompt 解析报告类型与时间范围 |
| git-analyzer.py | 分析 Git 提交，提取时段内进展 |
| todo-paser.py | 解析 Todo/Issue 文件 |
| user-content-paser.py | 提取 problems/growth/knowledge |
| report-filler.py | 将数据填充到 HTML 模板 |
| html-to-pdf.py | 转换 HTML 为 PDF |

## 操作步骤

### 标准流程

1. **解析用户 prompt** — 运行 date-range-resolver.py，确定报告类型与时间范围
   ```bash
   python scripts/date-range-resolver.py --prompt "帮我生成本月的月报"
   ```
   输出 JSON 包含：`report_type`、`start_date`、`end_date`、`output_html`、`output_pdf`、`labels` 等。

   也可显式指定参数：
   ```bash
   python scripts/date-range-resolver.py --type weekly --start-date 2024-01-08 --end-date 2024-01-14
   ```

   **Prompt 识别规则**：
   | 关键词 | 报告类型 | 默认时间范围 |
   |--------|----------|--------------|
   | 日报、今天、今日 | daily | 当天 |
   | 周报、本周、这周 | weekly | 本周一至周日 |
   | 月报、本月、这个月 | monthly | 本月首日至末日 |
   | 昨天、上周、上月 | 对应类型 | 相对日期 |
   | 显式日期范围 | 自动推断 | 用户指定 |

2. **收集 Git 数据** — 使用解析出的日期范围运行 git-analyzer.py
   ```bash
   python scripts/git-analyzer.py --start-date 2024-01-08 --end-date 2024-01-14 --repo-path .
   ```

3. **收集 Todo/Issue 数据** — 运行 todo-paser.py
   ```bash
   python scripts/todo-paser.py --repo-path .
   ```

4. **收集用户内容文件** — 运行 user-content-paser.py
   ```bash
   python scripts/user-content-paser.py --repo-path .
   ```

5. **整合数据** — 将三个脚本的输出与 `report_meta`（来自步骤 1）合并为 JSON
   ```json
   {
     "report_meta": { "...date-range-resolver 输出..." },
     "git": { "...git-analyzer 输出..." },
     "todo": { "...todo-paser 输出..." },
     "user_content": { "...user-content-paser 输出..." }
   }
   ```

6. **填充模板生成 HTML** — 运行 report-filler.py
   ```bash
   python scripts/report-filler.py \
     --template assets/report-template.html \
     --data combined-data.json \
     --output monthly-report-2024-01-31.html \
     --start-date 2024-01-01 \
     --end-date 2024-01-31 \
     --report-meta report-meta.json
   ```
   若 `combined-data.json` 已包含 `report_meta`，可省略 `--report-meta`。

7. **生成 PDF**（可选）— 运行 html-to-pdf.py
   ```bash
   python scripts/html-to-pdf.py \
     --input monthly-report-2024-01-31.html \
     --output monthly-report-2024-01-31.pdf
   ```

### 可选分支

- **当项目非 Git 仓库**：跳过步骤 2，直接使用 Todo 和用户内容
- **当缺少用户内容文件**：提示用户手动输入或仅生成基于 Todo 的简版报告
- **当 PDF 转换失败**：仅输出 HTML 文件，告知用户手动打印
- **当 prompt 未明确报告类型**：默认生成周报（本周一至周日）

### 用户内容文件说明

用户需要在项目中提供以下文件（Markdown 格式）：

| 文件 | 用途 | 必需 |
|------|------|------|
| problems.md | 遇到的问题 | 可选 |
| growth.md | 个人成长 | 可选 |
| knowledge.md | 相关知识分享 | 可选 |

## 使用示例

### 示例 1：生成今日日报
- 场景/输入：用户说"帮我生成今天的日报"
- 解析结果：`report_type=daily`，日期为当天
- 预期产出：`daily-report-2024-01-15.html` 和 `.pdf`

### 示例 2：生成本周周报
- 场景/输入：用户说"帮我生成本周的周报"
- 解析结果：`report_type=weekly`，本周一至周日
- 预期产出：`weekly-report-2024-01-14.html` 和 `.pdf`

### 示例 3：生成上月月报
- 场景/输入：用户说"生成上个月的月报"
- 解析结果：`report_type=monthly`，上月首日至末日
- 预期产出：`monthly-report-2024-01-31.html`

### 示例 4：指定时间范围
- 场景/输入：用户说"生成 2024年1月1日到7日的周报"
- 解析结果：`report_type=weekly`，指定日期范围
- 预期产出：`weekly-report-2024-01-07.html`

### 示例 5：特定项目目录
- 场景/输入：用户提供项目路径，要求生成报告
- 关键要点：使用 `--repo-path` 参数指定项目路径

## 资源索引

- 脚本：见 [scripts/date-range-resolver.py](scripts/date-range-resolver.py)（用途：解析 prompt 与报告类型）
- 脚本：见 [scripts/git-analyzer.py](scripts/git-analyzer.py)（用途：分析 Git 提交）
- 脚本：见 [scripts/todo-paser.py](scripts/todo-paser.py)（用途：解析 Todo/Issue）
- 脚本：见 [scripts/user-content-paser.py](scripts/user-content-paser.py)（用途：提取用户内容）
- 脚本：见 [scripts/report-filler.py](scripts/report-filler.py)（用途：填充 HTML 模板）
- 脚本：见 [scripts/html-to-pdf.py](scripts/html-to-pdf.py)（用途：HTML 转 PDF）
- 参考：见 [references/data-extraction.md](references/data-extraction.md)（何时读取：了解数据提取规则）
- 参考：见 [references/report-structure.md](references/report-structure.md)（何时读取：了解报告结构）
- 参考：见 [references/template-filling.md](references/template-filling.md)（何时读取：了解模板填充逻辑）
- 资产：见 [assets/report-template.html](assets/report-template.html)（直接用于生成：HTML 报告模板）

## 注意事项

- 首先运行 date-range-resolver.py 解析用户 prompt，再按返回的日期范围收集数据
- 仅在需要时读取参考文档，保持上下文简洁
- 若项目非 Git 仓库，跳过 Git 分析步骤
- 若缺少用户内容文件，提示用户手动补充关键进展
- PDF 转换依赖系统工具，确保已安装 wkhtmltopdf/weasyprint/pyppeteer 之一
- 输出文件命名：`daily-report-YYYY-MM-DD.html`、`weekly-report-YYYY-MM-DD.html`、`monthly-report-YYYY-MM-DD.html`
