from __future__ import annotations

from scripts.build_study_package import ORDER
from scripts.render_study_sheets import (
    STUDY_DRAWINGS,
    draw_floor,
    draw_implantation,
)


def test_pdf_study_package_contains_only_generated_canonical_plan_previews():
    assert tuple(name for name, _ in ORDER) == tuple(name for name, _ in STUDY_DRAWINGS)
    assert len(ORDER) == 3
    assert all("ESQUEMÁTICA" in title for _, title in ORDER)


def test_renderer_emits_all_canonical_blocks_and_two_admin_levels(
    canonical_layout, monkeypatch, tmp_path
):
    import scripts.render_study_sheets as renderer

    monkeypatch.setattr(renderer, "OUT", tmp_path)
    draw_implantation(canonical_layout)
    draw_floor(canonical_layout, 1)
    draw_floor(canonical_layout, 2)

    implant = (tmp_path / "01-implantacao.svg").read_text(encoding="utf-8")
    floor_01 = (tmp_path / "02-planta-pavimento-01.svg").read_text(encoding="utf-8")
    floor_02 = (tmp_path / "03-planta-pavimento-02.svg").read_text(encoding="utf-8")
    for block in canonical_layout.blocks:
        assert block.component_id in implant
    admin_l1 = next(
        room.logical_id
        for room in canonical_layout.rooms
        if room.component_id == "ADMIN_ACOLHIMENTO" and room.level == 1
    )
    admin_l2 = next(
        room.logical_id
        for room in canonical_layout.rooms
        if room.component_id == "ADMIN_ACOLHIMENTO" and room.level == 2
    )
    residential_l1 = next(
        room.logical_id
        for room in canonical_layout.rooms
        if room.component_id.startswith("RES_PAV_") and room.level == 1
    )
    assert admin_l1 in floor_01
    assert admin_l2 in floor_02
    assert residential_l1 not in floor_02
    assert all((tmp_path / (name + ".png")).is_file() for name, _ in STUDY_DRAWINGS)
    assert not any("elevacao" in name or "corte" in name for name, _ in STUDY_DRAWINGS)
