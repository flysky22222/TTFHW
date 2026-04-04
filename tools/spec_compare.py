#!/usr/bin/env python3
"""
spec_compare.py — T-04: 下载并对比两个社区的 RPM spec 文件规范差异

用法:
    # 从 URL 直接对比两个 spec 文件
    python spec_compare.py --urls https://gitee.com/.../git.spec https://src.fedoraproject.org/.../git.spec

    # 从本地文件对比
    python spec_compare.py --files openeuler.spec fedora.spec

    # 仅解析单个 spec 文件
    python spec_compare.py --files mypkg.spec --single

    # 输出 JSON 格式（供 report_gen.py 使用）
    python spec_compare.py --files a.spec b.spec --json
"""

import argparse
import re
import sys
import json
import urllib.request
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Spec 字段解析 ─────────────────────────────────────────────────────────────

# 已知在 Fedora 中明确禁止的字段
FEDORA_FORBIDDEN = {"Copyright", "Packager", "Vendor", "PreReq"}
# 已知在 Fedora 中已废弃的字段/宏
FEDORA_DEPRECATED = {"BuildRoot", "Group", "%clean"}
# 所有常见 spec 顶层标签
KNOWN_TAGS = {
    "Name", "Version", "Release", "Summary", "License", "URL",
    "Source0", "Source1", "Patch0", "Patch1",
    "BuildRequires", "Requires", "Provides", "Obsoletes", "Conflicts",
    "BuildArch", "ExclusiveArch", "Description",
    "Copyright", "Packager", "Vendor", "PreReq", "BuildRoot", "Group",
    "Epoch", "AutoReq", "AutoProv",
}


@dataclass
class SpecInfo:
    """解析一个 spec 文件提取出的关键信息。"""
    source: str                          # 文件名或 URL
    present_tags: dict = field(default_factory=dict)   # tag -> value
    missing_mandatory: list = field(default_factory=list)
    forbidden_found: list = field(default_factory=list)
    deprecated_found: list = field(default_factory=list)
    subpackages: list = field(default_factory=list)    # %package 声明
    has_autosetup: bool = False
    has_make_build: bool = False
    has_make_install: bool = False
    patches: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    build_requires: list = field(default_factory=list)
    raw_lines: int = 0


MANDATORY_TAGS = ["Name", "Version", "Release", "Summary", "License", "URL", "Source0"]


def parse_spec(content: str, source: str = "unknown") -> SpecInfo:
    info = SpecInfo(source=source)
    info.raw_lines = len(content.splitlines())

    for line in content.splitlines():
        stripped = line.strip()

        # 提取 tag: value
        tag_match = re.match(r'^(\w[\w()]*)\s*:\s*(.*)', stripped)
        if tag_match:
            tag, value = tag_match.group(1), tag_match.group(2).strip()
            info.present_tags[tag] = value
            if tag in FEDORA_FORBIDDEN:
                info.forbidden_found.append(tag)
            if tag in FEDORA_DEPRECATED:
                info.deprecated_found.append(tag)
            if tag == "BuildRequires":
                info.build_requires.append(value)
            if re.match(r'^Source\d+$', tag):
                info.sources.append(value)
            if re.match(r'^Patch\d+$', tag):
                info.patches.append(value)

        # 检测子包
        if re.match(r'^%package\s+', stripped):
            pkg_name = re.sub(r'^%package\s+', '', stripped)
            info.subpackages.append(pkg_name)

        # 检测废弃宏（在脚本段中）
        if "%clean" in stripped:
            info.deprecated_found.append("%clean")
        if "BuildRoot" in stripped and "BuildRoot:" not in stripped:
            # 在脚本段中使用 BuildRoot 变量
            pass

        # 推荐宏检测
        if "%autosetup" in stripped:
            info.has_autosetup = True
        if "%make_build" in stripped:
            info.has_make_build = True
        if "%make_install" in stripped:
            info.has_make_install = True

    # 检查必填字段缺失
    for tag in MANDATORY_TAGS:
        if tag not in info.present_tags:
            info.missing_mandatory.append(tag)

    # 去重
    info.forbidden_found = list(set(info.forbidden_found))
    info.deprecated_found = list(set(info.deprecated_found))

    return info


# ── 获取 spec 内容 ─────────────────────────────────────────────────────────────

def fetch_url(url: str) -> str:
    """从 URL 下载文本内容。自动处理 Gitee/GitHub raw URL 转换。"""
    # Gitee HTML 页面 → raw 链接转换
    if "gitee.com" in url and "/blob/" in url:
        url = url.replace("gitee.com", "gitee.com").replace("/blob/", "/raw/")
    # GitHub HTML 页面 → raw 链接转换
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    print(f"  下载: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "ttfhw-spec-compare/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  错误: 无法下载 {url}: {e}")
        sys.exit(1)


# ── 输出格式 ──────────────────────────────────────────────────────────────────

def print_single(info: SpecInfo):
    print(f"\n{'='*60}")
    print(f"  Spec 解析结果: {info.source}")
    print(f"{'='*60}")
    print(f"  总行数       : {info.raw_lines}")
    print(f"  子包数量     : {len(info.subpackages)}  {info.subpackages or ''}")
    print(f"  Source 文件  : {len(info.sources)}")
    print(f"  Patch 数量   : {len(info.patches)}")
    print(f"  BuildRequires: {len(info.build_requires)}")
    print(f"  %autosetup   : {'✅' if info.has_autosetup else '❌'}")
    print(f"  %make_build  : {'✅' if info.has_make_build else '❌'}")
    print(f"  %make_install: {'✅' if info.has_make_install else '❌'}")

    if info.missing_mandatory:
        print(f"\n  ⚠️  缺失必填字段: {info.missing_mandatory}")
    else:
        print(f"\n  ✅ 所有必填字段均存在")

    if info.forbidden_found:
        print(f"  ❌ 发现禁止字段 (Fedora): {info.forbidden_found}")
    if info.deprecated_found:
        print(f"  ⚠️  发现废弃字段: {info.deprecated_found}")

    print(f"\n  主要字段:")
    for tag in ["Name", "Version", "Release", "License", "URL"]:
        val = info.present_tags.get(tag, "<未找到>")
        print(f"    {tag:15}: {val}")


def print_diff_table(a: SpecInfo, b: SpecInfo):
    label_a = Path(a.source).name if "/" not in a.source else a.source.split("/")[-1]
    label_b = Path(b.source).name if "/" not in b.source else b.source.split("/")[-1]

    col = 28
    print(f"\n{'='*70}")
    print(f"  对比: {label_a}  vs  {label_b}")
    print(f"{'='*70}")
    print(f"  {'维度':<22} {label_a[:col]:<{col}} {label_b[:col]:<{col}}")
    print(f"  {'-'*22} {'-'*col} {'-'*col}")

    rows = [
        ("总行数",       str(a.raw_lines),              str(b.raw_lines)),
        ("子包数量",     str(len(a.subpackages)),        str(len(b.subpackages))),
        ("Source 文件",  str(len(a.sources)),            str(len(b.sources))),
        ("Patch 数量",   str(len(a.patches)),            str(len(b.patches))),
        ("BuildRequires",str(len(a.build_requires)),     str(len(b.build_requires))),
        ("%autosetup",   "✅" if a.has_autosetup else "❌", "✅" if b.has_autosetup else "❌"),
        ("%make_build",  "✅" if a.has_make_build else "❌", "✅" if b.has_make_build else "❌"),
        ("缺失必填字段", str(a.missing_mandatory) or "无", str(b.missing_mandatory) or "无"),
        ("禁止字段",     str(a.forbidden_found) or "无", str(b.forbidden_found) or "无"),
        ("废弃字段",     str(a.deprecated_found) or "无",str(b.deprecated_found) or "无"),
    ]
    for label, va, vb in rows:
        print(f"  {label:<22} {va:<{col}} {vb:<{col}}")

    # 共有标签的值差异
    common_tags = set(a.present_tags) & set(b.present_tags)
    diff_tags = [(t, a.present_tags[t], b.present_tags[t])
                 for t in sorted(common_tags)
                 if a.present_tags[t] != b.present_tags[t]]
    if diff_tags:
        print(f"\n  值不同的公共字段:")
        for tag, va, vb in diff_tags[:10]:
            print(f"    {tag:<20} {str(va)[:col]:<{col}} {str(vb)[:col]:<{col}}")

    only_a = sorted(set(a.present_tags) - set(b.present_tags))
    only_b = sorted(set(b.present_tags) - set(a.present_tags))
    if only_a:
        print(f"\n  仅在 {label_a} 中存在的字段: {only_a}")
    if only_b:
        print(f"\n  仅在 {label_b} 中存在的字段: {only_b}")


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="T-04: 对比两个社区的 RPM spec 文件")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--urls", nargs="+", metavar="URL", help="spec 文件的 URL（1 或 2 个）")
    group.add_argument("--files", nargs="+", metavar="FILE", help="本地 spec 文件路径（1 或 2 个）")
    parser.add_argument("--single", action="store_true", help="仅解析单个文件（不对比）")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args()

    # 获取内容
    specs = []
    if args.urls:
        for url in args.urls[:2]:
            content = fetch_url(url)
            specs.append(parse_spec(content, source=url))
    else:
        for fpath in args.files[:2]:
            p = Path(fpath)
            if not p.exists():
                print(f"错误: 文件不存在: {fpath}")
                sys.exit(1)
            specs.append(parse_spec(p.read_text(encoding="utf-8"), source=str(p)))

    if args.json:
        print(json.dumps([asdict(s) for s in specs], ensure_ascii=False, indent=2))
        return

    if len(specs) == 1 or args.single:
        print_single(specs[0])
    else:
        print_single(specs[0])
        print_single(specs[1])
        print_diff_table(specs[0], specs[1])


if __name__ == "__main__":
    main()
