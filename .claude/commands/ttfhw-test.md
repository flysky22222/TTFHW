# /ttfhw-test — 运行 TTFHW 用例测试

## 用途
模拟人工执行一个 TTFHW 用例的完整测试流程，输出 `test_data.json`、`report.md`、`fixes.md`，并自动提交到 main 分支。

## 用法
```
/ttfhw-test <UC-ID>
/ttfhw-test UC-07
/ttfhw-test UC-01 --phases understanding acquisition
```

## 执行步骤

当用户输入 `/ttfhw-test <UC-ID>` 时，按以下步骤执行：

### 1. 确认用例信息
- 查阅 `use-cases.md` 中对应用例的描述
- 打印用例 ID、社区、角色、目标

### 2. 运行模拟器（调用 ttfhw_simulator.py）
```bash
cd /home/user/TTFHW
python tools/ttfhw_simulator.py --use-case <UC-ID> \
  --output-dir use-cases/<uc-dir>/
```

UC-ID 到目录映射：
- UC-01 → use-cases/cann-contributor
- UC-02 → use-cases/cann-user
- UC-03 → use-cases/mindie-user
- UC-04 → use-cases/mindie-contributor
- UC-05 → use-cases/mindspeed-user
- UC-06 → use-cases/mindspore-user
- UC-07 → use-cases/openeuler-contributor
- UC-08 → use-cases/openubmc-contributor

### 3. 生成报告和修复文档（调用 report_gen.py）
```bash
python tools/report_gen.py --data use-cases/<uc-dir>/test_data.json
```
这会在同目录生成 `report.md` 和 `fixes.md`

### 4. 对发现的问题尝试修复
- 读取 `fixes.md` 中 status=open 的问题
- 对于 blocker/major 问题，通过 web 搜索寻找修复方案
- 将修复尝试结果更新到 `fixes.md`

### 5. 提交到 main 分支
```bash
git add use-cases/<uc-dir>/
git commit -m "test(<UC-ID>): add TTFHW test results for <title>"
git push -u origin main
```

## 注意事项
- 需要设置 `ANTHROPIC_API_KEY` 环境变量
- 每个用例独立提交，不要批量提交
- fixes.md 和 report.md 分开，不要混用
