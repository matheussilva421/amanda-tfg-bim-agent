# P6-T01 — RUN-003 R04 visual/geometric acceptance

**Date:** 2026-09-26
**Status:** `PENDING` — `CANON-011` remains open
**Scope:** Compare saved R04 against the four canonical boards. No mass geometry was changed. No R05, GeoNatal research, or RC01 changes occurred.

## Live model and persistence

Horizun 1.3.3 was `HEALTHY` on Revit 2027 build 27.2.0.39. The registry was clean (73/73), 80/80 tools were visible, and no other Horizun clients were active. After reopening the exact RUN-003 target, it was active and targetable. Final health confirmed it as the sole open document. The exclusive writer lease was released after readback.

Target: `revit/production/working/AMANDA-RUN-003-PAVILION-CANONICAL-STUDY.rvt`, 4,612,096 bytes, SHA-256 `7097faf9b92a812e6488bed39b0dc573d37fe23790671179cd28cba607761095`. The immutable copy at `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-IMMUTABLE-SNAPSHOT.rvt` and its manifest have the same SHA-256; `CheckpointManager.verify_checkpoint` passed. Revit closed and reopened the exact target without upgrade.

The repository's `.gitignore:44` excludes `*.rvt`; the working model and snapshot binaries stay local. Their manifests, hashes, reports, and PNG captures are committed as evidence.

Fresh typed post-reopen queries returned all seven `OST_Mass` objects (complete coverage, zero unreadable) and all six evidence views. The views use template ID 105778, which displays masses. Coordinates remain a local normalized, unsurveyed study.

## Visual evidence

The six accepted images are real Revit wireframe massing captures copied to `revit/production/evidence/AMANDA-RUN-003-R04/views/`:

| View | Revit ID | Image | SHA-256 |
|---|---:|---|---|
| Top/site massing | 328666 | `site-top.png` | `76b89c6faab22e8e031cc7ab28edee8d75df2fb8b85e896de50bc6c20c18918e` |
| Overall isometric | 328677 | `overall-isometric.png` | `d6dd393517f21ff2bbca2f3510cca5fb107753ee9193d6c60a1d8de606c80c79` |
| Administrative | 328688 | `administration.png` | `796d7656e9ff5b301cd7bc579a2271a10bb71d3173cc6a1f7e31cd4a620b7a42` |
| Residential | 328699 | `residential.png` | `65231eec15fca5f3e3867042099fe7f7ee623ae996cec90ada69f5d94f8c920e` |
| Services/capacitation | 328710 | `services.png` | `a549bc418e3fa4238c7e7fea37752edb626a44c4c9de144b750a26427c1caeb6` |
| Child sector | 328721 | `child-sector.png` | `1b974e92e8d1fa618415a7c6ecf7d38b49bd01bcac0cbd58d0e4fca5566eb65a` |

The first experimental capture is excluded; a temporary orientation attempt produced a blank view. The six listed captures succeeded and their hashes were checked.

## Comparison against the canonical references

The four current board hashes are `30d009357a095e7794e0e915dcd2fdb04cd6b9aab9f4d13f5663ed54d6f20240` (01), `123b95633ae1be643da84f2226c6337d65a74f7d1337d6b27d94bdead1c3a263` (02), `5b96c2d5cc770742ee32d51b83b25993fe8b8a1638bf94da56ba8ef771031381` (03), and `c56b806f805d9c4aa1e6015ba6b56ac960204066721f93ef08cbadfb312c0386` (04). The official program PDF hash is `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`; it remains authoritative for 20 people, 626 m² internal useful area, and 260 m² programmed external area.

| Relationship | Result | Evidence and limit |
|---|---|---|
| Broad implantation zoning | `PASS_FOR_MASSING_ONLY` | Top view places administration at the lower/public edge, child mass west, services east/southeast, and four residential masses deeper/interior. Axes are local/normalized; this does not prove geographic north, frontage, road context, or parcel fit. |
| Central therapeutic garden, protected patio, eastern horta, organic/covered links | `PENDING` | Voids are visible between masses and inside the service composition, but no garden, horta, paths, or covered links are model elements. The two distinct 80 m² garden/patio spaces and 30 m² horta in the official program are not identified or measured in the model. |
| Separate public and service access | `PENDING` | No entrance or access-route elements are modeled; separation cannot be verified. |
| Board 02 administrative floor split | `PENDING` | One 6.40 m high mass exists, but no floors/rooms or floor-by-floor functional assignments are represented. Measured mass footprint is 237.407 m² (about 13.31 × 17.84 m); the board's approximate 10 × 20 m per-floor label implies 200 m², a +37.407 m² / +18.7% difference. This is a board-geometry discrepancy, not an official PDF area. |
| Board 03 residential composition | `PASS_FOR_COUNT_AND_SEPARATION` | The residential view shows four independent pavilion masses A/B/C/D; D is identified as communal. Bedroom/bathroom counts, the exact free central garden, and covered/semi-open circulation are not modeled or verified. |
| Board 04 curved services/capacitation courtyard | `PASS_FOR_OVERALL_FORM` | The services view shows a curved C/U composition with six interior rings around an open space, not a generic rectangle. Printed functions, official room areas, public access, and load/service access are not represented as model elements. The 446.501 m² mass area is not an official programmed area. |
| Child rooms and green/playground relationship | `PENDING` | One west-side child mass is present (94.481 m²). It reads as one rectangular block and does not show the official brinquedoteca (24 m²), apoio pedagógico (18 m²), bathroom (6 m²), and deposit (4 m²) as distinct rooms; the green/playground relation is not modeled. If this is the building footprint, it is 42.481 m² above the 52 m² room sum; if it represents the broader child zone, it does not prove 40 m² of open playground. The interpretation is unresolved. |

This evidence supports broad massing topology and the curved service form. It does not satisfy the unmodeled site, access, landscape, or internal functional relationships required for CANON-011. The official PDF remains authoritative for capacity and room areas; no official area was changed to fit a mass.

## Review, tests, and decision

Independent read-only review by **Bacon** confirmed that all six captures are usable for massing comparison and recommended keeping P6-T01 pending. It independently rated the broad zone order as pass for massing only, the four separate residential volumes as pass for count/separation, and the curved service composition as pass for overall form. It confirmed the pending items in the table: site/landscape/access, child program/playground, administrative floor functions and footprint discrepancy, and internal program/area verification. The reviewer also identified that P5's `NOT_ACCEPTED` capture status needed an explicit as-of-P5 note; that clarification is recorded in the P5 report and evidence JSON without changing the historical P5 outcome.

No software tests were run for this visual/evidence-only closeout; no code or mass geometry changed. Manual validation consisted of inspecting the six Revit captures, rehashing the images and canonical inputs, verifying the checkpoint hash/manifest, and querying the saved target after reopening.

**Decision:** keep `P6-T01` `PENDING` and `CANON-011` open. Do not advance to R05. Any next Revit mutation requires a scoped decision for missing landscape/access/internal functional elements and a source-backed resolution of the administrative footprint discrepancy. The five existing site-data limitations remain separate and unresolved.

Machine-readable evidence: `revit/production/evidence/AMANDA-RUN-003-R04/visual-geometric-evidence.json`.
