# Rule admission and placement policy

Use this policy whenever deciding whether persistent project guidance belongs in an `AGENTS.md` file.

## Build a rule card

For each candidate, identify:

- instruction: the exact behavior future agents need;
- evidence: repository fact or explicit durable project policy;
- owner: project, package, user, tool, or unknown;
- scope: every task, one subtree, one domain, one workflow, or one task;
- stability: whether it survives likely file and module movement;
- actionability: a concrete action, boundary, or check;
- enforcement: whether config, lint, tests, CI, or hooks should own it instead;
- destination: root, nested file, existing documentation, Skill, personal layer, automation, question, or removal.

## Admit a rule to the root only when it passes every test

1. Nearly every project task needs it.
2. It is non-default or cannot be reliably inferred at the moment of use.
3. It changes behavior through a concrete command, boundary, or routing pointer.
4. It has current evidence or is an explicit project-level policy owned by the user or team.
5. It remains useful after plausible directory restructuring.
6. It does not duplicate a more authoritative source.

Around 50 lines is a review signal, never a correctness threshold. A short file containing vague rules still fails; a larger file may be justified when every line is globally necessary.

## Place at the narrowest durable scope

| Candidate | Destination |
| --- | --- |
| Project purpose, non-default tooling, shared validation, global boundaries | Root `AGENTS.md` |
| Stable rule needed by nearly every task in one subtree | Nearest nested `AGENTS.md` |
| Language, testing, API, release, or Git detail used only for related work | Existing focused documentation, linked once when useful |
| Repeated multi-step operational workflow | A dedicated Skill |
| Personal preference | User-level instructions or personal Skill |
| Mechanically enforceable requirement | Configuration, lint, tests, CI, or hooks |
| One-off request, obvious default, unsupported claim, or vague aspiration | Do not persist |

Classify by scope, not topic. A test prohibition shared by the entire repository may belong at root; a package-specific test command does not.

## Prefer stable capabilities over path maps

Do not inventory the repository or promise that implementation lives at a volatile file path. Describe the stable domain or capability and tell the agent to locate the current implementation when needed. Keep a path only when it is itself a durable interface, such as an official command entrypoint or linked policy file, and verify it exists.

## Handle conflicts conservatively

- Exact duplicate: keep one authoritative occurrence and replace other copies with a pointer only when a pointer is useful.
- Clear stale fact: propose removal; write automatically only when removal cannot change policy meaning.
- Different scopes: keep both only when the narrower rule intentionally specializes the broader one.
- Genuine contradiction or unknown owner: stop and request a decision.
- Explicit user statement: accept it as policy intent after confirming it is project-level rather than personal or one-off; cross-check technical facts when possible.
