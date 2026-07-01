# 模板填充逻辑

## 目录

- [概览](#概览)
- [填充流程](#填充流程)
- [数据对应关系](#数据对应关系)
- [自定义内容](#自定义内容)

## 概览

本章节说明如何将解析后的数据填充到报告模板中，支持日报/周报/月报三种类型。

## 填充流程

```
┌─────────────────┐
│  解析 Prompt    │
├─────────────────┤
│ date-range-     │
│ resolver.py     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   收集数据      │
├─────────────────┤
│ - Git 提交      │
│ - Todo/Issue    │
│ - 用户内容文件  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   解析数据      │
├─────────────────┤
│ - 分析 Git      │
│ - 解析 Todo     │
│ - 提取内容      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   数据整合      │
├─────────────────┤
│ - 合并 report_  │
│   meta + 数据   │
│ - 格式化        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   模板填充      │
├─────────────────┤
│ - 替换占位符    │
│ - 生成 HTML    │
│ - 输出文件      │
└─────────────────┘
```

## 数据对应关系

### 报告元数据（来自 date-range-resolver）

| 模板占位符 | 数据来源 | 说明 |
|------------|----------|------|
| `{{REPORT_TITLE}}` | `report_meta.report_title` | 工作日报/周报/月报 |
| `{{REPORT_TYPE}}` | `report_meta.report_type` | daily/weekly/monthly |
| `{{PERIOD_LABEL}}` | `report_meta.period_label` | 日期范围展示 |
| `{{START_DATE}}` | `report_meta.start_date` | 起始日期 |
| `{{END_DATE}}` | `report_meta.end_date` | 结束日期 |
| `{{LABEL_*}}` | `report_meta.labels.*` | 各章节标题 |

### Git 数据

| 模板占位符 | 数据来源 | 说明 |
|------------|----------|------|
| `{{GIT_COMMITS}}` | `git.categories` | 提交分类列表 |
| `{{GIT_STATS_TOTAL}}` | `git.stats.total_commits` | 提交总数 |
| `{{GIT_STATS_AUTHORS}}` | `git.stats.unique_authors` | 参与人数 |

### Todo 数据

| 模板占位符 | 数据来源 | 说明 |
|------------|----------|------|
| `{{TODO_ITEMS}}` | `todo.todo_files` | Todo 列表 |

### 用户内容数据

| 模板占位符 | 数据来源 |
|------------|----------|
| `{{PROBLEMS}}` | `user_content.problems.files` |
| `{{GROWTH}}` | `user_content.growth.files` |
| `{{KNOWLEDGE}}` | `user_content.knowledge.files` |

### 元数据

| 模板占位符 | 数据来源 |
|------------|----------|
| `{{START_DATE}}` / `{{WEEK_START}}` | 命令行参数或 report_meta |
| `{{END_DATE}}` / `{{WEEK_END}}` | 命令行参数或 report_meta |
| `{{GENERATED_DATE}}` | 当前日期 |

## 自定义内容

### 使用场景
- 数据源无法覆盖的内容
- 人工补充的关键信息
- 临时性、非结构化内容

### 填充方式

通过自定义内容 dict 传入：

```json
{
  "progress": "自定义进展...",
  "todo": "自定义任务...",
  "problems": "自定义问题...",
  "growth": "自定义成长...",
  "knowledge": "自定义知识...",
  "plan": "自定义计划...",
  "risks": "自定义风险..."
}
```

### 优先级

1. 自定义内容优先
2. 解析数据作为补充
3. 缺失字段显示为空提示

## HTML 模板变量

### 必填变量
- `{{REPORT_TITLE}}` - 报告标题
- `{{PERIOD_LABEL}}` - 日期范围
- `{{GENERATED_DATE}}` - 生成日期

### 章节标签变量
- `{{LABEL_STATS}}` - 数据统计
- `{{LABEL_PROGRESS}}` - 进展
- `{{LABEL_TODO}}` - 任务完成情况
- `{{LABEL_PROBLEMS}}` - 遇到的问题
- `{{LABEL_GROWTH}}` - 个人成长
- `{{LABEL_KNOWLEDGE}}` - 知识分享
- `{{LABEL_PLAN}}` - 下期计划
- `{{LABEL_RISKS}}` - 风险与问题

### 内容变量
- `{{GIT_COMMITS}}` - Git 提交区块
- `{{TODO_ITEMS}}` - Todo 区块
- `{{PROBLEMS}}` - 问题区块
- `{{GROWTH}}` - 成长区块
- `{{KNOWLEDGE}}` - 知识区块
- `{{PLAN}}` - 计划区块
- `{{RISKS}}` - 风险区块

## 错误处理

| 情况 | 处理方式 |
|------|----------|
| Git 非仓库 | 显示"非 Git 仓库"提示 |
| 文件不存在 | 显示"未找到文件"提示 |
| 解析失败 | 显示错误，保留原始内容 |
| 字段缺失 | 显示默认值或空 |
