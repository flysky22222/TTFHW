# 使用说明

本文档说明如何在 `flysky22222/TTFHW` 仓库中使用这套 issue 自动执行工具。

## 适用范围

只有标题中包含 `【小数】` 的 issue 会被处理，其他 issue 会被忽略。

例如以下标题会触发：

- `【小数】新增一个 hello 接口`
- `修复登录页样式【小数】`

例如以下标题不会触发：

- `修复登录页样式`
- `新增一个 hello 接口`

## 仓库内的关键文件

- `.github/workflows/issue-to-pr.yml`：GitHub Actions 入口
- `scripts/issue-to-pr.mjs`：执行 issue 解析、代码生成、提交和创建 PR 的脚本
- `.github/ISSUE_TEMPLATE/decimal-task.yml`：用于发起任务的 issue 模板

## 使用前准备

在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 中配置：

- `OPENAI_API_KEY`：必填，模型调用密钥
- `OPENAI_BASE_URL`：可选，默认使用 `https://api.openai.com/v1`
- `OPENAI_MODEL`：可选，默认使用 `gpt-4.1`

工作流运行时使用 GitHub 自动提供的 `GITHUB_TOKEN` 来推送分支和创建 PR。

## 在 GitHub 上使用

1. 在仓库中创建一个新 issue。
2. 确保 issue 标题中包含 `【小数】`。
3. 在 issue 正文中写清楚任务描述和验收标准。
4. 提交 issue 后，GitHub Actions 会自动执行。
5. 工具会读取仓库上下文，生成改动，推送分支，并创建或复用 PR。
6. 完成后，脚本会在 issue 下回帖说明 PR 编号。

## 推荐的 issue 写法

建议按下面的方式描述任务：

- 标题：`【小数】新增一个 hello 接口`
- 任务描述：说明要改什么文件、增加什么能力、修复什么问题
- 验收标准：说明完成后应该能看到什么结果

## 本地调试

如果需要本地运行脚本，可以在仓库根目录执行：

```bash
npm run issue:run
```

至少需要准备这些环境变量：

```bash
GITHUB_EVENT_PATH=./sample-event.json
GITHUB_TOKEN=xxx
OPENAI_API_KEY=xxx
```

仓库中的 `sample-event.json` 可以作为本地调试的示例事件。

## 运行结果

当命中可处理的 issue 后，这套工具会自动执行以下步骤：

1. 读取 issue 内容
2. 收集仓库上下文
3. 调用模型生成结构化文件改动
4. 将改动写入工作区
5. 创建分支并提交代码
6. 推送分支
7. 创建或复用 PR

## 注意事项

- 标题不包含 `【小数】` 的 issue 不会被处理
- 如果模型没有生成有效文件改动，流程会直接失败
- 自动化脚本默认只会处理当前仓库中的代码和 issue 上下文
