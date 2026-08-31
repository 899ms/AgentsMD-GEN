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
| Independent app, package, service, or plugin purpose and local boundary | Its root `AGENTS.md` |
| Stable rule needed by nearly every task in one subtree | Nearest nested `AGENTS.md` |
| Language, testing, API, release, or Git detail used only for related work | Existing focused documentation, linked once when useful |
| Repeated multi-step operational workflow | A dedicated Skill |
| Personal preference | User-level instructions or personal Skill |
| Mechanically enforceable requirement | Configuration, lint, tests, CI, or hooks |
| One-off request, obvious default, unsupported claim, or vague aspiration | Do not persist |

Classify by scope, not topic. A test prohibition shared by the entire repository may belong at root; a package-specific test command does not.

## Recognize independent subprojects

Treat a subtree as an independent subproject when current repository evidence gives it its own development lifecycle. Strong evidence includes:

- membership in a declared workspace;
- a package or build manifest at the subtree root with its own name, dependencies, or commands;
- CI, task, or maintained documentation that builds, tests, deploys, or publishes it separately.

An independent subproject receives a minimal nested `AGENTS.md` by default. Its stable purpose and technology boundary are useful local context even when it has no extra prohibition or convention yet.

Do not equate directories with subprojects. Source groupings such as `src`, `tests`, `utils`, generated output, vendored code, examples, and fixtures inherit their nearest applicable instructions unless repository evidence establishes a maintained independent lifecycle. If the boundary or purpose cannot be established without guessing, ask before writing.

## Prefer stable capabilities over path maps

Do not inventory the repository or promise that implementation lives at a volatile file path. Describe the stable domain or capability, the repository's broad shape when useful, and tell the agent to locate the current implementation during planning. Nested `AGENTS.md` files are discovered from the current tree and scope; the root does not need a package-by-package path table.

Keep a path only when it is itself a durable interface, such as an official command entrypoint or focused policy file, and verify it exists. A link is not durable merely because it currently resolves. Prefer a short natural pointer such as “See each independent subproject's AGENTS.md for local guidance” over a copied directory map.

## Handle conflicts conservatively

- Exact duplicate: keep one authoritative occurrence and replace other copies with a pointer only when a pointer is useful.
- Clear stale fact: propose removal; write automatically only when removal cannot change policy meaning.
- Different scopes: keep both only when the narrower rule intentionally specializes the broader one.
- Genuine contradiction or unknown owner: stop and request a decision.
- Explicit user statement: accept it as policy intent after confirming it is project-level rather than personal or one-off; cross-check technical facts when possible.
