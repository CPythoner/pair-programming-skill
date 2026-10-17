# P2 验收记录

日期：2026-10-15。范围：P2-01 至 P2-06，统一进入 PR #7。

代码已提交并推送到 `codex/p2-dashboard-enhancement`，统一评审入口：
[PR #7](https://github.com/CPythoner/pair-programming-skill/pull/7)。

## 自动化检查

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider`：77 项通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-package.py`：通过，包含 6 份 schema 和安装包运行文件检查。
- `bash -n scripts/install.sh`：通过。
- `git diff --check`：通过；提交前另检查暂存区。

测试覆盖依赖图错误与 readiness、完成步骤来源指标、显式验证结果、会话元数据和旧记录兼容、稳定历史 ID 与重建、workspace 故障隔离、Watch 输入/重试/退出、JSON-only，以及安装后 Python 入口。

## CLI 与浏览器实测

使用临时 workspace 与明确标记为 DEMO 的 `.pair` 数据，生成本地静态页面：

- 实际运行 Watch，修改步骤后输出 `Step: graph -> tests`，页面由 4/7 更新为 5/7。
- 写入无效 YAML 后保留上一份有效业务数据，显示 stale 和诊断建议；修复源文件后恢复 fresh。
- 依赖图包含 7 个节点、6 条真实依赖边；节点链接定位到步骤详情。
- 实现来源保留 human / ai / mixed / unknown，并显示完成步骤分母和记录覆盖率。
- 同日多个会话分别导出；历史链接可打开 JSON；旧 Markdown 的真实时间和结果显示未知。
- workspace 显示 3 个项目，单个 YAML 错误被隔离；错误项目显示未知，项目详情与 Projects 链接可往返。
- 恢复异常、待批准设计和 takeover 示例显示处理建议，不引导直接进入下一步。
- 系统/浅色/深色主题切换有效；320px 和 390px 页面无横向溢出，依赖图在自身容器滚动。
- 浏览器未记录 console warning/error。

截图和演示产物位于本地 `.pair/dashboard`，不进入 Git。

## 验收边界

Dashboard 为只读静态产物，Watch 更新文件后仍需手动刷新浏览器；建议命令仅供复制。
PowerShell 安装脚本通过包静态检查，未在 Windows 实际执行。
合并与发布不在本次操作范围内；代码通过同一个 PR 供审阅。

## Step 同步复核（2026-10-15）

- 修复旧 `progress.plan` 与 `progress.steps` 并存时误读旧状态的问题；兼容完成状态的
  `completed / done / complete`，计数、依赖 readiness 与来源分母使用同一规则。
- 数字样式的字符串 ID 保持原值；错误的数字 YAML ID 明确报错，避免静默丢失完成状态。
  缺失的正式 manifest ID 不再用列表位置冒充。编号改为 `Step 1 · ID: 01`。
- 当前步骤卡片、竖向列表、图节点使用同一编号、ID、状态和 current 标记；明确列出
  skipped/superseded 的排除数量。历史事件标为 Recorded step，保留事件当时的 ID。
- 对不存在的 current、与 current 冲突的在进行步骤，以及 complete 阶段仍有未完成步骤，
  显示对账提示；不通过改写源状态掩盖矛盾。
- 修复 workspace 源文件失败时详情页仍显示旧 fresh 数据的问题。有上次有效快照时标为
  stale；否则输出 unavailable/未知。正常项目继续更新，源恢复后清除错误。
- 全量测试 **93 项通过**；包校验和 diff 检查通过。新增回归覆盖多位置一致性、重排 ID、
  状态切换、来源冲突、错误输入及 workspace 失败/恢复。
- 使用明确标为 DEMO 的 5 行计划（3 个计数步骤、1 skipped、1 superseded）实际运行
  workspace Watch。浏览器确认 `0% → 33% → 67% → 100%`、review 不提前计完成、
  完成后清除 current、历史 ID 不变，以及错误/恢复时总览与详情的提示和数据。
- 320px/390px 无页面横向溢出；图内文字未超出节点。Watch 仍需手动刷新页面。
