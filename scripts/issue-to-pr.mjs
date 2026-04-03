import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const TITLE_MARKER = "【小数】";
const EXECUTE_MARKER = "【小数】开始执行";
const MAX_FILE_BYTES = 120_000;
const MAX_PROMPT_CHARS = 180_000;
const MAX_COMMENT_CHARS = 20_000;
const EXCLUDED_DIRS = new Set([
  ".git",
  ".github",
  "node_modules",
  "tmp"
]);
const PROTECTED_PATH_PREFIXES = [
  ".git/",
  ".github/workflows/"
];

async function main() {
  const eventPath = process.env.GITHUB_EVENT_PATH;

  if (!eventPath) {
    throw new Error("Missing GITHUB_EVENT_PATH.");
  }

  const payload = readJsonFile(eventPath);
  const issue = payload.issue;

  if (!issue) {
    log("No issue payload found. Skipping.");
    return;
  }

  if (issue.pull_request) {
    log("Pull request comments are not supported. Skipping.");
    return;
  }

  if (!String(issue.title || "").includes(TITLE_MARKER)) {
    log(`Issue #${issue.number} ignored because title does not contain ${TITLE_MARKER}.`);
    return;
  }

  const owner = payload.repository?.owner?.login;
  const repo = payload.repository?.name;
  const defaultBranch = payload.repository?.default_branch || "main";
  const eventName = process.env.GITHUB_EVENT_NAME || detectEventName(payload);

  if (!owner || !repo) {
    throw new Error("Missing repository owner or name in the webhook payload.");
  }

  if (eventName === "issue_comment") {
    await handleIssueCommentEvent({
      payload,
      issue,
      owner,
      repo,
      defaultBranch
    });
    return;
  }

  await handleIssueEvent({
    issue,
    owner,
    repo,
    defaultBranch
  });
}

async function handleIssueEvent({ issue, owner, repo, defaultBranch }) {
  const apiKey = requiredEnv("OPENAI_API_KEY");
  const githubToken = requiredEnv("GITHUB_TOKEN");
  const repoContext = collectRepositoryContext(process.cwd());
  const analysis = await requestAnalysisPlan({
    apiKey,
    issue,
    repoContext,
    owner,
    repo,
    defaultBranch
  });

  validateAnalysis(analysis);

  await commentOnIssue({
    githubToken,
    owner,
    repo,
    issueNumber: issue.number,
    body: formatAnalysisComment(analysis)
  });

  log(`Analysis posted to issue #${issue.number}.`);
}

async function handleIssueCommentEvent({
  payload,
  issue,
  owner,
  repo,
  defaultBranch
}) {
  const commentBody = normalizeMultiline(payload.comment?.body);

  if (commentBody !== EXECUTE_MARKER) {
    log(`Issue comment ignored because it does not equal ${EXECUTE_MARKER}.`);
    return;
  }

  const apiKey = requiredEnv("OPENAI_API_KEY");
  const githubToken = requiredEnv("GITHUB_TOKEN");
  const repoContext = collectRepositoryContext(process.cwd());
  const comments = await listIssueComments({
    githubToken,
    owner,
    repo,
    issueNumber: issue.number
  });
  const issueDiscussion = summarizeComments(comments);
  const plan = await requestImplementationPlan({
    apiKey,
    issue,
    issueDiscussion,
    repoContext,
    owner,
    repo,
    defaultBranch
  });

  validatePlan(plan);

  if (plan.files.length === 0) {
    throw new Error("The model did not return any file changes.");
  }

  const branchName = sanitizeBranchName(
    plan.branchName || `issue/${issue.number}-${slugify(issue.title)}`
  );
  const commitMessage = normalizeLine(plan.commitMessage) || `feat: resolve issue #${issue.number}`;
  const prTitle = normalizeLine(plan.prTitle) || `Resolve #${issue.number}: ${issue.title}`;
  const prBody = String(plan.prBody || "").trim() || defaultPrBody(issue);

  applyFiles(plan.files);

  if (!hasChanges()) {
    await commentOnIssue({
      githubToken,
      owner,
      repo,
      issueNumber: issue.number,
      body: "已收到执行指令，但本次生成的结果没有产生代码变更，未创建 PR。"
    });
    log("The generated result did not change the repository. Skipping push and PR creation.");
    return;
  }

  git(["config", "user.name", "github-actions[bot]"]);
  git(["config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"]);
  git(["checkout", "-B", branchName]);
  git(["add", "-A"]);
  git(["commit", "-m", commitMessage]);
  git(["push", "--set-upstream", "origin", branchName, "--force-with-lease"]);

  const pr = await createOrReusePullRequest({
    githubToken,
    owner,
    repo,
    defaultBranch,
    branchName,
    title: prTitle,
    body: prBody
  });

  await commentOnIssue({
    githubToken,
    owner,
    repo,
    issueNumber: issue.number,
    body: `已收到执行指令并完成实现，PR：#${pr.number}`
  });

  log(`PR created or reused: #${pr.number}`);
}

function requiredEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function readJsonFile(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return JSON.parse(raw.replace(/^\uFEFF/, ""));
}

function detectEventName(payload) {
  return payload.comment ? "issue_comment" : "issues";
}

function log(message) {
  console.log(`[issue-worker] ${message}`);
}

function git(args) {
  return execFileSync("git", args, {
    stdio: "pipe",
    encoding: "utf8"
  }).trim();
}

function hasChanges() {
  return git(["status", "--porcelain"]).length > 0;
}

function collectRepositoryContext(rootDir) {
  const files = [];
  visitDirectory(rootDir, rootDir, files);

  let totalChars = 0;
  const parts = [];

  for (const file of files) {
    const block = `FILE: ${file.path}\n${file.content}\n`;
    if (totalChars + block.length > MAX_PROMPT_CHARS) {
      break;
    }
    parts.push(block);
    totalChars += block.length;
  }

  return parts.join("\n");
}

function visitDirectory(rootDir, currentDir, files) {
  const entries = fs.readdirSync(currentDir, { withFileTypes: true });

  for (const entry of entries) {
    if (EXCLUDED_DIRS.has(entry.name)) {
      continue;
    }

    const absolutePath = path.join(currentDir, entry.name);
    const relativePath = path.relative(rootDir, absolutePath).replace(/\\/g, "/");

    if (entry.isDirectory()) {
      visitDirectory(rootDir, absolutePath, files);
      continue;
    }

    const stat = fs.statSync(absolutePath);
    if (stat.size > MAX_FILE_BYTES) {
      continue;
    }

    const buffer = fs.readFileSync(absolutePath);
    if (buffer.includes(0)) {
      continue;
    }

    files.push({
      path: relativePath,
      content: buffer.toString("utf8")
    });
  }
}

async function requestAnalysisPlan({ apiKey, issue, repoContext, owner, repo, defaultBranch }) {
  const response = await requestModelJson({
    apiKey,
    systemPrompt: [
      "You are an autonomous software engineer preparing an implementation plan for a GitHub issue.",
      "Return strict JSON only.",
      "The JSON schema is:",
      "{",
      '  "summary": "string",',
      '  "steps": ["string"],',
      '  "files": ["string"],',
      '  "risks": ["string"]',
      "}",
      "Rules:",
      "1. Be concrete and concise.",
      "2. Mention only files that are likely to be touched.",
      "3. Do not include markdown fences.",
      "4. Do not promise work outside the current repository."
    ].join("\n"),
    userPrompt: [
      `Repository: ${owner}/${repo}`,
      `Default branch: ${defaultBranch}`,
      `Issue #${issue.number}: ${issue.title}`,
      "",
      "Issue body:",
      String(issue.body || "").trim() || "(empty)",
      "",
      "Current repository files:",
      repoContext || "(repository is empty)"
    ].join("\n")
  });

  return JSON.parse(response);
}

async function requestImplementationPlan({
  apiKey,
  issue,
  issueDiscussion,
  repoContext,
  owner,
  repo,
  defaultBranch
}) {
  const response = await requestModelJson({
    apiKey,
    systemPrompt: [
      "You are an autonomous software engineer working inside a GitHub Actions job.",
      "Return strict JSON only.",
      "The JSON schema is:",
      "{",
      '  "branchName": "string",',
      '  "commitMessage": "string",',
      '  "prTitle": "string",',
      '  "prBody": "string",',
      '  "files": [',
      "    {",
      '      "path": "string",',
      '      "content": "string",',
      '      "delete": false',
      "    }",
      "  ]",
      "}",
      "Rules:",
      "1. Modify only files that are necessary for the issue.",
      "2. Return full file contents for every file listed.",
      "3. Keep branchName, commitMessage, prTitle, and prBody concise.",
      "4. Do not use markdown fences.",
      "5. Prefer updating existing files instead of creating unnecessary new files.",
      "6. Never modify .github/workflows or .git contents.",
      "7. Follow the approved issue discussion when it contains an implementation plan."
    ].join("\n"),
    userPrompt: [
      `Repository: ${owner}/${repo}`,
      `Default branch: ${defaultBranch}`,
      `Issue #${issue.number}: ${issue.title}`,
      "",
      "Issue body:",
      String(issue.body || "").trim() || "(empty)",
      "",
      "Issue discussion:",
      issueDiscussion || "(no comments)",
      "",
      "Current repository files:",
      repoContext || "(repository is empty)"
    ].join("\n")
  });

  return JSON.parse(response);
}

async function requestModelJson({ apiKey, systemPrompt, userPrompt }) {
  const baseUrl = (process.env.OPENAI_BASE_URL || "https://api.openai.com/v1").replace(/\/$/, "");
  const model = process.env.OPENAI_MODEL || "gpt-4.1";
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ]
    })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Model request failed: ${response.status} ${text}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content;

  if (!content) {
    throw new Error("Model response did not include content.");
  }

  return content;
}

function validateAnalysis(analysis) {
  if (!analysis || typeof analysis !== "object") {
    throw new Error("The analysis response must be a JSON object.");
  }

  if (!Array.isArray(analysis.steps) || analysis.steps.length === 0) {
    throw new Error("The analysis response must include steps.");
  }
}

function validatePlan(plan) {
  if (!plan || typeof plan !== "object") {
    throw new Error("The model response must be a JSON object.");
  }

  if (!Array.isArray(plan.files)) {
    throw new Error("The model response must include a files array.");
  }
}

function formatAnalysisComment(analysis) {
  const lines = [
    "已完成任务分析，建议按以下方案执行：",
    "",
    "### 方案摘要",
    String(analysis.summary || "无"),
    "",
    "### 实施步骤"
  ];

  for (const [index, step] of analysis.steps.entries()) {
    lines.push(`${index + 1}. ${step}`);
  }

  if (Array.isArray(analysis.files) && analysis.files.length > 0) {
    lines.push("", "### 预计涉及文件");
    for (const file of analysis.files) {
      lines.push(`- ${file}`);
    }
  }

  if (Array.isArray(analysis.risks) && analysis.risks.length > 0) {
    lines.push("", "### 注意事项");
    for (const risk of analysis.risks) {
      lines.push(`- ${risk}`);
    }
  }

  lines.push(
    "",
    `如果确认执行，请在本 issue 评论中回复：\`${EXECUTE_MARKER}\``
  );

  return lines.join("\n");
}

function applyFiles(files) {
  for (const file of files) {
    const relativePath = String(file.path || "").trim().replace(/\\/g, "/");
    if (!relativePath) {
      throw new Error("Encountered a file entry without a path.");
    }

    ensureAllowedRelativePath(relativePath);

    const absolutePath = path.join(process.cwd(), relativePath);
    ensureInsideWorkspace(absolutePath);

    if (file.delete) {
      if (fs.existsSync(absolutePath)) {
        fs.rmSync(absolutePath);
      }
      continue;
    }

    fs.mkdirSync(path.dirname(absolutePath), { recursive: true });
    fs.writeFileSync(absolutePath, String(file.content ?? ""), "utf8");
  }
}

function ensureAllowedRelativePath(relativePath) {
  if (relativePath.startsWith("/") || relativePath.includes("..")) {
    throw new Error(`Refusing to write suspicious path: ${relativePath}`);
  }

  for (const prefix of PROTECTED_PATH_PREFIXES) {
    if (relativePath === prefix.slice(0, -1) || relativePath.startsWith(prefix)) {
      throw new Error(`Refusing to modify protected path: ${relativePath}`);
    }
  }
}

function ensureInsideWorkspace(targetPath) {
  const resolvedWorkspace = path.resolve(process.cwd());
  const resolvedTarget = path.resolve(targetPath);

  if (!resolvedTarget.startsWith(resolvedWorkspace)) {
    throw new Error(`Refusing to write outside the workspace: ${resolvedTarget}`);
  }
}

async function listIssueComments({ githubToken, owner, repo, issueNumber }) {
  const comments = await githubApi({
    githubToken,
    owner,
    repo,
    method: "GET",
    endpoint: `/issues/${issueNumber}/comments?per_page=100`
  });

  return Array.isArray(comments) ? comments : [];
}

function summarizeComments(comments) {
  let totalChars = 0;
  const blocks = [];

  for (const comment of comments) {
    const author = comment.user?.login || "unknown";
    const body = normalizeMultiline(comment.body);
    if (!body) {
      continue;
    }

    const block = `COMMENT BY ${author}:\n${body}\n`;
    if (totalChars + block.length > MAX_COMMENT_CHARS) {
      break;
    }
    blocks.push(block);
    totalChars += block.length;
  }

  return blocks.join("\n");
}

async function createOrReusePullRequest({
  githubToken,
  owner,
  repo,
  defaultBranch,
  branchName,
  title,
  body
}) {
  const existing = await githubApi({
    githubToken,
    owner,
    repo,
    method: "GET",
    endpoint: `/pulls?state=open&head=${encodeURIComponent(`${owner}:${branchName}`)}`
  });

  if (Array.isArray(existing) && existing.length > 0) {
    return existing[0];
  }

  return githubApi({
    githubToken,
    owner,
    repo,
    method: "POST",
    endpoint: "/pulls",
    body: {
      title,
      body,
      head: branchName,
      base: defaultBranch
    }
  });
}

async function commentOnIssue({ githubToken, owner, repo, issueNumber, body }) {
  return githubApi({
    githubToken,
    owner,
    repo,
    method: "POST",
    endpoint: `/issues/${issueNumber}/comments`,
    body: { body }
  });
}

async function githubApi({ githubToken, owner, repo, method, endpoint, body }) {
  const response = await fetch(`https://api.github.com/repos/${owner}/${repo}${endpoint}`, {
    method,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${githubToken}`,
      "Content-Type": "application/json",
      "User-Agent": "ttfhw-issue-worker"
    },
    body: body ? JSON.stringify(body) : undefined
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GitHub API failed: ${response.status} ${text}`);
  }

  return response.json();
}

function sanitizeBranchName(value) {
  return value
    .replace(/[^a-zA-Z0-9/_-]+/g, "-")
    .replace(/\/+/g, "/")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "issue/auto-task";
}

function slugify(value) {
  return String(value)
    .replace(TITLE_MARKER, "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function normalizeLine(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function normalizeMultiline(value) {
  return String(value || "").replace(/\r\n/g, "\n").trim();
}

function defaultPrBody(issue) {
  return `Automated implementation for issue #${issue.number}.`;
}

main().catch((error) => {
  console.error("[issue-worker] Failed:", error);
  process.exitCode = 1;
});
