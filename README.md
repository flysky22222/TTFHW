# TTFHW Issue Worker

这个仓库已经配置成一套最小可运行的自动化流程：

- 监听 GitHub issue 的 `opened`、`edited`、`reopened`
- 只处理标题中包含 `【小数】` 的 issue
- 读取 issue 内容和当前仓库上下文
- 调用兼容 OpenAI Chat Completions 的模型生成代码改动
- 自动创建分支、提交代码、推送并发起 PR

## 触发规则

只有标题中包含 `【小数】` 的 issue 才会进入自动处理，例如：

- `【小数】新增一个 hello 接口`
- `修复登录页样式【小数】`

其他 issue 会被 GitHub Actions 直接忽略，不会分析，也不会提 PR。

## 当前实现位置

- 工作流: [`.github/workflows/issue-to-pr.yml`](C:/zhongjun/code/test/auto/.github/workflows/issue-to-pr.yml)
- 执行脚本: [`scripts/issue-to-pr.mjs`](C:/zhongjun/code/test/auto/scripts/issue-to-pr.mjs)
- issue 模板: [`.github/ISSUE_TEMPLATE/decimal-task.yml`](C:/zhongjun/code/test/auto/.github/ISSUE_TEMPLATE/decimal-task.yml)

## 需要的 GitHub 配置

在 `flysky22222/TTFHW` 仓库里配置以下 Secret / Variable：

- `OPENAI_API_KEY`: 模型 API Key
- `OPENAI_BASE_URL`: 可选，默认 `https://api.openai.com/v1`
- `OPENAI_MODEL`: 可选，默认 `gpt-4.1`

`GITHUB_TOKEN` 由 GitHub Actions 自动提供，工作流已声明创建分支和 PR 所需权限。

## 运行流程

1. 用户新建或编辑 issue。
2. 工作流先判断标题里是否包含 `【小数】`。
3. 命中后，脚本读取 issue 和仓库代码上下文。
4. 模型返回结构化文件改动方案。
5. 脚本把改动写入仓库，创建分支并提交。
6. 脚本推送分支并创建或复用对应 PR。
7. 脚本回到 issue 下评论 PR 编号。

为避免自动任务误伤仓库控制面，脚本会拒绝改动 `.git` 和 `.github/workflows`。

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

仓库里已经提供了示例事件文件：[`sample-event.json`](C:/zhongjun/code/test/auto/sample-event.json)。
