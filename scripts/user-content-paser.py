#!/usr/bin/env python3
"""用户内容文件解析器：problems, growth, knowledge"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any


def find_user_content_files(repo_path: str) -> Dict[str, List[str]]:
    """查找用户内容文件"""
    patterns = {
        "problems": ["**/problems.md", "**/problems.json", "**/问题.md", "**/issues.md"],
        "growth": ["**/growth.md", "**/growth.json", "**/成长.md", "**/learning.md"],
        "knowledge": ["**/knowledge.md", "**/knowledge.json", "**/知识.md", "**/docs/*.md"]
    }
    
    found_files = {"problems": [], "growth": [], "knowledge": []}
    
    for category, pats in patterns.items():
        for pattern in pats:
            for f in Path(repo_path).glob(pattern):
                if not any(part.startswith('.') for part in f.parts[:-1]):
                    found_files[category].append(str(f))
    
    return found_files


def parse_frontmatter(content: str) -> tuple[Dict, str]:
    """解析Markdown前置元数据"""
    frontmatter = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()
    
    return frontmatter, body


def parse_problems_file(content: str) -> List[Dict]:
    """解析问题文件"""
    problems = []
    frontmatter, body = parse_frontmatter(content)
    
    sections = re.split(r'\n(?=#)', body)
    current_problem = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # 检测问题标题
        if section.startswith("#"):
            if current_problem:
                problems.append(current_problem)
            
            current_problem = {
                "title": section.lstrip("#").strip(),
                "description": "",
                "type": "technical",
                "solution": "",
                "lessons": []
            }
            
            # 从标题提取类型
            title_lower = current_problem["title"].lower()
            if "bug" in title_lower or "缺陷" in current_problem["title"]:
                current_problem["type"] = "bug"
            elif "阻塞" in current_problem["title"] or "blocker" in title_lower:
                current_problem["type"] = "blocker"
            elif "优化" in current_problem["title"] or "performance" in title_lower:
                current_problem["type"] = "optimization"
        
        elif current_problem:
            # 解析内容段落
            if "##" in section or "###" in section:
                parts = section.split("\n", 1)
                heading = parts[0].lstrip("#").strip().lower()
                content_text = parts[1].strip() if len(parts) > 1 else ""
                
                if "描述" in heading or "problem" in heading or "问题" in heading:
                    current_problem["description"] = content_text
                elif "解决" in heading or "solution" in heading or "方案" in heading:
                    current_problem["solution"] = content_text
                elif "经验" in heading or "lesson" in heading or "教训" in heading:
                    current_problem["lessons"].append(content_text)
            else:
                # 普通段落添加到描述
                if current_problem["description"]:
                    current_problem["description"] += "\n" + section
                else:
                    current_problem["description"] = section
    
    if current_problem:
        problems.append(current_problem)
    
    return problems


def parse_growth_file(content: str) -> List[Dict]:
    """解析成长文件"""
    growth_items = []
    frontmatter, body = parse_frontmatter(content)
    
    sections = re.split(r'\n(?=#)', body)
    current_item = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        if section.startswith("#"):
            if current_item:
                growth_items.append(current_item)
            
            current_item = {
                "title": section.lstrip("#").strip(),
                "category": "general",
                "content": "",
                "impact": ""
            }
            
            # 从标题提取类别
            title = current_item["title"]
            if any(kw in title for kw in ["技术", "tech", "skill"]):
                current_item["category"] = "technical"
            elif any(kw in title for kw in ["软技能", "soft", "沟通", "协作"]):
                current_item["category"] = "soft_skill"
            elif any(kw in title for kw in ["经验", "experience"]):
                current_item["category"] = "experience"
        
        elif current_item:
            if "##" in section or "###" in section:
                parts = section.split("\n", 1)
                heading = parts[0].lstrip("#").strip().lower()
                content_text = parts[1].strip() if len(parts) > 1 else ""
                
                if "内容" in heading or "detail" in heading:
                    current_item["content"] = content_text
                elif "影响" in heading or "impact" in heading:
                    current_item["impact"] = content_text
            else:
                if current_item["content"]:
                    current_item["content"] += "\n" + section
                else:
                    current_item["content"] = section
    
    if current_item:
        growth_items.append(current_item)
    
    return growth_items


def parse_knowledge_file(content: str) -> List[Dict]:
    """解析知识文件"""
    knowledge_items = []
    frontmatter, body = parse_frontmatter(content)
    
    sections = re.split(r'\n(?=#)', body)
    current_item = None
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        if section.startswith("#"):
            if current_item:
                knowledge_items.append(current_item)
            
            current_item = {
                "title": section.lstrip("#").strip(),
                "content": "",
                "links": []
            }
        
        elif current_item:
            if "##" in section or "###" in section:
                parts = section.split("\n", 1)
                heading = parts[0].lstrip("#").strip().lower()
                content_text = parts[1].strip() if len(parts) > 1 else ""
                
                if "内容" in heading or "content" in heading:
                    current_item["content"] = content_text
                elif "链接" in heading or "link" in heading or "资源" in heading:
                    current_item["links"] = extract_links(content_text)
            else:
                if current_item["content"]:
                    current_item["content"] += "\n" + section
                else:
                    current_item["content"] = section
    
    if current_item:
        knowledge_items.append(current_item)
    
    return knowledge_items


def extract_links(text: str) -> List[str]:
    """从文本中提取链接"""
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)|(https?://[^\s]+)'
    links = []
    
    for match in re.finditer(link_pattern, text):
        if match.group(2):  # Markdown链接
            links.append(match.group(2))
        elif match.group(3):  # 纯链接
            links.append(match.group(3))
    
    return links


def analyze_user_content(repo_path: str) -> Dict:
    """分析所有用户内容文件"""
    files = find_user_content_files(repo_path)
    
    results = {
        "problems": {"files": [], "total": 0},
        "growth": {"files": [], "total": 0},
        "knowledge": {"files": [], "total": 0}
    }
    
    for problem_file in files["problems"]:
        try:
            with open(problem_file, "r", encoding="utf-8") as f:
                content = f.read()
            problems = parse_problems_file(content)
            results["problems"]["files"].append({
                "path": problem_file,
                "relative_path": os.path.relpath(problem_file, repo_path),
                "items": problems
            })
            results["problems"]["total"] += len(problems)
        except Exception:
            continue
    
    for growth_file in files["growth"]:
        try:
            with open(growth_file, "r", encoding="utf-8") as f:
                content = f.read()
            growth_items = parse_growth_file(content)
            results["growth"]["files"].append({
                "path": growth_file,
                "relative_path": os.path.relpath(growth_file, repo_path),
                "items": growth_items
            })
            results["growth"]["total"] += len(growth_items)
        except Exception:
            continue
    
    for knowledge_file in files["knowledge"]:
        try:
            with open(knowledge_file, "r", encoding="utf-8") as f:
                content = f.read()
            knowledge_items = parse_knowledge_file(content)
            results["knowledge"]["files"].append({
                "path": knowledge_file,
                "relative_path": os.path.relpath(knowledge_file, repo_path),
                "items": knowledge_items
            })
            results["knowledge"]["total"] += len(knowledge_items)
        except Exception:
            continue
    
    return results


def main():
    parser = argparse.ArgumentParser(description="解析用户内容文件")
    parser.add_argument("--repo-path", default=".", help="项目路径")
    parser.add_argument("--category", choices=["problems", "growth", "knowledge", "all"])
    parser.add_argument("--output-format", default="json")
    
    args = parser.parse_args()
    
    results = analyze_user_content(repo_path=args.repo_path)
    
    if args.category and args.category != "all":
        filtered = {args.category: results[args.category]}
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
