# Project

This repository contains `agents-gen`, an Agent Skill that creates and maintains scoped project `AGENTS.md` files from repository evidence.

## Verification

- Validate the Skill: `python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" agents-gen`
- Run tests: `python3 -m unittest discover -s agents-gen/tests -v`

## Project Rules

- Keep `agents-gen/SKILL.md` focused on routing and the shared workflow; put conditional decision detail in `agents-gen/references/`.
- Keep the inspection script read-only and dependency-free.
