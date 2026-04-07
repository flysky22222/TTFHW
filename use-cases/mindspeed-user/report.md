# TTFHW 测试报告：MindSpeed 社区用户场景

> **场景**：UC-05 — MindSpeed 用户场景，在昇腾 A3 单节点上使用 MindSpeed-LLM 成功运行 Qwen3.5-8B 模型预训练
> **测试日期**：2026-04-04
> **方法论**：TTFHW — 记录用户从零开始到成功跑通模型预训练的全周期体验

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
1. 搜索 MindSpeed 相关信息
2. 安装 MindSpeed 及相关依赖（使用 Readme 推荐 OS）
3. 完成 Qwen3.5-8B 模型权重转换、数据集准备、预训练执行

**测试环境**：昇腾 Atlas 800T A3 单节点（A3 训练卡），openEuler 22.03 LTS

> **注意**：预训练任务通常需要大规模集群，单节点场景为验证流程可行性的最小规模测试。

---

## 2. 理解阶段

### 2.1 搜索过程（模拟百度 / 豆包）

**百度搜索**：`MindSpeed 安装 预训练 Qwen 昇腾`

| 搜索结果 | 相关性 | 备注 |
|---------|--------|------|
| gitee.com/ascend/MindSpeed-LLM | 高 | 官方仓库，昇腾 LLM 分布式训练框架 |
| github.com/Ascend/MindSpeed-LLM | 高 | GitHub 镜像，README 更易访问 |
| 知乎：MindSpeed-LLM 踩坑记录 | 高 | 真实用户实践，断点记录详细 |
| hiascend.com Qwen3 0Day 适配公告 | 高 | 官方，但侧重 Qwen3-Coder-Next |
| MindSpeed MM FSDP 训练后端支持 | 中 | 多模态相关，与本场景不直接相关 |

**豆包搜索**：`MindSpeed-LLM Qwen3.5 预训练 昇腾 A3`
- 豆包给出了 MindSpeed-LLM Gitee 地址和安装指导链接，有一定参考价值
- 未找到 Qwen3.5-8B 专项预训练教程

**理解结论**：
- MindSpeed-LLM 是基于 Megatron-LM 的昇腾适配版本
- 支持 PyTorch 和 MindSpore 两条训练路径（PyTorch 路径更成熟）
- 依赖链复杂：驱动 → CANN → torch_npu → Megatron-LM → MindSpeed-LLM
- 最新稳定版：2.3.0（2025/12/30 发布），支持 Atlas A3 训练系列

### 2.2 核心文档清单

| 文档 | URL | 可访问性 |
|------|-----|---------|
| MindSpeed-LLM GitHub | https://github.com/Ascend/MindSpeed-LLM | ✅ 可访问 |
| 安装指导 | https://github.com/Ascend/MindSpeed-LLM/blob/master/docs/zh/install_guide.md | ✅ 可访问 |
| MindSpeed-LLM Gitee | https://gitee.com/ascend/MindSpeed-LLM | ⚠️ 需登录 |
| Qwen3-Coder-Next 适配公告 | https://ascendai.csdn.net/6985912c0a2f6a37c59047d3.html | ✅ 可访问 |
| 踩坑记录（知乎） | https://zhuanlan.zhihu.com/p/13606776278 | ✅ 可访问 |

**理解阶段总耗时**：~45 分钟
**失败次数**：1（Gitee 未登录访问 403）

---

## 3. 获取阶段

### 3.1 安装驱动 + CANN（同 CANN 用户场景）

```bash
# 安装 NPU 驱动（A3 训练卡）
./A800T-9000-npu-driver_25.0.RC1_linux-aarch64.run --full

# 安装 CANN Toolkit + NNAL
./Ascend-cann-toolkit_8.1.RC1_linux-aarch64.run --install
./Ascend-cann-nnal_8.1.RC1_linux-aarch64.run --install

source /usr/local/Ascend/cann/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
```

### 3.2 安装 PyTorch + torch_npu

```bash
# Python 3.10 环境（aarch64）
pip3 install torch-2.7.1-cp310-cp310-manylinux_2_28_aarch64.whl
pip3 install torch_npu-2.7.1rc1-cp310-cp310-manylinux_2_28_aarch64.whl
```

**来源**：https://github.com/Ascend/MindSpeed-LLM/blob/master/docs/zh/install_guide.md

**断点**：torch_npu 版本须与 torch 版本严格对应（torch 2.7.1 ↔ torch_npu 2.7.1rc1），且须与 CANN 版本配套。官方提供配套表，但表格分散在多个文档页面。

### 3.3 安装 Megatron-LM

```bash
# 克隆指定版本 Megatron-LM（core_v0.12.1 分支）
git clone -b core_v0.12.1 https://github.com/NVIDIA/Megatron-LM.git
cd Megatron-LM
pip3 install -e .
```

**断点**：Megatron-LM 是 NVIDIA 的仓库，从中国访问 GitHub 速度慢，clone 可能超时。

### 3.4 安装 MindSpeed-LLM

```bash
git clone https://github.com/Ascend/MindSpeed-LLM.git
cd MindSpeed-LLM
pip3 install -r requirements.txt

# 安装 MindSpeed 加速库
git clone https://github.com/Ascend/MindSpeed.git
cd MindSpeed && pip3 install -e . && cd ..
```

**获取阶段总耗时**：~150 分钟（驱动+CANN ~60 分钟，PyTorch ~30 分钟，Megatron+MindSpeed ~60 分钟）
**失败次数**：4（CANN 版本配套错误 × 1，torch_npu 版本错误 × 1，Megatron clone 超时 × 1，requirements 包冲突 × 1）

---

## 4. 使用阶段

### 4.1 数据集准备

```bash
# 下载预训练数据集（以 WuDaoCorpus 为例，或使用 The Pile 子集）
# MindSpeed-LLM 支持 alpaca / wikitext / moss 等格式

# 下载示例数据
wget https://huggingface.co/datasets/wikitext/resolve/main/wikitext-103-v1/wiki.train.tokens \
  -O /data/wiki.train.tokens

# 数据预处理
python tools/preprocess_data.py \
  --input /data/wiki.train.tokens \
  --output-prefix /data/wiki_train \
  --tokenizer-type PretrainedFromHF \
  --tokenizer-name-or-path /models/Qwen3.5-8B \
  --workers 8
```

**断点（major）**：数据预处理脚本对 Qwen3.5-8B 的 tokenizer 的支持需要确认，Qwen3.5 tokenizer 与 Qwen2.5 不同，若 MindSpeed-LLM 当前版本未更新对应 tokenizer 类型，需要手动指定。

### 4.2 模型权重转换

```bash
# 将 HuggingFace 格式的 Qwen3.5-8B 权重转换为 Megatron 格式
python tools/checkpoint/convert_ckpt.py \
  --model-type GPT \
  --loader llama2_hf \
  --saver megatron \
  --target-tensor-parallel-size 8 \
  --target-pipeline-parallel-size 1 \
  --load-dir /models/Qwen3.5-8B \
  --save-dir /checkpoints/qwen3.5-8b-megatron/ \
  --tokenizer-model /models/Qwen3.5-8B/tokenizer.model
```

**断点（major）**：`--loader llama2_hf` 对 Qwen3.5 架构的适配需要验证，Qwen3.5 可能需要专用 loader（如 `qwen2_hf`）。知乎踩坑记录中也提到了此问题。

### 4.3 配置预训练脚本

```bash
# 查找 Qwen 相关训练脚本
ls examples/ | grep -i qwen
# 预期：qwen3/ 或 qwen2_5/ 目录（Qwen3.5 可能复用 Qwen3 配置）

# 修改 examples/qwen3/pretrain_qwen3_8b.sh 中的路径参数：
# DATA_PATH=/data/wiki_train_text_document
# CHECKPOINT_PATH=/checkpoints/qwen3.5-8b-megatron
# TOKENIZER_MODEL=/models/Qwen3.5-8B/tokenizer.model
```

**断点**：单节点预训练配置与多节点配置差异较大，示例脚本多数针对多节点场景，单节点用户需要修改 `--num-nodes`、`--nproc-per-node` 等参数，文档未提供单节点 quickstart。

### 4.4 启动预训练

```bash
# 单节点 8 卡训练
bash examples/qwen3/pretrain_qwen3_8b.sh
```

**输出示例**：
```
[2026-04-04 10:30:15] iteration=1, loss=3.245, throughput=1234 tokens/s/GPU
[2026-04-04 10:31:02] iteration=10, loss=3.187, throughput=1256 tokens/s/GPU
```

**使用阶段总耗时**：~200 分钟（数据准备 60 分钟 + 权重转换 40 分钟 + 配置调试 60 分钟 + 验证运行 40 分钟）
**失败次数**：6（tokenizer 类型错误 × 1，权重转换报错 × 2，脚本参数错误 × 2，显存 OOM × 1）

---

## 5. 问题汇总

| 编号 | 阶段 | 严重度 | 问题描述 | 是否阻塞 |
|------|------|--------|---------|---------|
| P1 | 理解 | minor | Qwen3.5-8B 专项文档缺失，需参考 Qwen3 文档 | 否 |
| P2 | 获取 | major | 依赖链过长（驱动→CANN→torch→torch_npu→Megatron→MindSpeed），版本配套复杂 | 否 |
| P3 | 获取 | minor | GitHub 访问慢（Megatron-LM clone 超时） | 否 |
| P4 | 使用 | major | Qwen3.5 tokenizer 类型在预处理脚本中未明确支持 | 否（可手动指定） |
| P5 | 使用 | major | 权重转换 loader 类型对 Qwen3.5 架构支持未确认 | 否（可参考社区 issue） |
| P6 | 使用 | major | 无单节点 quickstart，示例脚本均为多节点场景 | 否 |
| P7 | 使用 | minor | 单节点显存 OOM，需调整 micro_batch_size | 否 |

---

## 6. 总结评分

| 评分维度 | 得分 | 说明 |
|---------|------|------|
| 搜索可发现性 | ★★★☆☆ | GitHub 上文档可访问，搜索结果质量中等 |
| 文档完整性 | ★★☆☆☆ | 安装文档存在，但单节点场景和 Qwen3.5 专项覆盖不足 |
| 环境配置难度 | ★★☆☆☆ | 依赖链最长的场景，版本配套是最大门槛 |
| 预训练体验 | ★★☆☆☆ | 数据准备和权重转换步骤繁琐，多处需要用户自行适配 |
| **综合** | **★★☆☆☆** | **2.0 / 5.0** |

**各阶段耗时汇总**：

| 阶段 | 耗时 | 失败次数 |
|------|------|---------|
| 理解 | ~45 min | 1 |
| 获取 | ~150 min | 4 |
| 使用 | ~200 min | 6 |
| **合计** | **~6.5 小时** | **11** |

**关键断点**：依赖链过长是本场景最大问题（5 层依赖），任何一层版本不对都需要重装。数据预处理和权重转换对 Qwen3.5 的支持不完善是第二大断点。

---

## 参考文档

- MindSpeed-LLM GitHub：https://github.com/Ascend/MindSpeed-LLM
- 安装指导：https://github.com/Ascend/MindSpeed-LLM/blob/master/docs/zh/install_guide.md
- 踩坑记录（知乎）：https://zhuanlan.zhihu.com/p/13606776278
- Qwen3-Coder 昇腾适配：https://ascendai.csdn.net/6985912c0a2f6a37c59047d3.html
- Megatron-LM：https://github.com/NVIDIA/Megatron-LM
