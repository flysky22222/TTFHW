# TTFHW Issue Worker

这个仓库包含一套最小可运行的自动化流程：

- 监听 GitHub issue 的 `opened`、`edited`、`reopened`
- 只处理标题中包含 `【小数】` 的 issue
- 读取 issue 内容和当前仓库上下文
- 调用兼容 OpenAI Chat Completions 的模型生成代码改动
- 自动创建分支、提交代码、推送并发起 PR

## 触发规则

只有标题中包含 `【小数】` 的 issue 会被处理，例如：

- `【小数】新增一个 hello 接口`
- `修复登录页样式【小数】`

其他 issue 会被 GitHub Actions 直接忽略。

## 需要的 GitHub 配置

在仓库里配置以下 Secret / Variable：

- `OPENAI_API_KEY`：模型 API Key
- `OPENAI_BASE_URL`：可选，默认 `https://api.openai.com/v1`
- `OPENAI_MODEL`：可选，默认 `gpt-4.1`

`GITHUB_TOKEN` 由 Actions 自动提供，工作流已经声明了创建分支和 PR 所需权限。

## 工作流文件

- [`.github/workflows/issue-to-pr.yml`](C:/zhongjun/code/test/auto/.github/workflows/issue-to-pr.yml)

## 本地调试

```bash
npm run issue:run
```

本地调试时至少需要这些环境变量：

```bash
GITHUB_EVENT_PATH=./sample-event.json
GITHUB_TOKEN=xxx
OPENAI_API_KEY=xxx
```

## 设计说明

自动化脚本会让模型直接返回结构化 JSON 文件列表，然后把文件写入工作区，再由脚本统一执行：

1. 新建分支
2. 提交代码
3. 推送到远端
4. 创建或复用 PR

这样可以把 issue 筛选逻辑、代码生成逻辑和 git / GitHub 逻辑彻底分开，后续扩展更容易。
