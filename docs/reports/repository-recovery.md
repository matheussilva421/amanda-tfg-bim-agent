# Repository Recovery Report — 2026-09-24

## Safety anchor

- Annotated tag: `pre-repository-recovery-2026-09-24`
- Tag object: `2567d03cc8ff2860e80bda1ec9981195ddddee6c`
- Tagged commit: `30cc3b0f7860dfb5e46299402585213d1ac2d02b`
- main at capture: `7daf6f67a9980705d96bf25e0b648305feeef39b`
- codex/canonical-pavilion-migration at capture: `30cc3b0f7860dfb5e46299402585213d1ac2d02b`
- codex/p08-t08-concept-offline at capture: `125c7d956d40fab6c358e4c6702199b4eac4d854`
- Execution-start HEAD: `7daf6f67a9980705d96bf25e0b648305feeef39b` on `main`
- Remote: `https://github.com/matheussilva421/amanda-tfg-bim-agent.git`
- Tag was pushed and verified on `origin` before destructive file, branch, or worktree cleanup.

## Pre-recovery capture

- Captured UTC: `2026-09-24T14:56:20.511Z`
- git fetch --all --prune: completed; fetched branch SHAs matched live git ls-remote at capture.
- Primary worktrees: `1`
- Dirty status entries: `238` (8 tracked modifications, 230 untracked paths; no RC01 deletions in the elevated filesystem view).
- Full pre-recovery status/path/RVT snapshot: temporarily stored in `.recovery/pre-recovery-inventory.json`; remove only after this report carries the classified evidence.
- Session-start state facts: PROJECT_STATE.yaml named `P08-CAN-T09` as its next task, stage R04, and marked the writer lease stale/reclaimable. This recovery does not run Revit, reclaim a lease, or advance production.
- RC01 ACL check: regular sandbox Git listing falsely reported 34 deleted evidence files; elevated read confirmed the RC01 directory and its files still exist. No RC01 file was restored, edited, or staged as a deletion.

## Pre-recovery branches

| Ref | SHA | Initial classification |
|---|---|---|
| `codex/canonical-pavilion-migration` | `30cc3b0f7860dfb5e46299402585213d1ac2d02b` | UNCLASSIFIED |
| `codex/p08-t08-concept-offline` | `125c7d956d40fab6c358e4c6702199b4eac4d854` | UNCLASSIFIED |
| `main` | `7daf6f67a9980705d96bf25e0b648305feeef39b` | UNCLASSIFIED |
| `origin` | `7daf6f67a9980705d96bf25e0b648305feeef39b` | UNCLASSIFIED |
| `origin/codex/canonical-pavilion-migration` | `30cc3b0f7860dfb5e46299402585213d1ac2d02b` | UNCLASSIFIED |
| `origin/codex/p08-t08-concept-offline` | `125c7d956d40fab6c358e4c6702199b4eac4d854` | UNCLASSIFIED |
| `origin/main` | `7daf6f67a9980705d96bf25e0b648305feeef39b` | UNCLASSIFIED |

Remote heads observed live at capture:

- `origin/codex/canonical-pavilion-migration` -> `30cc3b0f7860dfb5e46299402585213d1ac2d02b`
- `origin/codex/p08-t08-concept-offline` -> `125c7d956d40fab6c358e4c6702199b4eac4d854`
- `origin/main` -> `7daf6f67a9980705d96bf25e0b648305feeef39b`

## Pre-recovery worktrees

| Path | Branch | HEAD | State | Classification |
|---|---|---|---|---|
| `C:/Users/slvma/Downloads/Github/Projeto Amanda` | `main` | `7daf6f67a9980705d96bf25e0b648305feeef39b` | dirty=True (238 entries) | DIRTY_REVIEW |

## Tracked working-tree changes at capture

- ` M PROJECT_STATE.yaml`
- ` M project/requirements/decision-register.yaml`
- ` M revit/production/journals/R03.json`
- ` M state/status.md`
- ` M state/task-graph.yaml`
- ` M state/task-history.yaml`
- ` M tool-lab/topologic/results/space.topology.json`
- ` M tool-lab/topologic/results/topologic-spike.json`

These 8 modifications remain unclassified until each file is reconciled with the post-fast-forward canonical state. No unrelated state/journal/tool-lab change has been committed by this recovery yet.

## Unique commits — canonical migration over main



Ancestry check: main is an ancestor of the canonical migration branch (git merge-base --is-ancestor exit 0); 26 canonical commits are ahead.

Exact unique commit list (26 commits; full hashes and subjects):
- `9fe08bc3365d592b5159d39d6ee6a88f79b20d31` — feat: establish canonical pavilion reference and archive R12
- `f466418561c101bf27bcf7e1fdd328018a683b32` — docs: record canonical migration checkpoint
- `3276976d1f47c9486d4de8f36086600042d57386` — refactor: define production layout protocol
- `5059cab11d897636e793eb1f59617768b4e8790b` — docs: record Task 2 layout protocol
- `4c24bacd93e60e5e1150eb70d6560d04d7050d46` — feat: build canonical pavilion layout
- `379e2eee043fa1432a95c3be7b68fee54b514f67` — docs: record canonical pavilion checkpoint
- `0cbf0fc8987831feeba492421da0f93549e4deb5` — test: enforce canonical pavilion parti
- `49d88912964d55a2f546d72e1cc6aab5c1080d79` — docs: record canonical QA checkpoint
- `ccfd410fe65ee074c0cdc76bff89e875a51bb443` — feat: bind production selection to canonical pavilion boards
- `ac9d79872be02aaf66d811273d9ae74696df2805` — docs: record canonical selection checkpoint
- `089bba5e234ddaaaa06c475bc4ab8362ec58e5a5` — refactor: route production consumers to canonical pavilion layout
- `3569483484415ec33ab8cbdf045c05953a4defe4` — docs: record canonical consumer migration checkpoint
- `98dba4718e85ad677de8745611de771db0f80c18` — feat: plan multi-block canonical BIM stages
- `cea23fa05b5496b363f2e85e81b66118ba59cf08` — docs: record canonical BIM planning checkpoint
- `06c524c512300ee8442b0909c512e7329f5ce724` — fix: prevent canonical rebuild from reusing legacy linear RVT
- `f73b7597ead9dfa28038f3f33dcd896bd4f1c18b` — docs: record canonical S02 handoff
- `59684b62683dc24389b725bae97d654d062abca1` — feat: build offline canonical pavilion run
- `e822b70c9d3d437dba0845ede6e27c0da19276d5` — docs: record canonical run artifact checkpoint
- `5eb767d9a6c96705c780bdab90b564e0a18b747b` — test: verify canonical pavilion migration
- `cd2267b583e6df30cd260a65a140913a7bfcf4a2` — docs: record canonical migration verification
- `af9c44e146cbb43caced4334f92da4f8a10bff07` — docs: switch production state to canonical pavilion run
- `a67c8ed517c5585885e5873da4a3eea0e51d7612` — feat: gate canonical R04 with BIM-00
- `b930e9ec5309157342e4cd1cd6ea5224900ab021` — docs: record canonical R04 access review checkpoint
- `82b257d061ff8668d5ba06d3be9640940e1a794f` — docs: record typed R04 mass route refusal
- `7111d6bf4e2c7159f34cdd5ad81a2b4bdffaa843` — docs: record canonical source and provider recheck
- `30cc3b0f7860dfb5e46299402585213d1ac2d02b` — feat: bind pavilion migration to fourth canonical board

## Unique commits — concept-offline over main at capture

Patch-equivalence comparison (git log --left-right --cherry-pick --oneline main...codex/p08-t08-concept-offline) records:

- `< 7daf6f6 docs: align status dashboard with published head`
- `< 044e2f1 docs: align project state with published head`
- `< e322d5d docs: reconcile git verification after r12 handoff`
- `< 0d4374f docs: handoff r12 materials delivery state`
- `< fd6754e docs: reconcile delivery state after r11 push`
- `< 5eceecc feat: persist canonical r11 landscape delivery evidence`
- `< 4a53154 docs: reconcile delivery state after r10 push`
- `< 5f5be46 feat: persist canonical r10 furniture evidence`
- `< 69e3c61 docs: reconcile delivery state after r09 push`
- `< 881bf01 feat: persist canonical r09 accessibility evidence`
- `< 33c3005 docs: reconcile delivery state after r08 push`
- `< 4eae893 feat: persist canonical r08 rooms delivery evidence`
- `< 39f498b docs: reconcile delivery state after push`
- `< f0d6b18 feat: persist canonical r07 openings delivery evidence`
- `< 8eaf925 docs: clarify preserved dirty files`
- `< 25c4b18 docs: refresh live status dashboard`
- `< 17b189c docs: align final delivery state`
- `< 2a51cdb docs: record R06 delivery commit`
- `< 880b0df feat: verify live R06 internal layout`
- `< e6f0e4e docs: record current session handoff`
- `> 125c7d9 docs: finalize P08-T08 offline handoff`
- `> e5c9a0e feat(bim): prepare offline conceptual candidates`

Commit list exclusive to the concept branch:

Exact unique commit list (2 commits; full hashes and subjects):
- `e5c9a0e8342423e9dbcdf4e4b56c94858970879f` — feat(bim): prepare offline conceptual candidates
- `125c7d956d40fab6c358e4c6702199b4eac4d854` — docs: finalize P08-T08 offline handoff



These two commits remain under review; neither branch nor commit is classified for deletion yet.

## Initial non-versioned evidence and source candidates

- Complete path inventory at capture: 230 non-versioned paths, listed in the appendix below.
- Groups include the current 4-board package, older generated plan packages/ZIPs, source/evidence candidates, local Codex config, Revit checkpoint manifests, BIM-00/canonical-acceptance evidence, R04 previews, and release preview pages.
- Preserve as current source candidates pending Task 7 hash verification: program PDF SHA-256 `11DAA9EFC4D1B022407D8BD02999E85B604A16539F29AE598DC45B339DE14A17`; TFG PDF SHA-256 `16ABE602AC50643482CE3C782780B4135FA8468B5CA814061FE426C8CA292A7E`; four board candidates SHA-256 `30D009357A095E7794E0E915DCD2FDB04CD6B9AAB9F4D13F5663ED54D6F20240`, `123B95633AE1BE643DA84F2226C6337D65A74F7D1337D6B27D94BDEAD1C3A263`, `5B96C2D5CC770742EE32D51B83B25993FE8B8A1638BF94DA56BA8EF771031381`, `C56B806F805D9C4AA1E6015BA6B56AC960204066721F93EF08CBADFB312C0386`.
- Current package also includes an overview sheet, prior 3-board images, reference/evidence images, manifests, and several historical docs; these are not promoted into the canonical source set without classification.
- Untracked production evidence to preserve until Task 9: 20 checkpoint RVTs/manifests, 3 R04/BIM-00 evidence JSONs, 8 production previews, one superseded-linear archive manifest, and 7 release preview pages.
- .codex/config.toml remains UNKNOWN until its content and purpose are inspected.
- Generated ZIPs and extracted plan packages are HISTORICAL_REPRODUCIBLE only after all authoritative sources and unique evidence are verified in their canonical locations.

## Important RVT inventory at capture

The list below records every non-temporary RVT discovered across the primary worktree (112 files; 368 additional ignored test/runtime RVTs were separately identified by the inventory counters).

| Relative path | Bytes | SHA-256 | Initial classification |
|---|---:|---|---|
| `revit/lab/baseline/LAB_R00_EMPTY.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/custom-api/LAB_CUSTOM_WALL.0004.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/custom-api/LAB_CUSTOM_WALL.rvt` | 4370432 | `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2` | initial classification: UNCLASSIFIED |
| `revit/lab/custom-api/T18_CRASH_WORK.rvt` | 4370432 | `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2` | initial classification: UNCLASSIFIED |
| `revit/lab/custom-api/T18_LAST_PASS.rvt` | 4370432 | `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2` | initial classification: UNCLASSIFIED |
| `revit/lab/exports/p06t14/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | initial classification: UNCLASSIFIED |
| `revit/lab/exports/p06t14/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_DOC.0002.rvt` | 4427776 | `6A1544D3075F86219CEC609010C2446608916F2BE7B917386836E93B051D829C` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_DOC.CROSSWALK-20260922.rvt` | 4435968 | `28CFC5434482F7E62239E7048F62FBE248F3FA7721F51BCD51648139D45EE02E` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_DOC.rvt` | 4435968 | `28CFC5434482F7E62239E7048F62FBE248F3FA7721F51BCD51648139D45EE02E` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_FLOOR.0002.rvt` | 4366336 | `962A1E6B5CBB1B7716EB9BF2F3A9D87F36E2E1507A5A1015216BE42ECAFD5B68` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_FLOOR.rvt` | 4370432 | `B7EF11F9DD866594AAEFCAB376846373071173BE5D73798EABA9056A084FE28B` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_LEVEL.0001.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_LEVEL.rvt` | 4370432 | `8B15D7360672D4CDAFDF5742F031F6B11A17DBD4D9EBA6D4FCDE725586FB3025` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_READ.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_ROOM.0002.rvt` | 4374528 | `329ED4148B40C8B104EDF35392489435350D5C3D9D26E7FBF1AA1403E72B4CEB` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_ROOM.rvt` | 4378624 | `9BF42C556BD6A57E52AA3F1184C6F5500B776949FD0DA34F9CD71AA1915B20C3` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.0001.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.0002.rvt` | 4370432 | `D1011D1BDCE5F2777B790CC55B01699BC39EB048C80064715FFC11BF9B1981E6` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_TOPO.rvt` | 4370432 | `5A66BFA4C79036232503ADA4842B60C53F45AD4B3AA23B0141013E843B2021A6` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_WALL.0001.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/LAB_HORIZUN_WALL.rvt` | 4370432 | `6FD0AB2DC2512847215A87E6AF2D0294943958AF9C5FE561CC3805F0BA558EB5` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/checkpoints/AMANDA-R04-MASS-CAPABILITY-20260923-before.rvt` | 3780608 | `1E1AAB8362B733A0BFF2ED62C193F2C8F9DCE63193D0F4A6FB5519D604231AF6` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/fixtures/AMANDA-R04-MASS-CAPABILITY-20260923.0001.rvt` | 3780608 | `1E1AAB8362B733A0BFF2ED62C193F2C8F9DCE63193D0F4A6FB5519D604231AF6` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/fixtures/AMANDA-R04-MASS-CAPABILITY-20260923.0002.rvt` | 3784704 | `B14513D7DE52BDC2436920BB830702BFEEB7551CDC16C6462F28B6598CA50D5B` | initial classification: UNCLASSIFIED |
| `revit/lab/horizun/fixtures/AMANDA-R04-MASS-CAPABILITY-20260923.rvt` | 3788800 | `83F972C4F4772945AFD75B0245C251BF126182B7668ED8CA7C4A17CE71BD6345` | initial classification: UNCLASSIFIED |
| `revit/lab/probe/LAB_ROUTE_PROBE.0001.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/probe/LAB_ROUTE_PROBE.rvt` | 4505600 | `8B9E766CB073499ABA5F32DA70352FB28B06D59F561C9B5B11C18D97E33FD6C5` | initial classification: UNCLASSIFIED |
| `revit/lab/release/LAB_RELEASE.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/revitcortex/LAB_RC_DOC.0001.rvt` | 4366336 | `15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` | initial classification: UNCLASSIFIED |
| `revit/lab/revitcortex/LAB_RC_DOC.rvt` | 4415488 | `8820C791781F7F411AAD5D3C8D044257A9130933FAB86E0D19FE18383D2059BA` | initial classification: UNCLASSIFIED |
| `revit/production/archive/superseded-linear/AMANDA-RUN-001-S01-R12-linear-historical-20260922.rvt` | 4345856 | `AC814642296CBC7074603B703F8DB20A63AE1C1475F435756A248516D1856E29` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R01-template.rvt` | 3780608 | `F5D4B0F52ECA096A29CA3F34BB50D9A83D76F1461EE1D35BC3EB4563318678F7` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R03-levels-and-grids-20260923.rvt` | 4046848 | `6199FEDF2468D621960C0A756EDF02D756DA55C05B03A11F6344A3D2C33A65B6` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R03-prewrite-20260923-2219.rvt` | 4046848 | `2702C626565ED426A8E3B9CC179EBF2008BA36284DDA60376DAE6E5BB9FF438E` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R04-canonical-covered-circulation-20260923.rvt` | 4046848 | `C5F866B135240CA1A202D68D1028952DB3FDEF5734F15CFA897FD8676B63156A` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R04-canonical-preview-20260923.rvt` | 3903488 | `554F27DDBF7BEE22105F5D564371F3FFC7633009D2D05DD91243B2C20A1A03FF` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R04-canonical-spatial-acceptance-20260923.rvt` | 3981312 | `49C8AA6E767CE6704C0285771651C8E3B300400D55A52C55163A7CEB11B77EED` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R04-massing-20260923.rvt` | 3899392 | `DD9C8AFE5808D4AD84EA7BEF381D3B6FB67FFEBF241A599A9E1CFAFE9F05058B` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/P08-T10-canonical-pre-promotion-20260922.rvt` | 3784704 | `4753F638F2B536B6CF0F3B1A5FB30F4B997601AE463A7E826111CA02CD57BF83` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/P08-T10-production-canonical-20260922.rvt` | 3977216 | `2135AC273634994C89FF7535C2DAFBAFA6236062068094E9A48CFB2189F966BC` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R05-live-persisted-20260922.rvt` | 4112384 | `10DF1CB1BE4A147218A822330A9EFAC5E540513FDEE3D95D1173BBAB7447228F` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R05-pre-save.rvt` | 4022272 | `F83D74D0548048EDA70FC8BF61E20D8155EEB15EBA6048C7C7A052353C9936CA` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-gallery-host-correction-20260922.rvt` | 3981312 | `228303210FE8766D0AED59463A365DAE65891CAC5954D4369D699A64F6F139C3` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-gallery-host-correction-metres-20260922.rvt` | 4067328 | `CCDC01F6D52A7D5A1EA91B8ECF29C203948148C6DE3E6B0CD7FCF438EC99DCD6` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-internal-layout-20260922.rvt` | 4120576 | `E10BBAE9BA31680A848BBAD9F63FA11CA25582A18E17D83FBEAE5F9C879712D3` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R06-internal-layout-3d-20260922.rvt` | 4124672 | `EBF18F98A8AC5548E65B677684A1EF467732F2055113BB0C24829DB71C0A0D0A` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R07-openings-20260922.rvt` | 4198400 | `BE46ACDDE8CBA35E301BEFC36A36BD2D140C8BFB2B4528CFA940830DD36655B8` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R08-rooms-20260922.rvt` | 4214784 | `F2A224DE1F47DD67844D3A8AD1532934E5D3BA9E906B0AC1A5755EF21812C44C` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R09-accessibility-20260922.rvt` | 4247552 | `B8145958EA27E85B232AFBC72081F42B47FFCAD310AC16F8E8057409D5A9548A` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R10-furniture-20260922.rvt` | 4304896 | `D7F899C6DD9B1CE86F0B933CBE51F47728DC61F6DF2FE92CB1FFECE6C00E8959` | initial classification: UNCLASSIFIED |
| `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R11-landscape-20260922.rvt` | 4325376 | `F4DD2D9CF72CCD7FA1703D543D11E6B657AE5893254A3F20E7FEE34A7A8B0699` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153602.0001.rvt` | 3780608 | `0F066EF16809A531416FA847A59FF7CEB5653610835ED79D2C24B39F2AAE3367` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153602.rvt` | 3796992 | `683B454DCB713650668BAE59872895CCCC25EEBF019810A6991C4CFD639E8112` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153750.0001.rvt` | 3780608 | `6C46180178D69F43F47EC99B64F769B57BEEE70E1CB99189AB8A4C1CB9032A75` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153750.rvt` | 3801088 | `9873EC3E3E0EED7F3ABD7087A9741D56CD7790A64CE0AF5D97C8CC6D3314D9CE` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153844.0001.rvt` | 3780608 | `CA568A92838F983749859343DB069085072602659A0AB3A8F89858185815FC73` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153844.rvt` | 3796992 | `6F8D57CF369211EC3780142189E992B1A99AA09D58D39AAE0E150E5ACCD66904` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153947.0001.rvt` | 3780608 | `6F47B119BE36C60B332BBD4AE15070806E3F8CE4A1DF20B3056D7F1F8C4919FD` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-153947.rvt` | 3796992 | `BEA291E82FF2D01AB4E99350024CE38B478C7A8EB8107D122D6A8B30856956B8` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154012.0001.rvt` | 3780608 | `87DB2FC1A729559C3F124B7F9DEAEA34F0B35193A7BD40430B41AE866C6CF6E2` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154012.rvt` | 3796992 | `B162207DEB77113ACE5730DF387D00740582BB19E73261FDE4C7E6EE84DFF10A` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154138.0001.rvt` | 3780608 | `388E01FB4BDA7712D0393E38D0E469AC52640FC06DEBF2AA0422D922D0CF977D` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154138.rvt` | 3796992 | `00B60E20AF912EFA6834B62C41470D7CE022698FC69DC9B9E6386D09A911E61C` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154250.0001.rvt` | 3780608 | `8896C560D00C165F9020BB21A495CE3B14733A3D4195F9893F6F7708E3836107` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154250.rvt` | 3878912 | `E0FB03ABE348A24C10ABE6B85E1555011C72C2216B1DF0007FDB3FDD4C444254` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154439.0001.rvt` | 3780608 | `145BCF746C1C228ACC3CD25F54015CAF011589657C9B115220CA92E2494BD3D9` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154439.rvt` | 3796992 | `B1924A80743E15ED7BF72ECAAE4FDC09CDC4A4B28C59771CD33442EDBCC88DC6` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154522.0001.rvt` | 3780608 | `26E41D816D520248384517DD3DE43133C03B7D39E4340E66C1EC6D47EE8E5D7F` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154522.rvt` | 3878912 | `964AB17A333CD4E83949A09964D714F9FDEF02FE461AD6FA869547E60FD3FE99` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154620.0001.rvt` | 3780608 | `E27EB303624297C8CB519F451A9C2FB68DB2B63F9420F855BB7807B53EB4BEB5` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154620.rvt` | 3878912 | `2975CF3D9E4F2F815D276069B075828B6708463122A8E4D233517206B39E8553` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154754.0001.rvt` | 3780608 | `6FED134DD3E8514BAAABD3F4B6522631603FAF1A0BA586BF4AD0DA1C64D105FC` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154754.rvt` | 4173824 | `264E463BFE3979856A72FAD5BFE9066B8632534991FF3C1EE198CF84D7C0FE61` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154924.0001.rvt` | 3780608 | `A2A5B33406BEB1F36EFA9550BC9B55905EA33BEA5AAD93D522AF6894D45F60AA` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-154924.rvt` | 3878912 | `ED4CA6EDDC53A0974E22181F61B798EE2C65E5C544DF9352B4749E49BE9E102B` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155012.0001.rvt` | 3780608 | `478CFC234ABBC90A3AF42DAE3B1CB96121D89FF0D363D9618FD03D07970D9FE4` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155012.rvt` | 3878912 | `EAB522D314FB8BCFD16CEFD16EF20DD04D84D8401406276FE9B297A7F45538B3` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155127.0001.rvt` | 3780608 | `6F417EC8833DA56D6ACF5B088A489AA196D1C2C22D234462963058EFD41B7A20` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155127.rvt` | 4177920 | `A5E271784BDBC290E6BDCF362B1CCEAADC0A307E3E5EF887C28142EEE5AABEBA` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155346.0001.rvt` | 3780608 | `3D2C4BCA016EDE2DB16CB702A9FC0A999481083807C377139AA2542111DEF614` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-155346.rvt` | 4173824 | `B96D0795DBF96B1669CF39C5BE2CA943F8472F0C3AE5A1CB8ADFC78AD1EA598D` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160421.0001.rvt` | 3780608 | `BC3D52E9E495C7F4ED789360A0B39ED527E65D6608BE411E371FD919C7A6C212` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160421.rvt` | 3796992 | `9B1A8F113F4D118B1558ACD1F27F20961751C067E05A090F204A4D29F7FBC16E` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160505.0001.rvt` | 3780608 | `FCD20FE1F5E61807BBD6B3B51D8704A6910751979A4CBA177CC689472C0DB215` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160505.rvt` | 4173824 | `32DCBBC8AD45DE1F57E0866021068AECE199935FF0F3521DACCED14FEEBA27A5` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160800.0001.rvt` | 3780608 | `AD24905743610415B1CF3BA1A7A662949D6580FAFFCBC25A28928969D588408F` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-160800.rvt` | 4042752 | `4159A08837FA1A4419F835852A64F9AE9E17DABD190794EEFF9A54765C3DF81E` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-161057.0001.rvt` | 3780608 | `72FA7308E62AF222FDE7E61E7F6E20AD9311A006785ACCF8CB44E3C4AAF243C9` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-161057.rvt` | 4173824 | `6D2C2CDEEB8828A1D62152740677374465BC7CF3F20D086BF2EF40671298CDA3` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-161306.0001.rvt` | 3780608 | `2C6C6A3AE10171F292D2CF0E0F705E1020E7FBC181B1DE46E2CE9B021C1CBDA5` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260916-161306.rvt` | 4182016 | `731D677622B8044B7B303CAAEFA81D154FD077470234F9FE10AC4938803D58D0` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-200931.0001.rvt` | 3780608 | `6D181874AD47711873ECCB2EE5CE55684F8AB19502264FCE82EFAA7E1C2FAF6D` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-200931.rvt` | 4104192 | `3A0C962F22B45FCA2820DCC8B08322EA355FAD63BD561E1520E14836ABD31E13` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-205228.0001.rvt` | 3780608 | `1F6827AAEE9D2DDA7AE25F06A12815729BBBBD3FF66719136E31ACA588EE73F8` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-205228.rvt` | 4104192 | `6961284C0AE22D27A1ABF8A497F5B31EBDBB65A91A47AFDB323658BF8350CEF4` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-211721.0001.rvt` | 3780608 | `1CB1985C656D354C162AB98A7E336D5A58045038C979706BFA16AB262C26189D` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-211721.rvt` | 4005888 | `5285FF9164868744E70E85121C0BDAEA4C76A6DC2DC79BF83222B9B1380E415B` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-213302.0004.rvt` | 4112384 | `634E8D2C4C40C958F0011DB809289B897DCF7DD3677991281A1EBCA2E3E9171C` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-235556.0001.rvt` | 3780608 | `F28CBD2798D281A80F0F45B7A51BC1E802C57CFD62273C011AA49D47CA369763` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260921-235556.rvt` | 3960832 | `C6AAA595CD1FDB2952F6D7264E60AAA5681CBAF423E54629381BA082DB5C1928` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260922-011340.0001.rvt` | 3780608 | `385DE562681A55C2B3E8606A5FF6A6B5AB98317A4C9016642D48E5D320689512` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_001.20260922-011340.rvt` | 3960832 | `CC7FD1E83B370AA930EB924EE9F0D9BA52D99E7D3340B91B2F09930A367FB1C8` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_002.0001.rvt` | 3780608 | `399E7B72DF474D8B9E035F6275DCBB1B4C134F7E3802B574C7CA8319D1735D3B` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_002.rvt` | 3784704 | `95A38E314CB744BF8723ECDB473B79704F9BB3C2E8D75C4816230AE0B92CC2C0` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_003.0001.rvt` | 3780608 | `54DA5CE492B60ED7583E63C4E2E0877A6B78B060E5F2C5A577CB46DB8F425622` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA_WORKING_003.rvt` | 3784704 | `02E31BBF354FD6AA230C98E197CC4946B8B2156BEE7F8547B9EFE4A300F57F3C` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA-RUN-002-PAVILION-S02.0005.rvt` | 3981312 | `49C8AA6E767CE6704C0285771651C8E3B300400D55A52C55163A7CEB11B77EED` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA-RUN-002-PAVILION-S02.0006.rvt` | 4046848 | `C5F866B135240CA1A202D68D1028952DB3FDEF5734F15CFA897FD8676B63156A` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA-RUN-002-PAVILION-S02.0007.rvt` | 4046848 | `2702C626565ED426A8E3B9CC179EBF2008BA36284DDA60376DAE6E5BB9FF438E` | initial classification: UNCLASSIFIED |
| `revit/production/working/AMANDA-RUN-002-PAVILION-S02.rvt` | 4046848 | `6199FEDF2468D621960C0A756EDF02D756DA55C05B03A11F6344A3D2C33A65B6` | initial classification: UNCLASSIFIED |
| `revit/production/working/PROBE_RTE.rvt` | 3780608 | `6242D4438B68AA2DEBD46097496A39FF3FC289EFA01C050E797415F6A5A04FBB` | initial classification: UNCLASSIFIED |

## Full initial untracked-path appendix

- `.codex/config.toml`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16.zip`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/2026-09-11-amanda-tfg-bim-agent-design.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/PLAN_SELF_REVIEW.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/README.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/SHA256SUMS.txt`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/START_HERE_FOR_CODEX.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/notes/2026-09-15-revisao-planos-handoff.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/archive-comparison.json`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/generated-plans-manifest.json`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/package_review.py`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/validate_documents.py`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/validation-after.json`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/review/validation-before.json`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/00-master-implementation-plan.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/01-foundation-environment-state.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/02-revit-tool-lab-providers.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/03-project-intelligence.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/04-design-engine.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/05-bim-compiler.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/06-qa-release-exports.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/07-autonomy-recovery-security.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/08-amanda-production-run.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/09-optional-render-cloud.md`
- `amanda-tfg-bim-agent-planos-CORRIGIDOS-2026-09-16/docs/superpowers/plans/10-revision-production-priority.md`
- `docs/2026-09-24-amanda-repository-recovery-design.md`
- `docs/2026-09-24-amanda-repository-recovery.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24.zip`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/2026-09-11-amanda-tfg-bim-agent-design.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/GOAL_CODEX_4_BOARD_RECONCILIATION_2026-09-24.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/GOAL_CODEX_DELIVERY_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/MERGE_REPORT.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/PACKAGE_MANIFEST_2026-09-24.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/PLAN_SELF_REVIEW.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/PROMPT_CODEX_APLICAR_PACOTE_CANONICO_E_LIMPAR_ANTIGO.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/README.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/README_2026-09-24.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/SHA256SUMS.txt`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/START_HERE_FOR_CODEX.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/UNIFIED_PACKAGE_SELF_REVIEW.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/UNIFIED_PACKAGE_VALIDATION.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-15-revisao-planos-handoff.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-22-canonical-migration-handoff.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-22-current-repo-snapshot.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-22-delivery-mode-audit.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-24-current-git-state.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/notes/2026-09-24-required-code-changes.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/MERGE_REPORT.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/archive-comparison.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/canonical-validation.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/generated-plans-manifest.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/package-validation.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/package_canonical.py`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/package_review.py`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/README.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/09-geometric-acceptance-rubric.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/10-r12-freeze-protocol.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/11-bim-write-gate.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/12-pavilion-semantic-definition.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/13-visual-regression-qa.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/superpowers-revision-patch/00-master-plan-addendum.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/superpowers-revision-patch/11-canonical-pavilion-migration-revision.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/superpowers-revision-patch/12-geometric-acceptance-rubric.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/superpowers-revision-patch/13-visual-regression-qa.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/source-patches/superpowers-revision-patch/14-r12-freeze-and-write-gate.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/unified-package-validation.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/validate_canonical_package.py`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/validate_documents.py`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/validation-after.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/review/validation-before.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/SOURCE_MANIFEST.json`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/SOURCE_MANIFEST.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/canonical/TFG_Amanda_Fernandes_ENTREGA_15.06.2026.pdf`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/canonical/programa_necessidades.pdf`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/2026-09-24-AUTHORITY-AND-CONFLICT-POLICY.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/BIM_WRITE_GATE_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_4_BOARD_RECONCILIATION_MATRIX.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_DEVIATION_TEMPLATE.yaml`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_GEOMETRIC_ACCEPTANCE.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_PARTIDO_OVERRIDE_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_QA_RUBRIC.yaml`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_QA_RUBRIC_2026-09-24.yaml`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_REFERENCE_MATRIX.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_REFERENCE_PROFILE.yaml`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/CANONICAL_REFERENCE_PROFILE_2026-09-24.yaml`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/PAVILION_SEMANTIC_DEFINITION.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/R12_HISTORICAL_FREEZE_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/VISUAL_REFERENCES_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/VISUAL_REGRESSION_QA_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/canonical/00_overview_4_pranchas.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/canonical/01_implantacao_geral_canonica.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/canonical/02_bloco_administrativo_canonico.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/canonical/03_bloco_residencial_canonico.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/canonical/04_bloco_servicos_capacitacao_canonico.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/evidence/01_revit_linear_desalinhado.jpg`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/evidence/02_multiplos_rvts_sem_avanco.jpg`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/evidence/03_brief_original_whatsapp.jpg`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/01_ref_admin_previa.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/02_ref_residencial_previa.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/03_ref_implantacao_previa.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/canonical-set-before-2026-09-24/01_implantacao_geral_canonica.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/canonical-set-before-2026-09-24/02_bloco_residencial_canonico.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/source/references/historical/canonical-set-before-2026-09-24/03_bloco_administrativo_canonico.png`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/00-master-implementation-plan.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/01-foundation-environment-state.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/02-revit-tool-lab-providers.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/03-project-intelligence.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/04-design-engine.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/05-bim-compiler.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/06-qa-release-exports.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/07-autonomy-recovery-security.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/08-amanda-production-run.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/09-optional-render-cloud.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/10-revision-production-priority.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/11-canonical-pavilion-migration.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/plans/12-four-board-canonical-reconciliation.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/specs/2026-09-22-canonical-pavilion-migration-design.md`
- `docs/amanda-tfg-bim-agent-RECONCILIADO-4-PRANCHAS-2026-09-24/docs/superpowers/specs/2026-09-24-four-board-canonical-reconciliation-design.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22.zip`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/2026-09-11-amanda-tfg-bim-agent-design.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/GOAL_CODEX_DELIVERY_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/MERGE_REPORT.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/PLAN_SELF_REVIEW.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/PROMPT_CODEX_APLICAR_PACOTE_CANONICO_E_LIMPAR_ANTIGO.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/README.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/SHA256SUMS.txt`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/START_HERE_FOR_CODEX.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/UNIFIED_PACKAGE_SELF_REVIEW.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/UNIFIED_PACKAGE_VALIDATION.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/notes/2026-09-15-revisao-planos-handoff.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/notes/2026-09-22-canonical-migration-handoff.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/notes/2026-09-22-current-repo-snapshot.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/notes/2026-09-22-delivery-mode-audit.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/MERGE_REPORT.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/archive-comparison.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/canonical-validation.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/generated-plans-manifest.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/package-validation.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/package_canonical.py`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/package_review.py`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/README.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/09-geometric-acceptance-rubric.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/10-r12-freeze-protocol.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/11-bim-write-gate.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/12-pavilion-semantic-definition.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/canonical-docs-patch/docs/superpowers/plans/13-visual-regression-qa.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/superpowers-revision-patch/00-master-plan-addendum.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/superpowers-revision-patch/11-canonical-pavilion-migration-revision.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/superpowers-revision-patch/12-geometric-acceptance-rubric.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/superpowers-revision-patch/13-visual-regression-qa.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/source-patches/superpowers-revision-patch/14-r12-freeze-and-write-gate.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/unified-package-validation.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/validate_canonical_package.py`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/validate_documents.py`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/validation-after.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/review/validation-before.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/SOURCE_MANIFEST.json`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/SOURCE_MANIFEST.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/canonical/TFG_Amanda_Fernandes_ENTREGA_15.06.2026.pdf`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/canonical/programa_necessidades.pdf`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/BIM_WRITE_GATE_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_DEVIATION_TEMPLATE.yaml`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_GEOMETRIC_ACCEPTANCE.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_PARTIDO_OVERRIDE_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_QA_RUBRIC.yaml`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_REFERENCE_MATRIX.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/CANONICAL_REFERENCE_PROFILE.yaml`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/PAVILION_SEMANTIC_DEFINITION.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/R12_HISTORICAL_FREEZE_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/VISUAL_REFERENCES_2026-09-22.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/VISUAL_REGRESSION_QA_PROTOCOL.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/canonical/01_implantacao_geral_canonica.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/canonical/02_bloco_residencial_canonico.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/canonical/03_bloco_administrativo_canonico.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/canonical/04_bloco_servicos_capacitacao_canonico.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/canonical/cec18cd5-044b-4f5f-a081-f42aaa7297a6.jpg`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/evidence/01_revit_linear_desalinhado.jpg`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/evidence/02_multiplos_rvts_sem_avanco.jpg`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/evidence/03_brief_original_whatsapp.jpg`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/historical/01_ref_admin_previa.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/historical/02_ref_residencial_previa.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/source/references/historical/03_ref_implantacao_previa.png`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/00-master-implementation-plan.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/01-foundation-environment-state.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/02-revit-tool-lab-providers.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/03-project-intelligence.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/04-design-engine.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/05-bim-compiler.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/06-qa-release-exports.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/07-autonomy-recovery-security.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/08-amanda-production-run.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/09-optional-render-cloud.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/10-revision-production-priority.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/plans/11-canonical-pavilion-migration.md`
- `docs/amanda-tfg-bim-agent-UNIFICADO-PRANCHAS-CANONICAS-2026-09-22/docs/superpowers/specs/2026-09-22-canonical-pavilion-migration-design.md`
- `docs/amanda-tfg-bim-agent-planos-DELIVERY-MODE-2026-09-22.zip`
- `docs/amanda-tfg-bim-agent-planos-DELIVERY-MODE-REFERENCIAS-2026-09-22.zip`
- `docs/amanda-tfg-bim-agent-planos-PRANCHAS-CANONICAS-2026-09-22 (1).zip`
- `docs/amanda-tfg-bim-agent-planos-PRANCHAS-CANONICAS-2026-09-22.zip`
- `docs/amanda-tfg-bim-agent-planos-PRANCHAS-CANONICAS-COMPLETO-2026-09-22-FINAL-VALIDATION.md`
- `docs/amanda-tfg-bim-agent-planos-PRANCHAS-CANONICAS-COMPLETO-2026-09-22.zip`
- `docs/amanda_tfg_Codex_EXECUTION_PACKAGE_CANONICAL_FINAL_2026-09-22.zip`
- `docs/amanda_tfg_canonical_docs_patch_2026-09-22.zip`
- `docs/amanda_tfg_superpowers_revision_patch_2026-09-22.zip`
- `docs/notes/2026-09-23-r04-canonical-handoff.md`
- `docs/superpowers/plans/11-canonical-pavilion-migration.md`
- `release/preview/pdf/page-0001.png`
- `release/preview/pdf/page-0002.png`
- `release/preview/pdf/page-0003.png`
- `release/preview/pdf/page-0004.png`
- `release/preview/pdf/page-0005.png`
- `release/preview/pdf/page-0006.png`
- `release/preview/pdf/page-0007.png`
- `revit/production/archive/superseded-linear/manifest.json`
- `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R03-levels-and-grids-20260923.rvt.manifest.json`
- `revit/production/checkpoints/AMANDA-RUN-002-PAVILION-S02/R03-prewrite-20260923-2219.rvt.manifest.json`
- `revit/production/evidence/AMANDA-RUN-002-PAVILION-S02-BIM-00-R03.json`
- `revit/production/evidence/AMANDA-RUN-002-PAVILION-S02-BIM-00.json`
- `revit/production/evidence/AMANDA-RUN-002-PAVILION-S02-CANONICAL-GEOMETRIC-ACCEPTANCE-R04.json`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R03-postreopen-implantation-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-canonical-preview-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-implantation-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-isometric-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-live-implantation-20260924.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-side-by-side-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-top-20260923.png`
- `revit/production/previews/AMANDA-RUN-002-PAVILION-S02-R04-top-flatcolors-20260923.png`


## Task 1 reversible checkpoint

- Stash commit: `2dbcacb34cd25e07cbed0672c818d797cb58f477` (8 tracked paths and 232 untracked paths, including report and inventory). It is retained until every useful file is reconciled; no source/evidence was dropped.

## Decisions during recovery

Append decisions and evidence after each task. S02 remains stale by canonical-reference expansion. The historical linear R12 hash remains `AC814642296CBC7074603B703F8DB20A63AE1C1475F435756A248516D1856E29`.

## Final validation

Pending Task 13.




## Task 1 supplemental recovery evidence

### Verified runtime facts

- Evidence captured UTC: `2026-09-24T15:57:49.0840204Z`. The annotated safety tag `pre-repository-recovery-2026-09-24` points to commit `30cc3b0f7860dfb5e46299402585213d1ac2d02b` and has tag object `2567d03cc8ff2860e80bda1ec9981195ddddee6c`. Verified on origin: `refs/tags/pre-repository-recovery-2026-09-24` points to annotated tag object `2567d03cc8ff2860e80bda1ec9981195ddddee6c`.
- Recovery stash: `2dbcacb34cd25e07cbed0672c818d797cb58f477`; 8 tracked paths and 232 untracked paths.
- Elevated worktree status at capture: clean (0 entries).
- RC01 directory existed and contained 36 files. Manifest SHA-256: `596CB7F878A05CC565D6A1831B7E19F8D10E6FE625F739339E9A61CF34DEE5AD`. Model SHA-256: `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744`.
- Task 1 execution record: Revit actions = `none`. This records activity only; no test result or model outcome is inferred from it.

### Supplemental full RVT inventory

- Supplemental scan captured UTC: `2026-09-24T15:57:48.0338523Z`; source: supplemental full RVT scan after reversible stash, before branch integration/cleanup.
- The full scan contains 480 unique RVT paths. The first pre-cleanup inventory captured hashes for 112 files at `2026-09-24T14:56:20.5115075Z`; all 112 were verified unchanged in the supplemental scan.
- The other 368 ignored test/runtime fixtures had their hashes captured in the supplemental scan before branch integration or cleanup. Their per-file hashes were not captured at the original timestamp.

| Relative path | Bytes | SHA-256 | Classification |
|---|---:|---|---|
| `.tmp-pytest-y5/test_ambiguous_hardlink_identi0/working/alias.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_ambiguous_hardlink_identi0/working/AMANDA_WORKING_001.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_copy_publishes0/R01_PROJECT_INITIALIZED.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_copy_publishes0/working.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_label_is_r01_p0/working.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_label_is_r01_p0/checkpoints/r01.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_protection_app0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_checkpoint_refuses_active0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_complete_drill_passes_qa_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_complete_drill_passes_qa_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_complete_record_bridges_a0/model.rvt` | 16 | `8754EFBF3CD1B6BB89195B8DE2B357C204BA015CF454CB907F16CC72794932FD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_corrupt_latest_checkpoint0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_corrupt_latest_checkpoint0/R02.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_corrupt_latest_checkpoint0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_corrupt_latest_checkpoint0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_crashed_state_selects_lat0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_crashed_state_selects_lat0/R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_crashed_state_selects_lat0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_crashed_state_selects_lat0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_divergent_export_hash_is_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_divergent_export_hash_is_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_empty_issue_list_does_not0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_existing_checkpoint_path_0/checkpoint.rvt` | 9 | `B4DDDECF813201F4A83F2AE71F6FA1A03EA961C3738E3DA7FFF94859C5AD1C17` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_existing_checkpoint_path_0/working.rvt` | 9 | `11E2DEFD59F47C7F2AAC84D6A5D6747E98E785AFFFB72C8BB7B05EC74E1D663C` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_existing_golden_is_never_0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_golden_cannot_be_used_as_0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_incomplete_mandatory_expo0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_incomplete_persistence_bl0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_interrupted_mutation_neve0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_interrupted_mutation_neve0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_interrupted_staging_never0/golden/.RC01.6en4nn_w.staging/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_interrupted_staging_never0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_invalid_mandatory_export_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_invalid_mandatory_export_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_manifest_does_not_hash_it0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_manifest_keeps_version_do0/R02_SITE.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_manifest_keeps_version_do0/working.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_manifest_serialization_is0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_missing_close_and_hash_ke0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_occupied_writer_lock_is_r0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_place_link_accepts_the_st0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_place_link_returns_a_metr0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_protected_target_is_refus0/lab/baseline-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_protected_target_is_refus1/lab/release-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_protected_target_is_refus2/lab/golden-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_qa_fail_blocks_promotion0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_reachable_provider_with_f0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_recovery_can_decide_retry0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_recovery_can_decide_retry0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_release_verify_detects_wr0/GOLDEN-001/model.rvt` | 6 | `E5C6FDE86910DED72DB5CC7AFC32F850440D4EF7CAA5DBB69F5BDC0D3E39CB3B` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_renamed_original_with_mat0/working/AMANDA_WORKING_001.rvt` | 14 | `E15BBC84603DC71F530B0A4ECC0DF7D987994BD14D57FF2678F499750763C701` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_required_artifact_without0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_resume_file_contains_dete0/R02.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_resume_file_contains_dete0/working.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_copies_to_a_new_0/checkpoints/R00-lab.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_copies_to_a_new_0/work/lab-r01.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_refuses_checkpoi0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_refuses_checkpoi0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_refuses_the_same0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_rejects_an_exist0/exists.rvt` | 16 | `708A546F370DEE0EC382F9BF24102AF0124EE649E0ADD925C577539E44E04F54` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_rejects_an_exist0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_rejects_a_hash_m0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_a_quies0/new.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_a_quies0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_current0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_current0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_current1/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_requires_current1/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_verifies_checkpo0/R01.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_rollback_verifies_checkpo0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_second_promotion_to_same_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_second_promotion_to_same_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_study_can_retain_visible_0/final/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_study_can_retain_visible_0/golden-study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_study_can_retain_visible_0/study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/model.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-01.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-02.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-03.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-04.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-05.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-06.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-07.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-08.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-09.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-10.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-11.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-12.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_synthetic_pipeline_runs_r0/stage-13.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_unreachable_provider_retu0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_unwaived_mandatory_blocke0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y5/test_verify_manifest_detects_t0/model.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_ambiguous_hardlink_identi0/working/alias.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_ambiguous_hardlink_identi0/working/AMANDA_WORKING_001.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_copy_publishes0/R01_PROJECT_INITIALIZED.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_copy_publishes0/working.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_label_is_r01_p0/working.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_label_is_r01_p0/checkpoints/r01.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_protection_app0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_checkpoint_refuses_active0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_complete_drill_passes_qa_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_complete_drill_passes_qa_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_complete_record_bridges_a0/model.rvt` | 16 | `8754EFBF3CD1B6BB89195B8DE2B357C204BA015CF454CB907F16CC72794932FD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_corrupt_latest_checkpoint0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_corrupt_latest_checkpoint0/R02.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_corrupt_latest_checkpoint0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_corrupt_latest_checkpoint0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_crashed_state_selects_lat0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_crashed_state_selects_lat0/R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_crashed_state_selects_lat0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_crashed_state_selects_lat0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_divergent_export_hash_is_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_divergent_export_hash_is_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_empty_issue_list_does_not0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_existing_checkpoint_path_0/checkpoint.rvt` | 9 | `B4DDDECF813201F4A83F2AE71F6FA1A03EA961C3738E3DA7FFF94859C5AD1C17` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_existing_checkpoint_path_0/working.rvt` | 9 | `11E2DEFD59F47C7F2AAC84D6A5D6747E98E785AFFFB72C8BB7B05EC74E1D663C` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_existing_golden_is_never_0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_golden_cannot_be_used_as_0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_incomplete_mandatory_expo0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_incomplete_persistence_bl0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_interrupted_mutation_neve0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_interrupted_mutation_neve0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_interrupted_staging_never0/golden/.RC01.0m2iss_r.staging/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_interrupted_staging_never0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_invalid_mandatory_export_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_invalid_mandatory_export_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_manifest_does_not_hash_it0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_manifest_keeps_version_do0/R02_SITE.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_manifest_keeps_version_do0/working.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_manifest_serialization_is0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_missing_close_and_hash_ke0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_occupied_writer_lock_is_r0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_place_link_accepts_the_st0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_place_link_returns_a_metr0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_protected_target_is_refus0/lab/baseline-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_protected_target_is_refus1/lab/release-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_protected_target_is_refus2/lab/golden-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_qa_fail_blocks_promotion0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_reachable_provider_with_f0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_recovery_can_decide_retry0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_recovery_can_decide_retry0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_release_verify_detects_wr0/GOLDEN-001/model.rvt` | 6 | `E5C6FDE86910DED72DB5CC7AFC32F850440D4EF7CAA5DBB69F5BDC0D3E39CB3B` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_renamed_original_with_mat0/working/AMANDA_WORKING_001.rvt` | 14 | `E15BBC84603DC71F530B0A4ECC0DF7D987994BD14D57FF2678F499750763C701` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_required_artifact_without0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_resume_file_contains_dete0/R02.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_resume_file_contains_dete0/working.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_copies_to_a_new_0/checkpoints/R00-lab.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_copies_to_a_new_0/work/lab-r01.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_refuses_checkpoi0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_refuses_checkpoi0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_refuses_the_same0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_rejects_an_exist0/exists.rvt` | 16 | `708A546F370DEE0EC382F9BF24102AF0124EE649E0ADD925C577539E44E04F54` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_rejects_an_exist0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_rejects_a_hash_m0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_a_quies0/new.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_a_quies0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_current0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_current0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_current1/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_requires_current1/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_verifies_checkpo0/R01.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_rollback_verifies_checkpo0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_second_promotion_to_same_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_second_promotion_to_same_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_study_can_retain_visible_0/final/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_study_can_retain_visible_0/golden-study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_study_can_retain_visible_0/study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/model.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-01.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-02.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-03.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-04.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-05.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-06.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-07.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-08.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-09.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-10.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-11.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-12.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_synthetic_pipeline_runs_r0/stage-13.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_unreachable_provider_retu0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_unwaived_mandatory_blocke0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y6/test_verify_manifest_detects_t0/model.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_ambiguous_hardlink_identi0/working/alias.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_ambiguous_hardlink_identi0/working/AMANDA_WORKING_001.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_copy_publishes0/R01_PROJECT_INITIALIZED.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_copy_publishes0/working.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_label_is_r01_p0/working.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_label_is_r01_p0/checkpoints/r01.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_protection_app0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_checkpoint_refuses_active0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_complete_drill_passes_qa_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_complete_drill_passes_qa_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_complete_record_bridges_a0/model.rvt` | 16 | `8754EFBF3CD1B6BB89195B8DE2B357C204BA015CF454CB907F16CC72794932FD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_corrupt_latest_checkpoint0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_corrupt_latest_checkpoint0/R02.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_corrupt_latest_checkpoint0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_corrupt_latest_checkpoint0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_crashed_state_selects_lat0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_crashed_state_selects_lat0/R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_crashed_state_selects_lat0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_crashed_state_selects_lat0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_divergent_export_hash_is_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_divergent_export_hash_is_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_empty_issue_list_does_not0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_existing_checkpoint_path_0/checkpoint.rvt` | 9 | `B4DDDECF813201F4A83F2AE71F6FA1A03EA961C3738E3DA7FFF94859C5AD1C17` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_existing_checkpoint_path_0/working.rvt` | 9 | `11E2DEFD59F47C7F2AAC84D6A5D6747E98E785AFFFB72C8BB7B05EC74E1D663C` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_existing_golden_is_never_0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_golden_cannot_be_used_as_0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_incomplete_mandatory_expo0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_incomplete_persistence_bl0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_interrupted_mutation_neve0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_interrupted_mutation_neve0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_interrupted_staging_never0/golden/.RC01.794t0wn8.staging/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_interrupted_staging_never0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_invalid_mandatory_export_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_invalid_mandatory_export_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_manifest_does_not_hash_it0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_manifest_keeps_version_do0/R02_SITE.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_manifest_keeps_version_do0/working.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_manifest_serialization_is0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_missing_close_and_hash_ke0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_occupied_writer_lock_is_r0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_place_link_accepts_the_st0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_place_link_returns_a_metr0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_protected_target_is_refus0/lab/baseline-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_protected_target_is_refus1/lab/release-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_protected_target_is_refus2/lab/golden-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_qa_fail_blocks_promotion0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_reachable_provider_with_f0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_recovery_can_decide_retry0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_recovery_can_decide_retry0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_release_verify_detects_wr0/GOLDEN-001/model.rvt` | 6 | `E5C6FDE86910DED72DB5CC7AFC32F850440D4EF7CAA5DBB69F5BDC0D3E39CB3B` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_renamed_original_with_mat0/working/AMANDA_WORKING_001.rvt` | 14 | `E15BBC84603DC71F530B0A4ECC0DF7D987994BD14D57FF2678F499750763C701` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_required_artifact_without0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_resume_file_contains_dete0/R02.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_resume_file_contains_dete0/working.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_copies_to_a_new_0/checkpoints/R00-lab.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_copies_to_a_new_0/work/lab-r01.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_refuses_checkpoi0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_refuses_checkpoi0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_refuses_the_same0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_rejects_an_exist0/exists.rvt` | 16 | `708A546F370DEE0EC382F9BF24102AF0124EE649E0ADD925C577539E44E04F54` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_rejects_an_exist0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_rejects_a_hash_m0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_a_quies0/new.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_a_quies0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_current0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_current0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_current1/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_requires_current1/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_verifies_checkpo0/R01.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_rollback_verifies_checkpo0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_second_promotion_to_same_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_second_promotion_to_same_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_study_can_retain_visible_0/final/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_study_can_retain_visible_0/golden-study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_study_can_retain_visible_0/study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/model.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-01.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-02.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-03.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-04.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-05.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-06.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-07.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-08.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-09.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-10.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-11.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-12.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_synthetic_pipeline_runs_r0/stage-13.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_unreachable_provider_retu0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_unwaived_mandatory_blocke0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y8/test_verify_manifest_detects_t0/model.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_ambiguous_hardlink_identi0/working/alias.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_ambiguous_hardlink_identi0/working/AMANDA_WORKING_001.rvt` | 11 | `E416D2EA33181719A9F727A65820257DB7CE56F2756C81A84B196FB5CEB08214` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_copy_publishes0/R01_PROJECT_INITIALIZED.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_copy_publishes0/working.rvt` | 18 | `B3F13D233334459A852183F6D1826324E11DCDE20275B49CD46EA5D3DEAFADCF` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_label_is_r01_p0/working.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_label_is_r01_p0/checkpoints/r01.rvt` | 13 | `E35AE756F91636C63A682031F5A294B28216280DEDE4939EED26A29F9A27C5CA` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_protection_app0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_checkpoint_refuses_active0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_complete_drill_passes_qa_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_complete_drill_passes_qa_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_complete_record_bridges_a0/model.rvt` | 16 | `8754EFBF3CD1B6BB89195B8DE2B357C204BA015CF454CB907F16CC72794932FD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_corrupt_latest_checkpoint0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_corrupt_latest_checkpoint0/R02.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_corrupt_latest_checkpoint0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_corrupt_latest_checkpoint0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_crashed_state_selects_lat0/R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_crashed_state_selects_lat0/R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_crashed_state_selects_lat0/working-R01.rvt` | 3 | `7692C3AD3540BB803C020B3AEE66CD8887123234EA0C6E7143C0ADD73FF431ED` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_crashed_state_selects_lat0/working-R02.rvt` | 3 | `3FC4CCFE745870E2C0D99F71F30FF0656C8DEDD41CC1D7D3D376B0DBE685E2F3` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_divergent_export_hash_is_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_divergent_export_hash_is_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_empty_issue_list_does_not0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_existing_checkpoint_path_0/checkpoint.rvt` | 9 | `B4DDDECF813201F4A83F2AE71F6FA1A03EA961C3738E3DA7FFF94859C5AD1C17` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_existing_checkpoint_path_0/working.rvt` | 9 | `11E2DEFD59F47C7F2AAC84D6A5D6747E98E785AFFFB72C8BB7B05EC74E1D663C` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_existing_golden_is_never_0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_golden_cannot_be_used_as_0/working.rvt` | 5 | `9372C470EEADD5ECD9C3C74C2B3CB633F8E2F2FAD799250A0F70D652B6B825E4` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_incomplete_mandatory_expo0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_incomplete_persistence_bl0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_interrupted_mutation_neve0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_interrupted_mutation_neve0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_interrupted_staging_never0/golden/.RC01.lyp7cx7l.staging/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_interrupted_staging_never0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_invalid_mandatory_export_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_invalid_mandatory_export_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_manifest_does_not_hash_it0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_manifest_keeps_version_do0/R02_SITE.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_manifest_keeps_version_do0/working.rvt` | 14 | `5A855430E6B6A41750A0928768920A774A02F00D02D79D2880A4204A2F1F22F5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_manifest_serialization_is0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_missing_close_and_hash_ke0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_occupied_writer_lock_is_r0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_place_link_accepts_the_st0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_place_link_returns_a_metr0/context.rvt` | 13 | `C3DA769E6A2A6886B8FCAA6FA7705A84EEACC5A9E14F876E3B356689A39266BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_protected_target_is_refus0/lab/baseline-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_protected_target_is_refus1/lab/release-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_protected_target_is_refus2/lab/golden-candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_qa_fail_blocks_promotion0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_reachable_provider_with_f0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_recovery_can_decide_retry0/R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_recovery_can_decide_retry0/working-R02.rvt` | 10 | `EDB89D09B913B577EFBD63F53446D060C97D339166531661A5196A0CF6B796BD` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_release_verify_detects_wr0/GOLDEN-001/model.rvt` | 6 | `E5C6FDE86910DED72DB5CC7AFC32F850440D4EF7CAA5DBB69F5BDC0D3E39CB3B` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_renamed_original_with_mat0/working/AMANDA_WORKING_001.rvt` | 14 | `E15BBC84603DC71F530B0A4ECC0DF7D987994BD14D57FF2678F499750763C701` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_required_artifact_without0/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_resume_file_contains_dete0/R02.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_resume_file_contains_dete0/working.rvt` | 6 | `F379CCB92B9116442DC65BDC35648A85D3786B34779DB7F704A901FA07B00CB6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_copies_to_a_new_0/checkpoints/R00-lab.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_copies_to_a_new_0/work/lab-r01.rvt` | 18 | `8D1A75DD2D7FFC51AB7B9552CB7D9D04E0E215B29D23F468F3B65D8C8872A03F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_refuses_checkpoi0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_refuses_checkpoi0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_refuses_the_same0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_rejects_an_exist0/exists.rvt` | 16 | `708A546F370DEE0EC382F9BF24102AF0124EE649E0ADD925C577539E44E04F54` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_rejects_an_exist0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_rejects_a_hash_m0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_a_quies0/new.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_a_quies0/R00.rvt` | 7 | `239F59ED55E737C77147CF55AD0C1B030B6D7EE748A7426952F9B852D5A935E5` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_current0/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_current0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_current1/R02.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_requires_current1/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_verifies_checkpo0/R01.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_rollback_verifies_checkpo0/working.rvt` | 10 | `BE8E11CCFAE3BB07404C5942CBD1F3904D1C2082813C9515C30FE1E7365FAF45` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_second_promotion_to_same_0/lab/GOLDEN/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_second_promotion_to_same_0/lab/RC01/model.rvt` | 53 | `01B7426E32C162EDE4249417A4735E699601A654C2738ED450F6C09B705B0744` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_study_can_retain_visible_0/final/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_study_can_retain_visible_0/golden-study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_study_can_retain_visible_0/study/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/model.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-01.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-02.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-03.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-04.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-05.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-06.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-07.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-08.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-09.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-10.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-11.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-12.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_synthetic_pipeline_runs_r0/stage-13.rvt` | 24 | `266F9C7BCF7CE2E1C832F89B9A2756B65ECAF303488E9E3F7427E3758A27AA5F` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_unreachable_provider_retu0/lab/candidate.rvt` | 20 | `6B89A963DDD21F5B2F6604311D7C2641E188498DF107319EFC1A90915D70D1B6` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_unwaived_mandatory_blocke0/RC01/model.rvt` | 12 | `766AA46F408D34EBB48DE3137B5D6FE5DE05D9B84575AFA0A2AE63F3A406C0CB` | TEMPORARY_TEST_FIXTURE |
| `.tmp-pytest-y9/test_verify_manifest_detects_t0/model.rvt` | 8 | `D121BE3103007B41EDF96F8262925F8C7D61894AFE9A041843B631F69445BC57` | TEMPORARY_TEST_FIXTURE |

## Task 2 — canonical branch consolidation

- Before fast-forward: `main` = `7daf6f67a9980705d96bf25e0b648305feeef39b`; `codex/canonical-pavilion-migration` = `daa200f34974065cb0b8adb56261354f0a3c3130`.
- `git merge-base --is-ancestor main codex/canonical-pavilion-migration` returned exit 0. `main` advanced with `git merge --ff-only codex/canonical-pavilion-migration`; no merge commit was created.
- After fast-forward and before the report-only commit: local `main`, local canonical, `HEAD`, and fetched `origin/main` all equaled `daa200f34974065cb0b8adb56261354f0a3c3130`.
- The initial `git push origin main` completed successfully; a subsequent `git fetch origin` confirmed local/remote equality. The report-only commit below is pushed and rechecked separately.
- Task 1 commits `0e14b1cab93d49b73807cc824bf087cf09450c37` and `daa200f34974065cb0b8adb56261354f0a3c3130` are part of the fast-forwarded history. Original safety tag remains at `30cc3b0f7860dfb5e46299402585213d1ac2d02b`.
- No tests were run because this task changed Git refs and recovery documentation only. No Revit/model action occurred. Branch deletion and worktree cleanup remain deferred to their named tasks.
- Evidence capture: `2026-09-24T16:20:11Z`; pre-report worktree status clean, ancestry gate passed, local/remote SHAs verified.


## Task 3 — concept-offline branch classification

Patch-equivalence-aware comparison of `main...origin/codex/p08-t08-concept-offline` produced two right-side-only commits; `git rev-list --no-merges main..origin/codex/p08-t08-concept-offline` confirmed the same two SHAs. Full diffs were inspected. Neither commit is integrated.

- `
e5c9a0e8342423e9dbcdf4e4b56c94858970879f
` — `INTENTIONALLY_SUPERSEDED`. Adds an offline candidate generator and tests bound to the AMANDA-RUN-001 F01/F02 candidates and the pre-reconciliation solution/geometry contract. The canonical source set now includes a fourth board; the old F01/F02 outputs are not bound to that four-board authority, and the next authorized phase P1-T01 reconciles the code contract. Activating these candidates now would present stale inputs as current. Their handoff also explicitly labels the artifacts synthetic/offline and live Revit persistence pending; no runtime claim is carried forward.
- `
125c7d956d40fab6c358e4c6702199b4eac4d854
` — `INTENTIONALLY_SUPERSEDED`. Adds only a publication note to the same P08-T08 handoff for the superseded offline candidate work; it has no independent current implementation value.

No SHA was classified `INTEGRATE`; `.recovery/concept-integrate.txt` exists and is empty (0 bytes), and no cherry-pick or branch-wide merge was performed. To preserve exact source/history before the later Task 12 branch decision, annotated tag `
superseded-p08-t08-concept-offline-2026-09-24
` was created at commit `
125c7d956d40fab6c358e4c6702199b4eac4d854
` (tag object `
1b505c1cdfc322128aa9b70350ffcd59a61441cf
`). The local/remote P08 branch remains intact; deletion is deferred to Task 12. No tests were run because no code was integrated. No Revit/model action occurred.

### Task 3 verification note — ACL and reviewer evidence

A non-elevated Git status may list 34 paths under `revit/lab/exports/p06t14/GOLDEN/RC01/` as deleted because that access context cannot enumerate the directory. The elevated status at this checkpoint showed only the required untracked `.recovery/concept-integrate.txt`. An elevated recursive read found all 36 RC01 files present; `manifest.json` SHA-256 remained `596CB7F878A05CC565D6A1831B7E19F8D10E6FE625F739339E9A61CF34DEE5AD` and `model.rvt` SHA-256 remained `01B7426E32C162EDE4249417A4735E699601A654C2738E450F6C09B705B0744`. No RC01 file was restored, staged, or modified.

The second unique P08 commit `125c7d956d40fab6c358e4e6702199b4eac4d854` was resolved as a commit and its full 8-line publication-addendum diff was inspected. A fresh `git ls-remote --tags origin` confirmed archive tag object `1b505c1cdfc322128aa9b70350ffcd59a61441cf` peels to that commit. See the task verification evidence in the ignored SDD workspace for command output.

## Task 4 — worktree topology

- Before prune: `git worktree list --porcelain` contained exactly one entry: `C:/Users/slvma/Downloads/Github/Projeto Amanda`, branch `main`, HEAD `0bb2d90c8b9aec38ad49221c2a045c583607f547`.
- Secondary worktree count: 0. Removed worktree count: 0. No `git worktree remove` command was needed, so there were no secondary status/ancestry/untracked/RVT gates to waive.
- `git worktree prune --dry-run --verbose` found no stale metadata. The ordinary `git worktree prune --verbose` completed without removing anything; the following porcelain list still contained exactly the primary worktree above.
- No tests were run; this task changed only Git worktree metadata/reporting. No Revit/model action occurred. The required temporary `.recovery/concept-integrate.txt` remains untouched for Task 13 cleanup.

## Task 6 — current-document architecture and state migration

Installed `START_HERE.md`, `docs/spec/CURRENT.md`, `docs/plan/CURRENT.md`, `docs/decisions/DECISIONS.md`, and `state/HANDOFF.md`. Updated `AGENTS.md` to route sessions through this single read order and explicitly prohibit Revit/model work during P0. The plan-required `amanda_agent status` command refreshed tracked `state/status.md` to show the recovery phase and current read-only environment/lease observations. The current specification includes the complete four-board-to-program reconciliation matrix, including all hard implantation rules, administration floor assignments, pavilion membership, curved services/patio constraints, and both permitted child-sector implementations. No design choice was made for the child rooms.

### State schema and consumer audit

`src/amanda_agent/models/state.py::ProjectState` defines the persisted schema-1 fields: `project`, `phase_id`, `phase_name`, `phase_status`, `last_completed_task`, `next_task`, `schema_version`, `state_revision`, `phase_gate`, `selected_design`, `revit_stage`, `current_checkpoint`, `blockers`, and `last_verified_commit`.

`src/amanda_agent/state/store.py::StateStore.load` parses YAML and validates through `ProjectState(**raw)`. The status dashboard, session start/end, state advancement, and CLI status paths use the typed store/model. The test `tests/unit/test_canonical_state_migration.py` reads YAML directly for assertions. Search found no application consumer that reads a S02-specific extra key directly from `PROJECT_STATE.yaml`. YAML reads in `session/start.py` and the dashboard are for separate provider/environment/blocker files, not `PROJECT_STATE.yaml`.

### Extra-field migration record

The dirty pre-recovery state carried these non-model keys. Their evidence is retained in the pre-recovery stash/tag and mapped as follows:

- Selection and approval data: `selection_authority`, `selection_review`, `parti_selection_authority`, `detailed_variant_authority`, `selected_run_id`, `selection_decision_id`, `parti_decision_id`, `supersession_decision_id`, `selection_approval_hash`, `parti_approval_hash`, and `detail_decision_approval_hash`. The old selection was `AMANDA-RUN-002-PAVILION-S02`, USER_DIRECTED for the parti but AGENT_DELEGATED for detail; its selection/detail approvals were `75afda89d6a18cd2834bdd571e761ea047305465c6579a4a9d0474e409f91bdf` and `89c57532d9bc215969d36ec0e0d26e1966e7e333adc734e216a3e9f01f4d620c`. Decision authority is summarized in `docs/decisions/DECISIONS.md`; exact prior IDs and hashes remain in the decision register and Git history. They do not authorize a current solution.
- S02 layout/build details: `layout_module`, `layout_content_hash`, `layout_net_internal_m2`, `layout_gross_enclosed_m2`, `layout_covered_total_m2`, `layout_external_program_m2`, `layout_gross_enclosed_estimate_m2`, `layout_covered_estimate_m2`, `production_driver`, `production_plan_stages`, `production_plan_operations`, and `layout_qa`. The old module/hash were `src/amanda_agent/design/canonical_pavilion_layout.py` / `20529b1d08c570546641397a4e9fd302a2a23bef917f50bfea6d22824a19f556`; its internal/external values were 626/260 m², measured gross/covered fields were null, and estimates were 783–814/850–950 m². Its plan named R01–R04 and its QA reported 11 PASS, 0 FAIL, 1 BLOCKED (CANON-011), with no Revit geometric acceptance or visual regression. Official area/capacity facts and estimates are in `docs/spec/CURRENT.md` under PDF authority. S02-specific implementation and QA values remain historical report/repository evidence.
- Run/resume/artifact pointers: `resume_note`, `study_ifc`, `study_dxf`, `study_pdf`, `canonical_target_path`, `canonical_target_status`, `canonical_target_exists`, `bim00_status`, `canonical_geometric_acceptance`, and `visual_regression_milestones`. The old note recorded P08-CAN-T07 as warning-pass after an R01 template checkpoint and BIM-00 PASS, then P08-CAN-T08 as BLOCKED_BY_TOOL because the only mapped Horizun mass route required indefinite arbitrary Python access rejected by automatic review; site/height inputs remained provisional. The old target was `revit/production/working/AMANDA-RUN-002-PAVILION-S02.rvt`, marked created from a clean template/existing, BIM-00 PASS, acceptance `BLOCKED_PENDING_R04`, and visual gates R04/R06/R08/R12/R13/R15 pending. The three study output fields were null. The report retains those old recovery facts; current routing and the no-Revit boundary are in `state/HANDOFF.md` and `docs/plan/CURRENT.md`. The target and its evidence were not altered by Task 6.
- Prior source/design/history references: `canonical_source_hashes`, `superseded_designs`, `historical_r12_checkpoint`, `historical_r12_checkpoint_sha256`, `historical_linear_study_ifc`, `historical_linear_study_dxf`, and `historical_linear_study_pdf`. The old three board hashes were `d7db84c0696f0018ed0bc0525bcc2128378d05ece8e3e5c09e2162493793de7b`, `12e35091f33352c21691eb083bf479ba2efd44af4c65774c89021b641de4a5c6`, and `80cdcccf99154d69ea87943950db420912e949d6320279695a2fd70d44ad286c`; they are stale as current authority. `AMANDA-RUN-001-S01` was superseded and its R12 archive/checkpoint hash was `ac814642296cbc7074603b703f8db20a63ae1c1475f435756a248516d1856e29`, with geometry reuse prohibited. The historical paths and study export/package pointers remain represented in the report, decision register, preserved source/evidence files, and Git history.

The old state also listed `REVIT_PIPE_SANDBOX_ACCESS:DEGRADING` and described P08-CAN-T08 as blocked by an unbounded provider route. That limitation remains historical evidence for S02 and was not carried into the recovery blocker list; P0 authorizes no provider or Revit action. State revision 173 was preserved. `PROJECT_STATE.yaml` now contains exactly the 14 schema-1 fields, phase `REPOSITORY_RECOVERY`, status `RUNNING`, `next_task: RECOVERY-VALIDATE`, null selected design/checkpoint/last verified commit, and the five recovery-plan blockers. No schema migration or model/design promotion occurred.

### Verification

- TDD RED: `& .\.venv\Scripts\python.exe -m pytest tests/unit/test_canonical_state_migration.py::test_project_state_is_repository_recovery_without_architectural_promotion -q` — 1 test, 0 passed, 1 failed as expected because the old YAML still said `PHASE_08`.
- GREEN compatibility: `& .\.venv\Scripts\python.exe -m pytest tests/unit/test_state_store.py tests/unit/test_status_dashboard.py tests/unit/test_canonical_state_migration.py -q` — 14 tests, 14 passed, 0 failed.
- Partial hygiene: `& .\.venv\Scripts\python.exe -m pytest tests/project/test_repository_hygiene.py -q` — 5 tests, 2 passed, 3 failed as expected pending Tasks 7–8. Remaining failures are the five superseded root documents, four tracked ZIPs, and not-yet-normalized board images. Current-document and stale-reference checks pass.
- Combined gate: `& .\.venv\Scripts\python.exe -m pytest tests/unit/test_state_store.py tests/unit/test_status_dashboard.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py -q` — 19 tests, 16 passed, 3 expected hygiene failures, 0 errors.
- `& .\.venv\Scripts\python.exe -m amanda_agent status` — exit 0; displayed `REPOSITORY_RECOVERY`, `RUNNING`, `RECOVERY-VALIDATE`, `PRE_R04`, no checkpoint, revision 173, and five blockers. It also reported writer lease `HELD` by `amanda-P08-CAN-T09-R03`; the lease was not reclaimed or changed. Recheck before any later BIM write.
- `git diff --check` on the Task 6 paths — passed (Git emitted only its normal LF-to-CRLF working-copy notices).
- No Revit/model action occurred. The pre-recovery commit baseline is preserved by the safety tag; the dirty working state is preserved in stash `2dbcacb34cd25e07cbed0672c818d797cb58f477`. `.recovery/` remains until final evidence transfer in Task 13.
