# SPDX-License-Identifier: MPL-2.0
"""Exposed compiler fixtures only; no protected science or qualification.

The complete 64-by-nine population below is synthetic metadata. Its toy
streams, custody descriptors and qualification records are not admissible
evidence, and no author/issue/reveal/native operation is performed.
"""

from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import programme_factorial_confirmation as phase
from empirical_lawhood.adapters.methods.matrix_scheduled_history import protected_factorial_preparation as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_factorial_confirmation_composition import lower_factorial_confirmation
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_inputs import (
    ProtectedFactorialOriginalSource, ProtectedFactorialPreparationSelection,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.protected_factorial_specification import (
    ProtectedFactorialAcquisitionRoster, ProtectedFactorialExperimentSpecification,
)
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_entry import StudyDefinition
from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
from empirical_lawhood.planning.study_authoring import DesignInputRole, SourceMaterializationRole
from empirical_lawhood.planning.study_issue import ImplementationSourceClosure
from empirical_lawhood.runtime.candidate_compiler import StandardCandidateCompilationContext, compile_study_candidate
from empirical_lawhood.runtime.execution_envelope import (
    ChildResourceTokenLimit, ExecutionResourceEnvelopeSpec, ExecutionResourceTaskCellSpec, NonTimeResourceBudget,
)
from empirical_lawhood.runtime.experiment_preparation import DependencyKind, ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
from tests.experiment_entry_support import entry_package_for_draft
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
from tests.test_matrix_programme_factorial_confirmation import _pin
from tests.test_matrix_programme_factorial_confirmation_seal import (
    _binding, _catalog, _qualified_projection, selected as seal_selected,  # noqa: F401
)
from tests.test_matrix_programme_factorial_confirmation import criteria as criteria
from tests.test_matrix_scheduled_programme_reduction import declared as declared
from tests.test_matrix_scheduled_history import scheduled as tiny_scheduled, CONSTRUCTION  # noqa: F401
from tests.test_matrix_factor_confirmation_eligibility import stock as stock, provenance as provenance


@pytest.fixture
def selected(seal_selected, tiny_scheduled, tmp_path):  # noqa: F811
    """Build actual typed metadata joins; explicitly no scientific authority."""
    seed = seal_selected
    _, tiny = tiny_scheduled
    template = tiny[0]
    programme = seed.config.programme
    coordinates, roots, cases, scopes = {}, [], [], []
    for group_index, group in enumerate(programme.group_ids):
        rows = tuple(row for row in programme.cases if row.independent_group_id == group)
        streams = tuple(MatrixHistorySeed(purpose, sha256(("EXPOSED.protected-software." + group + purpose).encode()).hexdigest())
            for purpose in HISTORY_PURPOSES)
        coordinate_refs = []
        for index, case in enumerate(rows):
            key = "coordinate.exposed.protected." + case.family_id + "." + str(index)
            bath, friction, coupling = case.factor_values
            coordinate = replace(template.coordinate, coordinate_id=key, family_id=case.family_id, clock_id="synthetic.clock",
                member=replace(template.coordinate.member, member_id="member." + key, cross_coupling_gamma=coupling),
                primary_view=replace(template.coordinate.primary_view, view_id="primary." + key,
                    bath_temperature=bath, friction_gamma=friction),
                fine_view=replace(template.coordinate.fine_view, view_id="fine." + key,
                    bath_temperature=bath, friction_gamma=friction))
            coordinates[key] = coordinate
            pin = coordinate_identity(coordinate)
            coordinate_refs.append(pin)
            root = MatrixProgrammeRoot(case.root_id, group, "regime." + key, key,
                MatrixProgrammeRole.CONFIRMATION, coordinate.clock_id)
            roots.append(scheduled.ScheduledRoot(root, pin, streams))
            cases.append(replace(case, coordinate=pin, streams_sha256=sha256(canonical_json_bytes(streams)).hexdigest()))
        scopes.append(scheduled.ScheduledMatchedScope("scope.exposed.protected." + str(group_index).zfill(2),
            MatrixProgrammeRole.CONFIRMATION, (group,), tuple(sorted(coordinate_refs, key=lambda row: row.object_id)), CONSTRUCTION))
    allocation = scheduled.ScheduledAllocation("allocation.exposed.protected-factorial",
        tuple(sorted(coordinates.values(), key=lambda row: row.coordinate_id)), tuple(roots), tuple(scopes), template.allocation.exposure)
    programme = replace(programme, allocation=scheduled.identity(allocation), cases=tuple(cases))
    statistics = replace(seed.config.specification, programme=programme.identity)
    config = replace(seed.binding.record.configuration, config_id="config." + phase.freeze_node_id(statistics),
        programme=programme, specification=statistics)
    frozen = replace(seed.binding.record, configuration=config, sampling_requirement=phase.protected_sampling_requirement(statistics))
    binding = _binding(frozen)
    changed = {seed.config.programme.identity: programme.identity, seed.config.programme.allocation: programme.allocation,
        seed.config.specification.identity: statistics.identity, seed.binding.record.identity: frozen.identity,
        ObjectIdentity.from_record(seed.binding.receipt.receipt_id, seed.binding.receipt):
            ObjectIdentity.from_record(binding.receipt.receipt_id, binding.receipt), seed.binding.identity: binding.identity}
    designs = tuple(replace(row, object_identity=changed.get(row.object_identity, row.object_identity),
        materialization_sha256=changed.get(row.object_identity, row.object_identity).object_fingerprint) for row in seed.root.design_inputs)
    root = replace(seed.root, design_inputs=designs)
    study = StudyDefinition("study.exposed.original.protected-factorial", root, entry_package_for_draft(root))
    roster = ProtectedFactorialAcquisitionRoster("roster.exposed.original.acquisition", seed.config.acquisitions)
    original = ProtectedFactorialOriginalSource("source.exposed.original.protected-factorial", study, binding, roster, allocation)
    spec = ProtectedFactorialExperimentSpecification("specification.exposed.protected-factorial",
        ObjectIdentity.from_record(study.package_id, study), binding.identity, roster.identity, root.question)
    lowered = lower_factorial_confirmation(root=root, criteria=binding, acquisitions=roster.acquisitions,
        bank_artifact=seed.bank, operational_budget=seed.lowered.draft.operations[0].resource_budget)
    lowered, qualifications = _qualified_projection(SimpleNamespace(lowered=lowered, config=config))
    configs = tuple(sorted((SourceMaterializationConfig("source-config.exposed." + str(index), external.input_id,
        SourceMaterializationRole.OBSERVATION_STREAM, external.expected_content_sha256, external.maximum_size_bytes,
        external.maximum_size_bytes, external.payload_schema, external.media_type, SourceReadMode.ORDINARY_BOUNDED,
        external.outcome_access, external.visibility_ceiling) for index, external in enumerate(lowered.external_inputs)),
        key=lambda row: row.fingerprint()))
    formal = _standard_fixture()[1]
    inventory = replace(formal.source_inventories[0], denominator_id=root.system.system_id,
        evidence_world=study.entry_package.checklist.portfolio_world,
        source_materializations=tuple(sorted((row.materialization for row in lowered.prospective_draft.source_materializations),
            key=lambda row: row.object_id)), independent_unit_ids=programme.group_ids,
        denominator_inapplicable_gap_ids=tuple(row.gap_id for row in study.entry_package.register.gaps))
    coverage = replace(study.entry_package.coverage, denominator_id=root.system.system_id,
        applicability=derive_formal_gap_applicability(study.entry_package.register, inventory))
    entry = replace(study.entry_package, coverage=coverage, checklist=replace(study.entry_package.checklist,
        formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage)))
    study = replace(study, entry_package=entry)
    original = replace(original, study=study)
    spec = replace(spec, original_study=ObjectIdentity.from_record(study.package_id, study))
    nodes = tuple(sorted((phase.assess_node_id(statistics), phase.input_seal_node_id(statistics))))
    budget = NonTimeResourceBudget("budget.exposed.protected", 1, 256 * 1024**2, 64 * 1024**2, 10, 64 * 1024**2)
    cells = tuple(ExecutionResourceTaskCellSpec("cell." + node, node, "child.exposed.protected", None, None,
        1, 0, 0, False, budget, None, None, None) for node in nodes)
    resources = ExecutionResourceEnvelopeSpec("resources.exposed.protected",
        _pin("extensions.exposed.unissued", "empirical-lawhood/runtime/issued-extension-set"), cells,
        (ChildResourceTokenLimit("child.exposed.protected", 0, 0),), (), (), (), None, None, 1, 256 * 1024**2,
        (), (), "a" * 64, True, True, True, True)
    selection = ProtectedFactorialPreparationSelection("selection.exposed.protected", seed.bank,
        seed.lowered.draft.operations[0].resource_budget, formal.formal_methods, (inventory,), qualifications, configs, resources)
    files = {"bank": PreparedExperimentFile(seed.bank, programme.bank.object_version, tmp_path / "original-bank.json", seed.bank.size_bytes)}
    return SimpleNamespace(original=original, specification=spec, selection=selection, files=files, directory=tmp_path)


def _derive(selected, **changes):
    return owner.derive_protected_factorial_experiment(changes.get("specification", selected.specification),
        changes.get("original", selected.original), changes.get("selection", selected.selection))


def test_complete_original_population_derives_two_operations_without_outcome_io(selected, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, "read_bytes", lambda *args, **kwargs: pytest.fail("preparation read outcomes"))
    original_bytes = selected.original.canonical_bytes()
    allocation, draft, records, spec = _derive(selected)
    assert len(allocation.units) == 64 and all(not row.exposed for row in allocation.units)
    assert len(draft.operations) == 2 and len(draft.links) == 9
    assert draft.prospective_draft.evaluation_unit_ids == allocation.unit_ids("confirmation")
    assert len(draft.prospective_draft.experiment.information_cutoffs) == 576
    assert spec.qualified_parent_bindings == () and draft.contribution_parents == ()
    assert selected.original.criteria.record.configuration.qualified_parent.binding is not None
    assert len(records) == 3 and selected.original.canonical_bytes() == original_bytes
    assert decode_canonical_bytes(selected.specification.canonical_bytes(), ProtectedFactorialExperimentSpecification,
        maximum_bytes=None) == selected.specification


def test_actual_compiler_and_standard_candidate_accept_derived_metadata_only(selected):
    allocation, draft, _, prospective = _derive(selected)
    registrations, registry, codecs = _catalog()
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="d" * 40, qualifications=prospective.qualifications,
        known_design_inputs=prospective.known_design_inputs, output_codecs=codecs)
    assert compilation.candidate_report.candidate is not None, compilation.candidate_report.diagnostics
    context = StandardCandidateCompilationContext("context.exposed.protected", compilation.candidate_context,
        prospective.formal_methods, prospective.formal_source_inventories)
    study = StudyDefinition("study.exposed.derived", compilation.candidate_draft, prospective.entry_package)
    from tests.runtime_platform.test_candidate_compiler import _materialization
    report = compile_study_candidate(authoring_package=study, authoring_materialization=_materialization(), context=context)
    assert report.candidate is not None, [(row.code, row.field_path, row.message) for row in report.diagnostics]
    owner.validate_protected_factorial_experiment_instance(specification=selected.specification, allocation=allocation,
        draft=draft, source_records=tuple(sorted(((selected.original.source_id, selected.original),
            (selected.selection.selection_id, selected.selection)))))


def test_preparation_discloses_software_dependencies_and_warrant_assessment_limitation(selected):
    resolved = owner.bind_protected_factorial_experiment_inputs(selected.specification,
        {"original": selected.original, "preparation": selected.selection}, files=selected.files)
    execution = ExecutionSelection(workers=1, environment_id="main.locked", output_root=str(selected.directory),
        source_snapshot=_pin("recursive-member.implementation", ImplementationSourceClosure.SCHEMA))
    prepared = owner.prepare_protected_factorial_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=execution)
    assert prepared.draft is not None and prepared.prospective_spec is not None and not prepared.executable
    assert tuple(row.kind for row in prepared.dependencies) == (DependencyKind.SOFTWARE, DependencyKind.SOFTWARE)
    assert tuple(row.kind for row in prepared.assessment_limitations) == (DependencyKind.SCIENTIFIC_EVIDENCE,)
    assert "SAMPLING_ASSUMPTION_NOT_AUTHENTICATED" in prepared.assessment_limitations[0].detail
    assert dict(prepared.census.role_counts) == {"acquisition-waves": 16, "comparison-family-slots": 12, "independent-groups": 64, "paired-cases": 576}


def test_closed_source_records_round_trip_without_rewriting_original_entry(selected):
    for record, kind in ((selected.original, ProtectedFactorialOriginalSource),
            (selected.selection, ProtectedFactorialPreparationSelection)):
        restored = decode_canonical_bytes(record.canonical_bytes(), kind, maximum_bytes=None)
        assert restored == record and restored.canonical_bytes() == record.canonical_bytes()
    assert selected.original.study.canonical_bytes() == decode_canonical_bytes(selected.original.canonical_bytes(),
        ProtectedFactorialOriginalSource, maximum_bytes=None).study.canonical_bytes()


def test_pure_handoff_join_preserves_existing_objects_and_refuses_resource_substitution(selected):
    allocation, draft, records, prospective = _derive(selected)
    registrations, registry, codecs = _catalog()
    compilation = compile_recursive_wave(draft=draft, registrations=registrations, registry=registry,
        implementation_commit="d" * 40, qualifications=prospective.qualifications,
        known_design_inputs=prospective.known_design_inputs, output_codecs=codecs)
    # This exercises only the pure domain selection join. The actual owning
    # cold loader and current authority replay remain required software work.
    authoring = SimpleNamespace(package_id=prospective.spec_id + ".executable", base=StudyDefinition(
        prospective.spec_id + ".standard", compilation.candidate_draft, prospective.entry_package))
    handoff = SimpleNamespace(compilation=compilation, authoring=authoring, resources=prospective.resources,
        context=SimpleNamespace(formal_methods=prospective.formal_methods, formal_source_inventories=prospective.formal_source_inventories))
    source_records = tuple(sorted(((selected.original.source_id, selected.original),
        (selected.selection.selection_id, selected.selection))))
    assert owner.validate_protected_experiment_handoff_selection(handoff, specification=selected.specification,
        allocation=allocation, source_records=source_records) == (selected.original, selected.selection, records)
    assert handoff.compilation is compilation and handoff.authoring is authoring
    handoff.resources = replace(prospective.resources, envelope_spec_id="resources.substituted")
    with pytest.raises(ValueError, match="handoff substitutes"):
        owner.validate_protected_experiment_handoff_selection(handoff, specification=selected.specification,
            allocation=allocation, source_records=source_records)


def test_missing_inputs_report_complete_denominators_and_never_supply_a_draft(selected):
    prepared = owner.prepare_protected_factorial_experiment(selected.specification,
        scientific_inputs={}, execution=ExecutionSelection())
    assert not prepared.executable and prepared.draft is None
    assert dict(prepared.census.role_counts)["paired-cases"] == 576
    assert dict(prepared.census.resolved_role_counts)["paired-cases"] == 0
    assert {row.source_key for row in prepared.dependencies if row.kind is DependencyKind.EXTERNAL_INPUT} == {"original", "preparation"}


@pytest.mark.parametrize("damage", ("missing-file", "file-size", "old-development-source-role", "missing-resource-envelope", "protocol-override"))
def test_prepare_refuses_operational_substitutions_without_outcome_io(selected, damage):
    files, selection = dict(selected.files), selected.selection
    closure = _pin("recursive-member.implementation", ImplementationSourceClosure.SCHEMA)
    protocol = None
    if damage == "missing-file":
        files = {}
    elif damage == "file-size":
        first = files["bank"]
        files["bank"] = replace(first, identity=replace(first.identity, size_bytes=0))
    elif damage == "old-development-source-role":
        closure = _pin("recursive-member.implementation", "empirical-lawhood/recursive-authoring/implementation-binding")
    elif damage == "missing-resource-envelope":
        selection = replace(selection, resources=None)
    else:
        protocol = b"replacement original scientific criteria"
    resolved = owner.bind_protected_factorial_experiment_inputs(selected.specification,
        {"original": selected.original, "preparation": selection}, files=files)
    prepared = owner.prepare_protected_factorial_experiment(selected.specification, scientific_inputs=resolved.scientific_inputs,
        method_inputs=resolved.method_inputs, execution=ExecutionSelection(workers=1, environment_id="main.locked",
            output_root=str(selected.directory), source_snapshot=closure), protocol_bytes=protocol)
    assert not prepared.executable
    extra = tuple(row for row in prepared.dependencies if row.code.rsplit(".", 1)[-1] not in {
        "owning-api-composition", "resource-projection", "sampling-warrant"})
    assert extra


@pytest.mark.parametrize("damage", ("criteria-role", "criteria-unit", "prior-receipt", "roster", "original-entry", "coordinate", "streams", "source-digest", "source-access", "source-version", "config-size", "missing-config", "resource-task"))
def test_independent_original_source_and_projection_substitutions_refuse(selected, damage):
    original, selection, spec = selected.original, selected.selection, selected.specification
    with pytest.raises((ValueError, PermissionError)):
        if damage in {"criteria-role", "criteria-unit"}:
            rows = original.study.draft.design_inputs
            pin = original.criteria.record.identity
            rows = tuple(replace(row, **({"role": DesignInputRole.MOTIVATION} if damage == "criteria-role"
                else {"physical_unit_ids": ("observed.synthetic.unit",)})) if row.object_identity == pin else row for row in rows)
            root = replace(original.study.draft, design_inputs=rows)
            study = replace(original.study, draft=root, entry_package=entry_package_for_draft(root))
            original = replace(original, study=study)
            spec = replace(spec, original_study=ObjectIdentity.from_record(study.package_id, study))
        elif damage == "prior-receipt":
            original = replace(original, criteria=replace(original.criteria, receipt=replace(original.criteria.receipt, task_id="same-wave.fake-original-criteria")))
        elif damage == "roster":
            original = replace(original, acquisitions=replace(original.acquisitions, acquisitions=original.acquisitions.acquisitions[:-1]))
        elif damage == "original-entry":
            spec = replace(spec, original_study=replace(spec.original_study, object_fingerprint="a" * 64))
        elif damage in {"coordinate", "streams"}:
            programme = original.criteria.record.configuration.programme
            first = programme.cases[0]
            changed = replace(first, **({"coordinate": replace(first.coordinate, object_fingerprint="b" * 64)}
                if damage == "coordinate" else {"streams_sha256": "b" * 64}))
            programme = replace(programme, cases=(changed, *programme.cases[1:]))
            config = replace(original.criteria.record.configuration, programme=programme,
                specification=replace(original.criteria.record.configuration.specification, programme=programme.identity))
            frozen = replace(original.criteria.record, configuration=config)
            original = replace(original, criteria=_binding(frozen))
            spec = replace(spec, criteria=original.criteria.identity)
        elif damage.startswith("source-"):
            first = selection.qualifications[0]
            kwargs = ({"content_sha256": "b" * 64} if damage == "source-digest"
                else {"materialization": replace(first.materialization, object_version="9.0.0")} if damage == "source-version"
                else {"outcome_access": owner.OutcomeAccess.DEVELOPMENT_VISIBLE})
            selection = replace(selection, qualifications=(replace(first, **kwargs), *selection.qualifications[1:]))
        elif damage == "config-size":
            first = selection.source_configs[0]
            configs = (replace(first, expected_size_bytes=first.expected_size_bytes - 1), *selection.source_configs[1:])
            selection = replace(selection, source_configs=tuple(sorted(configs, key=lambda row: row.fingerprint())))
        elif damage == "missing-config":
            selection = replace(selection, source_configs=selection.source_configs[:-1])
        elif damage == "resource-task":
            first = selection.resources.task_cells[0]
            selection = replace(selection, resources=replace(selection.resources,
                task_cells=(replace(first, task_id="task.unselected"), *selection.resources.task_cells[1:])))
        _derive(selected, original=original, selection=selection, specification=spec)


@pytest.mark.parametrize("damage", ("bank", "source-census", "forecast-design", "common-cutoff"))
def test_consistent_original_entry_republication_cannot_remove_owning_scope_premises(selected, damage):
    original = selected.original
    root = original.study.draft
    programme = original.criteria.record.configuration.programme
    if damage == "common-cutoff":
        first = root.design_inputs[0]
        rows = (replace(first, information_cutoff=replace(first.information_cutoff,
            cutoff_id="cutoff.coherently-republished")), *root.design_inputs[1:])
    else:
        pin = {"bank": programme.bank, "source-census": programme.source_census[0],
            "forecast-design": programme.forecast_design}[damage]
        rows = tuple(row for row in root.design_inputs if row.object_identity != pin)
    root = replace(root, design_inputs=rows, design_origin=replace(root.design_origin,
        declared_input_ids=tuple(row.input_id for row in rows)))
    entry = replace(original.study.entry_package, checklist=replace(original.study.entry_package.checklist,
        draft=ObjectIdentity.from_record(root.draft_id, root)))
    study = replace(original.study, draft=root, entry_package=entry)
    original = replace(original, study=study)
    spec = replace(selected.specification, original_study=ObjectIdentity.from_record(study.package_id, study))
    with pytest.raises(ValueError, match="original full scientific programme|common original design-decision cutoff"):
        _derive(selected, original=original, specification=spec)
