# P2 Dashboard Enhancement 设计

## 模块与数据流

- `state.py`：安全读取 YAML/JSON、版本检查；复用到源状态、会话、操作日志。
- `collector.py`：读取项目真值，构建 `DashboardSnapshot`；不写文件。
- `insights.py`：纯计算依赖层级/readiness、实现来源、验证证据和下一步建议。
- `sessions.py`：解析真实会话元数据，兼容旧 Markdown；生成稳定、路径安全的 history 文件名。
- `workspace.py`：直接子项目发现、独立收集与错误隔离。
- `export.py`：统一写入 JSON、受管理的 history JSON、静态 HTML/资源；历史随源记录重建。
- `watch.py`：显式源文件 polling；错误时发布 freshness 元数据并保留上次业务数据；支持单项目和 workspace。
- `renderer.py`：静态依赖图、指标/建议/历史、workspace 链接；不使用远程图形库或运行时网络依赖。

步骤依赖定义与执行状态分开。图错误明确展示，环/缺失依赖的节点不被标为 ready。
来源指标只使用 `progress.steps[*].origin`，分母为 completed/done 步骤；mixed 独立保留。
验证状态来自显式结果记录，命令字符串和步骤 completed 均不证明验证通过。
会话元数据在工作流开始/结束时写入 source；生成的 history 不是历史事实的备用存储。
Watch 只自动更新文件；浏览器刷新后展示。freshness 包含模式、fresh/stale、检查时间与错误。
Workspace 默认输出 `<workspace>/.pair/dashboard`，每个有效项目有独立详情页；不计算跨项目平均完成率。

## 会话源契约

`schema_version: 1`，稳定 `id`、`title`、`feature_slug`、`started_at`、可选 `ended_at`、
`status: active|completed|abandoned|unknown`、可选 `actor/current_step`。
在 `schemas/session.schema.json` 定义，可作为 Markdown frontmatter 或独立 YAML/JSON。
旧 Markdown 的文件修改时间只用于标注为 file_mtime 的时间线，不冒充真实会话时间。
重复 ID 不生成相互覆盖的 history；无效单条会话/操作记录显示警告与必要的处理建议。

## UI Design Specification

- Purpose：帮助用户识别当前阻塞、下一可执行步骤和已有验证证据，并查看来源与历史。
- Aesthetic：沿用已确认的工业控制台风格。
- Palette：`#0d1117`、`#151b23`、`#64dca7`、`#f0c075`；保持现有浅色变量。
- Typography：保留现有 `-apple-system / BlinkMacSystemFont / Segoe UI`。
- Layout：顶部“当前需要处理什么”；状态与进度并排；依赖层级与步骤详情；来源/验证/知识；历史和项目总览。
- 已确认设计覆盖技能默认字体/布局建议；用户无构建链与本地资源要求覆盖 Tailwind/远程图标库建议。
- 图使用生成的 SVG 和 HTML；保留键盘导航、减少动效设置、深浅色和窄屏适配。

## 验证边界

自动化检查源状态不变、链接/资源存在、HTML 转义、稳定历史 ID 与删除同步、单仓库错误隔离。
使用临时真实 `.pair` 数据运行 CLI/Watch；浏览器验证实际生成页面，演示数据明确标注。
PowerShell 若无可执行运行环境，仅报告静态包校验，不声称 Windows 已实测。
