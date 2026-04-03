# TTFHW 测试工具包

> **版本：** v1.0
> **适用范围：** 任何开源社区的 TTFHW（Time To First Hello World）可用性测试
> **设计目标：** 将本次 openEuler vs Fedora 测试中用到的 AI 辅助能力标准化为可复用工具，
> 下次执行 TTFHW 时直接复制对应工具的 Prompt 即可，大幅节省 token 和准备时间。

---

## 工具列表

| 工具编号 | 工具名称 | 适用阶段 | 核心能力 |
|---------|---------|---------|---------|
| T-01 | Issue 任务解析器 | 前置 | 从 Issue/需求文档中提取 TTFHW 测试要素 |
| T-02 | 社区信息探针 | 理解 | 系统搜集某社区的贡献流程与文档 |
| T-03 | 环境配置生成器 | 获取 | 生成目标社区的环境搭建步骤 |
| T-04 | Spec 文件分析器 | 使用 | 对比两社区的 spec 规范差异 |
| T-05 | 贡献流程映射器 | 贡献 | 映射完整 PR/Review 流程 |
| T-06 | TTFHW 对比报告生成器 | 输出 | 将收集的信息生成标准化对比报告 |

---

## T-01：Issue 任务解析器

**用途：** 从 GitHub Issue 或需求文档中自动提取 TTFHW 测试的关键要素，避免遗漏约束条件。

**何时使用：** 收到新的 TTFHW 测试任务时，第一步使用。

### Prompt 模板

```
请分析以下 GitHub Issue（或需求描述），提取 TTFHW 测试的关键要素，
并以结构化格式输出：

Issue URL（或内容）：[填入 URL 或粘贴 Issue 内容]

需要提取：
1. 测试目标：要贡献/测试的具体软件包名称
2. 测试社区：涉及哪些开源社区（如 openEuler、Fedora、Debian 等）
3. 四阶段约束：理解/获取/使用/贡献各阶段是否有特殊限制
4. 失败阈值：每阶段最多允许失败次数
5. 必须产出的文件/报告列表
6. 文档溯源要求：是否要求每步操作附上来源 URL
7. 其他特殊约束

输出格式：Markdown 表格 + 约束清单
```

### 示例调用

```
请分析以下 GitHub Issue，提取 TTFHW 测试的关键要素：

Issue URL：https://github.com/flysky22222/TTFHW/issues/1

[按上述模板提取]
```

### 预期输出示例

```markdown
| 要素 | 值 |
|------|-----|
| 测试软件包 | git |
| 测试社区 | openEuler, Fedora |
| 每阶段失败上限 | 10 次 |
| 文档溯源要求 | 是（URL + 标题 + 章节） |
| 必须产出 | report.md, prompts.md |
```

---

## T-02：社区信息探针

**用途：** 系统搜集某个开源社区的完整贡献流程信息，包含所有阶段的文档 URL。

**何时使用：** 针对每个待测社区，在理解阶段使用。每个社区运行一次。

### Prompt 模板

```
请系统搜集 [社区名称] 社区将 [软件包名称] 软件包纳入社区的完整贡献流程。

需要覆盖以下五个维度，每个维度必须提供：
① 具体操作步骤（命令级别）
② 对应的官方文档 URL
③ 潜在的失败点/注意事项

维度清单：
1. SIG/团队定位：如何找到负责该软件包的 SIG 或维护团队
2. 账号与权限：注册账号、签署 CLA、获取提交权限的完整流程
3. 本地环境配置：需要安装哪些工具、如何初始化工作目录
4. Spec 文件要求：该社区的 spec 编写规范、强制字段、禁止字段
5. 构建与测试：本地构建命令、chroot 隔离构建、lint 检查
6. 提交与 Review：提交 PR/patch 的方式、Review 流程、合并条件

额外要求：
- 如果文档有中英文版本，都提供 URL
- 标注哪些步骤可能对新贡献者造成最大摩擦
- 标注哪些步骤有自动化工具辅助

社区：[填入社区名称，如 openEuler / Fedora / Debian / Arch Linux 等]
软件包：[填入包名，如 git / nginx / python3 等]
```

### 示例调用（openEuler）

```
请系统搜集 openEuler 社区将 git 软件包纳入社区的完整贡献流程。
[按上述模板搜集]
```

### 示例调用（Fedora）

```
请系统搜集 Fedora 社区将 git 软件包纳入社区的完整贡献流程。
[按上述模板搜集]
```

### 关键搜索词参考

| 社区 | 推荐搜索词 |
|------|-----------|
| openEuler | `openEuler packaging contribution SIG sig-info.yaml spec requirements` |
| Fedora | `Fedora new package process Bugzilla review fedpkg mock koji` |
| Debian | `Debian new maintainer guide ITP sponsor mentors.debian.net` |
| Arch Linux | `Arch Linux AUR PKGBUILD contribution packaging guidelines` |
| Ubuntu | `Ubuntu MOTU universe packaging contribution PPA` |
| openSUSE | `openSUSE OBS package contribution spec requirements` |

---

## T-03：环境配置生成器

**用途：** 为指定社区生成可直接执行的环境配置脚本（带注释和文档来源）。

**何时使用：** 理解阶段完成后，进入获取阶段时使用。

### Prompt 模板

```
基于以下已知信息，为在 [操作系统发行版] 上向 [社区名称] 贡献 [软件包] 生成完整的环境配置步骤。

已知信息：
[粘贴 T-02 的输出结果]

要求：
1. 输出可直接执行的 bash 命令序列
2. 每条命令上方用注释说明用途
3. 每个关键步骤标注来源 URL
4. 将步骤按以下分类组织：
   a. 账号注册（手动步骤，给出 URL）
   b. 系统工具安装（dnf/apt/pacman 命令）
   c. 权限配置（用户组、CLA 等）
   d. 工作目录初始化
   e. 验证环境就绪（给出验证命令）
5. 标注哪些步骤需要等待人工审核（如 CLA 审批、Sponsor 等）

操作系统：[如 openEuler 24.03 / Fedora 41 / Ubuntu 24.04]
社区：[社区名称]
软件包：[包名]
```

### 预期输出示例

```bash
# ============================================================
# 环境配置：Fedora 贡献者工具链
# 来源：https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/
# ============================================================

# [手动步骤] 注册 FAS 账号（需要浏览器操作）
# URL: https://accounts.fedoraproject.org/

# [手动步骤] 签署 Fedora CLA
# URL: https://accounts.fedoraproject.org/ -> Agreements

# 安装 Fedora 打包工具套件
sudo dnf install -y fedora-packager rpm-build mock fedpkg rpmlint rpmdevtools koji

# 将用户加入 mock 组（必须重新登录才能生效）
sudo usermod -a -G mock $USER

# 初始化 rpmbuild 工作目录
rpmdev-setuptree

# 验证环境就绪
rpm --version && mock --version && fedpkg --version
```

---

## T-04：Spec 文件分析器

**用途：** 对比两个或多个社区的 spec 文件编写规范，生成差异对比表。

**何时使用：** 进入使用阶段，开始编写 spec 文件之前。

### Prompt 模板

```
请对比 [社区A] 和 [社区B] 的 RPM spec 文件编写规范，生成差异对比分析。

对于每个社区，分析：
1. 强制必须包含的字段（MUST）
2. 明确禁止出现的字段（MUST NOT）
3. 推荐但不强制的字段（SHOULD）
4. 已废弃应避免的写法（DEPRECATED）
5. 特有的社区规范（如子包拆分要求、命名约定等）
6. 构建前的自动检查工具（如 rpmlint）及其通过标准

参考现有 spec 文件（如有）：
- [社区A] 的 [包名] spec URL：[填入]
- [社区B] 的 [包名] spec URL：[填入]

输出格式：
- 差异对比表格（按字段维度）
- 各社区特有规范列表
- 新贡献者最容易犯错的点（TOP 5）

社区A：[填入]
社区B：[填入]
软件包：[填入]
```

### 示例调用

```
请对比 openEuler 和 Fedora 的 RPM spec 文件编写规范，生成差异对比分析。

参考现有 spec 文件：
- openEuler 的 git spec URL：https://gitee.com/src-openeuler/git/blob/master/git.spec
- Fedora 的 git spec URL：https://src.fedoraproject.org/rpms/git（通过 fedpkg clone 获取）

[按上述模板分析]
```

---

## T-05：贡献流程映射器

**用途：** 生成从"零基础"到"首次贡献合并"的完整操作路径图，标注每个决策节点。

**何时使用：** 进入贡献阶段前，用于规划完整路径、识别阻塞点。

### Prompt 模板

```
请为 [社区名称] 生成完整的"首次贡献"操作路径图，格式为步骤流程 + 决策树。

要求：
1. 覆盖从零账号到 PR/patch 被合并的所有步骤
2. 标注每个步骤的：
   - 操作类型（手动/命令行/等待）
   - 预计耗时（分钟/小时/天）
   - 失败风险等级（低/中/高）
   - 失败时的恢复方案
3. 标注哪些步骤有硬性等待（如人工 Review、Sponsorship 审批）
4. 标注自动化 CI 覆盖的步骤
5. 给出每个步骤的官方文档 URL

最终输出：
- Mermaid 流程图（可选）
- 步骤表格（含耗时、风险、文档 URL）
- 关键阻塞点清单

社区：[填入]
软件包类型：[填入，如 CLI 工具 / 库 / 字体 / Python 包等]
```

### 示例调用（Fedora）

```
请为 Fedora 社区生成完整的"首次贡献 git 包"操作路径图。
软件包类型：CLI 工具
[按上述模板生成]
```

---

## T-06：TTFHW 对比报告生成器

**用途：** 将 T-02 至 T-05 收集的所有信息综合生成标准化的 TTFHW 对比报告。

**何时使用：** 所有信息收集完成后，最后一步生成最终报告。

### Prompt 模板

```
请基于以下已收集的信息，生成一份完整的 TTFHW 对比分析报告（Markdown 格式）。

== 已收集信息 ==
[粘贴 T-02、T-03、T-04、T-05 的所有输出]

== 报告要求 ==

报告必须包含以下章节：
1. 方法论说明
   - TTFHW 四阶段定义（理解/获取/使用/贡献）
   - 测试约束（失败阈值、文档溯源要求等）

2. [社区A] 贡献流程（按四阶段组织）
   - 每个操作步骤含完整 bash 命令
   - 每个步骤附官方文档来源 URL
   - 各阶段耗时估算

3. [社区B] 贡献流程（同上格式）

4. 对比分析
   - 全流程对比表（≥10 个维度）
   - 各阶段耗时对比表
   - 核心差异深度分析（文字段落）

5. 文档质量评分（五星制，按维度打分）

6. 总结与建议
   - 对各社区的具体改进建议
   - 综合结论（各社区最适合的场景）

7. 参考文档列表

== 格式要求 ==
- 使用 GitHub Flavored Markdown
- 表格使用 Markdown 表格语法
- 命令块使用代码围栏（```bash）
- 文档 URL 使用完整 https:// 链接
- 中文报告（技术术语可保留英文）

社区A：[填入]
社区B：[填入]
测试软件包：[填入]
测试日期：[填入]
```

---

## 快速使用指南

### 场景一：测试一个新社区（如 Debian）

```
步骤 1: 运行 T-01，从 Issue 中提取测试要素
步骤 2: 运行 T-02（针对 Debian），收集完整流程信息
步骤 3: 运行 T-03，生成环境配置脚本
步骤 4: 运行 T-04，分析 spec/包格式规范
步骤 5: 运行 T-05，映射贡献路径
步骤 6: 运行 T-06，生成最终报告
```

### 场景二：复测已测过的社区（更新版本）

```
步骤 1: 直接运行 T-02（指定新版本号）
步骤 2: 对比上次报告，仅记录变更点
步骤 3: 运行 T-06（附上历史报告，要求生成 diff 报告）
```

### 场景三：快速对比两个未知社区

```
并行运行两个 T-02（节省时间）
→ 并行运行 T-03 和 T-04
→ 串行运行 T-05（每个社区）
→ 运行 T-06 生成对比报告
```

---

## Token 节省策略

| 策略 | 节省估算 | 说明 |
|------|---------|------|
| 使用 T-01 预处理 Issue | ~20% | 避免重复解析 Issue 内容 |
| T-02 并行运行多社区 | ~30% | 同时搜集多社区信息，减少重复上下文 |
| T-04 提供现有 spec URL | ~15% | 直接读取 spec 而非让模型猜测规范 |
| 历史报告复用（T-06） | ~40% | 增量更新比全量重新生成省大量 token |
| 使用 T-05 Mermaid 图 | ~10% | 流程图比文字描述更紧凑 |

---

## 工具适用性矩阵

| 工具 | RPM 系社区 | DEB 系社区 | 源码贡献 | Python 包 | JS 包 |
|------|-----------|-----------|---------|---------|------|
| T-01 | ✅ | ✅ | ✅ | ✅ | ✅ |
| T-02 | ✅ | ✅ | ✅ | ✅ | ✅ |
| T-03 | ✅ | ⚠️ 需调整 | ✅ | ⚠️ 需调整 | ⚠️ 需调整 |
| T-04 | ✅ | ⚠️ 改为 deb control | ✅ | ⚠️ 改为 setup.py/pyproject | ⚠️ 改为 package.json |
| T-05 | ✅ | ✅ | ✅ | ✅ | ✅ |
| T-06 | ✅ | ✅ | ✅ | ✅ | ✅ |

> ⚠️ = 可用但需要修改 Prompt 中的技术术语以匹配目标生态系统
