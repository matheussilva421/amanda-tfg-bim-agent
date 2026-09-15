# START HERE — Codex Handoff

Give Codex the repository containing the approved spec and plan files, then use this instruction:

> Implement the Amanda TFG BIM Agent using the approved Superpowers design and implementation plans in this repository.
>
> Start by reading, in order:
> 1. `AGENTS.md` if it already exists;
> 2. `docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`;
> 3. `docs/superpowers/plans/00-master-implementation-plan.md`;
> 4. the child plan for the current phase.
>
> Use `superpowers:subagent-driven-development` for task-by-task implementation, with fresh subagents where appropriate and review gates between tasks. Use `superpowers:using-git-worktrees` before implementation if this is an existing repository and you are not already in an isolated worktree. Use TDD for code changes, systematic debugging for failures, and verification-before-completion before marking any task/phase PASS.
>
> You have maximum local autonomy: clone/audit/build repositories, install project-scoped prerequisites, register MCPs, safely edit Codex configuration, launch/close Revit, run tests, create disposable RVTs, and use verified fallbacks without asking. Stop only for UAC, Autodesk/login/MFA/licensing, truly missing source data, the architectural finalist selection gate, or an irreversible external action.
>
> Never use an untested Revit capability on Amanda production. Tool Lab comes first. Every BIM write is WRITE→READ→VERIFY. GOLDEN/source/master RVTs are immutable. When a provider fails, classify the failure and follow `state/capabilities.yaml`; do not silently improvise a new production provider.
>
> After every task: run the plan's stated tests, persist evidence, update `PROJECT_STATE.yaml`, and commit. Do not skip GO/NO-GO gates.
>
> Begin with Plan 01. Do not install Revit providers until Plan 01's environment gate is green.

## Recommended first request inside Codex

```text
Read the approved design plus Plan 00 and Plan 01. Establish an isolated worktree if required by Superpowers, then execute Plan 01 task-by-task using TDD. Do not begin Plan 02 until Plan 01's verification gate is green.
```

## Later resume request

```text
Read AGENTS.md and PROJECT_STATE.yaml, verify Git/environment state, load the child plan for the current phase, and continue the exact next READY task. Do not rely on prior chat context.
```

## If Codex reports a Revit/MCP problem

```text
Use the project's systematic-debugging workflow. Classify the failure, preserve the last known-good checkpoint, inspect provider/tool evidence, and follow the verified fallback chain in state/capabilities.yaml. If the required fallback is UNTESTED, return to Tool Lab before touching production.
```
