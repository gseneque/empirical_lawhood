# SPDX-License-Identifier: MPL-2.0
"""Edited population/design declarations retain whole original source censuses."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from tests.test_matrix_selected_e3_e4_bridge import selected_bridge, transfer  # noqa: F401 - disclosed fixture
from tests.test_matrix_selected_protected import unpublished


def smaller_bank(f, *, groups_per_family, confidence, wave_groups):
    by_family = {}
    for source in f.bank.sources:
        by_family.setdefault(source.root.root.family_id if hasattr(source.root.root, "family_id") else
            next(case.family_id for case in f.programme.cases if case.root_id == source.root_id), set()).add(source.root.root.independent_group_id)
    chosen = {group for groups in by_family.values() for group in sorted(groups)[:groups_per_family]}
    originals = tuple(value for value in f.bank.sources if value.root.root.independent_group_id in chosen)
    roots = {value.root_id for value in originals}
    # A smaller declared population has its own complete shared parents. Its
    # original coordinate, stream and assay bodies remain the exposed fixture's.
    allocation = replace(f.bank.reservation.allocation, allocation_id="allocation.selected-e4.edited",
        roots=tuple(value for value in f.bank.reservation.allocation.roots if value.root.root_id in roots),
        matched_scopes=tuple(replace(value,
            independent_group_ids=tuple(group for group in value.independent_group_ids if group in chosen))
            for value in f.bank.reservation.allocation.matched_scopes
            if chosen.intersection(value.independent_group_ids)))
    reservation = replace(f.bank.reservation, reservation_id="reservation.selected-e4.edited",
        allocation=allocation, publication=unpublished(allocation, "publication.selected-e4.edited-allocation"))
    selection = replace(f.bank.specification.selection, selection_id="selection.selected-e4.edited",
        reservation=r.identity(reservation))
    specification = replace(f.bank.specification, specification_id="specification.selected-e4.edited",
        selection=selection, publication=unpublished(selection, "publication.selected-e4.edited-selection"))
    index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification,
        provenances=f.bank.provenances)
    sources = tuple(index.reference(source_id=value.source_id, root_id=value.root_id, provenance=value.provenance)
        for value in originals)
    by_root = {value.root_id: index.resolve(value) for value in sources}
    protocols = []
    for original in f.bank.response_selection.protocols:
        source = by_root.get(original.public_source.root.root_id)
        if source is None:
            continue
        templates = replace(original.templates, source=source.identity, producers=(source.identity,))
        protocol = replace(original, public_source=ScheduledPublicSource.from_source(source), templates=templates)
        assert replace(protocol, public_source=original.public_source, templates=original.templates) == original
        assert templates.array_artifact == original.templates.array_artifact and templates.members == original.templates.members
        protocols.append(protocol)
    response = replace(f.bank.response_selection, allocation=r.identity(allocation), protocols=tuple(protocols),
        panels=tuple(value for value in f.bank.response_selection.panels if value[0] in chosen))
    design = replace(f.bank.design, record_id="design.selected-e4.edited", group_count=len(chosen),
        confidence=confidence, wave_group_count=wave_groups)
    bank = replace(f.bank, bank_id="bank.selected-e4.edited", reservation=reservation, specification=specification,
        sources=sources, design=design, forecast_design=replace(f.bank.forecast_design, allocation=r.identity(allocation)),
        response_selection=response, response_selection_publication=unpublished(response, "publication.selected-e4.edited-responses"))
    assert len(sources) == len(allocation.roots) == len(chosen) * 9
    assert allocation.coordinates == f.bank.reservation.allocation.coordinates
    assert allocation.exposure == f.bank.reservation.allocation.exposure
    assert (selection.numerical_design, selection.prefix_policies, selection.coordinate_policies) == (
        f.bank.specification.selection.numerical_design, f.bank.specification.selection.prefix_policies,
        f.bank.specification.selection.coordinate_policies)
    assert tuple(value.root for value in sources) == tuple(value.root for value in originals)
    assert tuple(value.provenance for value in sources) == tuple(value.provenance for value in originals)
    assert response.template_publications == f.bank.response_selection.template_publications
    index.require_roster(sources, expected_root_ids=tuple(value.root.root_id for value in allocation.roots))
    return bank


def test_declared_population_confidence_and_wave_selection_drive_complete_products(selected_bridge):  # noqa: F811
    f = selected_bridge
    bank = smaller_bank(f, groups_per_family=2, confidence=D(".9"), wave_groups=2)
    programme = r.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id="programme.selected-e4.edited")
    assert len(programme.group_ids) == 8 and len(programme.cases) == 72
    assert programme.confidence == D(".9") and all(len(wave.group_ids) <= 2 for wave in programme.waves)
    r.validate_development_bank(programme, bank)
    cases = tuple(r.SelectedE3E4CaseResult.unentered(case) for case in programme.cases)
    reduction = science.reduce_cases(programme, cases, record_id="reduction.selected-e4.edited")
    assert len(reduction.cases) == 72 and len(reduction.group_residuals) == 8
    assert reduction.design == programme.design
    with pytest.raises(ValueError):
        replace(reduction, cases=reduction.cases[:-1])
    with pytest.raises(ValueError):
        replace(programme, confidence=D(".95"))


@pytest.mark.parametrize("damage", ("groups", "confidence", "factor", "wave"))
def test_explicit_design_refuses_incomplete_or_unsupported_declarations(selected_bridge, damage):  # noqa: F811
    design = selected_bridge.bank.design
    with pytest.raises((TypeError, ValueError)):
        if damage == "groups":
            replace(design, group_count=design.group_count - 1)
        elif damage == "confidence":
            replace(design, confidence=D(1))
        elif damage == "factor":
            replace(design, factors=design.factors[:-1])
        else:
            replace(design, wave_group_count=0)


def test_preparation_census_is_derived_from_edited_programme_and_actual_output_ports(selected_bridge):  # noqa: F811
    from collections import Counter
    from pathlib import Path
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
    from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as public
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.runtime.artifacts import ArtifactProfile
    from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
    from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
    from tests.matrix_e4_structure_support import disclosed_structure
    from tests.test_matrix_selected_e3_e4_bridge import disclosed_operational_resources
    f = selected_bridge
    bank = smaller_bank(f, groups_per_family=2, confidence=D(".9"), wave_groups=2)
    programme = r.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id="programme.selected-e4.census")
    evidence = replace(f.evidence, programme=programme.identity)
    campaign = campaign_fixture()[0].campaign
    specification = public.SelectedE3E4ExperimentSpecification("experiment.selected-e4.census", programme.identity,
        bank.identity, evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(bank, budget=dict(disclosed_operational_resources().phase_budgets)["collect"]))
    artifacts = dict(owner.contracts(programme, bank, evidence.identity, len(evidence.canonical_bytes()), produced_input_parents=evidence.produced_input_parents, secondary_readout=f.secondary_readout)[4])
    files = {key: PreparedExperimentFile(value, "1.0.0", Path("/media/chevre/EL/empirical-lawhood/checks/disclosed-census-templates.npz"),
        value.size_bytes) for key, value in artifacts.items()}
    bound = public.bind_inputs(specification, {"programme": programme, "bank": bank, "evidence": evidence,
        "campaign": campaign, "resources": disclosed_operational_resources(), "secondary_readout": f.secondary_readout}, files=files)
    preparation = public.prepare(specification, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=1, environment_id="main-locked", source_snapshot=evidence.identity,
            output_root="/media/chevre/EL/empirical-lawhood/checks/disclosed-census"))
    assert preparation.executable
    assert dict(preparation.census.role_counts) == {"groups": 8, "sources": 72}
    assert preparation.census.role_counts == preparation.census.resolved_role_counts
    declarations = {row.capability_key: row for row in owner.operation_declarations()}
    phases, outputs, native = Counter(), Counter(), 0
    for operation in preparation.draft.operations:
        declaration = declarations[operation.selection.capability_key]
        phases[operation.selection.capability_key.rsplit(".", 1)[-1]] += 1
        native += int(declaration.execution_properties.native_effect)
        for output in declaration.outputs:
            outputs["array-products" if output.profile is ArtifactProfile.MATRIX_ARRAY_NPZ else "canonical-products"] += 1
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.full_factor_bindings import key
    count = len(programme.cases)
    phases.update({key(False, "measure"): count, key(False, "assess"): count, key(False, "reduce"): 1})
    outputs.update({key(False, "measure") + ".product": count, key(False, "assess") + ".product": count,
        key(False, "reduce") + ".product": 1, key(False, "measure") + ".arrays": count})
    assert sum(phases[key(False, phase)] for phase in ("measure", "assess", "reduce")) == 2 * count + 1
    assert dict(preparation.census.operation_counts) == dict(phases)
    assert dict(preparation.census.output_counts) == dict(outputs)
    assert preparation.census.native_effect_count == native
    public.validate_instance(specification=specification, allocation=preparation.allocation,
        draft=preparation.draft, source_records=preparation.design_records)
