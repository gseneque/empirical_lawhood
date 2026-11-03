# SPDX-License-Identifier: MPL-2.0
"""Selected E4 DEV software controls; synthetic locators grant no authority.

The full32x9 fixture is disclosed typed metadata. No producer, native child,
source qualifier, signer, fit or protected future is invoked by these controls.
"""

from tests.matrix_e4_structure_support import disclosed_structure, published_secondary
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from itertools import product
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r, selected_e3_e4_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_experiment as public
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as old
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_records import ScheduledProgrammeFactor as old_factor
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource, FAMILY_MAP
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseArrays
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_public import MatrixSelectedPublicPackage
from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_entry import MatrixSelectedOriginalProduct
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import MatrixHistorySeed, HISTORY_PURPOSES
from empirical_lawhood.adapters.simulators.six_matrix_response.history_preparation import FOUR_FAMILY_PREPARATION_IDS
from empirical_lawhood.infrastructure.matrix_array_io import encode_matrix_arrays
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import DevelopmentStudySpec
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.runtime.artifacts import ArtifactProfile
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection, PreparedExperimentFile
from empirical_lawhood.runtime.recursive_compiler import compile_recursive_wave, validate_recursive_scientific_roots, decode_recursive_config_input
from empirical_lawhood.planning.recursive_authoring import RecursiveStudyDraft
from tests.runtime_platform.test_recursive_compiler import fixture as campaign_fixture
from tests.test_matrix_selected_protected import transfer, unpublished  # noqa: F401 - in-memory shared source fixture
from tests.test_matrix_selected_point import selected_design, feature
from tests.test_matrix_sampling_follow_on import prior_product
from tests.test_matrix_prepared_assay_method import literal_protocol


@pytest.fixture(scope="module")
def selected_bridge(transfer, tmp_path_factory):  # noqa: F811
    return build_selected_bridge(transfer, tmp_path_factory)


def build_selected_bridge(transferred, tmp_path_factory, *, public_package=None):
    closure = transferred.sources.closure
    selected = selected_design()
    package = MatrixSelectedPublicPackage.from_package(selected.package) if public_package is None else public_package
    matched = getattr(package.specification.measurement, 'is_matched', False)
    nominal = selected.sources[0][1].original.coordinate
    policy = selected.sources[0][1].original.policy
    families = tuple(sorted(FOUR_FAMILY_PREPARATION_IDS))
    high = D(4) if matched else D(3)
    grid = (*product((D(1), high), repeat=3), (D(2),) * 3)
    coordinates = []
    for family_index, family in enumerate(families):
        for index, (temperature, friction, coupling) in enumerate(grid):
            name = f"selected-e4.fixture.{family_index}.{index}"
            coordinate = replace(nominal, coordinate_id="coordinate." + name, family_id=family,
                member=replace(nominal.member, member_id="member." + name, cross_coupling_gamma=coupling),
                primary_view=replace(nominal.primary_view, view_id="view.primary." + name,
                    bath_temperature=temperature, friction_gamma=friction),
                fine_view=replace(nominal.fine_view, view_id="view.fine." + name,
                    bath_temperature=temperature, friction_gamma=friction))
            coordinates.append(coordinate)
    coordinates = tuple(sorted(coordinates, key=lambda row: row.coordinate_id))
    roots, scopes = [], []
    for family_index, family in enumerate(families):
        family_coordinates = tuple(value for value in coordinates if value.family_id == family)
        groups = tuple(f"group.selected-e4.disclosed.{family_index}.{index:02}" for index in range(8))
        for group in groups:
            streams = tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_SELECTED_E4." + group + purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)
            for index, coordinate in enumerate(family_coordinates):
                root_id = f"root.{group}.{index}"
                root = old.MatrixProgrammeRoot(root_id, group, "regime." + coordinate.coordinate_id, coordinate.coordinate_id,
                    old.MatrixProgrammeRole.DEVELOPMENT, coordinate.clock_id)
                roots.append(old.ScheduledRoot(root, old.coordinate_identity(coordinate), streams))
        scopes.append(old.ScheduledMatchedScope("scope.selected-e4." + str(family_index), old.MatrixProgrammeRole.DEVELOPMENT,
            groups, tuple(old.coordinate_identity(value) for value in family_coordinates),
            "COMMON_DECLARED_INITIAL_STATE_AND_FOUR_PURPOSE_PCG64DXSM_NOISE_COORDINATE_SPECIFIC_OU"))
    allocation = replace(closure.reservation.allocation, allocation_id="allocation.selected-e4.disclosed", coordinates=coordinates,
        roots=tuple(sorted(roots, key=lambda row: row.root.root_id)), matched_scopes=tuple(scopes))
    reservation = old.ScheduledReservation("reservation.selected-e4.disclosed", allocation, unpublished(allocation, "publication.selected-e4.allocation"))
    selection = old.ScheduledSelection("selection.selected-e4.disclosed", old.identity(reservation), closure.specification.selection.numerical_design,
        (policy,), tuple((old.coordinate_identity(value), old.identity(policy)) for value in coordinates))
    specification = old.ScheduledSpecification("specification.selected-e4.disclosed", selection, unpublished(selection, "publication.selected-e4.selection"))
    index=ScheduledSourceIndex.from_shared(reservation=reservation,specification=specification,provenances=closure.provenances)
    subjects=tuple(index.resolve(index.reference(source_id="source."+value.root.root_id,
        root_id=value.root.root_id,provenance=closure.provenances[0].identity)) for value in allocation.roots)
    base_protocol, _ = literal_protocol()
    template_arrays = {"generic_basis": np.zeros((3, 4, 4), dtype="<c16"), "force_coefficients": np.zeros((2, 3, 3), dtype="<f8"),
        "trace_coefficients": np.zeros((2, 3), dtype="<f8"), "receiver_coefficients": np.zeros((48, 2, 2, 3, 4), dtype="<f8")}
    raw, members = encode_matrix_arrays(template_arrays)
    artifact = ArtifactIdentity("array.selected-e4.disclosed-templates", "disclosed-software-input", "empirical-lawhood/matrix/array-input", sha256(raw).hexdigest(), "application/x-npz", len(raw))
    # Use the actual shared Matrix array schema, independent of a descriptor's schema.
    from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
    artifact = replace(artifact, payload_schema=MATRIX_ARRAY_SCHEMA)
    from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec, EXPOSURE as FACTOR_EXPOSURE
    from empirical_lawhood.adapters.methods.matrix_factor_response.protected_protocol import ORIGINAL_SCALAR_SOURCE_BYTES, ORIGINAL_SCALAR_SOURCE_SHA256
    from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseFrontierProtocol, MatrixResponseActionScale, MatrixResponseFactorRuleCompatibility
    prefix_rule = policy.factor_rule
    original_normalization = ArtifactIdentity("matrix.scalar.closure.normalization-owner01", "native-normalization-source",
        "empirical-lawhood/source/checksummed-uninterpreted-public-bytes", ORIGINAL_SCALAR_SOURCE_SHA256,
        "text/x-python", ORIGINAL_SCALAR_SOURCE_BYTES)
    # Disclosed fixture projection: retain its own thresholds and full nominal lattice.
    full_rule = FactorEventSpec(
        spec_id="rule.selected-e4.disclosed-full",
        sectors=prefix_rule.sectors,
        lattice=nominal.observation_ticks,
        primary_dt=prefix_rule.primary_dt,
        risk_start_tick=prefix_rule.risk_start_tick,
        trailing_persistence_ticks=prefix_rule.trailing_persistence_ticks,
        associative_leakage_maximum=prefix_rule.associative_leakage_maximum,
        lie_leakage_maximum=prefix_rule.lie_leakage_maximum,
        factor_fit_angle_maximum_degrees=prefix_rule.factor_fit_angle_maximum_degrees,
        adjacent_angle_maximum_degrees=prefix_rule.adjacent_angle_maximum_degrees,
        origin_angle_maximum_degrees=prefix_rule.origin_angle_maximum_degrees,
        identifiability_relative_gap=prefix_rule.identifiability_relative_gap,
        identifiability_absolute_fourth=prefix_rule.identifiability_absolute_fourth,
        frame_alignment_minimum_overlap=prefix_rule.frame_alignment_minimum_overlap,
        scalar_closure=replace(prefix_rule.scalar_closure, spec_id="scalar-rule.selected-e4.disclosed-full",
            normalization_owner=original_normalization),
        exposure=FACTOR_EXPOSURE)
    admission_rule = replace(full_rule, spec_id="rule.selected-e4.disclosed-admission", scalar_closure=None)
    compatibility = MatrixResponseFactorRuleCompatibility("compatibility.selected-e4.disclosed-admission", admission_rule, full_rule)
    criterion_record = MatrixResponseFrontierProtocol("criterion.selected-e4.disclosed", full_rule.identity,
            package.specification.measurement.primary_timestep, package.specification.measurement.horizons,
        tuple(MatrixResponseActionScale(value.role, value.amplitude, value.force_norm, 16) for value in base_protocol.actions),
        base_protocol.receiver_gram_tolerance, factor_rule_compatibilities=(compatibility,))
    criterion = criterion_record.identity
    protocols = []
    if matched:
        from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, MatrixIO48Construction
        base_protocol = replace(base_protocol, horizon_steps=package.specification.measurement.horizons,
            actions=tuple(replace(value, pulse_steps=16) for value in base_protocol.actions),
            mechanical_model=MatrixOriginResponseModel('test.e4.matched-origin', base_protocol.mechanical_model.implementation,
                MatrixIO48Construction('test.e4.io48')))
    for source in subjects:
        templates = ScheduledResponseArrays("templates." + source.root_id, "TEMPLATES", old.identity(source), artifact, members,
            (old.identity(source),), old.OutcomeAccess.OUTCOME_BLIND, old.VisibilityCeiling.PROSPECTIVE)
        protocols.append(replace(base_protocol, protocol_id="protocol." + source.root_id, public_source=ScheduledPublicSource.from_source(source),
            criterion=criterion, templates=templates, actions=tuple(replace(value, pulse_steps=16) for value in base_protocol.actions)))
    panels = []
    for group in allocation.independent_group_ids:
        root = next(value for value in allocation.roots if value.root.independent_group_id == group)
        pair = tuple(ScheduledResponsePanel("panel." + group + "." + str(index), group, role,
            "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES" if index == 0 else "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", root.streams if index == 0 else
            tuple(MatrixHistorySeed(purpose, sha256(("DISCLOSED_SELECTED_E4_FUTURE." + group + purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)) for index, role in enumerate(("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")))
        panels.append((group, pair))
    publication = unpublished(protocols[0].templates, artifact.artifact_id)
    publication = replace(publication, logical=replace(publication.logical, content_sha256=artifact.sha256, payload_schema=MATRIX_ARRAY_SCHEMA,
        profile=ArtifactProfile.MATRIX_ARRAY_NPZ, media_type="application/x-npz",
        generic_validation=replace(publication.logical.generic_validation, payload_schema=MATRIX_ARRAY_SCHEMA, profile=ArtifactProfile.MATRIX_ARRAY_NPZ)),
        materialization=replace(publication.materialization, physical_sha256=artifact.sha256, size_bytes=len(raw)))
    responses = ScheduledResponseSelection("responses.selected-e4.disclosed", ObjectIdentity.from_record(allocation.allocation_id, allocation), tuple(protocols), tuple(panels), (publication,), None)
    responses.validate_allocation(allocation)
    design = r.SelectedE3E4ForecastDesign("design.selected-e4.disclosed", package,
        old.identity(allocation), criterion_record, unpublished(criterion_record, "publication.selected-e4.criterion"),
        fit_target=r.selected_e3_fit_target(package))
    bank = r.SelectedE3E4DevelopmentBank("bank.selected-e4.disclosed", reservation, specification, closure.provenances,
        tuple(value.reference for value in subjects), closure.audit, closure.audit_publication, design,
        responses, unpublished(responses, "publication.selected-e4.responses"),
        r.SelectedE3E4Design("design.selected-e4.disclosed-factorial", 32, D(".95"),
            tuple(old_factor(name, "LOG" if matched else "LINEAR", D(1), D(2), high) for name in ("temperature", "friction", "coupling")), 4))
    programme = r.SelectedE3E4DevelopmentProgramme.from_selected_bank(bank, programme_id="programme.selected-e4.disclosed")
    package = design.package
    pins = (old.identity(package.models), old.identity(package.model_freeze), package.calibration, old.identity(package.calibrated_freeze))
    upstream = []
    for pin in sorted(pins, key=lambda value: value.object_id):
        prior = prior_product(pin)
        upstream.append(MatrixSelectedOriginalProduct(prior.prior_execution, prior.reveal_authority))
    evidence = r.SelectedE3E4Evidence("evidence.selected-e4.disclosed", programme.identity, tuple(upstream), disclosed_produced_parents(tuple(upstream)))
    target, secondary, plane = published_secondary(bank, tmp_path_factory.mktemp("e4-target-parent") / "custody")
    return SimpleNamespace(programme=programme, bank=bank, evidence=evidence, template_raw=raw, selected=selected,
        secondary_target=target, secondary_readout=secondary, secondary_plane=plane)


def disclosed_produced_parents(originals, *, development=()):
    """Literal exposed control labels; never actual receipt or access evidence."""
    from empirical_lawhood.runtime.artifacts import ArtifactLineageParent,lineage_parent_sort_key
    rows=[ArtifactLineageParent(pin,r.EXPOSED,r.DEV) for value in originals
        for pin in (value.record,value.prior_execution.receipt)]
    rows.extend(ArtifactLineageParent(pin,value.publication.logical.visibility_ceiling,value.publication.logical.outcome_access)
        for value in development for pin in (value.record,value.receipt))
    return tuple(sorted(set(rows),key=lineage_parent_sort_key))


def disclosed_produced_publication(record, name, parents):
    """Unwritten fixture handle with honest exposed labels, never custody."""
    from empirical_lawhood.kernel.evidence import inherited_visibility
    from empirical_lawhood.runtime.artifacts import derived_outcome_access
    publication=unpublished(record,name)
    access=derived_outcome_access(old.OutcomeAccess.OUTCOME_BLIND,*(value.outcome_access for value in parents))
    ceilings=tuple(value.visibility_ceiling for value in parents)
    return replace(publication,logical=replace(publication.logical,outcome_access=access,
        visibility_ceiling=inherited_visibility(ceilings,access),parent_visibility_ceilings=ceilings,lineage_parents=parents))


def test_full32x9_selected_bank_retains_original_physics_cold_bytes_and_no_cal_scores(selected_bridge):
    f = selected_bridge
    assert {value.identity for value in f.evidence.produced_input_parents} == {
        pin for value in f.evidence.upstream_products for pin in (value.record,value.prior_execution.receipt)}
    with pytest.raises(ValueError,match='produced-parent census'):
        replace(f.evidence,produced_input_parents=f.evidence.produced_input_parents[:-1])
    assert len(f.programme.cases) == len(f.bank.sources) == 288
    assert len(f.programme.group_ids) == 32
    assert all(len(wave.root_ids) == 9 * len(wave.group_ids) for wave in f.programme.waves)
    r.validate_evidence(f.evidence, f.programme, f.bank)
    for value in (f.bank, f.programme, f.evidence):
        assert decode_canonical_bytes(value.canonical_bytes(), type(value), maximum_bytes=None) == value
        assert b'"scores"' not in value.canonical_bytes()
    assert f.bank.forecast_design.package.original_package == f.selected.package.identity
    assert f.bank.forecast_design.package.calibration == old.identity(f.selected.package.calibration)


@pytest.mark.parametrize("damage", ("missing-case", "role", "calibration", "reserve", "clock", "action"))
def test_selected_bridge_refuses_scope_ancestry_or_instrument_substitution(selected_bridge, damage):
    f = selected_bridge
    with pytest.raises((TypeError, ValueError)):
        if damage == "missing-case":
            replace(f.bank, sources=f.bank.sources[:-1])
        elif damage == "role":
            replace(f.programme, mode="E4_REVISION_CALIBRATION")
        elif damage == "calibration":
            replace(f.evidence, upstream_products=f.evidence.upstream_products[:-1])
        elif damage == "reserve":
            f.bank.forecast_design.package.require_unused_groups(f.selected.package.selection_unit_ids)
        elif damage == "clock":
            first = f.bank.response_selection.protocols[0]
            changed = replace(first.public_source, policy=replace(first.public_source.policy, cutoff_tick=255))
            replace(f.bank, response_selection=replace(f.bank.response_selection,
                protocols=(replace(first, public_source=changed), *f.bank.response_selection.protocols[1:])))
        else:
            first = f.bank.response_selection.protocols[0]
            changed = replace(first, actions=tuple(replace(value, pulse_steps=8) for value in first.actions))
            replace(f.bank, response_selection=replace(f.bank.response_selection, protocols=(changed, *f.bank.response_selection.protocols[1:])))


def test_bounded_native_transport_is_exact_original_subject_and_predictor_is_seedless(selected_bridge):
    f = selected_bridge
    local = r.SelectedE3E4NativeSourceReference.from_bank(f.programme, f.bank, f.bank.sources[0],index=f.bank.source_index())
    assert old.identity(local) == local.identity
    assert local.identity != local.reference.identity
    assert local.public == ScheduledPublicSource.from_source(f.bank.source(local.root_id,index=f.bank.source_index()))
    assert decode_canonical_bytes(local.canonical_bytes(), type(local), maximum_bytes=None) == local
    assert len(local.canonical_bytes()) < 256 * 1024
    assert len(local.canonical_bytes()) * 10 < len(f.bank.canonical_bytes())
    assert b'"roots"' not in local.canonical_bytes() and b'"matched_scopes"' not in local.canonical_bytes()
    config = owner.SelectedE3E4PublicConfig("config." + owner.local_node(local.root_id, "account"),
        f.programme.identity, local.public, f.bank.response_selection.protocols[0], "account", secondary_readout=f.secondary_readout)
    assert all(word not in config.canonical_bytes() for word in (b'"streams"', b'effective_seed', b'"scores"'))
    with pytest.raises(ValueError):
        replace(local, public=replace(local.public, allocation=replace(local.public.allocation, object_fingerprint="f" * 64)))


def disclosed_operational_resources():
    # Software-only release controls, never measured native launch reservations.
    return public.SelectedE3E4OperationalSelection("resources.selected-e4.disclosed",
        tuple((phase, ResourceBudget(1, 64 * 1024**2 + owner.PHASES.index(phase), 0, None, None, None))
            for phase in sorted(owner.PHASES)))


def disclosed_operational_budgets(f):
    return disclosed_operational_resources().task_budgets(f.programme, f.bank, evidence=f.evidence)


def lowered_case(f):
    return owner.lower_selected_e3_e4_development(f.programme, f.bank, evidence=f.evidence,
        campaign=campaign_fixture()[0].campaign, draft_id="draft.selected-e4.disclosed", operational_budgets=disclosed_operational_budgets(f), secondary_target=f.secondary_target, secondary_readout=f.secondary_readout)


def compiler_inputs(draft):
    declarations = {value.capability_key: value for value in owner.operation_declarations()}
    registrations, configs = {}, []
    for operation in draft.operations:
        registration = declarations[operation.selection.capability_key].registration()
        registrations[operation.node_id] = registration
        configs.append(decode_recursive_config_input(operation, registration))
    return dict(root=draft.development_study, config_inputs=tuple(configs), registrations_for_node=registrations,
        requirements=(), connections=(), qualifications=(), known_design_inputs=(), links=draft.links, external_inputs=draft.external_inputs)


def test_current_e4_development_preserves_source_roles_and_cold_draft_bytes(selected_bridge):
    """Current E4 science inherits actual parent labels without reclassifying edges."""
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_produced_inputs import (
        produced_access, produced_record_parents,
    )
    f = selected_bridge
    assert f.evidence.produced_input_parents
    lowered = lowered_case(f)
    records = dict(lowered.input_records)
    inherited = []
    for external in lowered.draft.external_inputs:
        assert external.scientific_role == "SOURCE"
        parents = produced_record_parents(records.get(external.input_id), f.evidence.produced_input_parents)
        if parents:
            inherited.append(external.input_id)
            assert (external.outcome_access, external.visibility_ceiling) == produced_access(
                declared_access=r.DEV, declared_visibility=r.EXPOSED, parents=parents)
        else:
            assert (external.outcome_access, external.visibility_ceiling) == (r.DEV, r.EXPOSED)
    target, = (value for value in lowered.draft.external_inputs
        if value.payload_schema == f.secondary_target.SCHEMA)
    assert records[target.input_id] == f.secondary_target
    assert target.expected_content_sha256 == f.secondary_readout.target.object_fingerprint
    assert target.maximum_size_bytes == len(f.secondary_target.canonical_bytes())
    # The consumer alias is development-scoped; the pre-future publication
    # remains the exact blind original named by the entry seal.
    from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
    publication = f.secondary_plane.read_manifest(
        f.secondary_readout.publication.materialization.relative_path)
    assert publication.logical == f.secondary_readout.publication.logical
    assert (publication.logical.outcome_access, publication.logical.visibility_ceiling) == (
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE)
    assert publication.logical.lineage_parents == ()
    assert all(link.scientific_role == "SOURCE" for link in lowered.draft.links if link.external_input_id is not None)
    assert inherited, "the real bridge must exercise its model-bearing produced design"
    raw = lowered.draft.canonical_bytes()
    cold = decode_canonical_bytes(raw, RecursiveStudyDraft, maximum_bytes=None)
    assert cold.canonical_bytes() == raw
    assert cold.external_inputs == lowered.draft.external_inputs and cold.links == lowered.draft.links


def test_real_development_compiler_complete_graph_and_cold_canonical_inputs(selected_bridge):
    f = selected_bridge
    lowered = lowered_case(f)
    declarations = owner.operation_declarations()
    registry = CapabilityRegistry("registry.selected-e4.disclosed", tuple(value.manifest() for value in declarations))
    registrations = tuple(value.registration() for value in declarations)
    compiled = compile_recursive_wave(draft=lowered.draft, registry=registry, registrations=registrations,
        implementation_commit="a" * 40, output_codecs={schema: kind for row in declarations for schema, kind in row.record_codecs.items()})
    assert type(lowered.draft.development_study) is DevelopmentStudySpec
    assert lowered.draft.prospective_draft is None
    assert len(lowered.draft.operations) == len(compiled.execution_plan.tasks) == 3458
    assert sum(value.native_effect for value in registrations) == 3
    cold = decode_canonical_bytes(lowered.draft.canonical_bytes(), RecursiveStudyDraft, maximum_bytes=None)
    validate_recursive_scientific_roots(**compiler_inputs(cold))
    by_key = {value.selection.capability_key: value for value in registrations}
    for operation in cold.operations:
        value = decode_recursive_config_input(operation, by_key[operation.selection.capability_key]).record
        assert value.phase in owner.PHASES and b'"scores"' not in value.canonical_bytes()
    entry = owner.global_node(f.programme, "entry")
    for task in compiled.execution_plan.tasks:
        if task.task_id != entry:
            assert entry in task.dependency_task_ids
        if task.capability.capability_key.endswith((".continue", ".responses")):
            root = task.task_id.removeprefix(owner.NAMESPACE + ".").rsplit(".", 1)[0]
            assert {owner.local_node(root, "account"), owner.local_node(root, "mechanical")} <= set(task.dependency_task_ids)
    assert compiled.execution_plan.__class__.__name__ == "DevelopmentExecutionPlan"


@pytest.mark.parametrize("damage", ("entry-edge", "future-seal", "case-tail"))
def test_actual_compiler_refuses_graph_thinning(selected_bridge, damage):
    lowered = lowered_case(selected_bridge)
    links = list(lowered.draft.links)
    selected = next(value for value in links if value.consumer_input_id == ("entry" if damage == "entry-edge" else "account" if damage == "future-seal" else
        "cases." + selected_bridge.programme.cases[0].root_id))
    broken = replace(lowered.draft, links=tuple(value for value in links if value != selected))
    with pytest.raises(ValueError, match="graph|census|operand|input|port"):
        validate_recursive_scientific_roots(**compiler_inputs(broken))


def test_selected_account_preserves_all_actual_original_points_and_no_uncertainty(selected_bridge):
    f = selected_bridge
    public_source = ScheduledPublicSource.from_source(f.bank.source(f.bank.sources[0].root_id,index=f.bank.source_index()))
    original_feature = feature(f.selected, f.selected.sources[0][1])
    values = original_feature.values
    predictions = f.bank.forecast_design.package.predict(values=values, disposition="AVAILABLE")
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_package import predict_selected_points
    assert predictions == predict_selected_points(f.selected.package, values=values, disposition="AVAILABLE")
    assert dict(predictions)["SPECTRAL_RIDGE"] == (D(0), D(2), D(2)) * 5
    prefix = ObjectIdentity("causal.literal-selected-e4", r.SelectedE3E4CausalPrefix.SCHEMA, "1.0.0", "c" * 64)
    observed = r.SelectedE3E4Feature("feature.literal-selected-e4", public_source.source, prefix, public_source.root.root_id,
        public_source.root.independent_group_id, FAMILY_MAP[public_source.coordinate.family_id], public_source.coordinate.clock_id, D(".256"), "d" * 64, "AVAILABLE", values)

    seal = r.SelectedE3E4AccountSeal("seal.literal-selected-e4", f.bank.forecast_design.identity, public_source.source, prefix, observed,
        f.selected.package.identity, old.identity(f.selected.package.calibration), predictions)
    assert seal.uncertainty_status == r.POINT_ONLY
    assert decode_canonical_bytes(seal.canonical_bytes(), type(seal), maximum_bytes=None) == seal
    assert b'"radius"' not in seal.canonical_bytes() and b'"uppers"' not in seal.canonical_bytes()


def test_complete_adverse_reduction_never_drops_groups_or_promotes_point_evidence(selected_bridge):
    f = selected_bridge
    cases = tuple(r.SelectedE3E4CaseResult.unentered(case) for case in f.programme.cases)
    reduced = science.reduce_cases(f.programme, cases, record_id="reduction.actual-unentered-census")
    assert len(reduced.cases) == 288 and len(reduced.group_residuals) == 32
    assert all(value is None for _, scores in reduced.group_residuals for _, value in scores)
    assert all(case.disposition == "UNENTERED" for case in reduced.cases)
    assert reduced.scientific_standing == "EXPOSED_DEVELOPMENT_ONLY_NO_QUALIFICATION"
    with pytest.raises(ValueError, match="census"):
        science.reduce_cases(f.programme, cases[:-1], record_id="reduction.thinned")


def test_public_prepare_retains_exact_complete_science_and_real_missing_inputs(selected_bridge):
    f = selected_bridge
    campaign = campaign_fixture()[0].campaign
    spec = public.SelectedE3E4ExperimentSpecification("experiment.selected-e4.disclosed", f.programme.identity, f.bank.identity,
        f.evidence.identity, ObjectIdentity.from_record(campaign.campaign_id, campaign),
        *disclosed_structure(f.bank, budget=dict(disclosed_operational_resources().phase_budgets)["collect"]))
    missing = public.prepare(spec, scientific_inputs={}, execution=ExecutionSelection())
    assert not missing.executable and missing.census.role_counts == ()
    artifacts = dict(owner.contracts(f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()), produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)[4])
    files = {name: PreparedExperimentFile(value, "1.0.0", Path("/media/chevre/EL/empirical-lawhood/checks/unpublished-e4") / str(index),
        value.size_bytes) for index, (name, value) in enumerate(artifacts.items())}
    bound = public.bind_inputs(spec, {"programme": f.programme, "bank": f.bank, "evidence": f.evidence, "campaign": campaign, "secondary_readout": f.secondary_readout}, files=files)
    method_inputs = public.select_operational_budgets(bound.method_inputs, disclosed_operational_budgets(f))
    result = public.prepare(spec, scientific_inputs=bound.scientific_inputs, method_inputs=method_inputs,
        execution=ExecutionSelection(workers=1, environment_id="matrix.native.exposed", source_snapshot=ObjectIdentity.from_record(campaign.campaign_id, campaign),
            output_root="/media/chevre/EL/empirical-lawhood/checks/unpublished-e4"))
    assert result.executable and len(result.draft.operations) == 3458
    public.validate_instance(specification=spec, allocation=result.allocation, draft=result.draft, source_records=result.design_records)
    assert all(b'"scores"' not in value.canonical_bytes() for _, value in result.design_records)
    assert public.protocol_declaration().requires_development_runtime_binding
    from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
    assert public.protocol_declaration().input_storage_codecs == MATRIX_STORAGE_CODECS


def test_parent_refuses_missing_real_authored_custody_before_original_calibration_reads(monkeypatch):
    from empirical_lawhood.api import matrix_selected_e3_e4_runtime as api
    seen = []
    class RefusingCurrent:
        def current_task(self, context, runner):
            seen.append("actual-authored-custody")
            raise PermissionError("actual authored packet absent")
    class CurrentOriginalAccess:
        def require_current(self):
            seen.append("current-original-access")
    supplier = object.__new__(api.SelectedE3E4DevelopmentRuntimeInputSupplier)
    supplier.original_input_access = CurrentOriginalAccess()
    supplier.custody = RefusingCurrent()
    monkeypatch.setattr(api, "authenticate_original_products", lambda *args: pytest.fail("sealed read preceded actual current DEV custody"))
    declaration = next(value for value in owner.operation_declarations() if value.capability_key.endswith(".entry"))
    with pytest.raises(PermissionError, match="actual authored"):
        supplier.prepare_selected_e3_e4_development(SimpleNamespace(), declaration.runner_factory())
    assert seen == ["current-original-access", "actual-authored-custody"]


def test_pure_native_projection_keeps_exact_local_source_and_all_four_streams(selected_bridge):
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e3_e4_native import initial_native_work
    from empirical_lawhood.runtime.native_effects import NativeEffectContact

    f = selected_bridge
    local = r.SelectedE3E4NativeSourceReference.from_bank(f.programme, f.bank, f.bank.sources[0],index=f.bank.source_index())
    protocol = f.bank.response_selection.protocols[0]
    config = owner.SelectedE3E4CompactConfig("config." + owner.local_node(local.root_id, "prefix"), f.programme.identity, local, protocol,
        dict(f.bank.response_selection.panels)[local.root.root.independent_group_id], f.bank.response_selection.identity, "prefix")
    provenance = next(value for value in f.bank.provenances if value.identity == local.provenance)
    task = config.config_id.removeprefix("config.")
    parent = NativeEffectContact("run.disclosed-e4-native-scope", task, "attempt.disclosed-e4-native-scope",
        ObjectIdentity("plan.disclosed-e4-native-scope", "empirical-lawhood/runtime/execution-plan", "1.0.0", "a" * 64),
        ObjectIdentity(task, "empirical-lawhood/runtime/execution-task", "1.0.0", "b" * 64),
        provenance.observed_git_head, ("material.disclosed-e4-native-scope",), ())
    context = SimpleNamespace(run_id=parent.run_id, task_id=task, attempt_id=parent.attempt_id,
        input_materialization_ids=parent.input_materialization_ids, dependency_receipt_ids=(), prepared_invocation=None)
    work = initial_native_work(context, config, {"provenance": provenance}, {}, parent)
    assert work.scientific_unit_ids == (local.root.root.independent_group_id,)
    assert work.native_effect_slot_ids == ("prefix." + local.root_id,)
    definition, = work.definitions
    assert definition.configuration == ObjectIdentity.from_record(config.config_id, config)
    assert set(definition.streams) == {local.root.stream_identity(value) for value in local.root.streams}
    assert set(definition.sources) == {local.identity, local.provenance}
    assert definition.operation_id.endswith(".direct-operands.v2")
    assert tuple(value.output_id for value in definition.outputs) == ("arrays", "checkpoint")
    assert len(definition.canonical_bytes()) < 16 * 1024
    with pytest.raises(ValueError, match="current DEV parent"):
        initial_native_work(replace_context(context, task_id="foreign.task"), config, {"provenance": provenance}, {}, parent)


def test_development_projection_cache_repeats_cold_decimal_refusals(selected_bridge):
    from decimal import Inexact, Rounded, localcontext
    f = selected_bridge
    arguments = (f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()))
    owner.contracts(*arguments, produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)
    with localcontext() as context:
        context.prec = 1
        context.traps[Inexact] = False
        context.traps[Rounded] = True
        with pytest.raises(Rounded):
            owner.contracts.__wrapped__(*arguments, produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)
        misses = owner.contracts.cache_info().misses
        with pytest.raises(Rounded):
            owner.contracts(*arguments, produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)
        assert owner.contracts.cache_info().misses == misses + 1


def replace_context(context, **changes):
    return SimpleNamespace(**{**vars(context), **changes})


def test_failed_unknown_and_unentered_whole_cases_keep_complete_endpoints_and_receipt_pins(selected_bridge):
    f = selected_bridge
    original = tuple(r.SelectedE3E4CaseResult.unentered(case) for case in f.programme.cases)
    receipt = ObjectIdentity("receipt.actual-failed-placeholder", "empirical-lawhood/runtime/canonical-task-receipt", "1.0.0", "f" * 64)
    failed = replace(original[0], disposition="FAILED", numerical_disposition="UNKNOWN", score_disposition="FAILED",
        ordinary_receipts=(receipt,), reason_codes=("disclosed-software-failure",))
    unknown = replace(original[1], disposition="UNKNOWN", numerical_disposition="UNKNOWN", score_disposition="UNKNOWN",
        native=tuple(replace(value, disposition="UNKNOWN", reason_codes=("disclosed-contact-without-completion",)) for value in original[1].native),
        reason_codes=("disclosed-contact-without-completion",))
    result = science.reduce_cases(f.programme, (failed, unknown, *original[2:]), record_id="reduction.adverse-software-control")
    assert len(result.cases) == 288 and len(result.group_residuals) == 32
    assert result.cases[0].ordinary_receipts == (receipt,)
    assert result.cases[0].disposition == "FAILED" and result.cases[1].disposition == "UNKNOWN"
    assert all(value is None for _, scores in result.group_residuals for _, value in scores)
    assert decode_canonical_bytes(result.canonical_bytes(), type(result), maximum_bytes=None) == result


def test_actual_reader_shaped_failure_is_not_inferred_from_successful_receipt_map(selected_bridge):
    from empirical_lawhood.api.matrix_selected_e3_e4_read import incomplete_case
    case = selected_bridge.programme.cases[0]
    unentered = r.SelectedE3E4CaseResult.unentered(case)
    # This is the real reader shape: failed pure tasks have an authenticated
    # census/recovery event; scientific products['receipts'] contains successes.
    products = {"receipts": {}, "attempt_receipts": {}, "recovery_events": {}}
    census = ({"task_id": owner.local_node(case.root_id, "numerical"), "operational_status": "FAILED",
        "reason_code": "disclosed-software-pure-task-failure"},)
    failed = incomplete_case(case, products=products, task_census=census, native=unentered.native)
    assert failed.disposition == failed.score_disposition == "FAILED"
    assert failed.numerical_disposition == "UNKNOWN" and failed.ordinary_receipts == ()
    assert len(failed.paired_log_targets) == 30
    assert all(value.disposition == "UNENTERED" for value in failed.native)


def test_failed_case_preserves_actual_original_frozen_points_already_received(selected_bridge):
    from empirical_lawhood.api.matrix_selected_e3_e4_read import incomplete_case
    f, case = selected_bridge, selected_bridge.programme.cases[0]
    source = ScheduledPublicSource.from_source(f.bank.source(case.root_id,index=f.bank.source_index()))
    values = feature(f.selected, f.selected.sources[0][1]).values
    prefix = ObjectIdentity("causal.failed-after-account", r.SelectedE3E4CausalPrefix.SCHEMA, "1.0.0", "a" * 64)
    observed = r.SelectedE3E4Feature("feature.failed-after-account", case.source, prefix, case.root_id, case.independent_group_id,
        FAMILY_MAP[source.coordinate.family_id], source.coordinate.clock_id, D(".256"), "b" * 64, "AVAILABLE", values)
    account = r.SelectedE3E4AccountSeal("account.failed-after-forecast", f.bank.forecast_design.identity, case.source, prefix, observed,
        f.selected.package.identity, old.identity(f.selected.package.calibration),
        f.bank.forecast_design.package.predict(values=values, disposition="AVAILABLE"))
    baseline = r.SelectedE3E4CaseResult.unentered(case)
    census = ({"task_id": owner.local_node(case.root_id, "responses"), "operational_status": "FAILED"},)
    actual = incomplete_case(case, products={"receipts": {}}, task_census=census, native=baseline.native, account=account)
    assert actual.disposition == "FAILED" and actual.forecast == account.identity
    assert actual.original_log_points == account.log_points
    assert dict(actual.original_log_points)["SPECTRAL_RIDGE"] == (D(0), D(2), D(2)) * 5
    assert actual.paired_log_targets == (None,) * 30


def test_partial_original_targets_keep_finite_positions_and_full_paired30_denominator(selected_bridge):
    from decimal import localcontext
    from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponseLossCell, ScheduledResponseScore
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import ScheduledResponseTransitionControl

    f, case = selected_bridge, selected_bridge.programme.cases[0]
    protocol = f.bank.response_selection.protocols[0]
    panels = dict(f.bank.response_selection.panels)[case.independent_group_id]
    cells = tuple(sorted((ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
        None, None, None, None, None if predictor == PREDICTORS[0] and horizon == 128 else D(".5"))
        for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in PREDICTORS for horizon in protocol.horizon_steps), key=lambda value: value.key))
    # Literal received-score arithmetic only; this residual is disclosed and
    # never supplied as an acquired native branch or scientific qualification.
    control = ScheduledResponseTransitionControl("control.disclosed-paired-arithmetic",
        "SCHEDULED_PULSE_FULL192_LITERAL_TRACE_WORD_BAOAB_BOTH_KICKS", D(0), D(".01"), "SATISFIED", 1, 192, (D(0),), ())
    with localcontext() as context:
        context.prec = 50
        finite = D("1.5").ln()
    expected15 = (finite, finite, None, *((finite,) * 12))
    def pin(name, kind):
        return ObjectIdentity(name, kind.SCHEMA, kind.VERSION, "a" * 64)
    score = ScheduledResponseScore("score.disclosed-paired-arithmetic", case.source,
        pin("causal.disclosed", r.SelectedE3E4CausalPrefix), pin("account.disclosed", r.SelectedE3E4AccountSeal),
        pin("physical.disclosed", r.SelectedE3E4MechanicalForecast), pin("responses.disclosed", r.SelectedE3E4Responses),
        case.root_id, case.independent_group_id, "DEVELOPMENT", protocol.criterion, (control,), True, "PARTIAL", cells, expected15, ())
    observed = science.paired_targets(score, protocol, panels)
    assert observed == expected15 * 2 and len(observed) == 30
    assert observed.count(None) == 2 and sum(value is not None for value in observed) == 28

def test_scientific_root_retains_every_local_operand_and_distinct_original_subject(selected_bridge):
    f = selected_bridge
    root = owner.development_root(f.programme, f.bank, "study.selected-e4.operand-census", produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)
    hashes = {pin.object_fingerprint for pin in root.scientific_operands}
    configs = owner.contracts(f.programme, f.bank, f.evidence.identity, len(f.evidence.canonical_bytes()), produced_input_parents=f.evidence.produced_input_parents, secondary_readout=f.secondary_readout)[0]
    assert all(set(owner.digests(config)) <= hashes for _, config in configs)
    assert len({pin.object_id for pin in root.scientific_operands}) == len(root.scientific_operands)
    index=f.bank.source_index()
    for descriptor in f.bank.sources:
        source = r.SelectedE3E4NativeSourceReference.from_bank(f.programme,f.bank,descriptor,index=index)
        assert source.identity != source.reference.identity
        assert source.identity in root.scientific_operands
        assert source.reference.identity in root.scientific_operands
