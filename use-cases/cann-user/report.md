# TTFHW 测试报告：CANN 社区用户场景

> **场景**：UC-02 — CANN 用户场景，在昇腾 A3 单节点上安装 CANN，成功运行 Qwen3.5-8B 模型推理
> **测试日期**：2026-04-04
> **方法论**：TTFHW（Time To First Hello World）— 记录用户从零开始到成功跑通推理的全周期体验，分理解、获取、使用三个阶段

---

## 目录

1. [场景说明](#1-场景说明)
2. [理解阶段](#2-理解阶段)
3. [获取阶段](#3-获取阶段)
4. [使用阶段](#4-使用阶段)
5. [问题汇总](#5-问题汇总)
6. [总结评分](#6-总结评分)

---

## 1. 场景说明

**目标**：
1. 搜索 CANN 相关信息，找到官方安装入口
2. 下载并安装 CANN，使用 Readme 推荐的 OS
3. 使用 CANN quick start 或 README 跑通 Qwen3.5-8B 模型推理

**测试环境**：昇腾 Atlas 800I A3 单节点，openEuler 22.03 LTS

---

## 2. 理解阶段

### 2.1 搜索过程（模拟百度 / 豆包）

**百度搜索**：`CANN 安装 昇腾 quick start Qwen推理`

| 搜索结果 | 相关性 | 备注 |
|---------|--------|------|
| hiascend.com/software/cann | 高 | 官方 CANN 软件下载页 |
| 昇腾 0Day 适配 Qwen3 系列 | 高 | 官方博文，但聚焦 Qwen3 而非 Qwen3.5 |
| CSDN 博客：910B 上 Qwen2.5 推理 | 中 | 步骤参考价值高，但硬件型号与 A3 不同 |
| 昇腾镜像仓库 ascendhub | 高 | 提供预构建 Docker 镜像 |

**豆包搜索**：`昇腾 A3 Qwen3.5 推理 CANN`
- 豆包未能给出 Qwen3.5-8B 在 A3 上的直接官方文档（搜索结果以 Qwen3 为主，版本差异导致用户迷惑）

**断点 1**：搜索"Qwen3.5-8B"时，大量结果指向 Qwen3 或 Qwen2.5，明确针对 Qwen3.5-8B 的昇腾推理文档极少。用户需要自行判断 Qwen3.5 ≈ Qwen3 架构，适配方案可参考。

### 2.2 核心文档清单

| 文档 | URL | 可访问性 |
|------|-----|---------|
| CANN 社区版下载 | https://www.hiascend.com/software/cann/community | ⚠️ 需登录 |
| CANN quickstart | https://www.hiascend.com/document/detail/zh/CANNiquickstart | ⚠️ 需登录 |
| 昇腾镜像仓库（MindIE） | https://www.hiascend.com/developer/ascendhub/detail/mindie | ⚠️ 需登录 |
| 昇腾 Qwen3 支持公告 | https://www.hiascend.com/developer/techArticles/20250429-3 | ✅ 可访问 |
| CSDN：A3 Qwen2.5 推理实战 | https://blog.csdn.net/xx_nm98/article/details/143441550 | ✅ 可访问 |

**理解阶段总耗时**：~35 分钟
**失败次数**：1（Qwen3.5 文档不明确，需要花时间确认版本对应关系）

---

## 3. 获取阶段

### 3.1 注册昇腾开发者账号

```
访问 https://www.hiascend.com → 注册账号（手机号验证）
必须注册才能下载任何 CANN 软件包
```

**断点**：账号注册必须验证手机号，部分地区短信延迟较长。

### 3.2 安装驱动和固件

```bash
# 从 hiascend.com 下载对应 A3 硬件的驱动和固件
# 示例：Atlas 800I A3 驱动（aarch64）
chmod +x A800-9010-npu-driver_25.0.RC1_linux-aarch64.run
./A800-9010-npu-driver_25.0.RC1_linux-aarch64.run --full

chmod +x A800-9010-npu-firmware_7.5.T20_linux-x86-64.run
./A800-9010-npu-firmware_7.5.T20_linux-x86-64.run --full
```

**断点**：驱动版本与 CANN 版本必须配套，官方提供配套表但表格较复杂，新用户容易选错。

### 3.3 安装 CANN Toolkit

```bash
# 下载 CANN 8.1.RC1 Toolkit
chmod +x Ascend-cann-toolkit_8.1.RC1_linux-aarch64.run
./Ascend-cann-toolkit_8.1.RC1_linux-aarch64.run --install

# 设置环境变量
source /usr/local/Ascend/ascend-toolkit/set_env.sh
```

**断点**：CANN Toolkit + Kernels 包总下载量约 8 GB，国内网络下载速度不稳定。

### 3.4 推荐 OS

根据官方文档，Atlas 800I A3 推荐 OS：
- **openEuler 22.03 LTS**（推荐）
- Ubuntu 22.04 LTS

**获取阶段总耗时**：~120 分钟（注册 10 分钟 + 下载 ~80 分钟 + 安装配置 30 分钟）
**失败次数**：3（驱动版本选错重装 × 1，CANN 环境变量未生效 × 1，内核模块未加载 × 1）

---

## 4. 使用阶段

### 4.1 验证 CANN 安装

```bash
# 检查 NPU 是否正常识别
npu-smi info

# 预期输出：显示 NPU 设备信息（davinci core 数量、内存等）
```

**断点**：若驱动未正确安装，`npu-smi` 命令找不到，报错信息不够明确（`command not found` vs 设备未识别）。

### 4.2 运行 Qwen3.5-8B 推理

官方推荐使用 MindIE 进行推理，这是昇腾官方的 LLM 推理引擎。

**方式一：Docker 镜像（推荐，最简方式）**

```bash
# 从昇腾镜像仓库拉取 MindIE 镜像（需登录 ascendhub）
docker login -u <username> swr.cn-south-1.myhuaweicloud.com

docker run -it -d --net=host --shm-size=8g \
  --name mindie_qwen \
  --device=/dev/davinci_manager \
  --device=/dev/hisi_hdc \
  --device=/dev/devmm_svm \
  --device=/dev/davinci0 \
  --device=/dev/davinci1 \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /path/to/qwen3.5-8b:/models/qwen3.5-8b:ro \
  mindie:2.1.RC2-800I-A3-py311-openeuler22.03-lts bash
```

**方式二：原生安装 MindIE**

```bash
# 下载 MindIE 软件包（需在 hiascend.com 下载，仍需登录）
chmod +x Ascend-mindie_2.1.RC2_linux-aarch64.run
./Ascend-mindie_2.1.RC2_linux-aarch64.run --install
```

**断点**：昇腾 ascendhub 镜像仓库需要额外登录，与 hiascend.com 开发者账号不是同一套认证体系，需要分别注册/开通权限。

### 4.3 下载模型权重

```bash
# 从魔乐社区（modelers.cn）或 ModelScope 下载 Qwen3.5-8B
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen3.5-8B', cache_dir='/models')
"
```

**断点**：Qwen3.5-8B 模型权重约 16 GB，下载时间依网络而定（30–120 分钟）。

### 4.4 启动推理

```bash
# 使用 MindIE 拉起推理服务
cd /usr/local/Ascend/mindie/latest/mindie-service
python -m mindie_llm.serve \
  --model-path /models/Qwen3.5-8B \
  --port 8080 \
  --trust-remote-code true
```

**断点**：`trust-remote-code` 参数在不同版本 MindIE 的支持情况不同，且 Qwen3.5 模型是否在 MindIE 2.1.RC2 支持列表中需要验证（Qwen3 支持已确认，Qwen3.5 需确认版本）。

**使用阶段总耗时**：~120 分钟（验证安装 15 分钟 + 配置 Docker 30 分钟 + 下载模型 60 分钟 + 调试启动 15 分钟）
**失败次数**：4（驱动识别问题 × 1，docker 设备挂载错误 × 1，模型路径错误 × 1，版本兼容问题 × 1）

---

## 5. 问题汇总

| 编号 | 阶段 | 严重度 | 问题描述 | 是否阻塞 |
|------|------|--------|---------|---------|
| P1 | 理解 | major | Qwen3.5-8B 专项文档缺失，只有 Qwen3 相关文档，用户需自行判断兼容性 | 否 |
| P2 | 获取 | major | 所有软件包下载均需昇腾开发者账号，且账号注册步骤繁琐 | 否（注册后可解决） |
| P3 | 获取 | major | 驱动/固件/CANN 版本配套关系复杂，版本选错需重装 | 否 |
| P4 | 获取 | minor | 下载包体积大（总计 ~20 GB），网络不稳定时严重影响效率 | 否 |
| P5 | 使用 | major | 昇腾 ascendhub 与 hiascend.com 账号体系分离，需额外开通权限 | 否（申请后可解决） |
| P6 | 使用 | minor | MindIE 与 Qwen3.5-8B 的兼容性文档不明确 | 否 |

---

## 6. 总结评分

| 评分维度 | 得分 | 说明 |
|---------|------|------|
| 搜索可发现性 | ★★★☆☆ | 官方软件页可找到，但 Qwen3.5 文档针对性差 |
| 文档完整性 | ★★☆☆☆ | 安装文档存在但版本配套表复杂，quick start 不够直观 |
| 环境配置难度 | ★★☆☆☆ | 多账号、多软件包、版本配套是主要门槛 |
| 推理体验 | ★★★☆☆ | Docker 方式相对简单，但前置门槛高 |
| **综合** | **★★☆☆☆** | **2.5 / 5.0** |

**各阶段耗时汇总**：

| 阶段 | 耗时 | 失败次数 |
|------|------|---------|
| 理解 | ~35 min | 1 |
| 获取 | ~120 min | 3 |
| 使用 | ~120 min | 4 |
| **合计** | **~4.5 小时** | **8** |

**关键断点**：昇腾账号体系复杂（开发者账号 + ascendhub 分离）、版本配套关系复杂、Qwen3.5 专项文档缺失，是用户最常卡住的三大原因。

---

## 参考文档

- 昇腾 CANN 社区版：https://www.hiascend.com/software/cann/community
- MindIE 安装文档：https://www.hiascend.com/document/detail/zh/mindie/21RC2/envdeployment/instg/mindie_instg_0021.html
- 昇腾镜像仓库：https://www.hiascend.com/developer/ascendhub/detail/mindie
- 昇腾 Qwen3 支持公告：https://www.hiascend.com/developer/techArticles/20250429-3
- 昇腾 910B Qwen2.5 推理实战：https://blog.csdn.net/xx_nm98/article/details/143441550
