#!/usr/bin/env python3
"""Git 提交日志分析脚本，提取指定时段内的项目进展"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def get_git_log(start_date: str, end_date: str, repo_path: str = ".") -> List[Dict]:
    """获取指定日期范围内的git提交记录"""
    try:
        cmd = [
            "git", "log",
            f"--since={start_date}",
            f"--until={end_date}",
            "--pretty=format:%H|%an|%ae|%ad|%s|%b",
            "--date=iso",
            "--no-merges"
        ]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 5:
                commit = {
                    "hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date": parts[3],
                    "subject": parts[4],
                    "body": parts[5] if len(parts) > 5 else ""
                }
                commits.append(commit)
        return commits
    except subprocess.CalledProcessError:
        return []
    except FileNotFoundError:
        print(json.dumps({"error": "git not found", "commits": []}), file=sys.stderr)
        return []


def categorize_commits(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """将提交分类：功能开发、问题修复、技术改进等"""
    categories = {
        "features": [],
        "bugfixes": [],
        "improvements": [],
        "docs": [],
        "other": []
    }
    
    keywords = {
        "features": ["feat:", "feature", "add", "新增", "功能", "implement"],
        "bugfixes": ["fix:", "bug", "fix", "修复", "patch"],
        "improvements": ["refactor:", "improve:", "optimize:", "perf:", "优化", "改进", "重构"],
        "docs": ["docs:", "doc:", "readme", "文档", "wiki"]
    }
    
    for commit in commits:
        subject_lower = commit["subject"].lower()
        categorized = False
        for category, words in keywords.items():
            if any(word.lower() in subject_lower for word in words):
                categories[category].append(commit)
                categorized = True
                break
        if not categorized:
            categories["other"].append(commit)
    
    return categories


def get_commit_stats(commits: List[Dict]) -> Dict:
    """统计提交数据"""
    authors = set()
    for commit in commits:
        authors.add(commit["author_email"])
    
    return {
        "total_commits": len(commits),
        "unique_authors": len(authors),
        "authors_list": list(authors),
        "date_range": {
            "start": commits[-1]["date"] if commits else None,
            "end": commits[0]["date"] if commits else None
        }
    }


def main():
    parser = argparse.ArgumentParser(description="分析 Git 提交日志，提取报告数据")
    parser.add_argument("--start-date", required=True, help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--repo-path", default=".", help="仓库路径")
    
    args = parser.parse_args()
    
    commits = get_git_log(args.start_date, args.end_date, args.repo_path)
    categories = categorize_commits(commits)
    stats = get_commit_stats(commits)
    
    result = {
        "status": "success",
        "stats": stats,
        "categories": categories,
        "all_commits": commits
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
