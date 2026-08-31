# Post-change maintenance policy

Read this reference after a task changes project files.

## Decide whether the change affects persistent instructions

Update `AGENTS.md` when the final change introduces or removes one of these durable facts:

- a project-wide or package-specific non-default command;
- a new package manager, workspace, runtime, build, test, typecheck, lint, or deployment entrypoint future tasks must use;
- a stable architectural boundary or ownership rule that changes where future work belongs;
- a new, moved, renamed, merged, or removed independent subproject;
- a renamed or removed document currently linked from applicable instructions;
- an existing instruction that became false, contradictory, or misleading.

Normally report unchanged for:

- ordinary feature code under existing conventions;
- an internal refactor with the same workflows and boundaries;
- tests that use already documented commands;
- new ordinary directories that inherit all applicable parent guidance;
- temporary migration steps, incident notes, or facts relevant only to the current task.

## Maintain independent subproject scopes

Create a minimal nested `AGENTS.md` when current evidence establishes an independent app, package, service, or plugin. Its purpose and technology boundary are enough to earn the scope. Add local commands, conventions, and focused-document pointers only when evidence supports them; do not repeat inherited root guidance.

When a subproject moves or is renamed, rediscover its current root from manifests, workspace configuration, CI, and maintained documentation. Do not preserve an obsolete path map. Update stable links whose new target is unambiguous; otherwise stop and ask rather than guessing.

For an ordinary subtree that is not an independent subproject, create the nearest nested file only when all are true:

1. The subtree has at least one distinct instruction.
2. The instruction is stable and repeatedly relevant inside that subtree.
3. Keeping it at root would distract tasks elsewhere.
4. The nested file does not repeat inherited content.

When an independent subproject ceases to exist, or an ordinary nested file loses its last distinct rule, remove the file only after confirming it contains no user policy or other owned content.

## Make automatic edits narrow

Routine automatic changes may:

- add or correct a verified command;
- add a pointer whose target already exists;
- create a minimal root or nested file when the evidence and ownership are unambiguous;
- remove a purely factual statement whose referenced target demonstrably no longer exists, when doing so cannot change policy meaning.

Ask before:

- deleting or semantically rewriting a user-authored policy;
- choosing between conflicting parent and nested instructions;
- promoting a personal preference to a project rule;
- creating a new team convention or changing the rule owner;
- modifying tool-specific files outside v1 scope.

## Report the gate

Use one result even when several instruction files were inspected:

- `created`: the project had no usable root file and now has a verified minimal one;
- `updated`: at least one applicable file changed and was read back;
- `unchanged`: the project change introduced no durable instruction impact;
- `blocked`: evidence, ownership, or conflict prevented a safe result.

Name every changed instruction file. For unchanged, state the evidence class checked. For blocked, ask only the decision that cannot be derived from the project.
