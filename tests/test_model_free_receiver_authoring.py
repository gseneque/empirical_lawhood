# SPDX-License-Identifier: MPL-2.0
"""Receiver-study admission controls on disclosed inputs and ordinary pytest storage."""

from copy import deepcopy
from dataclasses import replace
import json
import math

import pytest

from empirical_lawhood.api import model_free_matrix as api
from empirical_lawhood.domains.matrix.model_free import receiver_preparation
from empirical_lawhood.domains.matrix.model_free.confirmation import (
    validate_confirmation,
)
from empirical_lawhood.domains.matrix.model_free.receiver_campaign import REVISION
from empirical_lawhood.domains.matrix.model_free.receiver_population import CASE
from empirical_lawhood.domains.matrix.model_free.records import (
    RootAssignment,
    json_text,
)
from empirical_lawhood.domains.matrix.model_free.science import normalise_settings
from tests.test_model_free_authoring import (
    confirmation_settings,
    decoded,
    definition,
    parent_fixture,
)


def test_signed_endpoint_binds_operative_width_and_measured_parent(
    tmp_path, monkeypatch
):
    fixture = parent_fixture(tmp_path, monkeypatch)
    settings = confirmation_settings(fixture)
    settings["receiver_study"] = {"revision": REVISION, "instrument": None}
    record = settings["confirmation"]
    record["endpoints"] = [
        {
            "name": "M3.signed_response_contrast",
            "units": "actuator-normalized-response",
            "practical_effect": "0.0010",
        }
    ]
    record["independent_verification"] += ["COUPLED_H_H2_H4", "WITHHELD_FUTURE_SUFFIX"]
    settings = normalise_settings(settings)
    roots = tuple(
        RootAssignment(i, ("M1", "M3"), "confirmation") for i in range(100, 116)
    )
    result = validate_confirmation(settings, roots, parent_readout=fixture.result)
    assert (
        result["endpoint_effect_roles"][0]["operative_setting"]
        == "receiver_study.M3.signed_halfwidth"
    )
    assert not result["endpoint_effect_roles"][0]["automatic_success_granted"]
    with pytest.raises(ValueError, match="authenticated parent readout"):
        validate_confirmation(
            settings, roots, parent_readout={**fixture.result, "changed": True}
        )
    settings["confirmation"]["endpoints"][0]["practical_effect"] = "0.01"
    with pytest.raises(ValueError, match="implemented threshold"):
        validate_confirmation(settings, roots)
    settings["confirmation"]["endpoints"][0].update(
        practical_effect="0.001", units="physical-momentum"
    )
    with pytest.raises(ValueError, match="physical units"):
        validate_confirmation(settings, roots)


def test_exact_age_risk_feasibility_uses_the_analysis_tail_and_independent_roots(
    tmp_path, monkeypatch
):
    settings = confirmation_settings(parent_fixture(tmp_path, monkeypatch))
    settings["receiver_study"] = {"revision": REVISION, "instrument": None}
    settings["confirmation"]["independent_verification"].append(
        "SEGMENT_AND_PROTOCOL_AGE_DIAGNOSTICS"
    )
    settings["confirmation"]["endpoints"] = [
        {
            "name": "M2.common_future_wrong_decision",
            "units": "probability",
            "practical_effect": "0.10",
        }
    ]
    settings = normalise_settings(settings)
    roots = tuple(RootAssignment(i, ("M2",), "confirmation") for i in range(16))
    report = validate_confirmation(settings, roots)["memory_family_feasibility"]
    # One half of the module family, two tails, two coordinates and five predictors.
    tail = 0.05 * 0.125 / (4 * 2 * 5)
    assert report["per_tail_alpha"] == pytest.approx(tail)
    assert report["upper_risk_with_zero_errors_and_complete_paths"] == pytest.approx(
        1 - tail ** (1 / 16)
    )
    minimum = math.ceil(math.log(tail) / math.log(0.9))
    assert report["minimum_independent_roots_if_all_correct"] == minimum
    settings["confirmation"]["precision_goal"] = "TASK_EQUIVALENCE_IF_CERTIFIED"
    with pytest.raises(ValueError, match="zero errors"):
        validate_confirmation(settings, roots)
    sufficient = tuple(
        RootAssignment(i, ("M2",), "confirmation") for i in range(minimum)
    )
    assert validate_confirmation(settings, sufficient)["power_established"] is False


@pytest.mark.parametrize("key", sorted(receiver_preparation.ORIGINAL_IDENTITY))
def test_each_original_instrument_identity_is_required_before_array_decoding(key):
    supplied = {
        **receiver_preparation.ORIGINAL_IDENTITY,
        key: "f" * 64,
        "physical_design": "",
        "template_hex": "",
        "template_members": {},
    }
    with pytest.raises(
        ValueError, match="another original packet, study or physical design"
    ):
        receiver_preparation.instrument_operands(supplied)


def test_retained_common_future_keeps_original_arrays_coordinates_and_clock(
    tmp_path, monkeypatch
):
    fixture = parent_fixture(tmp_path, monkeypatch)
    settings = normalise_settings(
        {
            **fixture.parent.settings,
            "receiver_study": {"revision": REVISION, "instrument": None},
        }
    )
    roots = [(20, ("M2",), "development")]

    def create(name, selected):
        path = definition(tmp_path, roots, selected, name=name + ".json")
        return api.create_reanalysis_inputs(
            definition_path=path,
            project_root=tmp_path,
            output_directory=tmp_path / name,
            parent_directory=fixture.parent_dir,
            parent_service=fixture.service,
        )

    result = create("original", settings)
    retained = decoded(tmp_path / "original" / "specification.json")
    assert (
        result["parent_authentication_performed"]
        and not result["native_acquisition_performed"]
    )
    assert retained.parent_lineage.parent_specification == fixture.parent.identity
    (array,) = retained.retained_arrays
    assert (
        tmp_path / "original" / (array.key + ".bin")
    ).read_bytes() == fixture.raw_arrays[array.identity.artifact_id]
    dropped = deepcopy(settings)
    dropped["receiver_study"]["M2"]["coordinates"] = ["nominal"]
    with pytest.raises(ValueError, match="every originally acquired coordinate"):
        create("dropped", dropped)
    changed = deepcopy(settings)
    changed["native"]["timestep"] = "0.002"
    with pytest.raises(ValueError, match="acquisition setting: native"):
        create("clock", changed)
    assert not (tmp_path / "dropped").exists() and not (tmp_path / "clock").exists()


@pytest.fixture
def signed_benchmark(tmp_path, monkeypatch):
    # The fake instrument isolates the benchmark authority boundary. Its real
    # identity guard is exercised separately above. No native call is allowed.
    instrument = {"fixture": "synthetic source for the admission boundary"}

    def fixture_instrument(selection):
        assert selection == instrument

    monkeypatch.setattr(receiver_preparation, "instrument_operands", fixture_instrument)
    settings = normalise_settings(
        {
            "population": {"frame_size": 4, "audit_size": 2},
            "receiver_study": {
                "revision": REVISION,
                "instrument": instrument,
                "M1": {"structural_service": False},
                "M5": {"sparse_use": "DISJOINT_DEVELOPMENT_AUDIT"},
            },
        }
    )
    parent = api.specification_for(
        "Disclosed signed benchmark fixture",
        tuple(RootAssignment(i, ("M1", "M5")) for i in range(1, 5)),
        settings,
    )
    fixture = parent_fixture(tmp_path, monkeypatch, parent=parent)
    rows, key, product = next(
        (records, name, item)
        for records in fixture.products["records"].values()
        for name, item in records.items()
        if item.config.phase == "synthesise" and item.config.module == "M5"
    )
    exact = {
        "status": "ESTIMATED",
        "full_frame_benchmark": {
            "status": "ENUMERATED",
            "missing_frame_indices": [],
            "full_frame_mean": 0.2,
            "actual_native_calls_omitted": 0,
        },
    }
    assigned = [r.seed for r in parent.assignments]
    summary = {
        "receiver_revision": REVISION,
        "signed_receiver": CASE,
        "acquisition_mode": "reveal_all",
        "root_seeds": assigned,
        "assigned_root_seeds": assigned,
        "sampled_root_seeds": [r.seed for r in parent.assignments if r.audit_selected],
        "frame_size": 4,
        "assigned_roots": 4,
        "assigned_cases": 4,
        "audit_size": 2,
        "decision": "MODELED_SAVING",
        "economically_supported_sparse_delivery": True,
        "economically_supported_suppliers": {
            "auxiliary": False,
            "one_coefficient": True,
        },
        "finite_frame_comparisons": {
            name: deepcopy(exact) for name in ("auxiliary", "one_coefficient", "zero")
        },
    }

    def publish(name, use="DISJOINT_DEVELOPMENT_AUDIT", supplier="auxiliary"):
        payload = {
            "schema": "matrix-model-free-synthesis.v1",
            "module": "M5",
            "modules": {"M5": summary},
        }
        rows[key] = replace(product, payload_json=json_text(payload))
        request = deepcopy(settings)
        request["population"]["mode"] = "sparse"
        request["receiver_study"]["M5"].update(sparse_use=use, sparse_supplier=supplier)
        path = definition(
            tmp_path,
            [(i, ("M1", "M5"), "development") for i in range(101, 105)],
            request,
            name=name + ".json",
        )
        return api.create_population_deployment_inputs(
            definition_path=path,
            project_root=tmp_path,
            output_directory=tmp_path / name,
            parent_directory=fixture.parent_dir,
            parent_service=fixture.service,
        )

    return summary, publish


def test_disjoint_scientific_audit_and_economic_use_charge_the_specific_supplier(
    tmp_path, signed_benchmark
):
    _, publish = signed_benchmark
    assert publish("development")["parent_authentication_performed"]
    with pytest.raises(ValueError, match="Economic sparse delivery"):
        publish("expensive", "ECONOMIC_DELIVERY", "auxiliary")
    assert not (tmp_path / "expensive").exists()
    assert publish("eligible", "ECONOMIC_DELIVERY", "one_coefficient")[
        "parent_authentication_performed"
    ]
    readout = json.loads(
        (tmp_path / "eligible" / "population-benchmark.json").read_bytes()
    )
    assert (
        readout["sparse_supplier"] == "one_coefficient"
        and readout["benchmark_supports_selected_supplier"]
    )


@pytest.mark.parametrize("damage", ["sample", "frame", "receiver", "missing_outcome"])
def test_reveal_all_gate_refuses_changed_srs_census_receiver_or_missing_native(
    tmp_path, signed_benchmark, damage
):
    summary, publish = signed_benchmark
    if damage == "sample":
        summary["sampled_root_seeds"] = [
            s for s in summary["root_seeds"] if s not in summary["sampled_root_seeds"]
        ]
    elif damage == "frame":
        summary["assigned_root_seeds"] = [1, 2, 3, 99]
    elif damage == "receiver":
        summary["signed_receiver"] = "different-horizon-or-port"
    else:
        summary["finite_frame_comparisons"]["zero"]["full_frame_benchmark"][
            "missing_frame_indices"
        ] = [2]
    with pytest.raises(ValueError, match="Reveal-all"):
        publish("refused")
    assert not (tmp_path / "refused").exists()
