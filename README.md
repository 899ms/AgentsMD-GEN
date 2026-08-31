# AgentsMD-GEN

Create and maintain small, scoped, evidence-backed `AGENTS.md` files as a project evolves.

[中文](#中文) | [English](#english)

---

<a id="中文"></a>
## 中文

### 项目简介

AgentsMD-GEN 提供 `agents-gen` Agent Skill。它既能响应“帮我创建 AGENTS.md”这类直接请求，也会在项目文件发生变化后执行一次强制影响检查：需要时创建或更新最小根文件和独立子项目的嵌套文件，没有长期规则变化时明确报告无需更新。

它把 `AGENTS.md` 当作稀缺的常驻上下文，而不是项目百科或文件系统地图。每条规则必须有仓库证据、正确作用域和长期价值。

### 核心能力

- 缺少根文件时，从真实项目信息创建最小 `AGENTS.md`，不写入易过期的源码位置和目录地图。
- 每次从 workspace、manifest、CI、任务入口和维护文档重新发现独立 app、package、service、插件，并为它们建立局部 `AGENTS.md`。
- 把 TypeScript、测试、API、发布等详细规则留在聚焦文档中，`AGENTS.md` 只保留必要的自然语言入口。
- 识别重复、冲突、失效命令、断链、个人偏好和疑似易漂移的文件路径。
- 默认自动完成安全、证据明确的最小修改；所有权或政策含义不明确时停止并询问。
- 只读检查脚本以 JSON 汇总指令层级、动态子项目候选、命令来源、Git 变化、路径引用和文档链接状态。

### 生成逻辑

| 层级 | 保留内容 |
| --- | --- |
| 根 `AGENTS.md` | 一句话项目说明、非默认包管理器或共享工具、非标准构建/类型检查命令、少量稳定文档入口 |
| 独立子项目 `AGENTS.md` | 子项目用途、技术边界、局部命令和只适用于该作用域的指导入口 |
| 聚焦文档 | TypeScript、测试、API、发布等只在相关任务中才需要的详细规则 |

根文件不会逐项复制 package 路径。对于多子项目仓库，它只需说明“每个独立子项目的具体规则请查看各自的 `AGENTS.md`”。Agent 进入对应目录时会获得根级和局部指令；检查器则在每次运行时从当前仓库重新发现真实结构。

只有稳定的政策文档或正式命令入口才适合链接。类似“认证逻辑位于 `src/auth/handlers.ts`”的实现路径会被视为审计候选，因为文件移动后会污染 Agent 上下文。

### 快速开始

#### 环境要求

- Python 3.9+
- 支持 Agent Skills 的宿主
- 可选：如需统一分发，可使用已配置的 [SkillManager](https://github.com/Niall-Young/SkillManager)

#### 交给你的 Agent 安装（推荐）

把下面这段提示词复制给你正在使用、且支持 Agent Skills 的编程 Agent：

```text
帮我安装这个 Agent Skill：https://github.com/Niall-Young/AgentsMD-GEN
请安装仓库中的 agents-gen Skill，完整保留 SKILL.md、assets、references、scripts 和 tests，并在安装后运行 Skill 验证，告诉我实际安装路径和验证结果。
```

#### 通过 MySkills 安装（可选）

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

当已安装的 Agent 执行会修改项目文件的任务时，`agents-gen` 还会在交付前检查这些变化是否产生了新的长期指令。普通功能代码通常得到 `AGENTS.md: unchanged`；具有独立开发生命周期的新 app、package、service 或插件会获得最小嵌套 `AGENTS.md`，普通代码目录仍继承上级规则。

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

AgentsMD-GEN provides the `agents-gen` Agent Skill. It responds to direct requests such as “create an AGENTS.md for me” and runs a mandatory impact gate after project files change. The gate creates or updates a minimal root and scoped files for independent subprojects, and explicitly reports when no update is needed.

It treats `AGENTS.md` as scarce persistent context, not a project encyclopedia or filesystem map. Every retained rule needs repository evidence, the correct scope, and lasting value.

### Features

- Create a minimal root `AGENTS.md` from real project evidence without persisting volatile source locations or directory maps.
- Rediscover independent apps, packages, services, and plugins from current workspaces, manifests, CI, task entrypoints, and maintained docs, then give them scoped `AGENTS.md` files.
- Keep detailed TypeScript, testing, API, and release rules in focused documents, with only lightweight natural-language pointers in `AGENTS.md`.
- Detect duplication, conflicts, stale commands, broken links, personal preferences, and suspicious volatile file references.
- Apply safe, evidence-backed minimal edits automatically, while stopping for unclear ownership or policy meaning.
- Use a read-only JSON inventory to summarize instruction hierarchy, dynamic subproject candidates, command sources, Git changes, path references, and documentation link health.

### Generation Model

| Level | Retained content |
| --- | --- |
| Root `AGENTS.md` | One-sentence project purpose, non-default package manager or shared tooling, non-standard build/typecheck commands, and a few stable documentation entrypoints |
| Independent subproject `AGENTS.md` | Subproject purpose, technology boundary, local commands, and guidance pointers that apply only within that scope |
| Focused documents | Detailed TypeScript, testing, API, release, and other guidance loaded only for relevant work |

The root does not copy a package-by-package path map. In a multi-project repository, it only needs to say that each independent subproject keeps local guidance in its own `AGENTS.md`. The host combines root and local instructions when work enters that directory, while the inspector rediscovers the current repository structure on every run.

Only stable policy documents and official command entrypoints should be linked. An implementation claim such as “authentication lives in `src/auth/handlers.ts`” is treated as an audit candidate because a later file move would pollute Agent context.

### Quick Start

#### Prerequisites

- Python 3.9+
- A host that supports Agent Skills
- Optional: a configured [SkillManager](https://github.com/Niall-Young/SkillManager) for managed multi-Agent distribution

#### Ask Your Agent to Install It (Recommended)

Copy this prompt into the coding Agent you currently use, as long as it supports Agent Skills:

```text
Install this Agent Skill for me: https://github.com/Niall-Young/AgentsMD-GEN
Install the agents-gen Skill from the repository, preserving SKILL.md, assets, references, scripts, and tests. After installation, validate the Skill and tell me the actual installation path and validation result.
```

#### Install through MySkills (Optional)

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

When an installed Agent performs a task that changes project files, `agents-gen` also checks whether those changes introduce durable instructions before handoff. Ordinary feature code will usually produce `AGENTS.md: unchanged`; a new app, package, service, or plugin with an independent development lifecycle receives a minimal nested `AGENTS.md`, while ordinary code directories inherit their parent guidance.

### Development and Verification

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" agents-gen
python3 -m unittest discover -s agents-gen/tests -v
python3 agents-gen/scripts/inspect_agents_context.py "$(pwd)"
```

[中文](#中文) · [Back to top](#agentsmd-gen)
