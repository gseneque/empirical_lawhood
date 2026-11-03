# SPDX-License-Identifier: MPL-2.0
"""Bounded public preparation metadata census; no native or protected effects."""

from collections import Counter
from pathlib import Path
import json

from empirical_lawhood.api.experiment_preparation import load_experiment_inputs, prepare_experiment
from empirical_lawhood.infrastructure import bounded_io
from empirical_lawhood.kernel.experimental_design import UnitAllocation
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
from tests.test_matrix_experiment_methods import fixture, selected_input_records
from tests.test_matrix_experiment_specification import PROTOCOL, execution


def embedded_allocations(document):
    if isinstance(document, dict):
        return int(document.get("schema") == UnitAllocation.SCHEMA) + sum(embedded_allocations(value) for value in document.values())
    if isinstance(document, (list, tuple)):
        return sum(embedded_allocations(value) for value in document)
    return 0


def test_public_preparation_retains_one_roster_and_reports_named_scope_scaling(tmp_path, monkeypatch):
    observed = []
    for selected64 in (False, True):
        counts = (64, 64, 64) if selected64 else (12, 20, 8)
        specification, source_inputs, _, method_inputs = fixture(selected64=selected64,
            train_count=counts[0], cal_count=counts[1], eval_count=counts[2],
            minimum_usable=58 if selected64 else 8)
        directory = tmp_path / ("selected64" if selected64 else "alternative12-20-8")
        directory.mkdir()
        bindings = []
        for index, (key, record) in enumerate(sorted(selected_input_records(source_inputs, method_inputs).items())):
            payload = record.canonical_bytes()
            path = directory / (str(index) + ".json")
            path.write_bytes(payload)
            bindings.append(ExperimentInputBinding(key, ObjectIdentity.from_record("fixture.scaling." + key, record), path.name, len(payload)))
        selection = ExperimentInputSelection("fixture.scaling.matrix-source-selection", "matrix.response-error.origin-only", tuple(bindings))
        selection_path = directory / "sources.json"
        selection_path.write_bytes(selection.canonical_bytes())
        counters = Counter()
        read = bounded_io.read_bounded_bytes
        validate = UnitAllocation.__post_init__
        unit_ids = UnitAllocation.unit_ids
        unit = UnitAllocation.unit

        def counted_read(path, **kwargs):
            payload = read(path, **kwargs)
            counters["bounded_input_read_calls"] += 1
            counters["bounded_input_read_bytes"] += len(payload)
            return payload

        def counted_validation(allocation):
            counters["allocation_validation_calls"] += 1
            counters["allocation_unit_validation_visits"] += len(allocation.units)
            counters["allocation_role_validation_visits"] += len(allocation.roles)
            return validate(allocation)

        def counted_unit_ids(allocation, role=None):
            counters["unit_ids_projection_calls"] += 1
            counters["unit_ids_role_row_visits"] += len(allocation.roles)
            return unit_ids(allocation, role)

        def counted_unit(allocation, unit_id):
            counters["binary_unit_lookup_calls"] += 1
            return unit(allocation, unit_id)

        with monkeypatch.context() as instrumentation:
            instrumentation.setattr(bounded_io, "read_bounded_bytes", counted_read)
            instrumentation.setattr(UnitAllocation, "__post_init__", counted_validation)
            instrumentation.setattr(UnitAllocation, "unit_ids", counted_unit_ids)
            instrumentation.setattr(UnitAllocation, "unit", counted_unit)
            resolved = load_experiment_inputs(specification, selection_path)
            preparation = prepare_experiment(specification, scientific_inputs=resolved.scientific_inputs,
                execution=execution(), protocol_bytes=PROTOCOL, method_inputs=resolved.method_inputs)
        assert preparation.executable and not preparation.dependencies
        draft = preparation.draft
        allocation = preparation.allocation
        allocation_inputs = tuple((key, record) for key, record in preparation.input_records if type(record) is UnitAllocation)
        config_documents = tuple(json.loads(operation.config_payload) for operation in draft.operations)
        assert len(allocation_inputs) == 1 and allocation_inputs[0][1] == allocation
        assert embedded_allocations(draft.to_document()) == 0
        assert all(embedded_allocations(document) == 0 for document in config_documents)
        assert counters["bounded_input_read_calls"] == 13
        config_sizes = tuple(len(operation.config_payload.encode()) for operation in draft.operations)
        observed.append({
            "selection": "selected64" if selected64 else "alternative12-20-8",
            "role_counts": dict(preparation.census.role_counts),
            "whole_unit_count": len(allocation.units), "operation_count": len(draft.operations),
            "external_input_count": len(preparation.input_records),
            "specification_bytes": len(specification.canonical_bytes()),
            "allocation_bytes": len(allocation.canonical_bytes()),
            "draft_bytes": len(draft.canonical_bytes()),
            "external_input_bytes": sum(len(record.canonical_bytes()) for _, record in preparation.input_records),
            "config_bytes": sum(config_sizes), "maximum_config_bytes": max(config_sizes),
            "minimum_config_bytes": min(config_sizes),
            "embedded_allocation_rosters_in_draft_and_configs": 0,
            "allocation_rosters_in_derived_inputs": len(allocation_inputs),
            "measured_traversals": dict(sorted(counters.items())),
            "specification_sha256": specification.fingerprint(),
            "allocation_sha256": allocation.fingerprint(), "draft_sha256": draft.fingerprint(),
        })
    assert [row["operation_count"] for row in observed] == [61, 261]
    assert [row["external_input_count"] for row in observed] == [60, 260]
    assert observed[1]["maximum_config_bytes"] - observed[0]["maximum_config_bytes"] < 128
    report = {
        "scope": "Public canonical input-selection loading and pure experiment preparation; counters exclude fixture construction, recursive custody authoring, workers, native effects and uninstrumented nested record validation.",
        "traversal_definition": "Allocation validation visits count its complete unit and role loops; unit_ids visits count its complete role projection. Bounded reads count actual generic source-loader reads. Binary unit lookups count calls; comparisons inside the shared logarithmic lookup are not instrumented.",
        "standing": "EXPOSED_CONFORMANCE_NONPROMOTABLE", "qualification": "NOT_ESTABLISHED",
        "wider_a04_closure": False, "cases": observed,
    }
    report_path = Path(tmp_path).parent / "matrix-e3-authoring-scaling.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
