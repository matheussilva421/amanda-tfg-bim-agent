from __future__ import annotations

from shapely.geometry import box

from amanda_agent.design.generate import canonical_geometry_hash, generate_designs

REQUIREMENTS = {
    "sectors": [
        {"logical_id": "public", "spaces": [{"target_area_m2": 50, "quantity": 1}]},
        {"logical_id": "controlled", "spaces": [{"target_area_m2": 50, "quantity": 1}]},
        {"logical_id": "residential", "spaces": [{"target_area_m2": 50, "quantity": 1}]},
    ]
}


def test_generation_repeats_geometry_hashes_for_same_seed_list():
    first = generate_designs(REQUIREMENTS, box(0, 0, 30, 20), run_id="RUN-A", seeds=[2, 5, 8])
    second = generate_designs(REQUIREMENTS, box(0, 0, 30, 20), run_id="RUN-B", seeds=[2, 5, 8])

    assert [item.geometry_hash for item in first.candidates] == [item.geometry_hash for item in second.candidates]
    assert [item.seed for item in first.candidates] == [2, 5, 8]
    assert first.candidate_count == len({item.geometry_hash for item in first.candidates})


def test_canonical_hash_excludes_run_id_and_volatile_fields():
    left = {"run_id": "A", "geometry": {"x": 1.00000004}, "duration_s": 4}
    right = {"run_id": "B", "geometry": {"x": 1.00000001}, "duration_s": 99}

    assert canonical_geometry_hash(left) == canonical_geometry_hash(right)


def test_configured_seed_list_explores_more_than_one_optimum_and_deduplicates():
    result = generate_designs(REQUIREMENTS, box(0, 0, 30, 20), run_id="RUN-C", seeds=[1, 2, 3, 4])

    assert result.generated_count == 4
    assert result.candidate_count >= 2
    assert result.candidate_count == len({item.geometry_hash for item in result.candidates})
