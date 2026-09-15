> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-09) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-09"></a>

# Optional Rendering and Cloud Fallback Extensions Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; Tool Lab validation remains mandatory for optional providers.

**Goal:** Add optional Blender rendering and Autodesk APS/Revit Automation fallback **without** making either a hidden dependency of the local production pipeline.

**Architecture:** Blender consumes a verified release/export; it never edits the authoritative Revit GOLDEN. APS is registered only for a concrete blocked local capability, uses separate credentials, and stays below verified local providers in routing priority.

**Tech Stack:** Blender MCP/uvx, Blender, Autodesk APS Automation API samples, Codex MCP, existing local pipeline.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Rendering consumes a verified export/release. APS need/audit/synthetic testing may follow 07A when a concrete local blocker prevents reaching GOLDEN; use the explicit exception in the master dependency contract.
- Cloud remains fallback-only.
- Optional provider failure cannot invalidate a valid local GOLDEN.
- No credentials in Git/logs.
- Every optional MCP gets a Tool Lab and capability entry.

---

### Task 1: Determine immediate rendering need [P09-T01]

- [ ] Read current Amanda deliverable requirements.
- [ ] If no render is required, set Blender scheduling decision `DEFERRED_OPTIONAL` and leave untested capability `UNTESTED` and do not install just for novelty.
- [ ] If renders are required, proceed.

---

### Task 2: Install/verify `uv` for Blender MCP [P09-T02]

Current upstream Blender MCP documentation uses `uvx`.

- [ ] Check:

```powershell
uv --version
uvx --version
```

- [ ] If absent, use current official Astral Windows installer documented by Blender MCP:

```powershell
# Download the official installer to a local file, inspect it and record its hash.
# Run the inspected file under the audited install scope; record version and rollback.
```

- [ ] Start a fresh shell and verify versions.
- [ ] Record versions in environment lock.

---

### Task 3: Register Blender MCP [P09-T03]

- [ ] Register:

```powershell
# Resolve UvxExe to the verified absolute executable path.
# Resolve BlenderPackage to blender-mcp==<the exact evaluated version> from the lock.
codex mcp add blender -- $UvxExe --from $BlenderPackage blender-mcp
codex mcp list
```

- [ ] Install addon:

```powershell
& $UvxExe --from $BlenderPackage blender-mcp install-addon
```

- [ ] Open Blender, enable installed MCP addon according to current upstream instructions.
- [ ] Do not load Amanda model yet.

---

### Task 4: Blender Tool Lab [P09-T04]

**Files:** `state/providers/blender-toolmap.yaml`, `tool-lab/blender/`.

- [ ] Inspect `/mcp` and record actual current tool names.
- [ ] Test read-only scene query on empty scene.
- [ ] Test creating exactly one cube in disposable `.blend`.
- [ ] Re-query object existence/properties.
- [ ] Save/close/reopen `.blend` and re-query.
- [ ] Test import/export format actually intended for Revit handoff.
- [ ] Read current upstream open issues for Codex schema/compatibility before promoting.
- [ ] Record PASS/DEGRADED/FAIL.

---

### Task 5: Rendering pipeline from verified BIM release [P09-T05]

- [ ] Choose export format based on validated Revit→Blender fidelity test (for example FBX/IFC/GLB if actually supported in the verified chain).
- [ ] Export from a **copy** of the validated release.
- [ ] Import to new Blender project whose metadata records source GOLDEN SHA256.
- [ ] Create controlled material translation map.
- [ ] Add lighting/environment.
- [ ] Add vegetation only from controlled assets/placeholders.
- [ ] Create named cameras.
- [ ] Render low-resolution previews first.
- [ ] Review previews.
- [ ] Render final resolution only after preview PASS.
- [ ] Keep renders under `deliverables/renders/<golden-release-id>/`.

---

### Task 6: APS need gate [P09-T06]

- [ ] Confirm a **specific required** local capability is `BLOCKED_BY_TOOL` after verified typed/custom/interchange fallbacks.
- [ ] If no concrete blocked capability exists, set APS scheduling decision `DEFERRED_OPTIONAL` (capability remains UNTESTED) and stop APS work.
- [ ] If one exists, write `tool-lab/aps/need-report.md` explaining exact capability and why local alternatives failed.

---

### Task 7: Audit official APS sample repos [P09-T07]

Current reference repos:
- `autodesk-platform-services/aps-sample-mcp-server-revit-automation`
- `autodesk-platform-services/aps-sample-revit-mcp-tools-bundle`

- [ ] Clone in experiment worktree only.
- [ ] Pin commits.
- [ ] Read README/source/config files.
- [ ] Record that the AppBundle sample currently describes itself as sample/proof-of-concept; do not treat it as hardened production middleware automatically.
- [ ] Audit credential locations, network/data flow, activity/AppBundle configuration, rollback; verify the available APS engine version can read the target RVT before any cloud test.
- [ ] Run tool trust score.

---

### Task 8: APS secret boundary [P09-T08]

If APS remains justified:

- [ ] Create `.env.example` with **names only**, e.g. APS client ID variables.
- [ ] Store actual credentials in Windows Credential Manager or another approved local secret mechanism.
- [ ] Test redaction against APS logs.
- [ ] User handles Autodesk login/app authorization/MFA when prompted.
- [ ] Record user authorization for intended model/data upload, destination and cost limit unless already granted in this session. Use synthetic data for sandbox tests; never upload unrelated source files.

---

### Task 9: APS sandbox deployment/test [P09-T09]

- [ ] Build current official sample projects locally.
- [ ] Deploy only to a dedicated test APS app/project/activity.
- [ ] Use synthetic/disposable Revit cloud model/input.
- [ ] Run a harmless query or tiny model mutation.
- [ ] Verify output file/state independently.
- [ ] Record latency/cost/data-residency implications.
- [ ] Register APS capability only for the exact tested semantic operation.

---

### Task 10: Preserve local-first routing [P09-T10]

- [ ] `state/capabilities.yaml` keeps verified local providers at higher priority.
- [ ] APS entry has lower priority than every verified local path for same capability.
- [ ] Disable optional APS MCP when not actively needed if practical.
- [ ] Re-run doctor and regression after registration.
- [ ] Commit only nonsecret manifests/audits.

---

## Phase 09 Verification Gate

### GO
Optional capability works and remains isolated/nonmandatory.

### GO_WITH_LIMITATIONS
Optional provider unavailable; local GOLDEN pipeline unaffected.

### NO_GO
Optional integration becomes an unverified mandatory dependency, leaks secrets, or changes routing ahead of verified local providers.
