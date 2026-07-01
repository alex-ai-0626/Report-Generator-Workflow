#!/usr/bin/env python3
"""根据用户 prompt 或显式参数解析报告类型与时间范围"""

import argparse
import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta
from typing import Optional, Tuple


REPORT_CONFIGS = {
    "daily": {
        "title": "工作日报",
        "short_name": "日报",
        "progress_label": "今日进展",
        "problems_label": "今日遇到的问题",
        "growth_label": "今日学习成长",
        "knowledge_label": "知识分享",
        "plan_label": "明日计划",
        "risks_label": "风险与问题",
        "todo_label": "任务完成情况",
        "stats_label": "数据统计",
        "file_prefix": "daily-report",
    },
    "weekly": {
        "title": "工作周报",
        "short_name": "周报",
        "progress_label": "本周进展",
        "problems_label": "本周遇到的问题",
        "growth_label": "本周个人成长",
        "knowledge_label": "相关知识分享",
        "plan_label": "下周计划",
        "risks_label": "风险与问题",
        "todo_label": "任务完成情况",
        "stats_label": "数据统计",
        "file_prefix": "weekly-report",
    },
    "monthly": {
        "title": "工作月报",
        "short_name": "月报",
        "progress_label": "本月进展",
        "problems_label": "本月遇到的问题",
        "growth_label": "本月个人成长",
        "knowledge_label": "相关知识分享",
        "plan_label": "下月计划",
        "risks_label": "风险与问题",
        "todo_label": "任务完成情况",
        "stats_label": "数据统计",
        "file_prefix": "monthly-report",
    },
}


def parse_date(text: str, default_year: Optional[int] = None) -> Optional[date]:
    """解析 YYYY-MM-DD、YYYY年M月D日、M月D日 等格式"""
    text = text.strip()
    year = default_year or date.today().year

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日?", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    m = re.match(r"(\d{1,2})月(\d{1,2})日?", text)
    if m:
        return date(year, int(m.group(1)), int(m.group(2)))

    return None


def week_range(target: date) -> Tuple[date, date]:
    """返回 target 所在周的周一到周日"""
    monday = target - timedelta(days=target.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def month_range(year: int, month: int) -> Tuple[date, date]:
    """返回指定月份的首尾日期"""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def detect_report_type(prompt: str) -> Optional[str]:
    """从 prompt 中识别报告类型"""
    if not prompt:
        return None

    p = prompt.lower()

    if re.search(r"月报|monthly\s*report|month\s*report|本月|这个月", p):
        return "monthly"
    if re.search(r"日报|daily\s*report|今日|今天|当日", p):
        return "daily"
    if re.search(r"周报|weekly\s*report|week\s*report|本周|这周", p):
        return "weekly"

    return None


def parse_date_range_from_prompt(prompt: str, today: date) -> Tuple[Optional[str], Optional[date], Optional[date]]:
    """从 prompt 解析报告类型与日期范围"""
    report_type = detect_report_type(prompt)

    # 显式日期范围：2024-01-01 到 2024-01-07 / 1月1日到7日
    range_patterns = [
        r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)\s*(?:到|至|~|-)\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)",
        r"(\d{1,2}月\d{1,2}日?)\s*(?:到|至|~|-)\s*(\d{1,2}月\d{1,2}日?)",
        r"(\d{4}-\d{2}-\d{2})\s*(?:到|至|~|-)\s*(\d{4}-\d{2}-\d{2})",
    ]
    for pattern in range_patterns:
        m = re.search(pattern, prompt)
        if m:
            start = parse_date(m.group(1), today.year)
            end = parse_date(m.group(2), today.year)
            if start and end:
                if not report_type:
                    delta = (end - start).days
                    if delta == 0:
                        report_type = "daily"
                    elif delta <= 7:
                        report_type = "weekly"
                    else:
                        report_type = "monthly"
                return report_type, start, end

    # 指定月份：2024年1月 / 1月
    m = re.search(r"(\d{4})年(\d{1,2})月", prompt)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        start, end = month_range(year, month)
        return report_type or "monthly", start, end

    m = re.search(r"(?<!\d)(\d{1,2})月(?!\d)", prompt)
    if m and (report_type == "monthly" or re.search(r"月报|本月|这个月", prompt)):
        month = int(m.group(1))
        start, end = month_range(today.year, month)
        return "monthly", start, end

    # 指定单日
    for pattern in [
        r"(\d{4}年\d{1,2}月\d{1,2}日?)",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2}月\d{1,2}日?)",
    ]:
        m = re.search(pattern, prompt)
        if m:
            d = parse_date(m.group(1), today.year)
            if d:
                if report_type == "weekly":
                    return "weekly", *week_range(d)
                if report_type == "monthly":
                    return "monthly", *month_range(d.year, d.month)
                return report_type or "daily", d, d

    # 相对时间关键词
    if re.search(r"昨天|昨日", prompt):
        d = today - timedelta(days=1)
        return report_type or "daily", d, d
    if re.search(r"前天", prompt):
        d = today - timedelta(days=2)
        return report_type or "daily", d, d
    if re.search(r"上周|上星期", prompt):
        start, end = week_range(today - timedelta(days=7))
        return "weekly", start, end
    if re.search(r"上月|上个月", prompt):
        first = today.replace(day=1)
        last_month_end = first - timedelta(days=1)
        start, end = month_range(last_month_end.year, last_month_end.month)
        return "monthly", start, end

    # 仅类型关键词，使用默认范围
    if report_type == "daily" or re.search(r"今天|今日", prompt):
        return "daily", today, today
    if report_type == "weekly" or re.search(r"本周|这周", prompt):
        return "weekly", *week_range(today)
    if report_type == "monthly" or re.search(r"本月|这个月", prompt):
        return "monthly", *month_range(today.year, today.month)

    return report_type, None, None


def resolve(
    prompt: str = "",
    report_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reference_date: Optional[str] = None,
) -> dict:
    """解析并返回完整报告元数据"""
    today = parse_date(reference_date) if reference_date else date.today()

    explicit_start = parse_date(start_date) if start_date else None
    explicit_end = parse_date(end_date) if end_date else None

    if report_type and report_type not in REPORT_CONFIGS:
        raise ValueError(f"Unsupported report type: {report_type}")

    if explicit_start and explicit_end:
        resolved_type = report_type
        if not resolved_type:
            delta = (explicit_end - explicit_start).days
            if delta == 0:
                resolved_type = "daily"
            elif delta <= 7:
                resolved_type = "weekly"
            else:
                resolved_type = "monthly"
        start, end = explicit_start, explicit_end
    elif report_type and not prompt:
        resolved_type = report_type
        if report_type == "daily":
            start = end = today
        elif report_type == "weekly":
            start, end = week_range(today)
        else:
            start, end = month_range(today.year, today.month)
    else:
        parsed_type, parsed_start, parsed_end = parse_date_range_from_prompt(prompt, today)
        resolved_type = report_type or parsed_type
        if parsed_start and parsed_end:
            start, end = parsed_start, parsed_end
        elif resolved_type:
            if resolved_type == "daily":
                start = end = today
            elif resolved_type == "weekly":
                start, end = week_range(today)
            else:
                start, end = month_range(today.year, today.month)
        else:
            resolved_type = "weekly"
            start, end = week_range(today)

    config = REPORT_CONFIGS[resolved_type]
    start_str = start.isoformat()
    end_str = end.isoformat()

    if start == end:
        period_label = start_str
    else:
        period_label = f"{start_str} ~ {end_str}"

    output_base = f"{config['file_prefix']}-{end_str}"

    return {
        "report_type": resolved_type,
        "report_title": config["title"],
        "report_short_name": config["short_name"],
        "start_date": start_str,
        "end_date": end_str,
        "period_label": period_label,
        "output_html": f"{output_base}.html",
        "output_pdf": f"{output_base}.pdf",
        "labels": {
            "stats": config["stats_label"],
            "progress": config["progress_label"],
            "todo": config["todo_label"],
            "problems": config["problems_label"],
            "growth": config["growth_label"],
            "knowledge": config["knowledge_label"],
            "plan": config["plan_label"],
            "risks": config["risks_label"],
        },
        "prompt": prompt,
    }


def main():
    parser = argparse.ArgumentParser(description="解析报告类型与时间范围")
    parser.add_argument("--prompt", default="", help="用户原始需求描述")
    parser.add_argument(
        "--type",
        choices=["daily", "weekly", "monthly"],
        help="显式指定报告类型",
    )
    parser.add_argument("--start-date", help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--reference-date", help="参考日期，用于测试 (YYYY-MM-DD)")

    args = parser.parse_args()

    try:
        result = resolve(
            prompt=args.prompt,
            report_type=args.type,
            start_date=args.start_date,
            end_date=args.end_date,
            reference_date=args.reference_date,
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
