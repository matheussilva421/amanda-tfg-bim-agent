from pathlib import Path

from amanda_agent.bim.checkpoints import CheckpointManager


root = Path(__file__).resolve().parent
source = root / "revit" / "lab" / "custom-api" / "LAB_CUSTOM_WALL.rvt"
target = root / "revit" / "lab" / "custom-api" / "T18_LAST_PASS.rvt"
manifest = root / "revit" / "lab" / "custom-api" / "T18_LAST_PASS.rvt.manifest.json"

record = CheckpointManager().create_checkpoint(
    source,
    target,
    stage="P02-T16_PASS",
    manifest_path=manifest,
    save_state="STABLE",
    source_stable=True,
    reopen_verify=True,
    provenance={
        "source_result": "tool-lab/custom-api/results/t16-host-create.json",
        "source_outcome": "PASS",
        "purpose": "P02-T18 crash/recovery disposable checkpoint",
    },
    writable_roots=[target.parent],
)

print(record.model_dump_json(indent=2))
print(f"verified={record.verify()}")
