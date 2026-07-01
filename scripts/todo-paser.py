#!/usr/bin/env python3
"""Todo/Issue文件解析器，整理完成情况"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional


def find_todo_files(repo_path: str) -> List[str]:
    """查找项目中的todo和issue文件"""
    patterns = [
        "**/todo*.md", "**/todo*.txt",
        "**/issue*.md", "**/issue*.txt",
        "**/TODO.md", "**/ISSUES.md",
        "**/.todo.md", "**/.issues.md"
    ]
    
    found_files = []
    for pattern in patterns:
        found_files.extend(Path(repo_path).glob(pattern))
    
    # 过滤隐藏目录
    found_files = [f for f in found_files if not any(
        part.startswith('.') for part in f.parts[:-1]
    )]
    
    return [str(f) for f in found_files]


def parse_todo_content(content: str) -> List[Dict]:
    """解析todo内容"""
    items = []
    lines = content.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # 匹配各种完成状态标记
        completed_match = re.match(
            r'^[-*]\s*\[([ xX])\]\s*(.+)$',
            line
        )
        if completed_match:
            status = completed_match.group(1).upper() == "X"
            text = completed_match.group(2).strip()
            items.append({
                "text": text,
                "completed": status,
                "type": "checkbox"
            })
            continue
        
        # 匹配数字编号
        numbered_match = re.match(r'^(\d+)[.、]\s*(.+)$', line)
        if numbered_match:
            items.append({
                "text": numbered_match.group(2).strip(),
                "completed": None,  # 需要用户判断
                "type": "numbered"
            })
            continue
        
        # 匹配优先级标记 [P0], [P1], [高], [中], [低]
        priority_match = re.match(r'^\[([^\]]+)\]\s*(.+)$', line)
        if priority_match:
            items.append({
                "text": priority_match.group(2).strip(),
                "priority": priority_match.group(1),
                "completed": None,
                "type": "priority"
            })
            continue
        
        # 其他普通文本行
        if len(line) > 3:
            items.append({
                "text": line,
                "completed": None,
                "type": "plain"
            })
    
    return items


def parse_issue_content(content: str) -> List[Dict]:
    """解析issue内容，支持更复杂的格式"""
    issues = []
    current_issue = None
    
    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        
        # 检测新issue标题（# 标题 或 ## 标题）
        if line.startswith("#") and not line.startswith("# "):
            if current_issue:
                issues.append(current_issue)
            
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            
            current_issue = {
                "title": title,
                "level": level,
                "status": "open",  # 默认状态
                "description": []
            }
            
            # 检测状态标签
            if "[closed]" in title.lower() or "[done]" in title.lower():
                current_issue["status"] = "closed"
            elif "[进行中]" in title or "[进行]" in title:
                current_issue["status"] = "in_progress"
        
        elif current_issue:
            current_issue["description"].append(line)
            
            # 检测状态变化
            if "状态" in line or "status" in line.lower():
                if "完成" in line or "closed" in line.lower():
                    current_issue["status"] = "closed"
    
    if current_issue:
        issues.append(current_issue)
    
    return issues


def analyze_directory(repo_path: str) -> Dict:
    """分析整个项目目录的todo/issue情况"""
    files = find_todo_files(repo_path)
    
    results = {
        "todo_files": [],
        "issue_files": [],
        "summary": {
            "total_todo_files": 0,
            "total_issue_files": 0,
            "pending_items": 0,
            "completed_items": 0
        }
    }
    
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            file_info = {
                "path": file_path,
                "relative_path": os.path.relpath(file_path, repo_path)
            }
            
            if "issue" in os.path.basename(file_path).lower():
                file_info["items"] = parse_issue_content(content)
                file_info["type"] = "issue"
                results["issue_files"].append(file_info)
                results["summary"]["total_issue_files"] += 1
            else:
                file_info["items"] = parse_todo_content(content)
                file_info["type"] = "todo"
                results["todo_files"].append(file_info)
                results["summary"]["total_todo_files"] += 1
                
                # 统计
                for item in file_info["items"]:
                    if item.get("completed") is True:
                        results["summary"]["completed_items"] += 1
                    elif item.get("completed") is None:
                        results["summary"]["pending_items"] += 1
        
        except Exception as e:
            continue
    
    return results


def main():
    parser = argparse.ArgumentParser(description="解析todo和issue文件")
    parser.add_argument("--repo-path", default=".", help="项目路径")
    parser.add_argument("--output-format", default="json", choices=["json", "summary"])
    
    args = parser.parse_args()
    
    results = analyze_directory(args.repo_path)
    
    if args.output_format == "summary":
        summary = results["summary"]
        print(f"TODO文件数: {summary['total_todo_files']}")
        print(f"Issue文件数: {summary['total_issue_files']}")
        print(f"已完成项: {summary['completed_items']}")
        print(f"待处理项: {summary['pending_items']}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
