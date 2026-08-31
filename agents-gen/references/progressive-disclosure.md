# Progressive-disclosure policy

Read this policy when organizing overloaded instructions or creating, maintaining, or auditing `.agent-guides`.

## Separate scope from activation

Decide every rule on two axes:

| Coverage | Needed for nearly every task | Needed only for named work |
| --- | --- | --- |
| Whole project | Root `AGENTS.md` | Root `.agent-guides` |
| Independent subproject | Nested `AGENTS.md` | Sibling `.agent-guides` |

Choose coverage first. Ask whether the rule still applies when work leaves the candidate subtree. Then choose activation: whether nearly every task inside that scope needs the rule immediately. Put mixed-domain guidance at the nearest established instruction scope covering all affected work and give it a capability-based trigger.

Do not create an ordinary nested `AGENTS.md` only to host conditional guidance. Do not use a temporary implementation path as a trigger.

## Keep discovery stable and dynamic

When the project has any guide, keep one discovery protocol in the root `AGENTS.md`. It must tell future agents to:

1. determine the root and nested `AGENTS.md` scopes applicable to the files they expect to change;
2. inspect the current guide entries beside those scopes;
3. read entry descriptions before loading bodies;
4. load only entries relevant to the task; and
5. after selecting a guide package, follow only the references whose stated conditions apply.

The root must not enumerate guide entry paths. Discovery uses the current filesystem, so adding, renaming, merging, or converting an entry does not require a root index update.

## Use one of two entry shapes

Use a single Markdown file for a cohesive topic:

```text
.agent-guides/
`-- security.md
```

Use a guide package only when the topic has multiple substantial conditional branches:

```text
.agent-guides/
`-- testing/
    |-- GUIDE.md
    `-- references/
        |-- unit-tests.md
        `-- integration-tests.md
```

The direct `*.md` file or one-level `*/GUIDE.md` is the discoverable entry. Every entry starts with exactly one short, single-line description:

```markdown
---
description: Use when creating or modifying database migrations.
---
```

Write the description as a trigger, not a title or summary. Prefer stable work and capability language over current source paths. If descriptions overlap enough that an agent would routinely load both by accident, merge the topics or clarify their boundary.

Keep `GUIDE.md` limited to shared topic guidance and conditional routing. Supporting files live directly under `references/`; do not create another guide or reference-routing layer below them. Link references relatively and only where a real branch needs them. Do not build an exhaustive topic index.

## Organize without losing policy

For an explicit organization request:

1. inventory every existing instruction and linked authoritative document;
2. surface genuine contradictions before writing;
3. build rule cards with both coverage and activation;
4. retain the rules needed by nearly every task in each `AGENTS.md`;
5. group the remaining supported rules by stable task trigger;
6. reuse authoritative documents and avoid copying their policy;
7. create the smallest guide entries needed and remove only exact duplicates from their old location; and
8. account for every original rule as retained, moved, automated, questioned, or safely removed.

An explicit request permits meaning-preserving movement. Ask before changing policy meaning, choosing between contradictions, deleting non-duplicate policy, or taking ownership of an existing `.agent-guides` directory whose purpose is unclear.

## Verify the guide system

After writing, confirm:

- the root discovery protocol exists whenever any guide exists;
- each guide directory is paired with a usable `AGENTS.md` scope;
- every entry is readable and has one valid description;
- a topic does not exist in both single-file and package form;
- package references are one level deep and are not discoverable entries;
- all relative and authoritative-document links resolve;
- root and nested files contain no guide path index; and
- the same evidence produces no further instruction change.
