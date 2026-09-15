# Production AGENTS.md

This repository's production work follows these rules:

1. Preserve model integrity above completion.
2. Never modify GOLDEN/source/master.
3. Never use an UNTESTED provider on production.
4. Every BIM write gets independent read/verify.
5. Never invent missing source data.
6. Separate facts, constraints, and hypotheses.
7. Requirements are immutable during optimization.
8. No mid-production dependency updates.
9. Use typed, verified tools first.
10. Use only registry-approved fallbacks.
11. Create a checkpoint before destructive work.
12. Maintain formal task status.
13. Never claim success without evidence.
14. If uncertain, preserve the last known-good state.

## Session-start protocol

At session start, read this file, inspect `git status`, load the current project
state, identify the active child plan and exact next task, and review blockers,
environment locks, and the production writer lease. Use the canonical plans in
`docs/superpowers/plans/` and the root combined plan
`2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`. Record facts, constraints,
and hypotheses separately before making an execution decision. During BIM work,
verify the Revit build and provider health before any write.

## Session-end protocol

Before ending a session, finish or formally suspend the current task, record the
relevant test commands and results, update task status and project state, and
write an incremental handoff with changes, evidence, blockers, and exact resume
instructions. If BIM was mutated, include the checkpoint and independent
read/verify evidence. Leave the next task and its status explicit.

## Required Superpowers skills

Use these skills when their conditions apply:

- `superpowers:subagent-driven-development`
- `superpowers:systematic-debugging`
- `superpowers:verification-before-completion`
