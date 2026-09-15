from __future__ import annotations

from amanda_agent.design.archetypes import (
    ArchetypeName,
    exploration_archetypes,
    generate_macro_seed,
    load_archetypes,
)
from amanda_agent.design.geometry import contains, validate_polygon

SITE = [(0, 0), (60, 0), (60, 40), (0, 40), (0, 0)]


def test_all_named_archetypes_are_configuration_driven():
    configurations = load_archetypes()

    assert set(configurations) == {name.value for name in ArchetypeName}
    assert all(
        configurations[name.value]["initialization"]
        and configurations[name.value]["relationships"]
        for name in ArchetypeName
    )


def test_each_archetype_produces_a_valid_macro_seed_inside_a_rectangular_site():
    for name in ArchetypeName:
        macro = generate_macro_seed(name, SITE, seed=17)

        assert macro.archetype is name
        assert macro.seed == 17
        assert macro.valid is True
        for sector in macro.sectors:
            polygon = validate_polygon(sector["geometry"])
            assert contains(SITE, polygon)


def test_same_seed_is_reproducible_and_exploration_does_not_force_a_winner():
    first = generate_macro_seed(ArchetypeName.COURTYARD, SITE, seed=23)
    second = generate_macro_seed(ArchetypeName.COURTYARD, SITE, seed=23)

    assert first.model_dump() == second.model_dump()
    assert set(exploration_archetypes()) == {
        ArchetypeName.COURTYARD,
        ArchetypeName.CLUSTER,
        ArchetypeName.PRIVACY_GRADIENT,
    }
    assert first.selected is None
