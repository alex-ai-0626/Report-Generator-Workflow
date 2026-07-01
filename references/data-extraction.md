# 数据提取方法

## 目录

- [Git 提交分析](#git-提交分析)
- [Todo/Issue 文件解析](#todoissue-文件解析)
- [用户内容文件解析](#用户内容文件解析)

## 概览

本 Skill 从三个主要数据源提取日报/周报/月报内容：
1. Git 仓库提交记录
2. Todo/Issue 跟踪文件
3. 用户维护的内容文件（problems/growth/knowledge）

## Git 提交分析

### 数据来源
- `.git/` 目录（本地仓库）
- 支持远程仓库拉取

### 提取内容
| 字段 | 说明 |
|------|------|
| commit_hash | 提交哈希（前7位） |
| author_name | 提交者姓名 |
| author_email | 提交者邮箱 |
| date | 提交日期 |
| subject | 提交标题 |
| body | 提交正文 |

### 分类规则

| 分类 | 关键词 |
|------|--------|
| features | `feat:`, `feature`, `add`, `新增`, `功能`, `implement` |
| bugfixes | `fix:`, `bug`, `fix`, `修复`, `patch` |
| improvements | `refactor:`, `improve:`, `optimize:`, `perf:`, `优化`, `改进`, `重构` |
| docs | `docs:`, `doc:`, `readme`, `文档`, `wiki` |

### 统计指标
- 提交总数
- 参与人数（唯一邮箱数）
- 各分类提交数

## Todo/Issue 文件解析

### 支持的文件格式

**文件名模式**：
- `todo*.md`, `todo*.txt`
- `issue*.md`, `issue*.txt`
- `TODO.md`, `ISSUES.md`
- `.todo.md`, `.issues.md`

**内容格式**：

```markdown
## 待办事项

- [x] 已完成的任务
- [ ] 待处理的任务
- [X] 另一个已完成

1. 数字编号任务
2. 第二个任务

[P0] 紧急任务
[P1] 重要任务
```

### 解析规则

| 标记 | 含义 |
|------|------|
| `- [x]` 或 `- [X]` | 已完成 |
| `- [ ]` | 待处理 |
| 数字 + `.` | 编号任务（需人工判断完成状态） |
| `[P0/P1/P2]` | 优先级标记 |

## 用户内容文件解析

### 文件类型

| 类型 | 文件名 | 内容 |
|------|--------|------|
| problems | `problems.md/json`, `问题.md` | 遇到的问题及解决方案 |
| growth | `growth.md/json`, `成长.md`, `learning.md` | 个人成长和学习 |
| knowledge | `knowledge.md/json`, `知识.md` | 技术知识分享 |

### 格式规范

#### problems.md 示例

```markdown
# 数据库连接超时问题

## 问题描述
描述问题的详细情况...

## 类型
- 技术问题 / Bug / 阻塞问题 / 优化需求

## 解决方案
具体解决方法...

## 经验教训
从问题中学到的经验...
```

#### growth.md 示例

```markdown
# 学习了微服务架构

## 类别
- 技术技能 / 软技能 / 经验总结

## 内容
具体学习内容...

## 影响
对工作的影响或帮助...
```

#### knowledge.md 示例

```markdown
# Docker 最佳实践

## 内容
技术知识点...

## 相关链接
- [官方文档](https://docs.docker.com)
- [教程](https://example.com)
```

### 路径查找规则
- 支持 glob 模式匹配
- 自动过滤隐藏目录
- 支持中文文件名

## 验证规则

1. 文件必须存在且可读
2. Markdown 文件应使用 UTF-8 编码
3. JSON 文件必须是有效 JSON 格式
4. 缺失字段使用默认值或空值
