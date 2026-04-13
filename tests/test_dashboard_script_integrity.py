from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_TEMPLATE = REPO_ROOT / "influxbro" / "app" / "templates" / "index.html"


def _extract_script_blocks(html: str) -> list[str]:
    blocks = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    cleaned: list[str] = []
    for block in blocks:
        block = re.sub(r"\{\{.*?\}\}", "0", block, flags=re.S)
        block = re.sub(r"\{%.*?%\}", "", block, flags=re.S)
        cleaned.append(block)
    return cleaned


def test_dashboard_script_blocks_pass_node_check(tmp_path: Path):
    html = INDEX_TEMPLATE.read_text()
    blocks = _extract_script_blocks(html)
    assert blocks, "No script blocks found in dashboard template"

    for idx, block in enumerate(blocks):
        script_path = tmp_path / f"dashboard_script_{idx}.js"
        script_path.write_text(block)
        proc = subprocess.run(
            ["node", "--check", str(script_path)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, (
            f"dashboard script block {idx} failed node --check\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def test_dashboard_critical_functions_are_not_duplicated():
    body = INDEX_TEMPLATE.read_text()
    critical = [
        "highlightOutlierAtIndex",
        "_prepareStep",
        "refreshAll",
        "clearAnalysisCacheForCurrentSeries",
        "showRawManualDialog",
        "promptForValue",
        "editRawValueInline",
        "doRawOverwrite",
    ]
    for name in critical:
        count = len(
            re.findall(rf"^(?:\s*async\s+function|\s*function)\s+{name}\s*\(", body, flags=re.M)
        )
        assert count == 1, f"Expected exactly one definition of {name}, found {count}"


def test_dashboard_raw_undo_listener_exists_only_once():
    body = INDEX_TEMPLATE.read_text()
    marker = "if($rawUndo) $rawUndo.addEventListener('click'"
    assert body.count(marker) == 1
