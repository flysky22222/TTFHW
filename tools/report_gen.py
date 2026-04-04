#!/usr/bin/env python3
"""
report_gen.py — T-06: 从 test_data.json 生成 TTFHW 测试报告（无需 API）

用法:
    # 从测试数据生成报告
    python report_gen.py --data use-cases/openeuler-contributor/test_data.json

    # 指定输出路径
    python report_gen.py --data test_data.json --output report.md

    # 生成数据模板（手动填写后再生成报告）
    python report_gen.py --template UC-07 --output template.json

    # 批量生成所有用例报告
    python report_gen.py --all --base-dir use-cases/
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def fmt_min(minutes) -> str:
    minutes = int(minutes or 0)
    if minutes < 60:
        return f"{minutes} 分钟"
    elif minutes < 1440:
        return f"{minutes/60:.1f} 小时"
    else:
        return f"{minutes/1440:.1f} 天"


def severity_icon(s: str) -> str:
    return {"blocker": "🔴", "major": "🟡", "minor": "🔵"}.get(s, "⚪")


def result_icon(r: str) -> str:
    return {"pass": "✅", "fail": "❌", "partial": "⚠️", "skip": "⏭️"}.get(r, "❓")


PHASE_LABEL = {
    "understanding": "理解阶段",
    "acquisition": "获取阶段",
    "usage": "使用阶段",
    "contribution": "贡献/验证阶段"
}


# ── 报告各节渲染 ──────────────────────────────────────────────────────────────

def render_header(meta: dict) -> str:
    role_cn = "贡献者" if meta.get("role") == "contributor" else "用户"
    return f"""# TTFHW 测试报告：{meta.get('title', '未知')}

> **用例 ID：** {meta.get('use_case_id', '-')}
> **社区/项目：** {meta.get('community', '-')}（{meta.get('domain', '-')}领域）
> **测试角色：** {role_cn}
> **测试目标：** {meta.get('target', '-')}
> **测试日期：** {meta.get('test_date', str(date.today()))}
> **搜索平台：** {', '.join(meta.get('search_platforms', ['Baidu', 'Doubao']))}

---
"""


def render_summary(summary: dict, problems: list) -> str:
    overall = result_icon(summary.get("overall_result", "pass")) + " " + \
              {"pass": "通过", "fail": "失败", "partial": "部分通过"}.get(
                  summary.get("overall_result", "pass"), "未知")
    blockers = [p for p in problems if p.get("severity") == "blocker"]
    majors = [p for p in problems if p.get("severity") == "major"]
    minors = [p for p in problems if p.get("severity") == "minor"]

    lines = [
        "## 测试摘要\n",
        f"| 项目 | 结果 |",
        f"|------|------|",
        f"| 总体结果 | {overall} |",
        f"| 总耗时估算 | {fmt_min(summary.get('total_minutes', 0))} |",
        f"| 摩擦感评分 | {summary.get('friction_score', '-')}/10（1=极流畅，10=极困难）|",
        f"| 文档质量评分 | {'★' * int(summary.get('doc_quality_score', 3))}{'☆' * (5 - int(summary.get('doc_quality_score', 3)))} |",
        f"| 发现问题数 | 🔴 {len(blockers)} 个 blocker，🟡 {len(majors)} 个 major，🔵 {len(minors)} 个 minor |",
        "",
    ]

    if summary.get("key_blockers"):
        lines.append("**关键阻塞点：**")
        for b in summary["key_blockers"]:
            lines.append(f"- {b}")
        lines.append("")

    if summary.get("recommendations"):
        lines.append("**改进建议：**")
        for r in summary["recommendations"]:
            lines.append(f"- {r}")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def render_phase(phase_name: str, phase: dict) -> str:
    label = PHASE_LABEL.get(phase_name, phase_name)
    result = result_icon(phase.get("result", "pass"))
    duration = fmt_min(phase.get("duration_minutes", 0))
    steps = phase.get("steps", [])
    frictions = phase.get("friction_points", [])
    notes = phase.get("notes", "")

    lines = [
        f"### {label}  {result}  _{duration}_\n",
    ]

    if notes:
        lines += [f"> {notes}\n"]

    if steps:
        lines.append("**操作步骤：**\n")
        for i, step in enumerate(steps, 1):
            step_icon = result_icon(step.get("result", "pass"))
            fc = step.get("failure_count", 0)
            fail_note = f"（失败 {fc} 次后成功）" if fc > 0 else ""
            lines.append(f"{i}. {step_icon} {step.get('desc', '')}{fail_note}")
            if step.get("command"):
                lines.append(f"   ```bash\n   {step['command']}\n   ```")
            if step.get("doc_url"):
                title = step.get("doc_title") or step["doc_url"]
                lines.append(f"   📄 [{title}]({step['doc_url']})")
            if step.get("failure_reason"):
                lines.append(f"   ❗ 失败原因：{step['failure_reason']}")
            if step.get("workaround"):
                lines.append(f"   🔧 绕过方式：{step['workaround']}")
            lines.append("")

    if frictions:
        lines.append("**摩擦点：**\n")
        for f in frictions:
            lines.append(f"- ⚠️ {f}")
        lines.append("")

    return "\n".join(lines)


def render_problems_overview(problems: list) -> str:
    if not problems:
        return "## 发现的问题\n\n> 本次测试未发现明显问题。\n\n---\n"

    lines = [
        "## 发现的问题（概览）\n",
        "> 详细问题分析和修复记录见 `fixes.md`\n",
        f"| ID | 阶段 | 严重度 | 问题描述 | 修复状态 |",
        f"|----|------|--------|---------|---------|",
    ]
    for p in problems:
        icon = severity_icon(p.get("severity", "minor"))
        phase = PHASE_LABEL.get(p.get("phase", ""), p.get("phase", "-"))
        fix_status_cn = {
            "open": "待处理", "attempted": "已尝试修复",
            "fixed": "已修复", "wontfix": "不修复"
        }.get(p.get("fix_status", "open"), "待处理")
        lines.append(
            f"| {p.get('id', '-')} | {phase} | {icon} {p.get('severity','').upper()} "
            f"| {p.get('description', '')[:60]} | {fix_status_cn} |"
        )
    lines += ["", "---\n"]
    return "\n".join(lines)


def render_docs_list(phases: dict) -> str:
    seen = set()
    lines = ["## 参考文档\n"]
    for phase_name, phase in phases.items():
        for step in phase.get("steps", []):
            url = step.get("doc_url", "")
            if url and url not in seen:
                seen.add(url)
                title = step.get("doc_title") or url
                lines.append(f"- [{title}]({url})")
    if len(lines) == 1:
        lines.append("_本次测试未记录文档来源_")
    return "\n".join(lines)


def generate_report(data: dict) -> str:
    meta = data.get("meta", {})
    phases = data.get("phases", {})
    problems = data.get("problems", [])
    summary = data.get("summary", {})

    parts = [
        render_header(meta),
        render_summary(summary, problems),
        "## 各阶段详情\n",
    ]
    for phase_name, phase in phases.items():
        parts.append(render_phase(phase_name, phase))
        parts.append("---\n")

    parts.append(render_problems_overview(problems))
    parts.append(render_docs_list(phases))

    return "\n".join(parts)


# ── 修复文档生成 ──────────────────────────────────────────────────────────────

def generate_fixes_doc(data: dict) -> str:
    meta = data.get("meta", {})
    problems = data.get("problems", [])

    if not problems:
        return f"""# 问题修复记录：{meta.get('title', '未知')}

> **用例 ID：** {meta.get('use_case_id', '-')}
> **测试日期：** {meta.get('test_date', str(date.today()))}

本次测试未发现需要记录的问题。
"""

    lines = [
        f"# 问题修复记录：{meta.get('title', '未知')}\n",
        f"> **用例 ID：** {meta.get('use_case_id', '-')}  ",
        f"> **测试日期：** {meta.get('test_date', str(date.today()))}  ",
        f"> **问题总数：** {len(problems)} 个\n",
        "---\n",
    ]

    for p in problems:
        icon = severity_icon(p.get("severity", "minor"))
        phase = PHASE_LABEL.get(p.get("phase", ""), p.get("phase", "-"))
        lines += [
            f"## {p.get('id', 'P-?')} {icon} {p.get('severity', '').upper()}：{p.get('description', '')}\n",
            f"- **发现阶段：** {phase}",
            f"- **修复状态：** {p.get('fix_status', 'open')}",
            "",
            "### 问题描述\n",
            p.get("description", "_未填写_"),
            "",
            "### 证据 / 错误信息\n",
            f"```\n{p.get('evidence', '_未记录_')}\n```" if p.get("evidence") else "_未记录_",
            "",
            "### 修复尝试\n",
            "_TODO: 填写修复步骤_\n" if p.get("fix_status") == "open" else p.get("fix_pr_url", ""),
            "",
            "### 修复结论\n",
            "_TODO: 填写修复结论和建议_",
            "",
            "---\n",
        ]

    return "\n".join(lines)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="从 test_data.json 生成 TTFHW 报告")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data", metavar="JSON", help="test_data.json 路径")
    group.add_argument("--all", action="store_true", help="批量处理所有用例")
    group.add_argument("--template", metavar="UC_ID", help="生成指定用例的数据模板")
    parser.add_argument("--output", default=None, help="输出 report.md 路径")
    parser.add_argument("--base-dir", default="use-cases", help="批量模式的基础目录")
    args = parser.parse_args()

    if args.template:
        from ttfhw_simulator import USE_CASE_MAP
        uc = USE_CASE_MAP.get(args.template)
        if not uc:
            print(f"未知用例: {args.template}")
            sys.exit(1)
        template = {
            "meta": {
                "use_case_id": args.template,
                "title": uc["title"],
                "community": uc["community"],
                "domain": uc["domain"],
                "role": uc["role"],
                "target": uc["target"],
                "test_date": str(date.today()),
                "search_platforms": ["Baidu", "Doubao"]
            },
            "phases": {p: {"result": "pass", "duration_minutes": 0, "steps": [], "friction_points": [], "notes": ""} for p in uc["phases"]},
            "problems": [],
            "summary": {"overall_result": "pass", "total_minutes": 0, "friction_score": 0, "doc_quality_score": 3, "key_blockers": [], "recommendations": []}
        }
        out = args.output or "template.json"
        Path(out).write_text(json.dumps(template, ensure_ascii=False, indent=2))
        print(f"✅ 模板已生成: {out}")
        return

    if args.all:
        base = Path(args.base_dir)
        for data_file in sorted(base.glob("*/test_data.json")):
            data = json.loads(data_file.read_text())
            report = generate_report(data)
            fixes = generate_fixes_doc(data)
            report_path = data_file.parent / "report.md"
            fixes_path = data_file.parent / "fixes.md"
            report_path.write_text(report, encoding="utf-8")
            fixes_path.write_text(fixes, encoding="utf-8")
            print(f"✅ {data_file.parent.name}: report.md + fixes.md")
        return

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"错误: 文件不存在: {args.data}")
        sys.exit(1)

    data = json.loads(data_path.read_text(encoding="utf-8"))
    report = generate_report(data)
    fixes = generate_fixes_doc(data)

    out_dir = data_path.parent
    report_path = Path(args.output) if args.output else out_dir / "report.md"
    fixes_path = out_dir / "fixes.md"

    report_path.write_text(report, encoding="utf-8")
    fixes_path.write_text(fixes, encoding="utf-8")
    print(f"✅ 报告已生成: {report_path}")
    print(f"✅ 修复记录已生成: {fixes_path}")


if __name__ == "__main__":
    main()
