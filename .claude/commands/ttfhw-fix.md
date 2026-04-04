# /ttfhw-fix — 对 TTFHW 测试发现的问题尝试修复

## 用途
读取指定用例的 `fixes.md`，对 `open` 状态的问题逐一搜索修复方案并记录结果。
修复记录**仅更新** `fixes.md`，不修改 `report.md`。

## 用法
```
/ttfhw-fix <UC-ID>
/ttfhw-fix UC-07
```

## 执行步骤

### 1. 读取问题列表
读取 `use-cases/<uc-dir>/fixes.md`，找出所有 `fix_status: open` 的问题。

### 2. 对每个问题执行
按严重度排序（blocker > major > minor），对每个 open 问题：

1. **搜索修复方案**
   - 在 Baidu/Doubao/官方文档搜索问题的解决方案
   - 记录找到的文档 URL 和解决步骤

2. **尝试修复**
   - 如果问题是文档缺失/错误：记录正确信息和来源
   - 如果是命令/配置问题：提供正确命令
   - 如果是社区流程问题：提供改进建议

3. **更新 fixes.md**
   - 将 fix_status 从 `open` 改为 `attempted` 或 `fixed`
   - 在"修复尝试"章节填入具体步骤
   - 在"修复结论"章节填入结论

### 3. 保存并提交
```bash
git add use-cases/<uc-dir>/fixes.md
git commit -m "fix(<UC-ID>): attempt fixes for problems found in TTFHW test"
git push origin main
```

## 注意事项
- 不要修改 report.md，报告是测试的客观记录
- 修复记录应包含：问题根因分析 + 修复步骤 + 验证方式
- 如无法修复，记录原因并标记为 wontfix
