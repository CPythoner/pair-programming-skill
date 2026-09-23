# State Model

## `.pair/config.yaml`

用户偏好和默认行为。除非用户显式修改，不要频繁重写。

## `.pair/design.md`

Canonical implementation design for the current feature.

If `/pair plan` receives only a feature goal or incomplete design, the agent creates this
document and must wait for explicit user approval before creating Shadow or implementing
source code.

If the user supplies an implementation-ready design, normalize or reference that design
here so future sessions have a stable canonical artifact.

The current approval state is tracked in `manifest.yaml`; do not infer approval merely
from this file existing.

Approval is revision-scoped. Implementation is permitted only when
`status == approved` and `approved_revision == revision`. Any material edit to the design
increments `revision` and invalidates the previous approval.

## `.pair/manifest.yaml`

描述“这个 Feature 是什么，以及 Shadow/Guide 得出的实现地图是什么”。

它包含：
- design source/status/revision/approval evidence；
- baseline；
- feature goal；
- acceptance criteria；
- Shadow solution；
- Guide branch；
- steps；
- validation；
- pitfall IDs mapped to Guide steps；
- risks；
- assumptions。

Manifest 代表计划和参考实现事实，不代表 Human Workspace 一定已经完成。

## `.pair/progress.yaml`

描述 Human Workspace 的实际进度。

每个 step 至少记录：
- pending / active / review / completed / skipped / superseded；
- origin: human / ai / mixed；
- validation；
- hint level；
- divergences；
- notes；
- pitfall communication state。

## `.pair/pitfalls.yaml`

Canonical structured journal of meaningful problems and hidden constraints discovered during
Shadow implementation.

Pitfalls are retained even after resolution because they are part of the teaching plan.
Each pitfall has a stable ID and maps to one or more Guide steps. Progress tracks whether
each pitfall has actually been surfaced/discussed with the user.

Do not use this file for trivial typos or generic activity logs.

## `.pair/notes.md`

保存不会很好地放进 YAML 的设计决策：

- 为什么选择某个方案；
- 为什么放弃某个 Shadow 设计；
- 项目约束；
- Review 中发现的重要知识；
- 后续值得处理但当前 Feature 不应顺手处理的问题。

## 状态一致性

开始新的 `/pair` 操作前检查：

1. 当前 repo root 与 manifest 一致；
2. Human branch 与 progress 中记录一致；
3. baseline/HEAD 是否发生未知移动；
4. Guide/Solution refs 是否还存在；
5. current design revision 是否已被批准；
6. 当前 step dependencies 是否满足。

Human Workspace 和 metadata 冲突时，以 Human Workspace 为准，修正 metadata。

不要为了恢复 metadata 状态去 reset Human Workspace。
