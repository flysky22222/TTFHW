# TTFHW Issue Worker

这个仓库已经配置成一套最小可运行的自动化流程：

- 监听 GitHub issue 的 `opened`、`edited`、`reopened`
- 监听 issue 评论的 `created`
- 只处理标题中包含 `【小数】` 的 issue
- 先分析任务并把方案评论回 issue
- 只有在评论中收到 `【小数】开始执行` 后才真正改代码
- 自动创建分支、提交代码、推送并发起 PR

## 触发规则

只有标题中包含 `【小数】` 的 issue 才会进入自动处理，例如：

- `【小数】新增一个 hello 接口`
- `修复登录页样式【小数】`

其他 issue 会被 GitHub Actions 直接忽略，不会分析，也不会提 PR。

## 执行规则

命中标题规则后，流程分成两个阶段：

1. 第一次在 issue 上触发时，只做分析，不直接改代码。
2. 脚本把实现方案评论回 issue。
3. 只有当用户再次在该 issue 评论中回复 `【小数】开始执行` 时，脚本才会真正执行实现并提交 PR。

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
4. 模型先返回分析方案，脚本把方案评论到 issue。
5. 用户在该 issue 下回复 `【小数】开始执行`。
6. 评论事件再次触发后，脚本读取 issue、评论上下文和仓库代码。
7. 模型返回结构化文件改动方案。
8. 脚本把改动写入仓库，创建分支并提交。
9. 脚本推送分支并创建或复用对应 PR。
10. 脚本回到 issue 下评论 PR 编号。

为避免自动任务误伤仓库控制面，脚本会拒绝改动 `.git` 和 `.github/workflows`。

## 本地调试

```bash
npm run issue:run
```

本地调试时至少需要这些环境变量：

```bash
GITHUB_EVENT_PATH=./sample-event.json
GITHUB_EVENT_NAME=issues
GITHUB_TOKEN=xxx
OPENAI_API_KEY=xxx
```

仓库里已经提供了示例事件文件：

- [`sample-event.json`](C:/zhongjun/code/test/auto/sample-event.json)：issue 分析阶段
- [`sample-comment-event.json`](C:/zhongjun/code/test/auto/sample-comment-event.json)：评论确认执行阶段
