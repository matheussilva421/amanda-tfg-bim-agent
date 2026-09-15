"""Behavioural contract for the evidence-bound design profiles."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from amanda_agent.design.profiles import (
    ProfileProvisionalError,
    ProfileValidationError,
    check_capacity,
    load_profiles,
    select_profile,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "design-engine" / "config" / "profiles.yaml"


def test_canonical_profiles_have_the_three_service_shapes_and_auditable_sectors():
    catalog = load_profiles(PROFILE_PATH)

    assert {profile.id for profile in catalog.profiles} == {
        "ambulatorial",
        "internacao",
        "centro-dia",
    }
    assert catalog.max_simultaneous_people.value == 20
    assert len(catalog.citations) >= 1

    for profile in catalog.profiles:
        assert profile.label
        assert profile.citations
        assert profile.mandatory_requirements
        assert set(profile.adjacency_rules) == {"mandatory", "permitted", "undesired"}
        assert sum(
            sector.share_of_useful_area.value for sector in profile.sectors
        ) == pytest.approx(1.0)
        for sector in profile.sectors:
            assert sector.minimum_rooms.value >= 1
            assert sector.area_per_person_m2.value > 0
            assert sector.privacy_level in {"low", "medium", "high", "very_high"}
            for metric in (
                sector.share_of_useful_area,
                sector.minimum_rooms,
                sector.area_per_person_m2,
            ):
                assert metric.citation_id in {
                    citation.id for citation in profile.citations
                }


def test_provisional_profile_requires_an_explicit_opt_in():
    load_profiles(PROFILE_PATH)

    with pytest.raises(ProfileProvisionalError, match="provisional"):
        select_profile("ambulatorial")

    profile = select_profile("ambulatorial", allow_provisional=True)
    assert profile.id == "ambulatorial"
    assert check_capacity(profile, 20, allow_provisional=True) is True
    assert check_capacity(profile, 21, allow_provisional=True) is False


def test_capacity_rejects_invalid_people_counts():
    load_profiles(PROFILE_PATH)
    profile = select_profile("centro-dia", allow_provisional=True)

    with pytest.raises(ValueError, match="people"):
        check_capacity(profile, -1, allow_provisional=True)
    with pytest.raises(TypeError, match="people"):
        check_capacity(profile, True, allow_provisional=True)


def test_invalid_document_is_refused_before_it_becomes_active(tmp_path: Path):
    invalid = tmp_path / "profiles.yaml"
    invalid.write_text(
        """
schema_version: 1
max_simultaneous_people:
  value: 20
profiles:
  - id: broken
    label: Quebrado
    sectors:
      - id: atendimento
        label: Atendimento
        share_of_useful_area:
          value: 1.0
        minimum_rooms:
          value: 1
        privacy_level: high
        area_per_person_m2:
          value: 9.0
    mandatory_requirements: []
    adjacency_rules:
      mandatory: []
      permitted: []
      undesired: []
    citations: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ProfileValidationError):
        load_profiles(invalid)

    with pytest.raises(ProfileProvisionalError, match="provisional"):
        select_profile("ambulatorial", allow_provisional=False)


def test_unknown_profile_id_is_refused():
    load_profiles(PROFILE_PATH)

    with pytest.raises(KeyError, match="does-not-exist"):
        select_profile("does-not-exist", allow_provisional=True)


def test_profile_shares_must_account_for_the_complete_useful_area(tmp_path: Path):
    payload = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    payload["profiles"][0]["sectors"][0]["share_of_useful_area"]["value"] = 0.19
    invalid = tmp_path / "profiles.yaml"
    invalid.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ProfileValidationError, match="shares"):
        load_profiles(invalid)
