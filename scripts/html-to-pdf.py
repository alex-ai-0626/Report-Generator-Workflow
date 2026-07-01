#!/usr/bin/env python3
"""HTML转PDF转换器"""

import argparse
import json
import subprocess
import sys
import os


def convert_html_to_pdf(input_html: str, output_pdf: str) -> Dict:
    """使用wkhtmltopdf或weasyprint转换HTML到PDF"""
    result = {
        "status": "pending",
        "input": input_html,
        "output": output_pdf
    }
    
    # 检查输入文件是否存在
    if not os.path.exists(input_html):
        result["status"] = "error"
        result["message"] = f"Input file not found: {input_html}"
        return result
    
    # 方法1: 尝试wkhtmltopdf
    try:
        cmd = ["wkhtmltopdf", "--enable-local-file-access", input_html, output_pdf]
        subprocess.run(cmd, check=True, capture_output=True)
        result["status"] = "success"
        result["method"] = "wkhtmltopdf"
        return result
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # 方法2: 尝试weasyprint
    try:
        from weasyprint import HTML
        HTML(filename=input_html).write_pdf(output_pdf)
        result["status"] = "success"
        result["method"] = "weasyprint"
        return result
    except ImportError:
        pass
    except Exception:
        pass
    
    # 方法3: 尝试puppeteer
    try:
        import asyncio
        from pyppeteer import launch
        
        async def convert():
            browser = await launch(args=['--no-sandbox'])
            page = await browser.newPage()
            await page.goto(f'file://{os.path.abspath(input_html)}')
            await page.pdf({'path': output_pdf, 'format': 'A4'})
            await browser.close()
        
        asyncio.get_event_loop().run_until_complete(convert())
        result["status"] = "success"
        result["method"] = "puppeteer"
        return result
    except ImportError:
        pass
    except Exception:
        pass
    
    result["status"] = "error"
    result["message"] = "No suitable converter found. Please install one of: wkhtmltopdf, weasyprint, or pyppeteer"
    return result


def convert_html_to_pdf_with_options(
    input_html: str,
    output_pdf: str,
    page_size: str = "A4",
    margin_top: str = "20mm",
    margin_bottom: str = "20mm",
    margin_left: str = "15mm",
    margin_right: str = "15mm",
    print_background: bool = True
) -> Dict:
    """使用更多选项转换HTML到PDF"""
    result = {
        "status": "pending",
        "input": input_html,
        "output": output_pdf
    }
    
    if not os.path.exists(input_html):
        result["status"] = "error"
        result["message"] = f"Input file not found: {input_html}"
        return result
    
    # weasyprint选项
    try:
        from weasyprint import HTML, CSS
        
        css = CSS(
            string=f"""
            @page {{
                size: {page_size};
                margin-top: {margin_top};
                margin-bottom: {margin_bottom};
                margin-left: {margin_left};
                margin-right: {margin_right};
            }}
            """
        )
        
        HTML(filename=input_html).write_pdf(
            output_pdf,
            stylesheets=[css] if css else None
        )
        result["status"] = "success"
        result["method"] = "weasyprint"
        return result
    except ImportError:
        pass
    except Exception as e:
        pass
    
    # wkhtmltopdf选项
    try:
        cmd = [
            "wkhtmltopdf",
            "--enable-local-file-access",
            "--page-size", page_size,
            "--margin-top", margin_top,
            "--margin-bottom", margin_bottom,
            "--margin-left", margin_left,
            "--margin-right", margin_right,
        ]
        if print_background:
            cmd.append("--print-media-type")
        cmd.extend([input_html, output_pdf])
        
        subprocess.run(cmd, check=True, capture_output=True)
        result["status"] = "success"
        result["method"] = "wkhtmltopdf"
        return result
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    result["status"] = "error"
    result["message"] = "No suitable converter found"
    return result


def main():
    parser = argparse.ArgumentParser(description="HTML转PDF转换器")
    parser.add_argument("--input", "-i", required=True, help="输入HTML文件路径")
    parser.add_argument("--output", "-o", required=True, help="输出PDF文件路径")
    parser.add_argument("--page-size", default="A4", help="页面大小 (A4, Letter)")
    parser.add_argument("--margin-top", default="20mm", help="上边距")
    parser.add_argument("--margin-bottom", default="20mm", help="下边距")
    parser.add_argument("--margin-left", default="15mm", help="左边距")
    parser.add_argument("--margin-right", default="15mm", help="右边距")
    parser.add_argument("--no-background", action="store_true", help="不打印背景色")
    
    args = parser.parse_args()
    
    result = convert_html_to_pdf_with_options(
        args.input,
        args.output,
        page_size=args.page_size,
        margin_top=args.margin_top,
        margin_bottom=args.margin_bottom,
        margin_left=args.margin_left,
        margin_right=args.margin_right,
        print_background=not args.no_background
    )
    
    if result["status"] == "success":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"PDF generated: {result['output']}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
