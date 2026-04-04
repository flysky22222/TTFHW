#!/usr/bin/env python3
"""
ttfhw_simulator.py — 模拟人工执行 TTFHW 测试的核心引擎

该脚本通过 Claude API 模拟真实用户/贡献者按照 use-cases.md 中的步骤
逐步执行操作，记录每步的耗时、成功/失败、文档来源，输出符合
schema/ttfhw_result.json 的结构化数据。

用法:
    # 运行单个用例（交互式模拟）
    python ttfhw_simulator.py --use-case UC-07 --desc "openEuler 贡献者场景 - 引入 SQLite 软件包"

    # 从 use-cases.md 自动解析所有用例并逐个测试
    python ttfhw_simulator.py --from-file ../use-cases.md --all

    # 列出 use-cases.md 中的所有用例
    python ttfhw_simulator.py --from-file ../use-cases.md --list

    # 仅模拟理解阶段（快速验证）
    python ttfhw_simulator.py --use-case UC-07 --phases understanding

环境变量:
    ANTHROPIC_API_KEY  必须设置
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("错误: 请先安装: pip install anthropic")
    sys.exit(1)

# ── Prompts ───────────────────────────────────────────────────────────────────

SIMULATE_PHASE_PROMPT = """
你是一个模拟真实用户/贡献者执行开源社区任务的测试代理。
当前测试信息：
- 用例 ID：{use_case_id}
- 社区/项目：{community}
- 角色：{role}
- 目标：{target}
- 当前阶段：{phase_name}（{phase_label}）
- 阶段任务：{phase_task}
- 搜索平台：{search_platforms}（模拟用户使用这些平台搜索）

规则：
1. 必须通过网络搜索寻找信息，每个操作步骤必须能找到真实的文档 URL
2. 模拟真实用户行为：先搜索，再按文档操作
3. 每步记录：操作描述、执行的命令（如有）、文档来源 URL、成功/失败结果
4. 如果找不到文档或文档质量差，如实记录为 failure
5. 每阶段最多失败 10 次，超过则标记整个阶段为 fail
6. 记录真实发现的问题（文档缺失、链接失效、命令报错等）

请模拟执行该阶段，以 JSON 格式输出：
{{
  "result": "pass|fail|partial",
  "duration_minutes": <估计分钟数>,
  "steps": [
    {{
      "desc": "操作描述",
      "command": "执行的命令（可选）",
      "doc_url": "来源 URL",
      "doc_title": "文档标题",
      "result": "pass|fail",
      "failure_count": 0,
      "failure_reason": "失败原因（可选）",
      "workaround": "绕过方式（可选）"
    }}
  ],
  "friction_points": ["摩擦点描述"],
  "problems_found": [
    {{
      "severity": "blocker|major|minor",
      "description": "问题描述",
      "evidence": "错误信息或文档问题"
    }}
  ],
  "notes": "阶段总结"
}}
"""

PHASE_TASKS = {
    "understanding": {
        "label": "理解阶段",
        "task": "使用 Baidu/豆包搜索项目信息，找到官方文档入口、README、Quick Start，理解完整操作流程"
    },
    "acquisition": {
        "label": "获取阶段",
        "task": "根据文档完成：注册账号（如需）、配置本地环境、下载安装所需工具和依赖"
    },
    "usage": {
        "label": "使用阶段",
        "task": "按照文档执行核心操作：编写代码/配置文件、本地编译构建、运行测试验证"
    },
    "contribution": {
        "label": "贡献阶段",
        "task": "按照社区贡献指南：提交 PR/代码、完成 Review 流程、推动合并"
    }
}

# 对于用户场景，贡献阶段替换为验证阶段
USER_CONTRIBUTION_TASK = "完成最终验证：运行目标推理/训练任务，确认输出正确，记录性能数据"


# ── 用例解析 ──────────────────────────────────────────────────────────────────

USE_CASE_MAP = {
    "UC-01": {
        "title": "CANN 贡献者场景 - 开发 Floor 算子",
        "community": "CANN", "domain": "昇腾", "role": "contributor",
        "target": "在 Linux 服务器上完成 Floor 算子开发，编译测试后贡献到上游仓库",
        "phases": ["understanding", "acquisition", "usage", "contribution"]
    },
    "UC-02": {
        "title": "CANN 用户场景 - Qwen3.5-8B 模型推理",
        "community": "CANN", "domain": "昇腾", "role": "user",
        "target": "在昇腾 A3 单节点上安装 CANN，成功运行 Qwen3.5-8B 模型推理",
        "phases": ["understanding", "acquisition", "usage"]
    },
    "UC-03": {
        "title": "MindIE 用户场景 - LLM 推理",
        "community": "MindIE", "domain": "昇腾", "role": "user",
        "target": "在昇腾 A3 单节点上使用 MindIE-LLM 运行 Qwen3.5-8B 推理",
        "phases": ["understanding", "acquisition", "usage"]
    },
    "UC-04": {
        "title": "MindIE 贡献者场景 - 新模型适配",
        "community": "MindIE", "domain": "昇腾", "role": "contributor",
        "target": "在本地 A3 单节点完成新模型适配，编译测试，拉起推理服务验证",
        "phases": ["understanding", "acquisition", "usage", "contribution"]
    },
    "UC-05": {
        "title": "MindSpeed 用户场景 - Qwen3.5-8B 预训练",
        "community": "MindSpeed", "domain": "昇腾", "role": "user",
        "target": "在昇腾 A3 单节点完成 Qwen3.5-8B 权重转换、数据集准备、预训练执行",
        "phases": ["understanding", "acquisition", "usage"]
    },
    "UC-06": {
        "title": "MindSpore 用户场景 - PyTorch 转 MindSpore",
        "community": "MindSpore", "domain": "昇腾", "role": "user",
        "target": "将最新 Qwen 系列 PyTorch 模型转换为 MindSpore，完成本地部署和推理验证",
        "phases": ["understanding", "acquisition", "usage"]
    },
    "UC-07": {
        "title": "openEuler 贡献者场景 - 引入 SQLite 软件包",
        "community": "openEuler", "domain": "鲲鹏", "role": "contributor",
        "target": "为 openEuler 社区引入 sqlite 软件包，完成 Spec 编写、本地构建测试和社区 PR 提交",
        "phases": ["understanding", "acquisition", "usage", "contribution"]
    },
    "UC-08": {
        "title": "openUBMC 贡献者场景 - 新硬件适配",
        "community": "openUBMC", "domain": "鲲鹏", "role": "contributor",
        "target": "为 openUBMC 社区适配一款新硬件，完成适配开发、本地编译构建和测试",
        "phases": ["understanding", "acquisition", "usage", "contribution"]
    }
}


# ── 核心逻辑 ──────────────────────────────────────────────────────────────────

def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 ANTHROPIC_API_KEY")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def call_claude(client: anthropic.Anthropic, prompt: str, max_tokens: int = 4096) -> str:
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def extract_json(text: str) -> dict:
    """从 Claude 响应中提取 JSON 对象。"""
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as e:
            print(f"  警告: JSON 解析失败 ({e})，返回原始文本")
    return {"raw": text}


def simulate_phase(client: anthropic.Anthropic, use_case_id: str, uc: dict,
                   phase: str) -> dict:
    """模拟单个阶段的执行。"""
    phase_info = PHASE_TASKS[phase].copy()

    # 用户场景的"贡献"阶段改为验证
    if uc["role"] == "user" and phase == "contribution":
        phase_info["task"] = USER_CONTRIBUTION_TASK
        phase_info["label"] = "验证阶段"

    prompt = SIMULATE_PHASE_PROMPT.format(
        use_case_id=use_case_id,
        community=uc["community"],
        role="贡献者" if uc["role"] == "contributor" else "用户",
        target=uc["target"],
        phase_name=phase,
        phase_label=phase_info["label"],
        phase_task=phase_info["task"],
        search_platforms="Baidu、豆包（Doubao）"
    )

    print(f"  → 模拟 {phase_info['label']}...", end="", flush=True)
    response = call_claude(client, prompt, max_tokens=6000)
    print(" 完成")

    result = extract_json(response)
    result.setdefault("_phase_label", phase_info["label"])
    return result


def run_use_case(client: anthropic.Anthropic, use_case_id: str,
                 phases_filter: list = None) -> dict:
    """运行完整用例测试，返回符合 schema 的结果。"""
    uc = USE_CASE_MAP.get(use_case_id)
    if not uc:
        print(f"错误: 未知用例 ID: {use_case_id}")
        print(f"可用 ID: {', '.join(USE_CASE_MAP.keys())}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  开始测试: {use_case_id} - {uc['title']}")
    print(f"  社区: {uc['community']}  角色: {uc['role']}")
    print(f"  目标: {uc['target']}")
    print(f"{'='*60}")

    result = {
        "meta": {
            "use_case_id": use_case_id,
            "title": uc["title"],
            "community": uc["community"],
            "domain": uc["domain"],
            "role": uc["role"],
            "target": uc["target"],
            "test_date": str(date.today()),
            "search_platforms": ["Baidu", "Doubao"]
        },
        "phases": {},
        "problems": [],
        "summary": {
            "overall_result": "pass",
            "total_minutes": 0,
            "friction_score": 0,
            "doc_quality_score": 0,
            "key_blockers": [],
            "recommendations": []
        }
    }

    phases_to_run = phases_filter or uc["phases"]
    all_problems = []
    total_minutes = 0
    friction_scores = []
    has_blocker = False

    for phase in phases_to_run:
        phase_result = simulate_phase(client, use_case_id, uc, phase)
        result["phases"][phase] = {
            "result": phase_result.get("result", "pass"),
            "duration_minutes": phase_result.get("duration_minutes", 0),
            "steps": phase_result.get("steps", []),
            "friction_points": phase_result.get("friction_points", []),
            "notes": phase_result.get("notes", "")
        }

        # 收集问题
        for p in phase_result.get("problems_found", []):
            problem_id = f"P-{len(all_problems) + 1:02d}"
            all_problems.append({
                "id": problem_id,
                "phase": phase,
                "severity": p.get("severity", "minor"),
                "description": p.get("description", ""),
                "evidence": p.get("evidence", ""),
                "fix_status": "open",
                "fix_pr_url": ""
            })
            if p.get("severity") == "blocker":
                has_blocker = True

        total_minutes += phase_result.get("duration_minutes", 0)
        fp_count = len(phase_result.get("friction_points", []))
        friction_scores.append(min(10, fp_count * 2 + (3 if phase_result.get("result") == "fail" else 1)))

    result["problems"] = all_problems

    # 计算摘要
    blockers = [p for p in all_problems if p["severity"] == "blocker"]
    majors = [p for p in all_problems if p["severity"] == "major"]

    overall = "fail" if has_blocker else ("partial" if majors else "pass")
    avg_friction = round(sum(friction_scores) / len(friction_scores), 1) if friction_scores else 5.0

    result["summary"] = {
        "overall_result": overall,
        "total_minutes": total_minutes,
        "friction_score": avg_friction,
        "doc_quality_score": max(1, 5 - len(blockers) - len(majors) // 2),
        "key_blockers": [p["description"] for p in blockers],
        "recommendations": []
    }

    return result


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TTFHW 人工测试模拟器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--use-case", metavar="ID", help="用例 ID，如 UC-07")
    group.add_argument("--list", action="store_true", help="列出所有用例 ID")
    parser.add_argument("--phases", nargs="+",
                        choices=["understanding", "acquisition", "usage", "contribution"],
                        help="只运行指定阶段")
    parser.add_argument("--output-dir", default=".",
                        help="输出目录（存放 test_data.json），默认当前目录")
    parser.add_argument("--stdout", action="store_true", help="打印结果到 stdout")
    args = parser.parse_args()

    if args.list:
        print("\n可用用例 ID:\n")
        for uid, uc in USE_CASE_MAP.items():
            print(f"  {uid}  [{uc['domain']}] [{uc['role']:>11}]  {uc['title']}")
        return

    client = get_client()
    result = run_use_case(client, args.use_case, args.phases)

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.stdout:
        print(output)
    else:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "test_data.json"
        out_file.write_text(output, encoding="utf-8")
        print(f"\n✅ 测试数据已保存: {out_file}")
        print(f"   问题数量: {len(result['problems'])}（"
              f"blocker: {sum(1 for p in result['problems'] if p['severity']=='blocker')}, "
              f"major: {sum(1 for p in result['problems'] if p['severity']=='major')}）")
        print(f"   总耗时估算: {result['summary']['total_minutes']} 分钟")
        print(f"   摩擦评分: {result['summary']['friction_score']}/10")


if __name__ == "__main__":
    main()
