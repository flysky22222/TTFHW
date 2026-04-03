# TTFHW 测试过程中使用的所有 Prompts 记录

> 本文件记录本次 openEuler vs Fedora TTFHW 对比测试中，向 AI 模型发出的所有关键 Prompt。
> 目的：供复盘参考，同时为后续测试提供 prompt 模板复用基础。

---

## P-001：任务分析 Prompt

**用途：** 解读 GitHub Issue，提取任务需求

```
分析 https://github.com/flysky22222/TTFHW/issues/1 任务，
然后完成任务分析报告文档，提交到仓库，并关联 issue
```

**输出：** 提取出以下关键信息
- 任务类型：openEuler vs Fedora 社区 TTFHW 对比
- 测试对象：贡献 `git` 软件包
- 四阶段方法论：理解、获取、使用、贡献
- 约束：文档溯源、失败计数（≤10次/阶段）
- 产出物：对比报告 + prompts 文档

---

## P-002：社区贡献流程研究 Prompt

**用途：** 通过 web 搜索研究两个社区的打包贡献完整流程

```
Research the following for a comparative analysis report. I need detailed information 
about the process of contributing/packaging software (specifically the "git" package) 
in both openEuler and Fedora communities.

For each community, find:
1. How to find the right SIG (Special Interest Group) for a package
2. How to set up the local development environment
3. How to write/create a spec file for packaging
4. How to build and test locally (mock, rpmbuild, etc.)
5. How to submit a pull request / contribution

Also find any official documentation URLs for these processes.

Please search the web for:
- openEuler packaging guidelines and contribution process
- Fedora packaging guidelines and contribution process
- Compare the complexity and documentation quality of both

Return detailed findings with URLs for each step.
```

**搜索关键词（实际执行）：**
- `Fedora packaging guidelines contribution process git package 2026`
- `openEuler packaging contribution guide SIG git spec`
- `openEuler community sig-info.yaml packaging requirements`
- `Fedora New Package Process Bugzilla review submission`
- `osc build openEuler OBS local build`
- `mock fedpkg mockbuild Fedora local RPM build`

**输出：** 两社区各五个阶段的详细文档与命令

---

## P-003：openEuler SIG 定位 Prompt

**用途：** 确认 git 包归属的 SIG

```
搜索 openEuler 社区中 git 软件包属于哪个 SIG，
查看 https://gitee.com/openeuler/community/tree/master/sig 目录结构，
确认 dev-utils SIG 是否包含 git 包
```

**结论：** git 包属于 **dev-utils SIG**
- 参考：https://gitee.com/openeuler/community/blob/master/sig/dev-utils/README.md

---

## P-004：Fedora 打包规范要点提取 Prompt

**用途：** 提取 Fedora spec 文件的强制规范，尤其是禁止字段

```
从 https://fedoraproject.org/wiki/Packaging:ReviewGuidelines 提取：
1. spec 文件必须包含的字段
2. 明确禁止出现的字段（MUST NOT）
3. 已废弃不应出现的字段（SHOULD NOT）
4. 提交前的必检项清单
```

**关键发现：**
- 禁止：`Copyright:`、`Packager:`、`Vendor:`、`PreReq:`
- 废弃：`BuildRoot:`、`Group:`、`%clean`
- 必须：rpmlint 清洁通过

---

## P-005：报告生成 Prompt

**用途：** 基于研究结果生成结构化对比报告

```
基于以下研究结果，生成一份完整的 TTFHW 对比分析报告（Markdown 格式），
包含：
1. 方法论说明（四阶段定义）
2. openEuler 完整贡献流程（含所有命令和文档 URL）
3. Fedora 完整贡献流程（含所有命令和文档 URL）
4. 对比分析表格
5. 各阶段耗时估算
6. 对两个社区的改进建议

要求：
- 每个命令都注明文档来源 URL
- 对比表格覆盖：平台、SIG、CLA、Sponsorship、spec规范、构建工具、Review流程、文档质量
- 耗时估算要区分理解/获取/使用/贡献四阶段
```

---

## P-006：工具包设计 Prompt

**用途：** 将测试能力总结为可复用工具，供未来 TTFHW 测试使用

```
把你模拟测试用到的能力可以总结成工具，这样的话我下次做 ttfhw 的时候我就可以
省掉很多 token，你工具要说明如何使用，而且是在其他项目进行 ttfhw 测试的时候
也能使用的那种才行
```

**输出：** `tools/ttfhw-toolkit.md`——包含 6 个标准化工具的完整工具包

---

## Prompt 模式总结

| Prompt ID | 阶段 | 类型 | 关键技巧 |
|-----------|------|------|---------|
| P-001 | 任务理解 | 任务解析 | 直接引用 Issue URL，让模型自动提取结构 |
| P-002 | 信息获取 | 多维搜索 | 明确列出 5 个维度 + 具体包名，避免泛化结果 |
| P-003 | 定位确认 | 精确查询 | 给出具体 URL，要求确认而非探索 |
| P-004 | 规范提取 | 结构化提取 | 用 MUST/SHOULD NOT 等规范语言约束输出格式 |
| P-005 | 报告生成 | 综合输出 | 明确报告结构 + 格式要求 + 内容约束 |
| P-006 | 工具化 | 元任务 | 将过程能力抽象为工具，提升可复用性 |
