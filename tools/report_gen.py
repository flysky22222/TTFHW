#!/usr/bin/env python3
"""
report_gen.py — T-06: 从 JSON 数据文件生成 TTFHW 对比报告（不调用 Claude API）

本脚本基于结构化 JSON 数据（由 ttfhw_runner.py probe 阶段产出）生成
标准化 Markdown 报告，无需网络连接或 API key。

用法:
    # 从 JSON 数据生成报告
    python report_gen.py --data ttfhw_data.json --output report.md

    # 生成示例数据模板（方便手动填写）
    python report_gen.py --template --output template.json

    # 生成报告并打印到 stdout
    python report_gen.py --data ttfhw_data.json --stdout

数据文件格式（ttfhw_data.json）:
    见 --template 输出
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path


# ── 模板数据结构 ──────────────────────────────────────────────────────────────

TEMPLATE = {
    "package": "git",
    "test_date": str(date.today()),
    "tester": "your-name",
    "communities_data": [
        {
            "community": "openEuler",
            "package": "git",
            "phases": {
                "understanding": {
                    "summary": "查找 SIG 归属，阅读贡献文档",
                    "steps": [
                        {
                            "desc": "浏览 SIG 列表，确认 git 包属于 dev-utils SIG",
                            "command": "",
                            "doc_url": "https://www.openeuler.org/en/sig/sig-list/",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 45,
                    "friction_points": ["部分文档仅有中文版", "Gitee/AtomGit 平台迁移导致链接失效"]
                },
                "acquisition": {
                    "summary": "注册账号、签署 CLA、安装构建工具",
                    "steps": [
                        {
                            "desc": "注册 Gitee 账号并签署 openEuler CLA",
                            "command": "",
                            "doc_url": "https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340",
                            "success": True,
                            "failures": 0
                        },
                        {
                            "desc": "安装 rpmdevtools 和 osc",
                            "command": "dnf install rpmdevtools rpm-build osc",
                            "doc_url": "https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 30,
                    "friction_points": ["OBS 账号需要单独注册"]
                },
                "usage": {
                    "summary": "编写 spec 文件，本地 rpmbuild 和 osc build",
                    "steps": [
                        {
                            "desc": "编写 git.spec，拆分为三个子包（主包/-libs/-help）",
                            "command": "rpmbuild -ba ~/rpmbuild/SPECS/git.spec",
                            "doc_url": "https://gitee.com/openeuler/community/blob/master/en/contributors/packaging.md",
                            "success": True,
                            "failures": 2
                        }
                    ],
                    "estimated_minutes": 90,
                    "friction_points": ["三子包拆分规范初次接触不直观"]
                },
                "contribution": {
                    "summary": "提交 PR 到 src-openeuler/git，CI 检查 + SIG review",
                    "steps": [
                        {
                            "desc": "Fork src-openeuler/git，提交 PR",
                            "command": "git push origin master",
                            "doc_url": "https://www.openeuler.org/en/community/contribution/detail.html",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 45,
                    "friction_points": ["需要先向 community 仓库提 PR 注册包"]
                }
            },
            "key_tools": ["rpmbuild", "osc", "rpmdev-setuptree"],
            "total_estimated_hours": 3.5
        },
        {
            "community": "Fedora",
            "package": "git",
            "phases": {
                "understanding": {
                    "summary": "阅读 Fedora 打包文档，理解 Bugzilla Review 流程",
                    "steps": [
                        {
                            "desc": "阅读 Joining the Package Maintainers 文档",
                            "command": "",
                            "doc_url": "https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 30,
                    "friction_points": []
                },
                "acquisition": {
                    "summary": "注册 FAS + Bugzilla，安装 fedora-packager，获取 Sponsorship",
                    "steps": [
                        {
                            "desc": "注册 FAS 账号、签署 CLA",
                            "command": "",
                            "doc_url": "https://accounts.fedoraproject.org/",
                            "success": True,
                            "failures": 0
                        },
                        {
                            "desc": "安装 fedora-packager 工具套件",
                            "command": "dnf install fedora-packager rpm-build mock fedpkg rpmlint",
                            "doc_url": "https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/",
                            "success": True,
                            "failures": 0
                        },
                        {
                            "desc": "添加用户到 mock 组",
                            "command": "sudo usermod -a -G mock $USER",
                            "doc_url": "https://fedoraproject.org/wiki/Using_Mock_to_test_package_builds",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 45,
                    "friction_points": ["Sponsorship 可能需要等待数天至数周", "需要注册多个账号（FAS + Bugzilla）"]
                },
                "usage": {
                    "summary": "编写 spec，mock 构建，rpmlint 检查",
                    "steps": [
                        {
                            "desc": "编写 spec，运行 mock 干净构建",
                            "command": "mock -r fedora-rawhide-x86_64 ~/rpmbuild/SRPMS/git-*.src.rpm",
                            "doc_url": "https://fedoraproject.org/wiki/Using_Mock_to_test_package_builds",
                            "success": True,
                            "failures": 3
                        },
                        {
                            "desc": "运行 rpmlint 清洁检查",
                            "command": "rpmlint ~/rpmbuild/SPECS/git.spec",
                            "doc_url": "https://docs.fedoraproject.org/en-US/packaging-guidelines/",
                            "success": True,
                            "failures": 1
                        }
                    ],
                    "estimated_minutes": 120,
                    "friction_points": ["rpmlint 规则严格，初次需要多次修正", "禁止字段多，容易遗漏"]
                },
                "contribution": {
                    "summary": "Bugzilla Review 申请 → dist-git 仓库 → fedpkg build → Bodhi 更新",
                    "steps": [
                        {
                            "desc": "在 Bugzilla 提交 Review 申请",
                            "command": "",
                            "doc_url": "https://docs.fedoraproject.org/en-US/package-maintainers/New_Package_Process_for_Existing_Contributors/",
                            "success": True,
                            "failures": 0
                        },
                        {
                            "desc": "申请 dist-git 仓库",
                            "command": "fedpkg request-repo git <bug-number>",
                            "doc_url": "https://docs.fedoraproject.org/en-US/package-maintainers/New_Package_Process_for_Existing_Contributors/",
                            "success": True,
                            "failures": 0
                        },
                        {
                            "desc": "导入并触发 Koji 构建",
                            "command": "fedpkg import git-*.src.rpm && fedpkg build",
                            "doc_url": "https://docs.fedoraproject.org/en-US/package-maintainers/New_Package_Process_for_Existing_Contributors/",
                            "success": True,
                            "failures": 0
                        }
                    ],
                    "estimated_minutes": 2880,
                    "friction_points": ["Bugzilla Review 周期完全不可控（数天至数周）", "Bodhi 更新需要额外操作"]
                }
            },
            "key_tools": ["fedpkg", "mock", "koji", "rpmlint", "spectool"],
            "total_estimated_hours": 50.0
        }
    ]
}


# ── 报告生成 ──────────────────────────────────────────────────────────────────

def format_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} 分钟"
    elif minutes < 1440:
        hours = minutes / 60
        return f"{hours:.1f} 小时"
    else:
        days = minutes / 1440
        return f"{days:.1f} 天"


def render_steps(steps: list) -> str:
    lines = []
    for i, step in enumerate(steps, 1):
        failures = step.get("failures", 0)
        status = "✅" if step.get("success") else "❌"
        fail_note = f"（失败 {failures} 次后成功）" if failures > 0 else ""
        lines.append(f"{i}. {status} {step['desc']}{fail_note}")
        if step.get("command"):
            lines.append(f"   ```bash\n   {step['command']}\n   ```")
        if step.get("doc_url"):
            lines.append(f"   来源: {step['doc_url']}")
    return "\n".join(lines)


def render_community_section(c: dict) -> str:
    community = c.get("community", "未知")
    package = c.get("package", "未知")
    phases = c.get("phases", {})
    key_tools = c.get("key_tools", [])
    total_hours = c.get("total_estimated_hours", 0)

    sections = [f"## {community} 社区贡献流程\n"]
    sections.append(f"**测试软件包：** `{package}`  |  **关键工具：** {', '.join(f'`{t}`' for t in key_tools)}  |  **总估计耗时：** {total_hours} 小时\n")

    phase_names = {
        "understanding": "理解阶段",
        "acquisition": "获取阶段",
        "usage": "使用阶段",
        "contribution": "贡献阶段",
    }
    for phase_key, phase_label in phase_names.items():
        phase = phases.get(phase_key, {})
        if not phase:
            continue
        est = format_minutes(phase.get("estimated_minutes", 0))
        summary = phase.get("summary", "")
        steps = phase.get("steps", [])
        frictions = phase.get("friction_points", [])

        sections.append(f"### {phase_label}（估计耗时：{est}）\n")
        sections.append(f"**概述：** {summary}\n")
        if steps:
            sections.append("**操作步骤：**\n")
            sections.append(render_steps(steps))
            sections.append("")
        if frictions:
            sections.append("**摩擦点：**")
            for f in frictions:
                sections.append(f"- {f}")
            sections.append("")

    return "\n".join(sections)


def render_comparison_table(communities: list) -> str:
    if len(communities) < 2:
        return ""

    a, b = communities[0], communities[1]
    ca, cb = a.get("community", "社区A"), b.get("community", "社区B")
    pa, pb = a.get("phases", {}), b.get("phases", {})

    phase_names = {
        "understanding": "理解阶段",
        "acquisition": "获取阶段",
        "usage": "使用阶段",
        "contribution": "贡献阶段",
    }

    lines = [
        f"## 对比分析\n",
        f"### 各阶段耗时对比\n",
        f"| 阶段 | {ca} | {cb} | 差异说明 |",
        f"|------|------|------|---------|",
    ]
    for phase_key, phase_label in phase_names.items():
        ta = format_minutes(pa.get(phase_key, {}).get("estimated_minutes", 0))
        tb = format_minutes(pb.get(phase_key, {}).get("estimated_minutes", 0))
        frictions_a = pa.get(phase_key, {}).get("friction_points", [])
        frictions_b = pb.get(phase_key, {}).get("friction_points", [])
        note = ""
        if frictions_a and not frictions_b:
            note = f"{ca} 摩擦更多"
        elif frictions_b and not frictions_a:
            note = f"{cb} 摩擦更多"
        elif len(frictions_b) > len(frictions_a):
            note = f"{cb} 摩擦更多"
        elif len(frictions_a) > len(frictions_b):
            note = f"{ca} 摩擦更多"
        lines.append(f"| {phase_label} | {ta} | {tb} | {note} |")

    total_a = format_minutes(int(a.get("total_estimated_hours", 0) * 60))
    total_b = format_minutes(int(b.get("total_estimated_hours", 0) * 60))
    lines.append(f"| **合计** | **{total_a}** | **{total_b}** | |")

    lines += [
        "",
        "### 综合对比\n",
        f"| 维度 | {ca} | {cb} |",
        "|------|------|------|",
        f"| 需要 Sponsorship | 否 | 是（可能等待数天） |",
        f"| PR/Review 方式 | Git PR（Gitee/AtomGit） | Bugzilla ticket |",
        f"| 本地 chroot 构建 | `osc build` | `mock` / `fedpkg mockbuild` |",
        f"| 构建系统 | OBS (build.openeuler.org) | Koji (koji.fedoraproject.org) |",
        f"| 关键工具 | {', '.join(a.get('key_tools', []))} | {', '.join(b.get('key_tools', []))} |",
        "",
    ]
    return "\n".join(lines)


def generate_report(data: dict) -> str:
    package = data.get("package", "未知")
    test_date = data.get("test_date", str(date.today()))
    tester = data.get("tester", "")
    communities = data.get("communities_data", [])

    parts = [
        f"# TTFHW 任务分析报告：{' vs '.join(c['community'] for c in communities)}\n",
        f"> **测试软件包：** `{package}`  ",
        f"> **测试日期：** {test_date}  ",
        *([ f"> **测试者：** {tester}  "] if tester else []),
        f"> **方法论：** TTFHW（Time To First Hello World）\n",
        "---\n",
        "## 方法论说明\n",
        "TTFHW 将贡献者体验分为四个阶段：\n",
        "| 阶段 | 定义 | 计时范围 |",
        "|------|------|---------|",
        "| **理解** | 查找文档、理解贡献流程 | 开始搜索 → 能描述完整流程 |",
        "| **获取** | 配置本地环境、安装工具 | 开始安装 → 环境就绪 |",
        "| **使用** | 编写/修改包文件，本地构建测试 | 开始编写 → 本地构建通过 |",
        "| **贡献** | 提交 PR/patch，等待 Review | 提交 → 合并或拒绝 |\n",
        "---\n",
    ]

    for c in communities:
        parts.append(render_community_section(c))
        parts.append("---\n")

    parts.append(render_comparison_table(communities))

    # 参考文档汇总
    parts.append("## 参考文档\n")
    seen_urls = set()
    for c in communities:
        parts.append(f"### {c.get('community', '未知')}\n")
        for phase in c.get("phases", {}).values():
            for step in phase.get("steps", []):
                url = step.get("doc_url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    parts.append(f"- {url}")
        parts.append("")

    return "\n".join(parts)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="T-06: 从 JSON 数据生成 TTFHW 报告")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data", metavar="JSON", help="输入数据文件路径")
    group.add_argument("--template", action="store_true", help="输出数据模板文件")
    parser.add_argument("--output", default="report.md", help="输出报告路径（默认 report.md）")
    parser.add_argument("--stdout", action="store_true", help="打印到 stdout 而非写文件")
    args = parser.parse_args()

    if args.template:
        out = Path(args.output) if not args.stdout else None
        content = json.dumps(TEMPLATE, ensure_ascii=False, indent=2)
        if args.stdout or out is None:
            print(content)
        else:
            out.write_text(content, encoding="utf-8")
            print(f"✅ 模板已生成: {out}")
        return

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"错误: 文件不存在: {args.data}")
        sys.exit(1)

    data = json.loads(data_path.read_text(encoding="utf-8"))
    report = generate_report(data)

    if args.stdout:
        print(report)
    else:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
        print(f"✅ 报告已生成: {out_path}  ({len(report)} 字符)")


if __name__ == "__main__":
    main()
