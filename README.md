# AgentsMD-GEN

Create and maintain small, scoped, evidence-backed `AGENTS.md` files as a project evolves.

[中文](#中文) | [English](#english)

---

<a id="中文"></a>
## 中文

### 项目简介

AgentsMD-GEN 提供 `agents-gen` Agent Skill。它既能响应“帮我创建 AGENTS.md”这类直接请求，也会在项目文件发生变化后执行一次强制影响检查：需要时创建或更新根级、模块级 `AGENTS.md`，没有长期规则变化时明确报告无需更新。

它把 `AGENTS.md` 当作稀缺的常驻上下文，而不是项目百科。每条规则必须有仓库证据、正确作用域和长期价值。

### 核心能力

- 缺少根文件时，从真实项目信息创建最小 `AGENTS.md`。
- 项目新增模块、命令或架构边界时，判断应更新根文件、拆出嵌套文件还是保持不变。
- 识别重复、冲突、失效命令、断链、个人偏好和易过期路径地图。
- 默认自动完成安全、证据明确的最小修改；所有权或政策含义不明确时停止并询问。
- 只读检查脚本以 JSON 汇总指令层级、项目清单、命令来源、Git 变化和链接状态。

### 快速开始

#### 环境要求

- Python 3.9+
- 支持 Agent Skills 的宿主
- 如需统一分发：已配置的 [SkillManager](https://github.com/Niall-Young/SkillManager)

#### 通过 MySkills 安装

```sh
skillmgr source add https://github.com/Niall-Young/AgentsMD-GEN.git --name agents-md-gen
skillmgr skill add agents-md-gen agents-gen --name agents-gen --agents codex,claude,qodercn,kimi
skillmgr plan
skillmgr sync --apply
skillmgr doctor
```

安装后重新打开 Agent 会话，让宿主重新发现 Skill。

### 使用方法

直接说：

```text
帮我创建 AGENTS.md
```

也可以显式调用：

```text
使用 $agents-gen，根据当前项目创建或整理 AGENTS.md。
```

当已安装的 Agent 执行会修改项目文件的任务时，`agents-gen` 还会在交付前检查这些变化是否产生了新的长期指令。普通功能代码通常得到 `AGENTS.md: unchanged`；新增模块只有具备独特、稳定的局部规则时才会获得嵌套 `AGENTS.md`。

### 开发与验证

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" agents-gen
python3 -m unittest discover -s agents-gen/tests -v
python3 agents-gen/scripts/inspect_agents_context.py "$(pwd)"
```

[English](#english) · [返回顶部](#agentsmd-gen)

---

<a id="english"></a>
## English

### Overview

AgentsMD-GEN provides the `agents-gen` Agent Skill. It responds to direct requests such as “create an AGENTS.md for me” and runs a mandatory impact gate after project files change. The gate creates or updates root and module-level `AGENTS.md` files when durable guidance changes, and explicitly reports when no update is needed.

It treats `AGENTS.md` as scarce persistent context, not a project encyclopedia. Every retained rule needs repository evidence, the correct scope, and lasting value.

### Features

- Create a minimal root `AGENTS.md` from real project evidence when one is missing.
- Decide whether new modules, commands, or architectural boundaries belong at root, in a nested file, or nowhere.
- Detect duplication, conflicts, stale commands, broken links, personal preferences, and brittle path maps.
- Apply safe, evidence-backed minimal edits automatically, while stopping for unclear ownership or policy meaning.
- Use a read-only JSON inventory to summarize instruction hierarchy, manifests, command sources, Git changes, and link health.

### Quick Start

#### Prerequisites

- Python 3.9+
- A host that supports Agent Skills
- For managed multi-Agent distribution: configured [SkillManager](https://github.com/Niall-Young/SkillManager)

#### Install through MySkills

```sh
skillmgr source add https://github.com/Niall-Young/AgentsMD-GEN.git --name agents-md-gen
skillmgr skill add agents-md-gen agents-gen --name agents-gen --agents codex,claude,qodercn,kimi
skillmgr plan
skillmgr sync --apply
skillmgr doctor
```

Start a new Agent session after installation so the host can discover the Skill again.

### Usage

Ask naturally:

```text
Create an AGENTS.md for this project.
```

Or invoke the Skill explicitly:

```text
Use $agents-gen to create or organize this project's AGENTS.md from current evidence.
```

When an installed Agent performs a task that changes project files, `agents-gen` also checks whether those changes introduce durable instructions before handoff. Ordinary feature code will usually produce `AGENTS.md: unchanged`; a new module receives a nested `AGENTS.md` only when it has distinct, stable local guidance.

### Development and Verification

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" agents-gen
python3 -m unittest discover -s agents-gen/tests -v
python3 agents-gen/scripts/inspect_agents_context.py "$(pwd)"
```

[中文](#中文) · [Back to top](#agentsmd-gen)
