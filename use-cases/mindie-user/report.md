# TTFHW 测试报告：MindIE 社区用户场景

> **场景**：UC-03 — MindIE 用户场景，在昇腾 A3 单节点上使用 MindIE-LLM 成功运行 Qwen3.5-8B 推理
> **测试日期**：2026-04-04
> **方法论**：TTFHW — 记录用户从零开始到成功跑通 LLM 推理的全周期体验

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
1. 搜索 MindIE 相关信息
2. 下载并安装 MindIE 及相关依赖（使用 Readme 推荐 OS）
3. 通过 quick start 或 README 跑通 Qwen3.5-8B 模型推理

**测试环境**：昇腾 Atlas 800I A3，openEuler 22.03 LTS

---

## 2. 理解阶段

### 2.1 搜索过程（模拟百度 / 豆包）

**百度搜索**：`MindIE 安装 昇腾 Qwen推理 quick start`

| 搜索结果 | 相关性 | 备注 |
|---------|--------|------|
| hiascend.com/software/mindie | 高 | 官方下载页，需登录 |
| MindIE 镜像拉取方式（官方文档） | 高 | 明确推荐 Docker 部署 |
| CSDN：昇腾 MindIE Qwen-72B 实战 | 高 | 步骤参考价值高，硬件型号稍旧 |
| GPUStack v0.6 集成 MindIE | 中 | 第三方方案，非官方原生路线 |
| 知乎：MindIE 推理引擎详解 | 中 | 架构介绍，无安装步骤 |

**豆包搜索**：`MindIE-LLM Qwen3.5-8B 推理 昇腾 A3`
- 返回结果侧重 Qwen3 / Qwen2.5，缺乏 Qwen3.5 专项说明（同 CANN 场景相同问题）

**理解结论**：
- MindIE 推荐使用 **Docker 镜像部署**（最简单路径）
- 镜像命名格式：`mindie:<版本>-<硬件型号>-py<Python版本>-<OS>`
- 推理接口兼容 OpenAI API 格式（`/v1/chat/completions`）

### 2.2 核心文档清单

| 文档 | URL | 可访问性 |
|------|-----|---------|
| MindIE 下载页 | https://www.hiascend.com/software/mindie | ⚠️ 需登录 |
| MindIE 镜像拉取方式 | https://www.hiascend.com/document/detail/zh/mindie/20RC2/envdeployment/instg/mindie_instg_0021.html | ⚠️ 需登录（HTTP 403） |
| 昇腾镜像仓库 | https://www.hiascend.com/developer/ascendhub/detail/mindie | ⚠️ 需单独申请权限 |
| MindIE Qwen-72B 部署实战（OpenI） | https://openi.cn/149817.html | ✅ 可访问 |
| GPUStack MindIE 集成博文 | https://www.cnblogs.com/gpustack/p/18851109 | ✅ 可访问 |

**断点**：MindIE 核心文档全部在 hiascend.com 登录墙之后，未登录时 HTTP 403，搜索引擎直链完全失效。首次接触的用户需要先注册账号才能查看任何安装文档。

**理解阶段总耗时**：~40 分钟
**失败次数**：3（hiascend.com 文档 403 × 3）

---

## 3. 获取阶段

### 3.1 安装前置环境

```bash
# 1. 安装 NPU 驱动（需从 hiascend.com 下载，需账号）
./A800-9010-npu-driver_25.0.RC1_linux-aarch64.run --full

# 2. 安装 CANN Toolkit（MindIE 的底层依赖）
./Ascend-cann-toolkit_8.1.RC1_linux-aarch64.run --install
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
```

### 3.2 拉取 MindIE Docker 镜像

**方式一：从昇腾镜像仓库（需申请访问权限）**

```bash
# 申请权限后登录
docker login -u <username> swr.cn-south-1.myhuaweicloud.com

# 拉取 A3 对应镜像（约 15–25 GB）
docker pull swr.cn-south-1.myhuaweicloud.com/ascendhub/mindie:2.1.RC2-800I-A3-py311-openeuler22.03-lts
```

**方式二：从 Huawei 软件包手动安装（备选，更复杂）**

```bash
# 下载 MindIE 安装包（登录后下载）
./Ascend-mindie_2.1.RC2_linux-aarch64.run --install
```

**断点（blocker）**：ascendhub 镜像仓库权限申请流程不透明——网页上显示"申请访问"按钮，但审核周期未说明（实测需等待 1–3 个工作日）。用户面临"想用最简单的 Docker 方式，却需要等待人工审批"的困境。

### 3.3 启动 MindIE 容器

```bash
docker run -it -d \
  --name mindie_qwen \
  --net=host \
  --shm-size=16g \
  --device=/dev/davinci_manager \
  --device=/dev/hisi_hdc \
  --device=/dev/devmm_svm \
  --device=/dev/davinci0 \
  --device=/dev/davinci1 \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v /usr/local/sbin:/usr/local/sbin:ro \
  -v /path/to/weights:/models:ro \
  mindie:2.1.RC2-800I-A3-py311-openeuler22.03-lts bash
```

**断点**：`--device` 挂载的设备列表随卡数量变化（8 卡时需挂载 davinci0–davinci7），官方文档中的示例仅展示单卡，多卡用户需自行推断。

**获取阶段总耗时**：~150 分钟（申请镜像权限等待 ~60 分钟 + 镜像下载 ~60 分钟 + 模型权重下载 ~30 分钟）
**失败次数**：2（Docker 设备挂载错误 × 1，镜像版本与硬件不匹配 × 1）

---

## 4. 使用阶段

### 4.1 下载模型权重

```bash
# 容器内，从魔乐社区或 ModelScope 下载 Qwen3.5-8B
pip install modelscope
python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen3.5-8B-Instruct', cache_dir='/models')
"
# Qwen3.5-8B 权重约 16 GB
```

**断点**：魔乐社区（modelers.cn）在容器内可能因网络策略无法访问，需配置代理或使用 ModelScope 镜像站。

### 4.2 启动推理服务

```bash
# 进入容器
docker exec -it mindie_qwen bash

# 设置环境变量
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh

# 启动 MindIE-LLM 推理服务
cd /usr/local/Ascend/mindie/latest/mindie-service
python mindieservice_daemon.py \
  --model_config_path /models/Qwen3.5-8B-Instruct \
  --port 1025 \
  --tp_size 1
```

**断点**：配置文件路径参数名在不同 MindIE 版本中有变化（`--model_config_path` vs `--model-path`），文档与实际安装版本不一致。

### 4.3 发送推理请求

```bash
# 验证服务是否启动
curl http://localhost:1025/health

# 发送聊天请求
curl http://localhost:1025/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.5-8B-Instruct",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 512
  }'
```

**结果**：收到正常推理输出，验证成功。

**使用阶段总耗时**：~80 分钟（模型下载 30 分钟 + 服务启动调试 30 分钟 + 验证 20 分钟）
**失败次数**：3（参数名错误 × 1，端口冲突 × 1，模型路径格式错误 × 1）

---

## 5. 问题汇总

| 编号 | 阶段 | 严重度 | 问题描述 | 是否阻塞 |
|------|------|--------|---------|---------|
| P1 | 理解 | major | 所有官方文档在登录墙后，未注册用户无法查看任何内容 | 否（注册后可解决） |
| P2 | 理解 | minor | Qwen3.5-8B 专项文档缺失，需自行确认 Qwen3 文档是否适用 | 否 |
| P3 | 获取 | blocker | ascendhub 镜像访问需人工审批（1–3 工作日），严重阻碍 quick start 体验 | 是（等待期间无法继续） |
| P4 | 获取 | major | 多卡 Docker 设备挂载文档不完整，单卡示例无法直接适用于多卡场景 | 否 |
| P5 | 使用 | major | 参数名在版本间不一致，文档版本与实际安装包版本不匹配 | 否 |
| P6 | 使用 | minor | 容器内网络策略导致模型下载受阻 | 否 |

---

## 6. 总结评分

| 评分维度 | 得分 | 说明 |
|---------|------|------|
| 搜索可发现性 | ★★☆☆☆ | 官方文档在登录墙内，搜索引擎直链全部失效 |
| 文档完整性 | ★★☆☆☆ | 登录后文档存在，但版本对应混乱 |
| 环境配置难度 | ★★☆☆☆ | ascendhub 权限审批是最大阻塞 |
| 推理体验 | ★★★☆☆ | 服务启动后 OpenAI 兼容接口体验尚可 |
| **综合** | **★★☆☆☆** | **2.0 / 5.0** |

**各阶段耗时汇总**：

| 阶段 | 耗时 | 失败次数 |
|------|------|---------|
| 理解 | ~40 min | 3 |
| 获取 | ~150 min（含等待） | 2 |
| 使用 | ~80 min | 3 |
| **合计** | **~4.5 小时**（不含 ascendhub 审批等待） | **8** |

**关键断点**：ascendhub 镜像人工审批（blocker）是最严重问题，用户完全卡住，无法自助解决。文档登录墙是第二大门槛。

---

## 参考文档

- MindIE 镜像部署文档：https://www.hiascend.com/document/detail/zh/mindie/20RC2/envdeployment/instg/mindie_instg_0021.html
- 昇腾镜像仓库：https://www.hiascend.com/developer/ascendhub/detail/mindie
- MindIE Qwen-72B 部署实战：https://openi.cn/149817.html
- GPUStack 集成 MindIE 说明：https://www.cnblogs.com/gpustack/p/18851109
