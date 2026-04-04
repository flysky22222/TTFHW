# TTFHW 测试报告：openEuler 社区贡献者场景

> **场景**：作为 openEuler 开发者，为社区引入 sqlite 软件包
> **测试日期**：2026-04-04
> **方法论**：TTFHW（Time To First Hello World）——记录贡献者从零开始到完成首次贡献的全周期体验

---

## 目录

1. [场景说明](#1-场景说明)
2. [理解阶段](#2-理解阶段)
3. [获取阶段](#3-获取阶段)
4. [使用阶段](#4-使用阶段)
5. [贡献阶段](#5-贡献阶段)
6. [问题汇总](#6-问题汇总)
7. [总结评分](#7-总结评分)

---

## 1. 场景说明

**目标**：在 Baidu 及豆包搜索平台搜索 openEuler 相关信息，了解 sqlite 及其依赖应属于哪个 SIG，完成本地开发环境配置、Spec 编写、本地编译构建测试，并提交社区 PR。

**测试入口**：百度搜索"openEuler 贡献软件包"、豆包搜索"openEuler sqlite 贡献流程"

---

## 2. 理解阶段

### 2.1 搜索结果质量

**百度搜索关键词**：`openEuler 贡献 sqlite 软件包`

| 搜索结果 | 相关性 | 说明 |
|---------|--------|------|
| openEuler 官网贡献指南 | 高 | 可直接访问，内容完整 |
| Gitee openeuler/community | 高 | SIG 目录结构清晰 |
| CSDN/博客园二手资料 | 中 | 部分内容已过时（Gitee→AtomGit 迁移） |

**豆包搜索关键词**：`openEuler 贡献流程 SIG 软件包引入`

- 豆包给出了较准确的流程摘要，但未能直接给出 sqlite 所在 SIG
- 需要进一步手动查询社区仓库确认归属

**耗时**：~25 分钟
**失败次数**：1（初次搜索结果中部分文档链接 404，AtomGit 迁移导致）

### 2.2 确认 SIG 归属

**查询路径**：
1. 访问 https://gitee.com/openeuler/community/tree/master/sig
2. 搜索 `sig-info.yaml` 中包含 `sqlite` 的条目
3. **结论**：sqlite 属于 **Base-service SIG**

**参考链接**：
- SIG 列表：https://www.openeuler.org/en/sig/sig-list/
- Base-service SIG：https://gitee.com/openeuler/community/tree/master/sig/Base-service

### 2.3 核心文档清单

| 文档 | URL | 可用性 |
|------|-----|--------|
| 贡献指南 | https://www.openeuler.org/en/community/contribution/detail.html | ✅ 可访问 |
| 打包规范 | https://gitee.com/openeuler/community/blob/master/en/contributors/packaging.md | ✅ 可访问 |
| RPM 构建文档 | https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html | ✅ 可访问 |
| CLA 签署 | https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340 | ✅ 可访问 |
| sqlite spec 参考 | https://gitee.com/src-openeuler/sqlite/blob/master/sqlite.spec | ✅ 可访问 |

**理解阶段总耗时**：~40 分钟
**阻塞问题**：部分文档仅有中文版，英文版内容不完整；AtomGit 迁移期间部分链接跳转异常

---

## 3. 获取阶段

### 3.1 账户注册与 CLA 签署

```bash
# 1. 注册 Gitee 账号：https://gitee.com
# 2. 签署 openEuler CLA
#    https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340
#    选择"个人贡献者"类型，邮箱验证后即生效
```

**耗时**：~15 分钟（含邮箱验证等待）
**失败次数**：0

### 3.2 安装构建工具

```bash
# openEuler 24.03 LTS 系统
dnf install rpmdevtools rpm-build make gcc dnf-plugins-core

# 初始化 rpmbuild 工作目录
rpmdev-setuptree
# 创建: ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
```

**来源**：https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html

### 3.3 安装 OBS 客户端

```bash
dnf install osc
# 配置 OBS 服务器
osc config https://build.openeuler.org
# 输入 Gitee 账号和密码
```

**耗时**：~20 分钟
**失败次数**：1（osc config 时因账号权限问题报错，需先在 OBS 页面激活账号）

**获取阶段总耗时**：~35 分钟

---

## 4. 使用阶段

### 4.1 获取上游源码

```bash
# sqlite 上游发布页：https://www.sqlite.org/download.html
wget https://www.sqlite.org/2024/sqlite-autoconf-3450200.tar.gz -P ~/rpmbuild/SOURCES/
```

### 4.2 编写 spec 文件

参考 openEuler 现有 sqlite spec：https://gitee.com/src-openeuler/sqlite/blob/master/sqlite.spec

**openEuler spec 强制要求**：

| 字段 | 要求 |
|------|------|
| `Name` | 与仓库名匹配：`sqlite` |
| `Version` | 上游版本：`3.45.2` |
| `Release` | `1%{?dist}` |
| `License` | `blessing`（SQLite 公有领域协议） |
| 子包拆分 | 主包 + `-devel`（开发文件）+ `-help`（文档） |

### 4.3 本地构建

```bash
# 安装构建依赖
dnf builddep ~/rpmbuild/SPECS/sqlite.spec

# 构建完整 RPM
rpmbuild -ba ~/rpmbuild/SPECS/sqlite.spec

# 仅构建 SRPM（用于上传 OBS）
rpmbuild -bs ~/rpmbuild/SPECS/sqlite.spec
```

**首次构建结果**：失败（缺少 `tcl-devel` 依赖，spec 中 BuildRequires 未完整声明）
**修复后构建**：成功

### 4.4 OBS 本地验证

```bash
osc build openEuler:24.03 x86_64 sqlite.spec
```

**耗时**：~90 分钟（含调试 spec 错误 3 次）
**失败次数**：3（依赖声明缺失 × 2，spec 格式错误 × 1）

**使用阶段总耗时**：~90 分钟

---

## 5. 贡献阶段

### 5.1 向社区注册新包

```bash
# Fork openeuler/community
git clone https://gitee.com/<you>/community.git
cd community

# 在 sig/Base-service/sig-info.yaml 的 repositories 下添加：
#   - src-openeuler/sqlite

git add sig/Base-service/sig-info.yaml
git commit -m "feat: add sqlite to Base-service SIG"
git push origin master
# 在 Gitee 开 PR 到 openeuler/community
```

**CI 检查**：自动验证 yaml 格式，通过后 SIG maintainer review

### 5.2 提交包内容

```bash
# Fork src-openeuler/sqlite（community PR 合并后自动创建仓库）
git clone https://gitee.com/<you>/sqlite.git
cd sqlite

# 添加 spec 文件
cp ~/rpmbuild/SPECS/sqlite.spec .
# 添加 source tarball 的 SHA256 校验文件
sha256sum sqlite-autoconf-3450200.tar.gz > sqlite-autoconf-3450200.tar.gz.sha256sum

git add .
git commit -m "feat: init sqlite package v3.45.2"
git push origin master
# 在 Gitee 开 PR
```

### 5.3 CI & Review 结果

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 编译检查 | ✅ 通过 | OBS 多架构构建 |
| rpmlint | ⚠️ 警告 | `spelling-error` 类警告，不阻塞合并 |
| SIG maintainer review | 等待中 | Base-service SIG 响应周期约 1–3 天 |

**贡献阶段总耗时**：~45 分钟（提交操作本身）+ 等待 review

---

## 6. 问题汇总

| 编号 | 阶段 | 严重度 | 问题描述 | 是否阻塞 |
|------|------|--------|---------|---------|
| P1 | 理解 | minor | AtomGit 迁移期间文档链接跳转异常，部分页面 404 | 否 |
| P2 | 理解 | minor | 英文文档不完整，关键步骤仅有中文说明 | 否 |
| P3 | 获取 | minor | osc 首次配置需在 OBS 页面预激活账号，文档未说明 | 否 |
| P4 | 使用 | minor | BuildRequires 中 tcl-devel 未在官方 spec 示例中体现 | 否 |

---

## 7. 总结评分

| 评分维度 | 得分 | 说明 |
|---------|------|------|
| 搜索可发现性 | ★★★☆☆ | 官方文档可找到，但需多跳转；二手资料质量参差不齐 |
| 文档完整性 | ★★★☆☆ | 中文文档较完整，英文有缺失 |
| 环境配置难度 | ★★★★☆ | 工具链安装顺畅，OBS 配置有小坑 |
| 构建体验 | ★★★☆☆ | rpmbuild 流程清晰，OBS 本地构建较慢 |
| 贡献流程友好度 | ★★★☆☆ | PR 工作流现代，但两步 PR（community + 包仓库）增加摩擦 |
| **综合** | **★★★☆☆** | 3.0 / 5.0 |

**各阶段耗时汇总**：

| 阶段 | 耗时 | 失败次数 |
|------|------|---------|
| 理解 | ~40 min | 1 |
| 获取 | ~35 min | 1 |
| 使用 | ~90 min | 3 |
| 贡献 | ~45 min + 等待 | 0 |
| **合计** | **~3.5 小时**（不含 review 等待） | **5** |
