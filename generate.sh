#!/usr/bin/env bash
# 一键生成日报/周报/月报
# 用法: ./generate.sh "<prompt>" [项目路径] [输出目录]

set -euo pipefail

PROMPT="${1:-生成本周周报}"
REPO_PATH="${2:-.}"
WORKDIR="${3:-./output}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$WORKDIR"

echo ">>> 1/5 解析 Prompt: $PROMPT"
python3 "$SCRIPT_DIR/scripts/date-range-resolver.py" --prompt "$PROMPT" \
  > "$WORKDIR/report-meta.json"

START_DATE=$(python3 -c "import json; print(json.load(open('$WORKDIR/report-meta.json'))['start_date'])")
END_DATE=$(python3 -c "import json; print(json.load(open('$WORKDIR/report-meta.json'))['end_date'])")
OUTPUT_HTML=$(python3 -c "import json; print(json.load(open('$WORKDIR/report-meta.json'))['output_html'])")
OUTPUT_PDF=$(python3 -c "import json; print(json.load(open('$WORKDIR/report-meta.json'))['output_pdf'])")

echo ">>> 2/5 收集数据 ($START_DATE ~ $END_DATE)"
python3 "$SCRIPT_DIR/scripts/git-analyzer.py" \
  --start-date "$START_DATE" --end-date "$END_DATE" --repo-path "$REPO_PATH" \
  > "$WORKDIR/git-data.json" 2>/dev/null \
  || echo '{"status":"skipped","stats":{},"categories":{}}' > "$WORKDIR/git-data.json"

python3 "$SCRIPT_DIR/scripts/todo-paser.py" --repo-path "$REPO_PATH" \
  > "$WORKDIR/todo-data.json"

python3 "$SCRIPT_DIR/scripts/user-content-paser.py" --repo-path "$REPO_PATH" \
  > "$WORKDIR/user-content-data.json"

echo ">>> 3/5 合并数据"
python3 - << PY
import json
from pathlib import Path

wd = Path("$WORKDIR")
combined = {
    "report_meta": json.loads((wd / "report-meta.json").read_text(encoding="utf-8")),
    "git": json.loads((wd / "git-data.json").read_text(encoding="utf-8")),
    "todo": json.loads((wd / "todo-data.json").read_text(encoding="utf-8")),
    "user_content": json.loads((wd / "user-content-data.json").read_text(encoding="utf-8")),
}
(wd / "combined-data.json").write_text(
    json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8"
)
PY

echo ">>> 4/5 生成 HTML"
python3 "$SCRIPT_DIR/scripts/report-filler.py" \
  --template "$SCRIPT_DIR/assets/report-template.html" \
  --data "$WORKDIR/combined-data.json" \
  --output "$WORKDIR/$OUTPUT_HTML" \
  --report-meta "$WORKDIR/report-meta.json"

echo ">>> 5/5 生成 PDF（可选）"
if python3 "$SCRIPT_DIR/scripts/html-to-pdf.py" \
  --input "$WORKDIR/$OUTPUT_HTML" \
  --output "$WORKDIR/$OUTPUT_PDF" 2>/dev/null; then
  echo "PDF: $WORKDIR/$OUTPUT_PDF"
else
  echo "PDF 跳过（未安装 wkhtmltopdf / weasyprint / pyppeteer）"
fi

echo ""
echo "完成！HTML 报告: $WORKDIR/$OUTPUT_HTML"
