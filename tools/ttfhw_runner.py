#!/usr/bin/env python3
"""
ttfhw_runner.py — TTFHW 全流程自动化测试工具（基于 Claude API）

用法:
    # 完整流程：从 Issue URL 到生成报告
    python ttfhw_runner.py --issue-url https://github.com/owner/repo/issues/1 \\
                           --package git \\
                           --communities openEuler Fedora

    # 跳过 Issue 解析，直接指定参数
    python ttfhw_runner.py --package nginx \\
                           --communities Fedora Debian \\
                           --output my_report.md

    # 单独运行某个阶段
    python ttfhw_runner.py --package git --communities openEuler --phase probe
    python ttfhw_runner.py --package git --communities openEuler Fedora --phase report \\
                           --data-file collected_data.json

环境变量:
    ANTHROPIC_API_KEY  必须设置
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("错误: 请先安装 anthropic 包: pip install anthropic")
    sys.exit(1)


# ── 各阶段 Prompt 模板 ────────────────────────────────────────────────────────

PROBE_PROMPT = """
你是一个开源社区贡献流程研究助手。请系统搜集 {community} 社区将 {package}
软件包纳入社区的完整贡献流程，覆盖以下五个维度：

1. SIG/团队定位：如何找到负责该软件包的 SIG 或维护团队
2. 账号与权限：注册账号、签署 CLA、获取提交权限的完整流程
3. 本地环境配置：需要安装哪些工具、如何初始化工作目录（给出具体命令）
4. Spec/包文件要求：该社区的打包规范、强制字段、禁止字段
5. 构建与测试：本地构建命令、chroot 隔离构建、lint 检查
6. 提交与 Review：提交 PR/patch 的方式、Review 流程、合并条件

每个维度必须提供：
- 具体操作步骤（命令级别，可直接执行）
- 对应的官方文档 URL
- 预计耗时
- 潜在失败点及恢复方案

以 JSON 格式输出，结构如下：
{{
  "community": "{community}",
  "package": "{package}",
  "phases": {{
    "understanding": {{
      "steps": [...],
      "docs": [...],
      "estimated_minutes": 0,
      "friction_points": [...]
    }},
    "acquisition": {{...}},
    "usage": {{...}},
    "contribution": {{...}}
  }},
  "key_tools": [...],
  "total_estimated_hours": 0
}}
"""

REPORT_PROMPT = """
基于以下已收集的社区贡献流程数据，生成一份完整的 TTFHW 对比分析报告（Markdown 格式）。

数据：
{data}

报告要求：
1. 方法论说明（TTFHW 四阶段定义）
2. 每个社区按四阶段组织的完整流程（含命令、文档 URL、耗时估算）
3. 全流程对比表（≥10 个维度）
4. 各阶段耗时对比
5. 核心差异深度分析
6. 文档质量评分（五星制）
7. 总结与建议
8. 参考文档列表

测试日期：{date}
格式：GitHub Flavored Markdown，命令使用 ```bash 代码块
"""

ISSUE_PARSE_PROMPT = """
分析以下 GitHub Issue 内容，提取 TTFHW 测试的关键要素，以 JSON 格式输出：

{{
  "package": "要贡献的软件包名",
  "communities": ["社区1", "社区2"],
  "max_failures_per_phase": 10,
  "require_doc_citation": true,
  "deliverables": ["report.md", "prompts.md"],
  "special_constraints": []
}}

Issue 内容：
{content}
"""


# ── 核心函数 ─────────────────────────────────────────────────────────────────

def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 ANTHROPIC_API_KEY")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def call_claude(client: anthropic.Anthropic, prompt: str, max_tokens: int = 4096) -> str:
    """调用 Claude API，返回文本响应。"""
    print(f"  → 调用 Claude API ({len(prompt)} chars prompt)...", end="", flush=True)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    print(" 完成")
    return message.content[0].text


def fetch_issue_content(issue_url: str) -> str:
    """从 GitHub Issue URL 获取内容（使用 requests，不需要 token 对公开 repo）。"""
    try:
        import urllib.request
        # 转换为 API URL
        # https://github.com/owner/repo/issues/123 → https://api.github.com/repos/owner/repo/issues/123
        parts = issue_url.rstrip("/").split("/")
        idx = parts.index("issues")
        owner, repo, issue_num = parts[idx - 2], parts[idx - 1], parts[idx + 1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"

        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3+json",
                                                        "User-Agent": "ttfhw-runner/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return f"Title: {data['title']}\n\nBody:\n{data.get('body', '')}"
    except Exception as e:
        print(f"  警告: 无法自动获取 Issue 内容 ({e})，请手动粘贴")
        return ""


def t01_parse_issue(issue_url: str, client: anthropic.Anthropic) -> dict:
    """T-01: 解析 Issue，提取测试要素。"""
    print("\n[T-01] 解析 Issue...")
    content = fetch_issue_content(issue_url)
    if not content:
        return {}

    response = call_claude(client, ISSUE_PARSE_PROMPT.format(content=content))
    # 提取 JSON（Claude 可能会在 JSON 前后加说明文字）
    import re
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        return json.loads(match.group())
    return {}


def t02_probe_community(community: str, package: str, client: anthropic.Anthropic) -> dict:
    """T-02: 搜集社区贡献流程信息。"""
    print(f"\n[T-02] 探测 {community} 社区（包: {package}）...")
    prompt = PROBE_PROMPT.format(community=community, package=package)
    response = call_claude(client, prompt, max_tokens=8192)

    import re
    match = re.search(r'\{[\s\S]*\}', response)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # 如果 JSON 解析失败，保存原始文本
    return {"community": community, "package": package, "raw": response}


def t06_generate_report(data: dict, client: anthropic.Anthropic) -> str:
    """T-06: 生成最终对比报告。"""
    print("\n[T-06] 生成对比报告...")
    prompt = REPORT_PROMPT.format(
        data=json.dumps(data, ensure_ascii=False, indent=2),
        date=date.today().isoformat()
    )
    return call_claude(client, prompt, max_tokens=8192)


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TTFHW 全流程自动化测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--issue-url", help="GitHub Issue URL（用于 T-01 自动解析）")
    parser.add_argument("--package", help="要测试的软件包名，如 git、nginx")
    parser.add_argument("--communities", nargs="+", help="目标社区列表，如 openEuler Fedora")
    parser.add_argument("--phase", choices=["all", "parse", "probe", "report"],
                        default="all", help="运行指定阶段（默认 all）")
    parser.add_argument("--data-file", help="已有数据文件路径（用于跳过探测阶段直接生成报告）")
    parser.add_argument("--output", default="report.md", help="报告输出路径（默认 report.md）")
    parser.add_argument("--save-data", default="ttfhw_data.json", help="中间数据保存路径")

    args = parser.parse_args()

    # 验证参数
    if not args.package and not args.issue_url and not args.data_file:
        parser.error("请提供 --package 或 --issue-url 或 --data-file")

    client = get_client()
    collected_data = {}

    # ── 阶段 1: 解析 Issue ──
    if args.phase in ("all", "parse") and args.issue_url:
        issue_data = t01_parse_issue(args.issue_url, client)
        if issue_data:
            args.package = args.package or issue_data.get("package")
            args.communities = args.communities or issue_data.get("communities", [])
            print(f"  Issue 解析结果: package={args.package}, communities={args.communities}")

    # ── 阶段 2: 探测社区 ──
    if args.phase in ("all", "probe"):
        if not args.package:
            parser.error("需要 --package 参数")
        if not args.communities:
            parser.error("需要 --communities 参数")

        collected_data["package"] = args.package
        collected_data["communities_data"] = []

        for community in args.communities:
            data = t02_probe_community(community, args.package, client)
            collected_data["communities_data"].append(data)

        # 保存中间数据
        data_path = Path(args.save_data)
        data_path.write_text(json.dumps(collected_data, ensure_ascii=False, indent=2))
        print(f"\n  中间数据已保存: {data_path}")

    # ── 阶段 3: 加载已有数据 ──
    if args.data_file and not collected_data:
        data_path = Path(args.data_file)
        if not data_path.exists():
            print(f"错误: 数据文件不存在: {args.data_file}")
            sys.exit(1)
        collected_data = json.loads(data_path.read_text())
        print(f"  已加载数据文件: {args.data_file}")

    # ── 阶段 4: 生成报告 ──
    if args.phase in ("all", "report") and collected_data:
        report_md = t06_generate_report(collected_data, client)
        output_path = Path(args.output)
        output_path.write_text(report_md, encoding="utf-8")
        print(f"\n✅ 报告已生成: {output_path} ({len(report_md)} chars)")
    elif args.phase == "report" and not collected_data:
        print("错误: 生成报告需要 --data-file 或先运行 probe 阶段")
        sys.exit(1)


if __name__ == "__main__":
    main()
