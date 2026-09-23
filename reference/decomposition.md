# Reverse Decomposition Rules

Shadow 实现已经完整以后，再做拆分。

## 目标

拆出的不是“文件修改批次”，而是“认知单元”。

好步骤：

```text
Step 1 Define RequestId value object
Step 2 Add pending-request index
Step 3 Route response lookup through the index
Step 4 Protect index with existing reactor-thread invariant
Step 5 Add timeout cleanup tests
```

差步骤：

```text
Step 1 Modify foo.h
Step 2 Modify foo.cpp
Step 3 Modify test.cpp
```

## 拆分算法

### 1. 提取最终 diff 中的语义变化

按以下类别归组：
- data model / invariant
- contract / interface
- algorithm
- integration
- lifecycle / ownership
- concurrency
- failure path
- persistence/protocol
- build/package
- tests

### 2. 建依赖图

对于每个语义变化确定：
- 它需要哪些类型/API 先存在；
- 哪些调用方依赖它；
- 哪些测试可独立验证。

### 3. 找教学顺序

优先：
- 从稳定概念到复杂集成；
- 从局部验证到系统验证；
- 从“为什么”清晰的步骤到复杂边界。

### 4. 控制大小

默认：
- 1 个主要概念；
- 1–3 个文件；
- ~150 effective diff lines；
- 一个明确验证点。

如果必须超过，记录 `size_exception_reason`。

### 5. 重建 Guide Branch

不要简单 cherry-pick Shadow 探索历史。

从 baseline 开始重新制作每个 step commit。

### 6. 验证 Guide 与 Solution 等价

至少比较：
- acceptance criteria；
- public behavior；
- tests；
- relevant generated artifacts；
- final build.

Guide final tree 不要求 byte-identical，但必须行为等价或明确解释差异。
