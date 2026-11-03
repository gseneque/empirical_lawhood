# SPDX-License-Identifier: MPL-2.0
"""Exact selected nested revisions; exposed operands grant no native admission."""

from dataclasses import fields
import json

import pytest

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as preparation
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import (
    control_contracts, nve_contracts, nve_roster, nve_science,
)
from empirical_lawhood.adapters.methods.rubisco_insilico_sampling.nve_preparation_admission import (
    SerializedPreparationNVEControlPlan, decode_plan,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from tests.test_rubisco_nve_durable_controls import staged as staged, plan as plan
from tests.test_rubisco_serialized_durable_chemical_admission import (
    durable_admitted as durable_admitted, reuse_admitted as reuse_admitted, original as original,
)


@pytest.fixture(params=("reuse", "durable"))
def selected_plan(request, staged, reuse_admitted, durable_admitted):
    old, _ = staged
    chemical = reuse_admitted.plan if request.param == "reuse" else durable_admitted.plan
    kwargs = {field.name: getattr(old, field.name) for field in fields(nve_contracts.NVEControlPlan)}
    kwargs["chemical_controls"] = chemical
    selected = chemical.selected_assets[0][0]
    key = next(row for row in preparation.model_roster() if control_contracts.model_id(row) == selected)
    kwargs["admitted_parents"] = ((selected, *old.admitted_parents[0][1:]),)
    kwargs["selected_cases"] = ((*key, *old.selected_cases[0][3:]),)
    return SerializedPreparationNVEControlPlan(**kwargs)


def test_canonical_nested_revisions_roundtrip_without_changing96_48_science(selected_plan, original):
    row = selected_plan
    raw = row.canonical_bytes()
    assert decode_plan(raw.decode()) == row
    assert decode_canonical_bytes(raw, SerializedPreparationNVEControlPlan, maximum_bytes=len(raw)) == row
    # The old declared type genuinely refused this revision; no widening occurs.
    with pytest.raises(ValueError):
        decode_canonical_bytes(raw, nve_contracts.NVEControlPlan, maximum_bytes=len(raw))
    result = nve_science.assess_nve(row, (), (), current_raw_root="/tmp/exposed-never-entered")
    assert len(result.cases) == 96 and len(result.refinements) == 48
    assert result.disposition is A.UNEVALUABLE
    assert len(row.full_census) == 96 and row.physical_independent_units == 0
    sources = (row.chemical_controls.identity, row.chemical_controls.source,
        *(identity for joined in row.admitted_parents for identity in joined[1:]))
    parent = original.supply.definition.parent_contact
    definitions = nve_roster.definitions(row, parent, sources=sources,
        input_materialization_ids=parent.input_materialization_ids)
    assert len(definitions) == 97


@pytest.mark.parametrize("change", ("nested-version", "outer-version", "full-census", "cases", "chemical-fields"))
def test_changed_nested_revision_or_complete_census_is_refused(selected_plan, change):
    document = json.loads(selected_plan.canonical_bytes())
    if change == "nested-version": document["value"]["chemical_controls"]["version"] = "1.0.0"
    if change == "outer-version": document["version"] = "1.0.0"
    if change == "full-census": document["value"]["full_census"] = document["value"]["full_census"][:-1]
    if change == "cases": document["value"]["selected_cases"] = []
    if change == "chemical-fields": document["value"]["chemical_controls"]["value"].pop("preparation_plan")
    with pytest.raises(ValueError):
        decode_plan(json.dumps(document, sort_keys=True, separators=(",", ":")))


def test_original_nve_route_retains_exact_old_type_and_bytes(staged):
    old, _ = staged
    before = old.canonical_bytes()
    assert type(decode_plan(before.decode())) is nve_contracts.NVEControlPlan
    assert old.canonical_bytes() == before
    with pytest.raises(ValueError):
        SerializedPreparationNVEControlPlan(**{field.name: getattr(old, field.name)
            for field in fields(nve_contracts.NVEControlPlan)})
    assert type(old.chemical_controls) is control_contracts.ChemicalForcePlan


def test_selected_decoder_is_used_at_actual_child_operand_boundary(selected_plan, monkeypatch):
    """Exercise the selected decoder, then stop before native prerequisites."""
    from types import SimpleNamespace
    from empirical_lawhood.adapters.methods.rubisco_insilico_sampling import (
        nve_native_entry, nve_preparation_admission,
    )

    class DecodedOperand(Exception):
        pass

    decoded = []

    def capture(raw):
        decoded.append(decode_plan(raw))
        raise DecodedOperand

    monkeypatch.setattr(nve_preparation_admission, 'decode_plan', capture)
    with pytest.raises(DecodedOperand):
        nve_native_entry._authenticated_child(
            SimpleNamespace(parent_contact=object()),
            {'plan': selected_plan.canonical_bytes().decode()},
        )
    assert decoded == [selected_plan]
