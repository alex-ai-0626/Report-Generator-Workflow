#!/usr/bin/env python3
"""报告数据填充脚本，将结构化数据填充到 HTML 模板（支持日报/周报/月报）"""

import argparse
import json
import re
import sys
from datetime import datetime
from typing import Dict, Any, Optional


DEFAULT_LABELS = {
    "stats": "数据统计",
    "progress": "本期进展",
    "todo": "任务完成情况",
    "problems": "遇到的问题",
    "growth": "个人成长",
    "knowledge": "相关知识分享",
    "plan": "下期计划",
    "risks": "风险与问题",
}


def load_template(template_path: str) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def load_data(data_path: str) -> Dict:
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_report_meta(data: Dict, meta_path: Optional[str] = None) -> Dict:
    if meta_path:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return data.get("report_meta", {})


def format_period_label(start: str, end: str) -> str:
    if start == end:
        return start
    return f"{start} ~ {end}"


def format_commits_section(git_data: Dict, empty_hint: str = "该时段无 Git 提交记录") -> str:
    if not git_data or git_data.get("error"):
        return f"<p class='empty'>{empty_hint}</p>"

    stats = git_data.get("stats", {})
    categories = git_data.get("categories", {})

    html_parts = [
        f"<p><strong>提交总数:</strong> {stats.get('total_commits', 0)}</p>",
        f"<p><strong>参与人数:</strong> {stats.get('unique_authors', 0)}</p>",
        "<div class='categories'>",
    ]

    category_names = {
        "features": "功能开发",
        "bugfixes": "问题修复",
        "improvements": "技术改进",
        "docs": "文档更新",
        "other": "其他",
    }

    for cat_key, cat_name in category_names.items():
        items = categories.get(cat_key, [])
        if items:
            html_parts.append(f"<h4>{cat_name} ({len(items)})</h4>")
            html_parts.append("<ul>")
            for item in items[:5]:
                html_parts.append(
                    f"<li><code>{item['hash'][:7]}</code> {item['subject']} - {item['author_name']}</li>"
                )
            if len(items) > 5:
                html_parts.append(f"<li>... 还有 {len(items) - 5} 条提交</li>")
            html_parts.append("</ul>")

    html_parts.append("</div>")
    return "\n".join(html_parts)


def format_todo_section(todo_data: Dict) -> str:
    if not todo_data or not todo_data.get("todo_files"):
        return "<p class='empty'>未找到 Todo 文件</p>"

    html_parts = []
    for file_info in todo_data.get("todo_files", []):
        items = file_info.get("items", [])
        completed = [i for i in items if i.get("completed")]
        pending = [i for i in items if not i.get("completed")]

        html_parts.append(f"<h4>{file_info.get('relative_path', 'Unknown')}</h4>")
        html_parts.append(f"<p>完成: {len(completed)} / 待处理: {len(pending)}</p>")

        if pending:
            html_parts.append("<ul class='pending'>")
            for item in pending[:5]:
                html_parts.append(f"<li>{item.get('text', '')}</li>")
            if len(pending) > 5:
                html_parts.append(f"<li>... 还有 {len(pending) - 5} 项</li>")
            html_parts.append("</ul>")

    return "\n".join(html_parts)


def format_problems_section(problems_data: Dict) -> str:
    if not problems_data or not problems_data.get("files"):
        return "<p class='empty'>未找到问题记录文件</p>"

    html_parts = []
    for file_info in problems_data.get("files", []):
        items = file_info.get("items", [])
        if items:
            html_parts.append(f"<h4>{file_info.get('relative_path', 'Unknown')}</h4>")
            for item in items:
                html_parts.append("<div class='problem-item'>")
                html_parts.append(f"<h5>{item.get('title', '')}</h5>")
                html_parts.append(f"<p><strong>类型:</strong> {item.get('type', 'N/A')}</p>")
                if item.get("description"):
                    html_parts.append(f"<p><strong>描述:</strong> {item.get('description', '')}</p>")
                if item.get("solution"):
                    html_parts.append(f"<p><strong>解决方案:</strong> {item.get('solution', '')}</p>")
                if item.get("lessons"):
                    html_parts.append("<p><strong>经验教训:</strong></p>")
                    html_parts.append("<ul>")
                    for lesson in item.get("lessons", []):
                        html_parts.append(f"<li>{lesson}</li>")
                    html_parts.append("</ul>")
                html_parts.append("</div>")

    return "\n".join(html_parts)


def format_growth_section(growth_data: Dict) -> str:
    if not growth_data or not growth_data.get("files"):
        return "<p class='empty'>未找到成长记录文件</p>"

    html_parts = []
    for file_info in growth_data.get("files", []):
        items = file_info.get("items", [])
        if items:
            html_parts.append(f"<h4>{file_info.get('relative_path', 'Unknown')}</h4>")
            for item in items:
                html_parts.append("<div class='growth-item'>")
                html_parts.append(f"<h5>{item.get('title', '')}</h5>")
                html_parts.append(f"<p><strong>类别:</strong> {item.get('category', 'N/A')}</p>")
                if item.get("content"):
                    html_parts.append(f"<p>{item.get('content', '')}</p>")
                if item.get("impact"):
                    html_parts.append(f"<p><strong>影响:</strong> {item.get('impact', '')}</p>")
                html_parts.append("</div>")

    return "\n".join(html_parts)


def format_knowledge_section(knowledge_data: Dict) -> str:
    if not knowledge_data or not knowledge_data.get("files"):
        return "<p class='empty'>未找到知识文档</p>"

    html_parts = []
    for file_info in knowledge_data.get("files", []):
        items = file_info.get("items", [])
        if items:
            html_parts.append(f"<h4>{file_info.get('relative_path', 'Unknown')}</h4>")
            for item in items:
                html_parts.append("<div class='knowledge-item'>")
                html_parts.append(f"<h5>{item.get('title', '')}</h5>")
                if item.get("content"):
                    html_parts.append(f"<p>{item.get('content', '')}</p>")
                if item.get("links"):
                    html_parts.append("<p><strong>相关链接:</strong></p>")
                    html_parts.append("<ul>")
                    for link in item.get("links", []):
                        html_parts.append(f"<li><a href='{link}' target='_blank'>{link}</a></li>")
                    html_parts.append("</ul>")
                html_parts.append("</div>")

    return "\n".join(html_parts)


def fill_template(
    template: str,
    data: Dict,
    start_date: str = "",
    end_date: str = "",
    report_meta: Optional[Dict] = None,
    custom_content: Optional[Dict] = None,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    meta = report_meta or {}
    labels = {**DEFAULT_LABELS, **meta.get("labels", {})}

    start = start_date or meta.get("start_date") or today
    end = end_date or meta.get("end_date") or today
    period_label = meta.get("period_label") or format_period_label(start, end)
    report_title = meta.get("report_title") or meta.get("report_short_name") or "工作报告"
    report_type = meta.get("report_type", "weekly")

    git_data = data.get("git", {})
    stats = git_data.get("stats", {}) if git_data else {}

    replacements = {
        "{{REPORT_TITLE}}": report_title,
        "{{REPORT_TYPE}}": report_type,
        "{{PERIOD_LABEL}}": period_label,
        "{{START_DATE}}": start,
        "{{END_DATE}}": end,
        "{{WEEK_START}}": start,
        "{{WEEK_END}}": end,
        "{{GENERATED_DATE}}": today,
        "{{GIT_STATS_TOTAL}}": str(stats.get("total_commits", 0)),
        "{{GIT_STATS_AUTHORS}}": str(stats.get("unique_authors", 0)),
        "{{LABEL_STATS}}": labels.get("stats", DEFAULT_LABELS["stats"]),
        "{{LABEL_PROGRESS}}": labels.get("progress", DEFAULT_LABELS["progress"]),
        "{{LABEL_TODO}}": labels.get("todo", DEFAULT_LABELS["todo"]),
        "{{LABEL_PROBLEMS}}": labels.get("problems", DEFAULT_LABELS["problems"]),
        "{{LABEL_GROWTH}}": labels.get("growth", DEFAULT_LABELS["growth"]),
        "{{LABEL_KNOWLEDGE}}": labels.get("knowledge", DEFAULT_LABELS["knowledge"]),
        "{{LABEL_PLAN}}": labels.get("plan", DEFAULT_LABELS["plan"]),
        "{{LABEL_RISKS}}": labels.get("risks", DEFAULT_LABELS["risks"]),
    }

    filled = template
    for key, value in replacements.items():
        filled = filled.replace(key, value)

    if custom_content:
        filled = filled.replace("{{GIT_COMMITS}}", custom_content.get("progress", ""))
        filled = filled.replace("{{TODO_ITEMS}}", custom_content.get("todo", ""))
        filled = filled.replace("{{PROBLEMS}}", custom_content.get("problems", ""))
        filled = filled.replace("{{GROWTH}}", custom_content.get("growth", ""))
        filled = filled.replace("{{KNOWLEDGE}}", custom_content.get("knowledge", ""))
        filled = filled.replace("{{PLAN}}", custom_content.get("plan", ""))
        filled = filled.replace("{{RISKS}}", custom_content.get("risks", ""))
    else:
        todo_data = data.get("todo", {})
        problems_data = data.get("user_content", {}).get("problems", {})
        growth_data = data.get("user_content", {}).get("growth", {})
        knowledge_data = data.get("user_content", {}).get("knowledge", {})

        filled = filled.replace("{{GIT_COMMITS}}", format_commits_section(git_data))
        filled = filled.replace("{{TODO_ITEMS}}", format_todo_section(todo_data))
        filled = filled.replace("{{PROBLEMS}}", format_problems_section(problems_data))
        filled = filled.replace("{{GROWTH}}", format_growth_section(growth_data))
        filled = filled.replace("{{KNOWLEDGE}}", format_knowledge_section(knowledge_data))
        filled = filled.replace("{{PLAN}}", "<p class='empty'>请手动补充计划</p>")
        filled = filled.replace("{{RISKS}}", "<p class='empty'>请手动补充风险与问题</p>")

    filled = re.sub(r"\{\{[^}]+\}\}", "", filled)
    return filled


def main():
    parser = argparse.ArgumentParser(description="填充日报/周报/月报模板")
    parser.add_argument("--template", required=True, help="HTML 模板路径")
    parser.add_argument("--data", required=True, help="JSON 数据文件路径")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--start-date", help="报告起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="报告结束日期 (YYYY-MM-DD)")
    parser.add_argument("--week-start", help="（兼容）报告起始日期")
    parser.add_argument("--week-end", help="（兼容）报告结束日期")
    parser.add_argument("--report-meta", help="报告元数据 JSON 文件（来自 date-range-resolver）")

    args = parser.parse_args()

    template = load_template(args.template)
    data = load_data(args.data)
    report_meta = load_report_meta(data, args.report_meta)

    start_date = args.start_date or args.week_start
    end_date = args.end_date or args.week_end

    result_html = fill_template(
        template,
        data,
        start_date=start_date or "",
        end_date=end_date or "",
        report_meta=report_meta,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result_html)

    print(f"Report generated: {args.output}")


if __name__ == "__main__":
    main()
