# TTFHW 任务分析报告：openEuler 社区 vs Fedora 社区

> **任务来源**：[Issue #1 - openEuler 社区和 Fedora 社区的 ttfhw 对比](https://github.com/flysky22222/TTFHW/issues/1)
> **测试对象**：将 `git` 软件包引入 openEuler / Fedora 社区的全流程体验
> **报告日期**：2026-04-03
> **方法论**：TTFHW（Time To First Hello World）——记录贡献者从零开始到完成首次贡献的全周期体验，分为理解、获取、使用、贡献四个阶段

---

## 目录

1. [方法论说明](#1-方法论说明)
2. [openEuler 社区贡献流程](#2-openeuler-社区贡献流程)
3. [Fedora 社区贡献流程](#3-fedora-社区贡献流程)
4. [对比分析](#4-对比分析)
5. [文档与资源评分](#5-文档与资源评分)
6. [总结与建议](#6-总结与建议)

---

## 1. 方法论说明

### TTFHW 四阶段定义

| 阶段 | 英文 | 定义 | 计时起点 | 计时终点 |
|------|------|------|---------|---------|
| 理解阶段 | Understanding | 查找并阅读相关文档，理解贡献流程 | 开始搜索 | 能够描述完整流程 |
| 获取阶段 | Acquisition | 配置本地环境、安装工具链 | 开始安装 | 环境就绪可以操作 |
| 使用阶段 | Usage | 编写/修改 spec 文件，本地编译测试 | 开始写 spec | 本地构建通过 |
| 贡献阶段 | Contribution | 提交 PR/补丁，等待 review | 提交 PR | PR 被合并或拒绝 |

### 测试约束

- 所有操作步骤均来源于可检索的官方文档
- 每个命令必须记录来源 URL、文章标题、章节
- 命令与文档保持一致，环境差异需注明
- 模拟人工操作（含失败后的思考时间）
- 每阶段最多允许失败 10 次
- 记录失败断点与耗时

---

## 2. openEuler 社区贡献流程

### 2.1 理解阶段

#### 2.1.1 找到正确的 SIG

openEuler 所有软件包由 SIG（Special Interest Group）负责维护，必须先确认归属 SIG。

**查找方式：**

1. 浏览 SIG 列表：https://www.openeuler.org/en/sig/sig-list/
2. 查看 `openeuler/community` 仓库的 SIG 目录结构：
   ```
   https://gitee.com/openeuler/community/tree/master/sig
   ```
   每个子目录对应一个 SIG，其中 `sig-info.yaml` 列出该 SIG 管理的所有 `src-openeuler/` 仓库。
3. 使用社区 advisor 工具 `psrtool.py` 查询归属 SIG。

**结论：** `git` 包属于 **dev-utils SIG**
- 参考：https://gitee.com/openeuler/community/blob/master/sig/dev-utils/README.md
- AtomGit 镜像：https://atomgit.com/src-openeuler/git

> **理解阶段耗时估算：** ~30–60 分钟（需要理解 SIG 架构、定位正确仓库）

---

#### 2.1.2 核心文档清单

| 文档 | URL | 作用 |
|------|-----|------|
| 完整贡献指南 | https://www.openeuler.org/en/community/contribution/detail.html | 全流程入口 |
| 打包规范（英文） | https://gitee.com/openeuler/community/blob/master/en/contributors/packaging.md | spec 编写规则 |
| 上传软件包指南 | https://www.openeuler.org/en/blog/gitee-cmd/Guide-for-Uploading-a-Software-Package-to-the-openEuler-Community.html | OBS/Gitee 操作步骤 |
| RPM 构建文档 | https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html | 本地 rpmbuild 流程 |
| CLA 签署 | https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340 | 贡献前置条件 |
| git 包 spec（Gitee） | https://gitee.com/src-openeuler/git/blob/master/git.spec | 现有 spec 参考 |

---

### 2.2 获取阶段（环境配置）

#### 前置账户准备

1. 注册 Gitee 账号（https://gitee.com）或 AtomGit 账号（https://atomgit.com）
2. 签署 openEuler CLA：
   ```
   https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340
   ```
   支持个人 / 员工 / 企业三种类型

#### 安装构建工具

```bash
# 在 openEuler 系统上
dnf install rpmdevtools rpm-build make gcc

# 初始化 rpmbuild 工作目录
rpmdev-setuptree
# 创建: ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
```

**来源：** https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html

#### 安装 OBS 客户端（osc）

```bash
dnf install osc
# 配置 OBS 账号（build.openeuler.org）
osc config https://build.openeuler.org
```

> **获取阶段耗时估算：** ~20–40 分钟（工具安装较快，主要时间在 CLA 签署和账号注册）

---

### 2.3 使用阶段（编写 spec & 本地构建）

#### spec 文件强制要求

| 字段 | 要求 |
|------|------|
| `Name` | 必须与仓库名完全匹配 |
| `Version` | 必须与上游版本一致 |
| `Release` | 从 `1` 开始，每次 spec 修改递增，必须含 `%{?dist}` |
| `Summary` | 简短单行描述 |
| `License` | 必须是 SPDX 合规表达式，不得在禁止列表中 |
| `URL` | 必须是可访问的上游项目 URL |
| `Source0` | 必须是可访问的上游 tarball URL |
| `BuildRequires` | 所有构建依赖必须显式列出 |

**openEuler 特有规范：**
- 必须拆分为三个子包：主包（二进制）、`-libs`（库文件）、`-help`（文档）
- 补丁文件必须有描述性命名
- 源码包需上传到 OBS source store

#### 本地构建命令

```bash
# 安装构建依赖
dnf builddep git.spec

# 构建完整 RPM（source + binary）
rpmbuild -ba ~/rpmbuild/SPECS/git.spec

# 仅构建 SRPM（用于上传 OBS）
rpmbuild -bs ~/rpmbuild/SPECS/git.spec
```

#### OBS 本地沙箱构建（推荐，等效 mock）

```bash
# 检出 OBS 项目
osc co home:<your-username> git

# 在干净 chroot 中构建（避免反复上传失败）
osc build openEuler:24.03 x86_64 git.spec
```

> **使用阶段耗时估算：** ~60–120 分钟（首次学习 spec 规范 + 调试构建错误）

---

### 2.4 贡献阶段（提交 PR）

#### 步骤 1：向社区注册新包（仅新包需要）

```bash
# Fork openeuler/community 仓库
git clone https://gitee.com/<you>/community.git

# 编辑 SIG 配置，添加包名
# 修改 sig/dev-utils/sig-info.yaml，在 repositories 下添加：
#   - src-openeuler/git
```

提交 PR 到 `openeuler/community`，CI 机器人合并后自动创建 `src-openeuler/git` 仓库及 OBS 项目。

#### 步骤 2：提交包内容

```bash
# Fork src-openeuler/git 仓库
git clone https://gitee.com/<you>/git.git
cd git

# 添加 spec 文件、源码 tarball、补丁
# 本地验证通过后
git add .
git commit -m "feat: add git package v2.x.x"
git push origin master

# 在 Gitee 上开 PR
```

#### 步骤 3：CI & Review

- CI 机器人自动运行：编译、rpmlint、基础测试
- SIG maintainer（来自 `sig-info.yaml` 的 committers）进行代码 review
- PR 合并后 OBS 自动触发多架构重新构建

**参考文档：**
- https://www.openeuler.org/en/community/contribution/detail.html
- https://gitee.com/openeuler/community/blob/master/en/contributors/packaging.md

> **贡献阶段耗时估算：** ~30–60 分钟（提交到首次 review 反馈，视 SIG 活跃程度）

---

## 3. Fedora 社区贡献流程

### 3.1 理解阶段

#### 3.1.1 包的归属

Fedora 没有强制性的包 SIG 分配机制。任意获得 `packager` 组资格的贡献者均可认领包。

- `git` 包当前维护页：https://src.fedoraproject.org/rpms/git
- 包信息查询：https://packages.fedoraproject.org/
- 维护者联系：`git-maintainers@fedoraproject.org`

**子包列表：** `git`、`git-core`、`git-email`、`perl-Git`、`git-gui`、`gitk` 等

#### 3.1.2 核心文档清单

| 文档 | URL | 作用 |
|------|-----|------|
| 加入 Package Maintainers | https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/ | 全流程入口 |
| 新包提交流程 | https://docs.fedoraproject.org/en-US/package-maintainers/New_Package_Process_for_Existing_Contributors/ | 新包上传步骤 |
| 获得 Sponsor | https://docs.fedoraproject.org/en-US/package-maintainers/How_to_Get_Sponsored_into_the_Packager_Group/ | Sponsorship 流程 |
| 打包教程 | https://docs.fedoraproject.org/en-US/package-maintainers/Packaging_Tutorial/ | 动手教程 |
| 打包规范 | https://docs.fedoraproject.org/en-US/packaging-guidelines/ | 详细规则（极丰富） |
| Review 规范 | https://fedoraproject.org/wiki/Packaging:ReviewGuidelines | PR Review 检查项 |
| Mock 使用 | https://fedoraproject.org/wiki/Using_Mock_to_test_package_builds | 干净 chroot 构建 |
| RPM 打包指南 | https://rpm-packaging-guide.github.io/ | 通用 RPM 教程 |

> **理解阶段耗时估算：** ~20–40 分钟（文档非常完整，英文质量高，入口清晰）

---

### 3.2 获取阶段（环境配置）

#### 前置账户准备

1. 注册 FAS 账号：https://accounts.fedoraproject.org/
2. 在 FAS 门户签署 Fedora CLA（"Agreements" 页面）
3. 上传 SSH 公钥到 FAS（用于推送 dist-git）
4. 注册 Red Hat Bugzilla 账号（邮箱需与 FAS 一致）：https://bugzilla.redhat.com
5. **获取 packager 组 Sponsorship**（见贡献阶段）

#### 安装构建工具链

```bash
# 安装 Fedora 打包工具套件
dnf install fedora-packager rpm-build mock fedpkg rpmlint rpmdevtools koji

# 将用户加入 mock 组（必须）
usermod -a -G mock $USER
# 重新登录使 mock 组生效

# 初始化 rpmbuild 工作目录
rpmdev-setuptree
```

**来源：** https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/

> **获取阶段耗时估算：** ~30–60 分钟（账号多、Sponsorship 可能需等待数天）

---

### 3.3 使用阶段（编写 spec & 本地构建）

#### spec 文件强制要求

| 字段 | 要求 |
|------|------|
| `Name` | 必须与 `%{name}.spec` 文件名匹配 |
| `Version` | 上游版本 |
| `Release` | 从 `1%{?dist}` 开始 |
| `Summary` | 结尾不加句号 |
| `License` | 必须是 Fedora 批准的 SPDX 表达式 |
| `URL` | 上游项目 URL |
| `Source0` | 上游 tarball URL |
| `BuildRequires` | 所有构建依赖必须显式列出，无例外 |

**明确禁止的字段：**
- `Copyright:`、`Packager:`、`Vendor:`、`PreReq:` — **必须不出现**
- `BuildRoot:`、`Group:`、`%clean` 段 — 已废弃，不应出现

**推荐宏：**
```spec
%autosetup
%make_build
%make_install
```

#### 本地构建命令

```bash
# 获取上游源码（通过 spec 中的 Source URL）
spectool -g -R git.spec

# 安装构建依赖
dnf builddep git.spec

# 构建 SRPM
rpmbuild -bs ~/rpmbuild/SPECS/git.spec

# 构建完整 RPM
rpmbuild -ba ~/rpmbuild/SPECS/git.spec
```

#### Mock 干净 chroot 构建（强烈推荐，提交前必做）

```bash
# 在 Fedora Rawhide 干净环境中构建
mock -r fedora-rawhide-x86_64 ~/rpmbuild/SRPMS/git-*.src.rpm

# 或使用 fedpkg 封装命令
fedpkg mockbuild
```

#### rpmlint 检查（提交前必须通过）

```bash
rpmlint ~/rpmbuild/SPECS/git.spec
rpmlint ~/rpmbuild/SRPMS/git-*.src.rpm
rpmlint ~/rpmbuild/RPMS/x86_64/git-*.rpm
```

> **使用阶段耗时估算：** ~60–150 分钟（spec 规范更细致，rpmlint 错误需逐一处理）

---

### 3.4 贡献阶段（提交 PR）

#### 步骤 1：Bugzilla 包 Review 申请

1. 将 `.spec` 和 SRPM 托管到可公开访问的 URL（如 GitHub 或 Fedora People）
2. 在 Bugzilla 提交 Review 申请：
   ```
   https://bugzilla.redhat.com（选择 Fedora New Package 类型）
   ```
   在 description 中提供 SPEC URL 和 SRPM URL
3. 社区 Reviewer 检查并标记每项（`+` 通过 / `-` 失败 / `?` 需澄清）
4. 迭代修改直至 Reviewer 标记 `APPROVED`

#### 步骤 2：申请 dist-git 仓库

```bash
fedpkg request-repo git <bugzilla-ticket-number>
# 仓库创建于 https://src.fedoraproject.org/rpms/git
```

#### 步骤 3：导入并推送

```bash
fedpkg clone git
cd git

# 将已批准的 SRPM 导入 Rawhide 分支
fedpkg import git-*.src.rpm

git commit -m "Initial import"
git push

# 在官方 Koji 上触发构建
fedpkg build
```

#### 步骤 4：为稳定版分支构建

```bash
fedpkg switch-branch f41
git merge main
git push
fedpkg build
```

#### 步骤 5：通过 Bodhi 推送更新

在 https://bodhi.fedoraproject.org 提交 update，从 `updates-testing` 推进到 `stable`。

> **贡献阶段耗时估算：** ~1–7 天（Bugzilla Review 周期不固定，Sponsorship 可能额外等待）

---

## 4. 对比分析

### 4.1 全流程对比表

| 维度 | openEuler | Fedora |
|------|-----------|--------|
| **代码托管平台** | Gitee + AtomGit（迁移中） | src.fedoraproject.org（Pagure） |
| **组织架构** | 强制 SIG 归属，包需注册在 `sig-info.yaml` | 无强制 SIG，任意 sponsored packager 可认领 |
| **CLA** | openEuler CLA（个人/员工/企业） | Fedora CLA via FAS |
| **需要 Sponsorship？** | 否，SIG maintainer 审核 PR 即可 | **是**，必须获得 packager 组 sponsor |
| **spec 规范复杂度** | 中等（规则较简洁，有三子包分拆要求） | 高（规范文档极详尽，禁止字段多，rpmlint 必须通过） |
| **本地 chroot 构建工具** | `osc build`（OBS 客户端） | `mock` 或 `fedpkg mockbuild` |
| **官方构建系统** | OBS（build.openeuler.org） | Koji（koji.fedoraproject.org） |
| **Review 流程** | Gitee/AtomGit PR + CI 机器人 + SIG committer | Bugzilla ticket peer review + mock build + rpmlint |
| **更新推送机制** | OBS 自动多架构重建 | Bodhi update 提交 |
| **文档语言** | 中英双语（部分核心文档仅有中文） | 几乎全英文，覆盖全面 |
| **文档丰富程度** | 中等（存在英文文档缺失） | **非常丰富**（Tutorial、Guidelines、Wiki、Magazine 均有） |
| **新人门槛** | 中（SIG 注册有额外步骤，平台迁移增加摩擦） | 高（Sponsorship 流程最高，但文档指引清晰） |

### 4.2 各阶段耗时对比（估算）

| 阶段 | openEuler | Fedora | 差异说明 |
|------|-----------|--------|---------|
| 理解 | ~30–60 min | ~20–40 min | Fedora 文档更完整，入口更清晰 |
| 获取 | ~20–40 min | ~30–60 min | Fedora 账号体系更复杂，Sponsorship 可能需数天 |
| 使用 | ~60–120 min | ~60–150 min | Fedora 规范检查更严格（rpmlint、禁止字段等） |
| 贡献 | ~30–60 min | ~1–7 天 | Fedora Bugzilla Review 周期不可控 |

### 4.3 核心差异深度分析

#### 4.3.1 包管理架构

openEuler 的 SIG 制度使得每个包都有明确的责任人和分类，但也带来了额外的注册成本——贡献者需要先修改 `community` 仓库注册包，才能实际开始打包工作，增加了贡献摩擦。

Fedora 的无强制 SIG 模型更灵活，任何 sponsored packager 均可认领包，但在 Sponsorship 获取前贡献者处于"观察期"，无法实际推送代码。

#### 4.3.2 代码 Review 流程

openEuler 采用标准 Git PR 工作流（在 Gitee/AtomGit 上），与现代开发习惯高度一致，学习成本低。

Fedora 的 Bugzilla Review 流程较为独特，需要将 spec/SRPM 托管到外部 URL 供审核，且 Bugzilla 的使用界面对新人不友好。这是 Fedora 贡献流程中摩擦最大的环节。

#### 4.3.3 文档质量

Fedora 的官方文档系统（docs.fedoraproject.org）质量显著高于 openEuler，覆盖全面、英文完整、有互动教程。

openEuler 文档存在明显的中英文不对称问题——部分重要文档仅有中文版，对非中文母语的贡献者不友好；AtomGit 平台迁移也导致部分文档链接失效。

#### 4.3.4 工具链

两个社区的基础工具链（rpmbuild、rpmdev-setuptree）一致，但上层工具不同：
- openEuler 使用 `osc`（OBS 客户端），需要额外学习 OBS 概念
- Fedora 使用 `fedpkg`、`mock`、`koji` 三件套，工具更多但各司其职，文档齐全

---

## 5. 文档与资源评分

| 评分维度 | openEuler | Fedora |
|---------|-----------|--------|
| 入门文档完整性 | ★★★☆☆ | ★★★★★ |
| 英文文档质量 | ★★☆☆☆ | ★★★★★ |
| 打包规范清晰度 | ★★★☆☆ | ★★★★☆ |
| 流程可重复性 | ★★★☆☆ | ★★★★☆ |
| 工具链易用性 | ★★★☆☆ | ★★★★☆ |
| 社区响应活跃度 | ★★★☆☆ | ★★★★☆ |

---

## 6. 总结与建议

### 对 openEuler 社区的建议

1. **完善英文文档**：关键贡献流程文档应提供高质量英文版，降低国际化贡献门槛
2. **简化新包注册流程**：SIG 注册 PR 可考虑自动化，减少 `community` 仓库 PR 的等待
3. **文档更新及时性**：AtomGit 平台迁移期间，应同步更新所有文档中的 URL
4. **提供 Quickstart**：为新贡献者提供类似 Fedora Packaging Tutorial 的动手教程

### 对 Fedora 社区的建议

1. **简化 Bugzilla Review 流程**：可考虑迁移至 Pagure PR 方式，降低新人使用 Bugzilla 的门槛
2. **Sponsorship 加速机制**：为有经验的贡献者（来自其他社区）提供更快速的 Sponsorship 通道

### 综合结论

- **对新贡献者最友好（流程理解）**：Fedora（文档完整，教程丰富）
- **对实际贡献最快捷（首次合并）**：openEuler（无 Sponsorship 门槛，PR 流程现代）
- **工具链成熟度**：Fedora 略优
- **社区可持续性**：两者均有大公司（华为/红帽）支持，长期可信

---

## 参考文档

### openEuler
- https://www.openeuler.org/en/community/contribution/detail.html
- https://gitee.com/openeuler/community/blob/master/en/contributors/packaging.md
- https://www.openeuler.org/en/blog/gitee-cmd/Guide-for-Uploading-a-Software-Package-to-the-openEuler-Community.html
- https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html
- https://www.openeuler.org/en/sig/sig-list/
- https://gitee.com/openeuler/community/tree/master/sig
- https://gitee.com/src-openeuler/git/blob/master/git.spec
- https://atomgit.com/src-openeuler/git

### Fedora
- https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/
- https://docs.fedoraproject.org/en-US/package-maintainers/New_Package_Process_for_Existing_Contributors/
- https://docs.fedoraproject.org/en-US/package-maintainers/How_to_Get_Sponsored_into_the_Packager_Group/
- https://docs.fedoraproject.org/en-US/package-maintainers/Packaging_Tutorial/
- https://fedoraproject.org/wiki/Packaging_Guidelines
- https://fedoraproject.org/wiki/Packaging:ReviewGuidelines
- https://fedoraproject.org/wiki/Using_Mock_to_test_package_builds
- https://rpm-packaging-guide.github.io/
- https://src.fedoraproject.org/rpms/git
- https://packages.fedoraproject.org/pkgs/git/git/
