# SPDX-License-Identifier: MPL-2.0
"""Independent public E3 projections over disclosed software-only originals.

Every source group, qualification and availability in these fixtures is
synthetic conformance metadata. They provide no genuine protected source,
scientific qualification, authority or fresh result.
"""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_records import project_protected_e3_response_numerics
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_source_records import identity
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_statistical_bindings import ConfiguredProtectedE3FitConfig, statistical_task_id
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.planning.study_authoring import DesignInputRecord, DesignInputRole, SourceMaterializationRole
from empirical_lawhood.planning.formal_analysis import derive_formal_gap_applicability
from empirical_lawhood.runtime.experiment_preparation import PreparedExperimentFile
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig, SourceReadMode
from tests.experiment_entry_support import entry_package_for_draft
from tests.runtime_platform.test_standard_formal_candidate import _standard_fixture
from tests.test_matrix_e3_response_records import qualification
from tests.test_matrix_factor_confirmation_eligibility import publish


from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_preparation as owner
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_preparation import ConfiguredProtectedE3PreparationSelection
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_lowering import lower_protected_matrix_response_error
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import project_protected_e3_protocol
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_response_selection import ConfiguredProtectedE3ResponseSelection
from empirical_lawhood.api.experiment_preparation import load_experiment_specification, load_experiment_inputs, prepare_experiment
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_configured_protected_e3 import selected as configured_inputs, original_metadata
from tests.test_matrix_e3_protected_public_lowering import original_case, resource_selection
ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "matrix.response-error.configured-protected-v2"

def prepared_case(directory):
    case = original_case(directory)
    inputs, allocation = configured_inputs(case)
    case.publications = case.fit_config.publications
    publications, originals = original_metadata(case, inputs, allocation)
    from tests.test_matrix_configured_protected_statistical import _native_bank_context
    native = _native_bank_context(SimpleNamespace(**{**vars(case), "inputs":inputs, "allocation":allocation,
        "originals":originals, "publications":tuple((row.key,row.publication,row.availability) for row in publications)}),
        "configured-public")
    inputs, allocation = native.inputs, native.allocation
    case.train_features, case.train_outcomes = native.train_features, native.train_outcomes
    case.originals = native.originals
    case.publications = native.publications
    fit = ConfiguredProtectedE3FitConfig("config." + statistical_task_id(inputs.specification.identity, allocation.identity, "fit"),
        inputs.specification.identity, allocation.identity,
        tuple((role, len(allocation.unit_ids(role))) for role in ("calibration", "evaluation")),
        identity(case.manifest), inputs.training_allocation.identity, case.fit_config.fit_cutoff,
        native.publications, inputs.training_coordinates, native.originals)
    mathematical = case.mathematical_protocol
    full_rule, = tuple(row.target for row in mathematical.factor_rule_compatibilities
        if row.target.identity == mathematical.factor_rule)
    projections = tuple(project_protected_e3_protocol(specification=inputs.specification,
        nominal=inputs.nominal, nearby=inputs.nearby, shifted=inputs.shifted,
        mathematical_protocol=mathematical, original_factor_rule=full_rule, prefix_policy=policy,
        scalar_definition=case.manifest.scalar_definition,
        normalization_source=full_rule.scalar_closure.normalization_owner,
        normalization_source_bytes=(ROOT / "src/empirical_lawhood/adapters/simulators/six_matrix_response/response_observer.py").read_bytes(),
        record_id="projection.configured-public." + str(index))
        for index, policy in enumerate(case.manifest.native_specification.selection.prefix_policies))
    old = case.response_selection
    responses = ConfiguredProtectedE3ResponseSelection(old.record_id + ".configured",
        inputs.specification.identity, old.source_manifest, old.root_protocols, old.group_panels,
        old.template_publications, tuple(sorted((identity(row) for row in projections), key=lambda row: row.object_id)))
    publication = publish(case.plane, responses, "literal.configured-public.responses")
    numerical_qualification = qualification(responses, publication, "configured-public.responses")
    numerical_profiles = tuple(project_protected_e3_response_numerics(protocol,
        provenance=responses, publication=publication, qualification=numerical_qualification) for protocol in case.protocols)
    pins = (inputs.specification.identity, allocation.identity, identity(case.manifest),
        *(identity(row) for row in projections), identity(responses))
    design = tuple(DesignInputRecord("design.literal.configured-public." + str(index), pin,
        pin.object_fingerprint, fit.fit_cutoff, DesignInputRole.READINESS_METADATA,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, "human.synthetic-software")
        for index, pin in enumerate(sorted(pins, key=lambda row: row.object_id)))
    case.root = replace(case.root, question=inputs.specification.question, design_inputs=design,
        design_origin=replace(case.root.design_origin, declared_input_ids=tuple(row.input_id for row in design)))
    case.entry_package = entry_package_for_draft(case.root)
    case.inputs, case.specification, case.allocation, case.fit_config = inputs, inputs.specification, allocation, fit
    case.projections, case.response_selection = projections, responses
    case.numerical_profiles, case.response_qualification = numerical_profiles, numerical_qualification
    resources = resource_selection(case, maximum_parallel_tasks=4)
    formal = _standard_fixture()[1]
    training = []
    files = {}
    for name, record in (("features", case.train_features), ("outcomes", case.train_outcomes)):
        artifact = ArtifactIdentity(record.record_id, "disclosed-native-schema-training-" + name,
            record.SCHEMA, record.fingerprint(), "application/json", len(record.canonical_bytes()))
        training.append(artifact)
        path = case.plane.root.resolve("literal-training/" + name + ".json", for_write=True)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(record.canonical_bytes())
        files[artifact.artifact_id] = PreparedExperimentFile(artifact, record.VERSION, path, artifact.size_bytes)
    for publication in case.response_selection.template_publications:
        artifact = next(protocol.templates.array_artifact for protocol in case.protocols
            if protocol.templates.array_artifact.artifact_id == publication.logical.logical_artifact_id)
        files[artifact.artifact_id] = PreparedExperimentFile(artifact, "1.0.0",
            case.plane.root.resolve(publication.materialization.relative_path, for_write=False), artifact.size_bytes)
    selection = ConfiguredProtectedE3PreparationSelection(selection_id="selection.literal.public-e3", root=case.root,
        entry_package=case.entry_package, fit_config=case.fit_config, manifest=case.manifest,
        training_allocation=case.inputs.training_allocation, sources=case.sources, projections=case.projections,
        mathematical_protocol=case.mathematical_protocol, response_selection=case.response_selection,
        protocols=case.protocols, panels=case.panels, numerical_profiles=case.numerical_profiles,
        training_features=training[0], training_outcomes=training[1], formal_methods=formal.formal_methods,
        formal_source_inventories=formal.source_inventories, resource_selection=resources,
        numerical_qualifications=(case.response_qualification,))
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, selection)
    # Explicitly declare this synthetic world's policy from the actual candidate
    # ceiling. Production preparation never enlarges a supplied policy.
    aggregate = lowered.draft.campaign.budget
    declared_ceiling = lowered.draft.prospective_draft.resource_ceiling
    policy = replace(case.root.system.authority_policy, budget_ceiling=declared_ceiling)
    system = replace(case.root.system, authority_policy=policy)
    campaign = replace(case.root.campaign, budget=aggregate,
        authority_policy=ObjectIdentity.from_record(policy.policy_id, policy))
    case.root = replace(case.root, system=system, campaign=campaign, resource_ceiling=declared_ceiling)
    case.entry_package = entry_package_for_draft(case.root)
    selection = replace(selection, root=case.root, entry_package=case.entry_package)
    lowered = lower_protected_matrix_response_error(case.specification, case.allocation, selection)
    input_records = dict(lowered.input_records)
    records = {external.logical_artifact_id: input_records[external.input_id]
        for external in lowered.draft.external_inputs if external.input_id in input_records}
    configs, qualifications = [], []
    for index, external in enumerate(lowered.draft.external_inputs):
        version = records[external.logical_artifact_id].VERSION if external.logical_artifact_id in records else files[external.logical_artifact_id].record_version
        pin = ObjectIdentity(external.logical_artifact_id, external.payload_schema, version, external.expected_content_sha256)
        config = SourceMaterializationConfig("source-config.literal.public-e3." + str(index), external.input_id,
            # This test uses the same exact role as the existing protected
            # factorial source projection; domain meaning stays in records.
            SourceMaterializationRole.OBSERVATION_STREAM,
            external.expected_content_sha256, external.maximum_size_bytes, external.maximum_size_bytes,
            external.payload_schema, external.media_type, SourceReadMode.ORDINARY_BOUNDED,
            external.outcome_access, external.visibility_ceiling)
        configs.append(config)
        qualifications.append(replace(case.template_qualification,
            receipt_id="qualification.literal.public-e3." + str(index), source_id=external.input_id,
            materialization=pin, content_sha256=pin.object_fingerprint,
            evidence_world_id=case.root.system.world.world_id,
            clock_ids=tuple(clock.clock_id for clock in case.root.system.clocks),
            outcome_access=external.outcome_access, visibility_ceiling=external.visibility_ceiling))
    inventory = replace(formal.source_inventories[0], denominator_id=case.root.system.system_id,
        evidence_world=case.entry_package.checklist.portfolio_world,
        source_materializations=tuple(sorted((row.materialization for row in qualifications), key=lambda row: row.object_id)),
        independent_unit_ids=case.allocation.unit_ids("evaluation"),
        denominator_inapplicable_gap_ids=tuple(row.gap_id for row in case.entry_package.register.gaps))
    coverage = replace(case.entry_package.coverage, denominator_id=case.root.system.system_id,
        applicability=derive_formal_gap_applicability(case.entry_package.register, inventory))
    entry = replace(case.entry_package, coverage=coverage, checklist=replace(case.entry_package.checklist,
        formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage)))
    selection = replace(selection, entry_package=entry, formal_source_inventories=(inventory,),
        qualifications=tuple(sorted(qualifications, key=lambda row: row.receipt_id)),
        source_configs=tuple(sorted(configs, key=lambda row: row.fingerprint())))
    case.selection, case.files, case.lowered = selection, files, lowered
    return case

def write_public_file_selection(case):
    """Select existing original files through the installed public FILE schema."""
    from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputSelection, ExperimentInputBinding

    root = Path(case.plane.root.contract.canonical_path)
    record_path = root / "selected-protected-e3.canonical.json"
    raw = case.selection.canonical_bytes()
    record_path.write_bytes(raw)
    bindings = (ExperimentInputBinding("protected-selection",
        ObjectIdentity.from_record(case.selection.selection_id, case.selection), record_path.name, len(raw)),)
    files = tuple(ExperimentFileInputBinding(key, value.identity, value.record_version,
        value.path.relative_to(root).as_posix(), value.maximum_bytes) for key, value in sorted(case.files.items()))
    selection = ExperimentFileInputSelection("selection.literal.public-e3.files", PROTOCOL, bindings, files)
    path = root / "selected-protected-e3-file-inputs.json"
    path.write_bytes(selection.canonical_bytes())
    return path


@pytest.fixture(scope="module")
def public_case(tmp_path_factory):
    return prepared_case(tmp_path_factory.mktemp("configured-protected-public-originals"))

def test_public_files_prepare_and_cold_replay_complete_versioned_graph(public_case, tmp_path):
    case = public_case
    before = tuple(value.canonical_bytes() for value in (case.manifest, case.inputs.training_allocation))
    specification_path = tmp_path / "configured-specification.json"
    specification_path.write_bytes(case.specification.canonical_bytes())
    specification = load_experiment_specification(specification_path)
    assert type(specification) is type(case.specification) and specification == case.specification
    bound = load_experiment_inputs(specification, write_public_file_selection(case))
    result = prepare_experiment(specification, scientific_inputs=bound.scientific_inputs, method_inputs=bound.method_inputs,
        execution=ExecutionSelection(workers=4, environment_id="environment.configured-public.fixture",
            source_snapshot=ObjectIdentity("source.configured-public.fixture", "empirical-lawhood/source/exact-fixture", "1.0.0", "a" * 64),
            output_root=str(case.plane.root.contract.canonical_path)))
    assert result.draft is not None and result.allocation == case.allocation
    assert tuple(row.code for row in result.dependencies) == (owner.RESOURCE_BINDING_DEPENDENCY,)
    declared = result.draft.prospective_draft.resource_ceiling
    policy = result.draft.prospective_draft.system.authority_policy
    assert declared.memory_bytes == 4 * 2 * 1024**3
    assert policy.budget_ceiling == declared and policy.budget_ceiling.contains(result.draft.campaign.budget)
    queries = sum(len(case.allocation.unit_ids(role)) for role in ("calibration", "evaluation"))
    counts = dict(result.census.operation_counts)
    assert sum(counts.values()) == 10 * queries + 6 and result.census.native_effect_count == 2 * queries
    assert all(row.selection.capability_key.startswith("matrix-e3-configured-protected.") for row in result.draft.operations)
    cold = decode_canonical_bytes(case.selection.canonical_bytes(), type(case.selection), maximum_bytes=None)
    owner.validate_protected_e3_experiment_instance(specification=specification,
        allocation=result.allocation, draft=result.draft, source_records=((cold.selection_id, cold),))
    resources = owner.derive_protected_e3_resource_selection(result)
    assert resources.maximum_parallel_tasks == 4 and len(resources.task_cells) == sum(counts.values())
    assert all(row.resource_budget.cpu_cores == 1 and row.resource_budget.memory_bytes == 2 * 1024**3 for row in resources.task_cells)
    assert before == tuple(value.canonical_bytes() for value in (case.manifest, case.inputs.training_allocation))

def test_public_configured_protocol_refuses_separate_prose(public_case):
    with pytest.raises(ValueError, match="typed protocol"):
        owner.prepare_protected_e3(public_case.specification, scientific_inputs={},
            execution=ExecutionSelection(workers=4), protocol_bytes=b"unrelated old prose")

def test_public_workers_match_frozen_explicit_resource_selection(public_case):
    case = public_case
    bound = owner.ConfiguredProtectedE3ExperimentInputs(case.selection, tuple(sorted(case.files.items())))
    result = prepare_experiment(case.specification,
        scientific_inputs={row.source_key: case.allocation for row in case.specification.populations},
        method_inputs=bound, execution=ExecutionSelection(workers=1))
    assert any(row.code == "matrix.e3.worker-resource-selection" for row in result.dependencies)
    assert owner.derive_protected_e3_resource_selection(result).maximum_parallel_tasks == 4
