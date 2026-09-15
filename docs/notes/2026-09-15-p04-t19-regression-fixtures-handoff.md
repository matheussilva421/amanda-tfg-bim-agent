# Handoff — P04-T19 core regression fixtures

Data: 2026-09-15. State: work done, NO commit (commits are the orchestrator's). Scope: docs/superpowers/plans/04-design-engine.md task 19.

## O que foi feito

Created five core regression fixtures under tests/regression/fixtures/ plus the engine-executing test suite. Every fixture is pure data (input.json, seed.json, expected_invariants.json, expected_hash.json) and is executed against the real engine in src/amanda_agent/design through tests/regression/regression_support.py (no re-implementation, no stub).

| Fixture | Scenario | Engine areas (declared and evidenced) |
| --- | --- | --- |
| simple-3-room | seeded pipeline | generation, pipeline, macrozones, blocks, rooms, constraints |
| courtyard | archetype + external + heuristics | archetypes, external_spaces, environmental, scoring, pareto, explain |
| two-access | independent circulations | flows |
| privacy-gradient | privacy transitions | privacy |
| accessible-route | accessible rooms + width gate | blocks, rooms, constraints, flows |

The union of fixtures covers the full required set (macrozones, blocks, rooms, external spaces, scoring, pareto, environmental, generation, pipeline, explain); the test_regression_set_exercises_the_whole_core_engine test proves it, and each fixture records non-empty runtime evidence per declared area.

## Arquivos criados

- tests/regression/regression_support.py — shared harness (loads fixture data, runs real engine, returns observed + canonical payload)
- tests/regression/test_regression_fixtures.py — parametrized suite: artifact completeness, invariants comparison, same-seed determinism, canonical hash reproducibility (or documented), engine coverage, evidence presence, substantive invariants
- tests/regression/test_fixture_{simple_3_room,courtyard,two_access,privacy_gradient,accessible_route}.py — per-fixture semantic regression tests
- tests/regression/fixtures/<name>/{input,seed,expected_invariants,expected_hash}.json — 5 directories x 4 files

## Testes executados

- pytest tests/regression -q -p no:cacheprovider --basetemp="../../.tmp-jupiter-r1" — 47 passed, 0 failed
- RED demo (expected reason): temporarily removed accessible: true from simple-3-room/input.json — test_fixture_matches_its_expected_invariants[simple-3-room] failed on finalist_accessible_room_ids (expected 1, got 0) and the canonical hash test failed with a drifted digest; reverted, suite green again.
- Full suite: pytest tests -q -p no:cacheprovider --basetemp="../../.tmp-jupiter-r2" --ignore=tests/unit/test_destructive_threshold.py --ignore=tests/unit/test_stage_project.py --ignore=tests/unit/test_stage_site.py — 483 passed, 1 skipped, 0 failed
- ruff check tests/regression --line-length 120 — clean

## Determinismo e hash canonico

All five fixtures were evaluated twice; observed values and canonical hashes were identical in both runs. Stable hashes were recorded in expected_hash.json (status STABLE, sha256, engine version design-engine-v1) and are re-asserted by the suite. If an environment/dependency change ever shifts a hash, the test fails loudly instead of pretending stability.

## Bloqueadores / observacoes (fora do escopo do P04-T19)

- tests/unit/test_stage_project.py and tests/unit/test_stage_site.py are untracked files created by another agent (2026-09-15 11:26) importing amanda_agent.bim.stages, which does not exist yet. That is an in-flight RED state of another block; I did not touch or implement it. Run the full suite with the two --ignore flags above until that block lands its module.
- tests/unit/test_destructive_threshold.py ignored per block instruction.
- No commit made (per instruction). PROJECT_STATE.yaml and state/task-graph.yaml untouched.

## Proximo passo

- Orquestrador: commitar tests/regression/** (explicit paths, no git add -A).
- Proxima tarefa do plano: P04-T20 (TopologicPy spike, optional) ou P04-T22 (CLI design/compare).
