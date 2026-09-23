# Pair Programming Skill

[English](README.md) | **简体中文**

<p align="center">
  <img src="assets/banner.png" alt="Pair Programming Skill 横幅" width="100%" />
</p>

> AI 先在隔离环境里把功能做通，再带你一步一步把它真正变成“你能理解、能维护、敢继续改”的代码。

现代 Coding Agent 的问题已经不再是“不会写代码”，而是：

> **AI 的编码速度正在超过人的理解速度。**

如果一个 Agent 一次性改几十个文件、生成上千行代码，即使测试全部通过，你也可能很快失去对项目的掌控。

Pair Programming Skill 的目标不是限制 AI，而是重新安排 AI 和人的分工：

- AI 先在 **Shadow Workspace** 中完整探索、实现、编译、测试；
- 用户确认设计后，AI 再把已验证方案反向拆成可理解的小步骤；
- 真正的工作分支仍由用户主导；
- 用户随时可以让 AI 提示、展示参考实现，或者直接接管某一部分；
- AI 在 Shadow 阶段踩过的坑不会丢失，而会在后续结对编程中主动告诉用户。

核心原则：

> **AI coding throughput <= Human comprehension throughput**

---

## 安装

### 推荐：直接让你的 Coding Agent 安装

把下面这段话发给 Codex、Claude Code、Cursor、OpenCode、Gemini CLI 或 GitHub Copilot：

> 帮我安装 Pair Programming Skill：
> https://github.com/CPythoner/pair-programming-skill
>
> 请自动识别你当前运行在哪个 Coding Agent 中，并安装到该平台推荐的 Skill 目录。
>
> 如果平台支持，优先使用共享目录：
> `.agents/skills/pair-programming/`
>
> 否则使用该平台原生的 Skill 目录。
>
> 如果已经存在旧版本，不要直接覆盖，先告诉我。
>
> 安装完成后：
> 1. 检查 `SKILL.md` 和 supporting files 是否完整；
> 2. 告诉我实际安装路径；
> 3. 告诉我是否需要 reload / restart；
> 4. 告诉我如何开始使用 Pair Programming Skill。

这是推荐的安装方式，因为 Agent 可以根据自己所在的平台选择正确的发现目录，并在安装后直接验证结果。

### 从终端安装

推荐共享的 portable 安装：

```bash
git clone https://github.com/CPythoner/pair-programming-skill.git
cd pair-programming-skill
bash scripts/install.sh portable
```

默认安装到：

```text
.agents/skills/pair-programming/
```

用户级共享安装：

```bash
bash scripts/install.sh portable --scope user
```

Windows PowerShell：

```powershell
git clone https://github.com/CPythoner/pair-programming-skill.git
cd pair-programming-skill
.\scripts\install.ps1 portable
```

### 按平台安装

如果不希望使用共享 portable 路径，也可以按宿主安装：

```bash
bash scripts/install.sh codex
bash scripts/install.sh cursor
bash scripts/install.sh gemini-cli
bash scripts/install.sh github-copilot
bash scripts/install.sh claude-code
bash scripts/install.sh opencode
```

Cursor、Gemini CLI、GitHub Copilot 还可以使用各自原生目录：

```bash
bash scripts/install.sh cursor --native
bash scripts/install.sh gemini-cli --native
bash scripts/install.sh github-copilot --native
```

PowerShell：

```powershell
.\scripts\install.ps1 cursor -Native
.\scripts\install.ps1 gemini-cli -Native
.\scripts\install.ps1 github-copilot -Native
```

安装到其他项目时，Bash 使用 `--target /path/to/repo`，PowerShell 使用
`-Target C:\path\to\repo`。

已有安装默认不会被覆盖，只有显式传入 `--force` / `-Force` 才会替换。

### 支持的平台

| 平台 | 默认项目级目录 | 默认用户级目录 | 显式触发 |
|---|---|---|---|
| Portable Agent Skills | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | 由宿主决定 |
| Codex | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | `$pair-programming plan ...` |
| Cursor | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | `/pair-programming plan ...` |
| Gemini CLI | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | 激活 Skill 后提供 `/pair ...` 语义 |
| GitHub Copilot | `.agents/skills/pair-programming/` | `~/.agents/skills/pair-programming/` | 在 Prompt 中要求使用 `/pair-programming` |
| Claude Code | `.claude/skills/pair-programming/` | `~/.claude/skills/pair-programming/` | `/pair-programming plan ...` |
| OpenCode | `.opencode/skills/pair-programming/` | `~/.config/opencode/skills/pair-programming/` | `/pair-programming plan ...` |

各平台详细发现机制和调用方式见 [adapters/README.md](adapters/README.md)。

### 校验适配包

```bash
python3 scripts/validate-package.py
```

---

## 为什么需要它

传统 Coding Agent 的典型模式是：

```text
需求
 ↓
Agent
 ↓
大量代码
 ↓
测试通过
 ↓
“看起来没问题”
 ↓
几周之后：这段代码我已经不敢动了
```

Pair Programming Skill 把流程改成：

```text
需求 / 设计
    ↓
Design Gate
    ↓
Shadow 完整实现
    ↓
Build / Test / Debug
    ↓
记录踩坑与隐藏约束
    ↓
反向拆解为 Guide Steps
    ↓
你逐步实现
    ↓
AI Review / Hint / Explain
    ↓
需要时 AI 接管局部
    ↓
最终得到你真正能维护的代码
```

Shadow 是 AI 已经提前飞过一次的航线。

Human Workspace 才是最终代码。

---

## 核心设计

整个 Skill 有四个关键层次：

```text
┌──────────────────────────────┐
│ 1. Design Gate               │
│ 先把“要做什么”变成可实现设计 │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 2. Shadow Workspace          │
│ AI 完整实现、测试、踩坑       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 3. Guide Branch              │
│ 把最终方案反向拆成教学步骤    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 4. Human Workspace           │
│ 用户真正完成和拥有的代码      │
└──────────────────────────────┘
```

---

## 1. Design Gate：先设计，再实现

`/pair plan` 并不意味着立刻写代码。

如果你只给出一个目标：

```text
/pair plan 增加远程 MCP 自动重连
```

这只是一个 **Feature Goal**，不是 implementation-ready design。

AI 会先：

1. 阅读相关现有代码；
2. 理解当前数据流、接口、生命周期和约束；
3. 设计具体方案；
4. 保存到：

```text
.pair/design.md
```

5. 将状态设为：

```yaml
design:
  source: ai_generated
  status: awaiting_approval
  revision: 1
  approved_revision: 0
```

然后 **停止**。

此时：

- 不创建 Shadow Worktree；
- 不创建实现分支；
- 不修改业务代码；
- 不生成完整实现。

直到你明确确认：

```text
按这个方案实现
```

才进入 Shadow Implementation。

### 设计确认绑定 revision

设计确认不是永久有效的。

例如：

```text
revision 3
   ↓
用户确认
   ↓
approved_revision = 3
   ↓
设计发生实质修改
   ↓
revision 4
status = awaiting_approval
approved_revision = 0
```

新的设计必须重新确认。

只有满足：

```text
design.status == approved
AND
design.approved_revision == design.revision
```

才允许开始实现。

如果 `/pair plan` 一开始传入的就是足够完整的设计方案、ADR、PRD 或设计文档，Skill 会读取并确认其是否 implementation-ready，保存/规范化为 `.pair/design.md` 后再进入实现阶段。

---

## 2. Shadow Workspace：让 AI 先把整条路走通

设计确认后，AI 会创建隔离的 Git Worktree：

```text
pair-shadow/<feature>/solution
```

Shadow Workspace 允许 AI：

- 完整实现功能；
- 尝试不同方案；
- 编译；
- 运行测试；
- Debug；
- 验证边界条件；
- 修复错误；
- 做必要的实验性修改。

但 Shadow 不会直接覆盖你的真实工作区。

### 默认 Worktree 布局

```text
workspace/
├── my-project/
│   ├── .git/
│   │   └── worktrees/...          # Git 自己维护的 metadata
│   ├── .pair/                     # Pair Programming 状态
│   └── src/
│
└── .pair-worktrees/
    └── my-project/
        └── feature-name/
            └── shadow/            # 实际 Shadow checkout
```

Skill 使用：

```bash
git rev-parse --show-toplevel
git rev-parse --git-common-dir
```

解析真实 Git 路径，而不是假设 `.git` 一定是目录。

> 实际源码 Worktree 不放进 `.git`。  
> `.git/worktrees/*` 只由 Git 自己维护。

每个 Feature 默认只保留一个物理 Shadow Checkout。

完整实现保存在：

```text
pair-shadow/<feature>/solution
```

教学提交链保存在：

```text
pair-shadow/<feature>/guide
```

---

## 3. Pitfall Journal：AI 踩过的坑必须告诉你

Shadow 最大的价值不只是提前得到正确答案。

它还提前替你发现：

- 错误假设；
- 生命周期问题；
- 并发问题；
- API 隐藏约束；
- 构建和依赖问题；
- 平台差异；
- 测试才会暴露的边界情况；
- 看起来合理但实际上走不通的实现方式。

这些信息不会随着最终代码通过测试而消失。

所有有学习价值的坑都会记录到：

```text
.pair/pitfalls.yaml
```

例如：

```yaml
- id: P003
  title: Registry teardown order causes dangling provider references
  status: resolved
  severity: high
  category: lifetime

  symptom: Integration test crashes during Plugin destruction.

  wrong_assumption:
    Registry entries could outlive Plugin instances.

  root_cause:
    Registry does not own Provider lifetime.

  resolution:
    Remove capability registrations before Plugin destruction.

  related_steps:
    - plugin-lifecycle

  lesson_for_human:
    Registry entries must never outlive their Provider.

  avoidance:
    Always unregister before destroying Plugin.
```

### 后续会主动提醒

当你执行：

```text
/pair next
```

如果当前步骤关联了某个 Shadow Pitfall，AI 必须主动告诉你。

例如：

```text
Shadow pitfall P003

Shadow 实现最初把 unregister 放到了 Plugin 析构之后，
测试出现悬空引用。

根因：
Registry 不拥有 Provider。

你这一阶段需要守住的约束：
先 unregister，再销毁 Plugin。
```

你不需要主动问：

> “AI 当时有没有踩坑？”

`/pair review` 也会检查你的实现是否重新落入这些已知问题。

因此 Shadow 同时承担：

```text
Reference Implementation
        +
Pre-mortem / Pitfall Discovery
```

---

## 4. Reverse Decomposition：从正确答案反推学习路径

Shadow 完整实现并验证以后，Skill 不会简单按文件拆 diff。

例如这种拆法没有意义：

```text
Step 1 修改 foo.h
Step 2 修改 foo.cpp
Step 3 修改 test.cpp
```

Skill 会按：

- dependency；
- concept；
- architecture；
- verification point；

反向拆解。

例如：

```text
Step 1  Define Capability identity
        ↓
Step 2  Implement CapabilityRegistry
        ↓
Step 3  Integrate with PluginManager
        ↓
Step 4  Define lifecycle / concurrency rules
        ↓
Step 5  Add integration tests
        ↓
Step 6  Final verification
```

默认建议每一步：

- 一个主要概念；
- 1–3 个文件；
- 约 150 行有效 diff；
- 一个明确验证点。

复杂步骤可以超过这个限制，但必须保持逻辑完整。

---

## 5. Guide Branch：每一步都有稳定参考答案

最终方案验证完成后，Skill 会从 baseline 重新构造一条教学提交链：

```text
pair-shadow/<feature>/guide
```

例如：

```text
baseline
   │
   ├── Step 1 commit
   ├── Step 2 commit
   ├── Step 3 commit
   ├── Step 4 commit
   └── Step 5 commit
```

这样：

```text
/pair show step 3
```

可以准确查看 Step 3 的 reference diff。

而：

```text
/pair take step 3
```

也能精确拿到这一阶段的实现，而不是临时从一个几百行的大 diff 中猜。

Guide Branch 不要求和 Shadow 探索过程的 commit history 一致。

它的目标是：

> **正确 + 可验证 + 可教学。**

---

## 6. Guided Reconstruction：你坐驾驶位

之后真正的 Human Workspace 开始逐步实现。

执行：

```text
/pair next
```

AI 默认只告诉你当前一步需要知道的内容：

- Goal；
- Why；
- 当前代码路径；
- 关键约束；
- 需要修改的文件/符号；
- 验证命令；
- Shadow 阶段已经发现的坑；
- 推荐的第一步动作。

不会默认把完整答案直接贴出来。

---

## 命令

这些命令是 **对话协议**，并不要求 Coding Agent 真正注册 Slash Command。

### `/pair plan <goal-or-design>`

启动一个新的 Pair Programming Feature。

如果输入不够具体：

```text
设计
→ 保存 .pair/design.md
→ 等待用户确认
```

如果已经提供完整设计：

```text
确认 design
→ Shadow Implementation
→ Guide
```

---

### `/pair next`

进入下一个可执行 Guide Step。

AI 会先讲清楚：

- 为什么现在做；
- 应该改什么；
- 哪些约束不能破坏；
- Shadow 在这里踩过什么坑；
- 如何验证。

然后停下来让你写。

---

### `/pair review [scope]`

Review 你的实现。

Review 优先级：

```text
correctness
→ behavioral gap
→ regression
→ ownership / lifetime
→ error handling
→ concurrency
→ API / ABI
→ maintainability
→ style
```

Shadow 只是参考答案。

如果你的实现更简单、更符合项目习惯，而且行为正确，Skill 应该保留你的实现。

---

### `/pair hint [scope] [level]`

渐进式提示：

```text
Level 1  概念提示
Level 2  API / 数据结构 / 控制流提示
Level 3  伪代码
Level 4  Reference excerpt / diff
Level 5  AI takeover
```

重复请求 hint 时默认逐级提升。

---

### `/pair explain <scope>`

只解释，不修改代码。

可以解释：

- 当前 Step；
- 文件；
- Symbol；
- 架构决策；
- 生命周期；
- 数据流；
- 某个 Pitfall；
- Reference Diff。

---

### `/pair show <scope>`

查看参考实现，但不应用。

例如：

```text
/pair show step 3
/pair show file src/plugin_manager.cpp
/pair show symbol PluginManager::registerCapability
/pair show tests
/pair show cmake
```

---

### `/pair take <scope>`

这一部分直接交给 AI。

例如：

```text
/pair take step 3
/pair take tests
/pair take cmake
/pair take conan
/pair take file src/foo.cpp
/pair take symbol Foo::bar
/pair take remaining
/pair take all
```

Skill 优先使用：

```text
Semantic Port
      ↓
Cherry-pick Guide Commit
      ↓
3-way Patch
      ↓
Manual Adaptation
```

如果你的代码已经和 Shadow 不同，AI 不应该粗暴覆盖，而应该把参考实现的“意图”移植到你的当前设计里。

每次 Takeover 前都会记录恢复信息。

---

### `/pair challenge [scope]`

AI 不写代码，而是问你 1–3 个真正影响维护能力的问题，例如：

```text
为什么 Registry 不应该拥有 Provider？

如果 Plugin 先析构，会发生什么？

为什么这个锁应该放在 Registry 而不是 PluginManager？
```

不是考语法，而是检查你是否掌握关键设计约束。

---

### `/pair status`

查看完整状态：

```text
Feature: Plugin Capability Management
Design: approved revision 3
Shadow: verified
Guide: 6 steps

[✓] 1 Capability model          human
[✓] 2 CapabilityRegistry        human
[✓] 3 Plugin integration        mixed
[→] 4 Concurrency protection    current
[ ] 5 Integration tests
[ ] 6 Final verification

Shadow pitfalls:
✓ P001 surfaced
✓ P002 discussed
! P004 unresolved

Next:
Step 4 — locking boundary
```

---

### `/pair rebase-plan`

这里的 rebase 不是 Git rebase。

如果你在实现过程中设计发生了变化，甚至写出了比 Shadow 更好的方案：

```text
Human implementation
        +
remaining goal
        ↓
new Shadow generation
        ↓
new remaining Guide
```

Skill 会：

- 以你的当前代码为权威；
- 保留已经完成的工作；
- 重做剩余 Shadow；
- 更新剩余 Guide；
- 让失效步骤变成 `superseded`。

不会把你的代码 reset 回 AI 最初的方案。

---

## 状态文件

Pair Programming Skill 使用 `.pair/` 保存当前 Feature 的工作状态：

```text
.pair/
├── config.yaml
├── design.md
├── manifest.yaml
├── progress.yaml
├── pitfalls.yaml
├── notes.md
├── checkpoints/
├── patches/
└── sessions/
```

### `design.md`

当前 Feature 的 Canonical Design。

设计未确认时，禁止进入实现。

### `manifest.yaml`

描述 Feature 本身和 Reference Implementation：

- feature goal；
- design revision / approval；
- baseline；
- Shadow branch；
- Guide branch；
- validation；
- steps；
- risks；
- Pitfall 映射。

### `progress.yaml`

Human Workspace 的真实进度：

- 当前阶段；
- 当前 Step；
- human / ai / mixed；
- hint level；
- divergences；
- knowledge coverage；
- Pitfall 是否已经告诉用户。

### `pitfalls.yaml`

Shadow 阶段积累的工程知识：

- symptom；
- failed approach；
- root cause；
- resolution；
- validation；
- related steps；
- lesson for human；
- avoidance。

### `notes.md`

记录设计决策、重要发现、Deferred Work 等。

### `checkpoints/`

在 `/pair take` 等操作前保存恢复信息，避免 AI 覆盖用户未提交工作。

### `sessions/`

保存跨会话摘要，方便下一次继续：

- 当前 Step；
- 重要决策；
- 验证结果；
- 已讨论 Pitfalls；
- 下一步。

---

## 一个完整示例

开始：

```text
/pair plan 为 Plugin 增加 Capability Registry
```

因为这只是 Feature Goal，AI 先生成：

```text
.pair/design.md
```

然后：

```text
Design revision 1
Status: awaiting_approval
```

你：

```text
方案没问题，开始实现
```

AI 在 Shadow 中实现并验证，期间发现：

```text
P001 Duplicate provider semantics were ambiguous
P002 Registry ownership caused lifetime issue
P003 Existing test fixture destroys Plugin too early
```

最终反向生成：

```text
Step 1 Capability identity
Step 2 CapabilityRegistry
Step 3 Duplicate provider semantics
Step 4 Plugin lifecycle integration
Step 5 Tests
Step 6 Final verification
```

然后你：

```text
/pair next
```

AI 开始带你完成 Step 1。

做到 Step 4 时，它会主动提醒：

```text
Shadow pitfall P002

这里 Shadow 曾经出现生命周期错误。
Registry 不应该拥有 Provider。
注销必须发生在 Provider 销毁之前。
```

如果你觉得测试代码没必要自己写：

```text
/pair take tests
```

AI 直接完成测试，再把控制权交还给你。

---

## Human Workspace 永远是权威

这是整个 Skill 最重要的一条规则。

```text
Shadow implementation != 标准答案
```

Shadow 只是：

- 已验证参考实现；
- 探路结果；
- Pitfall Discovery 环境。

如果你的实现：

- 更简单；
- 更符合现有架构；
- 更少 abstraction；
- 行为同样正确；

那么应该保留你的方案，并更新后续 Guide。

---

## 安全边界

Skill 默认不会：

- `git reset --hard`
- `git clean -fd`
- 强制 checkout 覆盖用户代码
- 自动合并 Shadow Branch
- 自动 push Shadow Branch
- force-push
- 在未确认设计时开始完整实现
- 因为 Shadow 与 Human 不同就强迫 Human 改成 Shadow
- 在用户未要求时顺手重构无关代码

任何可能覆盖 Human Workspace 的 Takeover 操作都应该先创建 checkpoint。

---


## 推荐配置

默认模板：

```text
templates/config.yaml
```

推荐保持：

```yaml
interaction:
  human_controls_main_workspace: true
  auto_advance_after_review: false
  explain_before_human_step: true
  show_reference_by_default: false

limits:
  preferred_files_per_step: 3
  preferred_effective_diff_lines: 150
  hard_effective_diff_lines: 300

takeover:
  prefer_semantic_port: true
  create_checkpoint: true
  preserve_human_changes: true
  return_control_after_apply: true
```

这些默认值的目的只有一个：

> 不让 AI 的有效产出速度超过你的理解速度。

---

## 项目结构

```text
pair-programming-skill/
├── LICENSE
├── README.md
├── README.zh-CN.md
├── assets/
│   ├── banner.png
│   └── icon.png
├── SKILL.md
│
├── examples/
│   └── example-session.md
│
├── adapters/
│   ├── README.md
│   ├── codex.md
│   ├── cursor.md
│   ├── gemini-cli.md
│   ├── github-copilot.md
│   ├── claude-code.md
│   └── opencode.md
│
├── scripts/
│   ├── install.sh
│   ├── install.ps1
│   └── validate-package.py
│
├── reference/
│   ├── command-protocol.md
│   ├── decomposition.md
│   ├── design-gate.md
│   ├── pitfall-journal.md
│   ├── review-rubric.md
│   ├── state-model.md
│   └── takeover.md
│
└── templates/
    ├── config.yaml
    ├── design.md
    ├── manifest.yaml
    ├── notes.md
    ├── pitfalls.yaml
    ├── progress.yaml
    └── session-summary.md
```

---

## 适合什么场景

特别适合：

- 中大型 Feature；
- 系统软件；
- 架构改造；
- 并发和生命周期复杂的代码；
- Coding Agent 一次会改很多文件的任务；
- 你想使用强 AI，但又不想失去代码掌控力的项目。

对于一两行明显修复、拼写修改、简单配置变化，不一定需要启动完整 Shadow → Guide 流程。

---

## 最终目标

这个 Skill 不追求：

> “所有代码必须由人亲手输入。”

也不追求：

> “把整个项目交给 Agent 自己跑。”

它追求的是：

> **重要代码我理解，关键设计我参与，低价值工作我可以交给 AI，而且任何时候我都能重新接管项目。**

如果几个月以后你回来维护这个 Feature，你应该仍然知道：

- 为什么这样设计；
- 关键生命周期是什么；
- 哪些地方最容易出错；
- AI 当时踩过哪些坑；
- 修改它时需要守住哪些 invariant。

这才是这个 Skill 对“AI 时代如何继续拥有自己的代码”的回答。
