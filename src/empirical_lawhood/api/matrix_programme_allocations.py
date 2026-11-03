# SPDX-License-Identifier: MPL-2.0
"""Publish the complete declared programme inputs before native TRAIN.

This compiler creates canonical metadata only. Actual source qualification,
sampling, issue, execution and protected access retain their ordinary owners.
"""

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import sys

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_researcher_programme.known_inputs import (
    PHASE_INPUT_ROLES, MatrixProgrammeInputCommitments, MatrixProgrammePhaseInputs, MatrixProgrammePublishedInput,
)
from empirical_lawhood.adapters.methods.matrix_researcher_programme.e1_allocation import (
    e1_allocation, ordinary_streams as _ordinary_streams,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import (
    ScheduledExposureAudit, authenticate_publication, corpus_artifact,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_population import (
    CONSTRUCTION, _selected_e4_population_members,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_streams import SelectedE4StreamRecipe
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.source_closure import require_admitted_target_source_current
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import validate_sha256, validate_stable_id
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
from empirical_lawhood.planning.approval import SystemDecisionClock
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, ArtifactWriteResult

from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import (
    ResolvedMatrixProgrammeInputs, ResolvedMatrixProgrammePhaseInputs, validate_programme_input_records,
)


_NATIVE_ROLES = {
    "e2": MatrixProgrammeRole.DEVELOPMENT, "train": MatrixProgrammeRole.DEVELOPMENT,
    "e3.calibration": MatrixProgrammeRole.CALIBRATION, "e3.confirmation": MatrixProgrammeRole.CONFIRMATION,
    "e4.development": MatrixProgrammeRole.DEVELOPMENT, "e4.calibration": MatrixProgrammeRole.CALIBRATION,
    "e4.confirmation": MatrixProgrammeRole.CONFIRMATION, "e5.development": MatrixProgrammeRole.DEVELOPMENT,
    "e5.confirmation": MatrixProgrammeRole.CONFIRMATION, "e6.nearby": MatrixProgrammeRole.WITHHELD_TRANSFER,
    "e6.shifted": MatrixProgrammeRole.WITHHELD_TRANSFER,
}
_FUTURE_ROLES = (("CALIBRATION", "e3.calibration"), ("EVALUATION", "e3.confirmation"),
    ("TRANSFER_NEARBY", "e6.nearby"), ("TRANSFER_SHIFTED", "e6.shifted"))


@dataclass(frozen=True, slots=True)
class PublishedMatrixProgrammeAllocations:
    resolved: ResolvedMatrixProgrammeInputs
    commitment: MatrixProgrammePublishedInput
    audit: ScheduledExposureAudit
    audit_publication: ArtifactWriteResult
    provenance: NumericalProducingProvenance
    output_bytes: int


@dataclass(frozen=True, slots=True)
class _Population:
    name: str
    coordinates: tuple
    roots: tuple
    scopes: tuple
    numerical_design: object
    prefix_policies: tuple
    coordinate_policies: tuple


def _process_rss_bytes():
    """Observe bounded current Linux RSS, without claiming a peak-memory proof."""
    try:
        with Path("/proc/self/status").open("rb") as stream:
            raw = stream.read(65537)
    except OSError as error:
        raise ValueError("programme metadata requires the selected Linux current-RSS observation") from error
    if len(raw) > 65536:
        raise ValueError("programme current-RSS observation exceeds its bounded host record")
    rows = tuple(row.split() for row in raw.splitlines() if row.startswith(b"VmRSS:"))
    if len(rows) != 1 or len(rows[0]) != 3 or rows[0][2] != b"kB" or not rows[0][1].isdigit():
        raise ValueError("programme metadata cannot observe the selected Linux current RSS")
    return int(rows[0][1]) * 1024


def _body_size(value, seen=None):
    """Measure actual immutable Python shapes, without traversing class graphs."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if is_dataclass(value):
        size += sum(_body_size(getattr(value, field.name), seen) for field in fields(value))
    elif type(value) in (tuple, list, set, frozenset):
        size += sum(_body_size(item, seen) for item in value)
    elif type(value) is dict:
        size += sum(_body_size(key, seen) + _body_size(item, seen) for key, item in value.items())
    return size


def _require_memory(limit):
    from empirical_lawhood.runtime.metadata_memory import metadata_rss_limit
    limit = metadata_rss_limit(limit)
    if _process_rss_bytes() > limit:
        from empirical_lawhood.infrastructure.process_memory import release_unused_process_memory
        # Completed metadata decodes can leave free allocator pages resident.
        # Reclaim only unused storage, then enforce the selected actual RSS limit.
        release_unused_process_memory()
        if _process_rss_bytes() > limit:
            raise ValueError("programme metadata exceeds its selected current-process memory ceiling")


def _admit_source_plan(*, design, census, namespace, material, budget, source_bytes):
    """Refuse oversized cardinalities before constructing group/root tuples.

    Shared scientific operands are deliberately charged once per root here.
    This measured-shape overestimate and later RSS checkpoints are operational
    admission, not a guarantee about unobserved peaks or native graph capacity.
    """
    counts = dict(design.phase_group_counts)
    roots = sum(count * (9 if role.startswith("e4.") else 1) for role, count in counts.items())
    groups = sum(counts.values())
    width = max(3, len(str(max(counts.values()) - 1)))
    group = "group." + namespace + ".e4.confirmation.3." + "9" * width
    coordinate = max((*design.e1_coordinates, *design.training_protocol.coordinates,
        *design.e2.coordinates, *design.e4_preparation_coordinates), key=_body_size)
    row = scheduled.ScheduledRoot(MatrixProgrammeRoot("root." + group + ".8", group,
        "regime." + coordinate.coordinate_id, coordinate.coordinate_id, MatrixProgrammeRole.CONFIRMATION,
        coordinate.clock_id), scheduled.coordinate_identity(coordinate), _ordinary_streams(material, group))
    policy_bytes = max(_body_size(policy) for policy in (*design.training_protocol.prefix_policies, *design.e2.prefix_policies))
    assay_bytes = max(_body_size(design.training_assay), _body_size(design.e2.assay))
    # Charge source/protocol objects and several live maps/sets using their real
    # selected shapes. These charges overcount shared operands and E4 streams.
    ownership = {stream.effective_seed: ("e4.confirmation", group, "INDEPENDENT_FUTURE", stream.purpose)
        for stream in row.streams}
    row_bytes = _body_size(row) + _body_size(coordinate) + policy_bytes + assay_bytes + 4 * _body_size(ownership)
    constant_bytes = _body_size(design) + _body_size(census) + source_bytes
    estimate = constant_bytes + roots * row_bytes + groups * _body_size((group, row.streams))
    if _process_rss_bytes() + estimate > budget.memory_bytes:
        raise ValueError("programme source cardinalities exceed the conservative selected current-process memory ceiling")
    # Every root is embedded in at least one allocation. This lower bound is a
    # cheap early refusal; cumulative exact writes enforce the full byte limit.
    if roots * len(row.canonical_bytes()) > budget.output_bytes:
        raise ValueError("programme source cardinalities exceed the selected metadata output-byte lower bound")


def _source_plan(*, design, census, namespace, root_material, future_material, e4_streams,
        e5_root_material, e5_future_material, checkpoint=None):
    """Build all actual members and check the complete cross-phase ownership."""
    design.__post_init__()
    census.__post_init__()
    counts = dict(design.phase_group_counts)
    if tuple(counts) != PHASE_INPUT_ROLES:
        raise ValueError("programme design changes its complete input-role census")
    if len(design.e2.coordinates) != 1:
        raise ValueError("programme E2 requires one explicit coordinate; multiple coordinates need an explicit allocation rule")
    groups, futures, populations = {}, {}, []
    e1 = e1_allocation(namespace=namespace, coordinates=design.e1_coordinates,
        family_requirements=design.e1_criterion.family_requirements, census=census, root_material=root_material)
    groups["e1"] = tuple(sorted(row.root.independent_group_id for row in e1.roots))
    if checkpoint is not None:
        checkpoint()

    def ordinary_population(name, roles, coordinates, scientific):
        roots, scopes = [], []
        selected = {}
        for role, coordinate in zip(roles, coordinates, strict=True):
            pin = scheduled.coordinate_identity(coordinate)
            selected[pin] = coordinate
            assigned = tuple("group." + namespace + "." + role + "." + str(index).zfill(3)
                for index in range(counts[role]))
            groups[role] = assigned
            material = e5_root_material if role.startswith("e5.") else root_material
            future = e5_future_material if role.startswith("e5.") else future_material
            for group in assigned:
                root = MatrixProgrammeRoot("root." + group, group, "regime." + coordinate.coordinate_id,
                    coordinate.coordinate_id, _NATIVE_ROLES[role], coordinate.clock_id)
                roots.append(scheduled.ScheduledRoot(root, pin, _ordinary_streams(material, group)))
                futures[group] = _ordinary_streams(future, group)
            scopes.append(scheduled.ScheduledMatchedScope("scope." + namespace + "." + role,
                _NATIVE_ROLES[role], assigned, (pin,), CONSTRUCTION))
        policy_by_coordinate = dict(scientific.coordinate_policies)
        policy_pins = {policy_by_coordinate[pin] for pin in selected}
        populations.append(_Population(name, tuple(sorted(selected.values(), key=lambda co: co.coordinate_id)),
            tuple(sorted(roots, key=lambda row: row.root.root_id)), tuple(sorted(scopes, key=lambda row: row.scope_id)),
            scientific.numerical_design, tuple(policy for policy in scientific.prefix_policies
                if scheduled.identity(policy) in policy_pins),
            tuple(sorted(((pin, policy_by_coordinate[pin]) for pin in selected), key=lambda row: row[0].object_id))))
        if checkpoint is not None:
            checkpoint()

    ordinary_population("e2", ("e2",), design.e2.coordinates, design.e2)
    coordinates = {scheduled.coordinate_identity(co): co for co in design.training_protocol.coordinates}
    role_coordinates = dict(design.e3.role_coordinates)
    nominal = coordinates[role_coordinates["TRAIN"]]
    ordinary_population("train", ("train",), (nominal,), design.training_protocol)
    ordinary_population("future", tuple(role for _, role in _FUTURE_ROLES),
        tuple(coordinates[role_coordinates[role]] for role, _ in _FUTURE_ROLES), design.training_protocol)
    ordinary_population("e5", ("e5.development", "e5.confirmation"), (nominal, nominal), design.training_protocol)

    preparations = tuple(sorted(design.e4_preparation_coordinates, key=lambda co: co.family_id))
    designs = (("CALIBRATION", design.e4_calibration), ("CONFIRMATION", design.e4_confirmation),
        ("DEVELOPMENT", design.e4_development))
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_population import selected_e4_population_groups
    e4_groups = selected_e4_population_groups(namespace=namespace + '.e4', population_designs=designs,
        preparations=preparations, streams=e4_streams)
    e4_history = tuple((group, e4_streams.streams(group, future=False))
        for group in sorted(group for _, _, assigned in e4_groups for group in assigned))
    e4_coordinates, roots, scopes = _selected_e4_population_members(namespace=namespace + ".e4",
        preparations=preparations, population_designs=designs, group_ids=e4_groups, history_streams=e4_history)
    nominal_policy_pin = dict(design.training_protocol.coordinate_policies)[role_coordinates["TRAIN"]]
    nominal_policy, = (policy for policy in design.training_protocol.prefix_policies
        if scheduled.identity(policy) == nominal_policy_pin)
    populations.append(_Population("e4", e4_coordinates, roots, scopes, design.training_protocol.numerical_design,
        (nominal_policy,), tuple((scheduled.coordinate_identity(co), nominal_policy_pin) for co in e4_coordinates)))
    if checkpoint is not None:
        checkpoint()
    for phase, _, assigned in e4_groups:
        role = "e4." + phase.lower()
        groups[role] = tuple(sorted((*groups.get(role, ()), *assigned)))
        for group in assigned:
            futures[group] = e4_streams.streams(group, future=True)

    # A repeated E4 coordinate is one matched case of its original group. All
    # other cross-role group or effective stream sharing is refused here.
    group_owner, seed_owner, nontransfer, transfer = {}, {}, set(), set()
    exposed_groups, exposed_seeds = set(census.exposed_independent_groups), set(census.effective_seed_exclusions)
    for role in PHASE_INPUT_ROLES:
        if len(groups[role]) != counts[role]:
            raise ValueError("programme source plan changes its complete assigned group denominator")
        for group in groups[role]:
            if group in exposed_groups or group_owner.setdefault(group, role) != role:
                raise ValueError("programme source plan reuses an exposed or cross-phase group")
    all_rows = [("e1", row, next(co for co in e1.coordinates if scheduled.coordinate_identity(co) == row.coordinate))
        for row in e1.roots]
    for population in populations:
        by_coordinate = {scheduled.coordinate_identity(co): co for co in population.coordinates}
        for row in population.roots:
            role = group_owner[row.root.independent_group_id]
            all_rows.append((role, row, by_coordinate[row.coordinate]))
        # These checks do not need an invented allocation or publication.
        by_root = {row.root.root_id: row for row in population.roots}
        if len(by_root) != len(population.roots):
            raise ValueError("programme source plan aliases different native roots")
        for scope in population.scopes:
            if len({scheduled.matched_key(by_coordinate[pin]) for pin in scope.coordinates}) != 1:
                raise ValueError("programme source plan changes matched preparation clocks")
    for role, row, coordinate in all_rows:
        group = row.root.independent_group_id
        if row.root.clock_id != coordinate.clock_id:
            raise ValueError("programme source plan changes its actual root clock")
        (transfer if role.startswith("e6.") else nontransfer).add(scheduled.physical_key(coordinate))
        for category, streams in (("history", row.streams), ("future", futures.get(group, ()))):
            for stream in streams:
                owner = (role, group, category, stream.purpose)
                if stream.effective_seed in exposed_seeds or seed_owner.setdefault(stream.effective_seed, owner) != owner:
                    raise ValueError("programme source plan reuses exposed or cross-phase effective streams")
    prior = {value.key for value in census.scheduled_physical_exclusions}
    constant = {value.key for value in census.constant_physical_exclusions}
    if (len(transfer) != 2 or transfer & (nontransfer | prior)
            or any((key[0], key[1], key[2], key[3], key[5], key[4], key[7], key[8]) in constant for key in transfer)):
        raise ValueError("programme source plan consumes a full physical key reserved for E6")
    families = {co.family_id: sorted(row.root.independent_group_id for row in roots
        if row.root.role is MatrixProgrammeRole.DEVELOPMENT
        and row.coordinate in {scheduled.coordinate_identity(value) for value in e4_coordinates if value.family_id == co.family_id})
        for co in preparations}
    # Nine matched coordinates must not count as nine revision units.
    families = {family: sorted(set(assigned)) for family, assigned in families.items()}
    folds = tuple(sorted((families[family][ordinal], fold) for family, ordinal, fold in design.e4_revision.fold_slots))
    if {group for group, _ in folds} != set(groups["e4.development"]):
        raise ValueError("programme source plan changes the complete pre-TRAIN E4 fold assignment")
    return e1, tuple(populations), groups, futures, folds


def publish_matrix_programme_allocations(*, design, census, namespace,
        root_seed_material_sha256, future_seed_material_sha256, e4_streams,
        e5_root_seed_material_sha256, e5_future_seed_material_sha256, provenance,
        support_publications, file_bindings, request_path, project_root, artifact_writer,
        metadata_directory, execution, metadata_budget, validate_copied_inputs=None, _admitted_source=None):
    """Publish known inputs C after all prospective child metadata, without entry."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_protocol import project_protected_e3_protocol
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import build_e6_transport_policy
    from empirical_lawhood.infrastructure.matrix_array_io import decode_matrix_arrays
    from .experiment_preparation import _input_member
    from .matrix_numerical_provenance import capture_matrix_provenance
    from .selected_e4_bank_recipe import _current_selection, _metadata_record_size, _publication_from_manifest

    validate_stable_id(namespace)
    if validate_copied_inputs is not None and not callable(validate_copied_inputs):
        raise TypeError("programme copied-input boundary requires a callable byte validator")
    if (type(design) is not MatrixProgrammeScientificDesign or type(census) is not MatrixFactorExposureCensus
            or type(provenance) is not NumericalProducingProvenance or type(e4_streams) is not SelectedE4StreamRecipe
            or type(metadata_budget) is not ResourceBudget):
        raise TypeError("programme allocation requires exact scientific inputs, stream materials and an explicit metadata budget")
    for value in (design, census, provenance, e4_streams, metadata_budget):
        value.__post_init__()
    materials = (root_seed_material_sha256, future_seed_material_sha256,
        e4_streams.prefix_seed_material_sha256, e4_streams.future_seed_material_sha256,
        e5_root_seed_material_sha256, e5_future_seed_material_sha256)
    if e4_streams.family_seed_material_sha256 is not None:
        materials = (*materials, e4_streams.family_seed_material_sha256)
    for value in materials:
        validate_sha256(value)
    if len(set(materials)) != len(materials):
        raise ValueError("programme allocation requires distinct explicit history/future/family seed materials")
    for name in ("memory_bytes", "source_scan_bytes", "output_bytes"):
        if type(getattr(metadata_budget, name)) is not int or getattr(metadata_budget, name) < 1:
            raise ValueError("programme metadata requires a finite positive " + name)
    root, admitted = _current_selection(project_root=project_root, artifact_writer=artifact_writer, execution=execution,
        _admitted_source=_admitted_source)
    current = capture_matrix_provenance(project_root=root, _admitted_source=admitted)
    if current != provenance or current.observed_git_head != admitted.implementation_commit:
        raise ValueError("programme allocation changes its actual selected numerical/source provenance")
    directory = Path(metadata_directory)
    plane = Path(artifact_writer.root.contract.canonical_path)
    if (not directory.is_absolute() or directory != directory.resolve(strict=False)
            or directory == plane or not directory.is_relative_to(plane) or directory.is_relative_to(root)):
        raise ValueError("programme allocation requires its exact separate guarded metadata directory")
    prefix = directory.relative_to(plane).as_posix()
    artifact_writer.root.resolve(prefix + "/publications/commitments.json", for_write=True)

    # One NPZ can serve more than one assay. Its byte identity does not make
    # either declaration's member hashes authoritative for its sibling.
    assays = (design.training_assay, design.e2.assay)
    templates = {artifact: tuple(assay for assay in assays if assay.array_artifact == artifact)
        for artifact in {assay.array_artifact for assay in assays}}
    if design.prepared_assay.template_artifact not in templates:
        raise ValueError("prepared assay requires its actual complete shared template publication")
    scalar_records = {design.e1_factor_rule.scalar_closure.normalization_owner: design.e1_scalar_definition,
        design.training_protocol.scalar_artifact: design.training_protocol.scalar_definition}
    for policy in design.e2.prefix_policies:
        owner = policy.factor_rule.scalar_closure.normalization_owner
        previous = scalar_records.setdefault(owner, design.e2.scalar_definition)
        if previous != design.e2.scalar_definition:
            raise ValueError("programme aliases different typed scalar definitions")
    expected = set(templates) | set(scalar_records)
    if (type(support_publications) is not tuple
            or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not ArtifactIdentity
                or type(row[1]) is not ArtifactWriteResult for row in support_publications)
            or tuple(artifact.artifact_id for artifact, _ in support_publications) !=
                tuple(sorted({artifact.artifact_id for artifact, _ in support_publications}))
            or not {artifact for artifact, _ in support_publications} <= expected):
        raise ValueError("programme allocation substitutes declared template or scalar publications")
    normalization = design.training_protocol.full_factor_rule.scalar_closure.normalization_owner
    provided = {artifact for artifact, _ in support_publications}
    needed_files = (set(templates) - provided) | {normalization}
    if (type(file_bindings) is not tuple
            or any(type(row) is not ExperimentFileInputBinding for row in file_bindings)
            or len(file_bindings) != len(needed_files) or {row.identity for row in file_bindings} != needed_files):
        raise ValueError("programme allocation requires exact unpublished templates and original normalization FILE bindings")
    for binding in file_bindings:
        binding.__post_init__()
    bindings = {row.identity: row for row in file_bindings}
    source_bytes = sum(artifact.size_bytes for artifact in expected) + normalization.size_bytes
    source_bytes += len(design.canonical_bytes()) + len(census.canonical_bytes()) + len(provenance.canonical_bytes())
    if source_bytes > metadata_budget.source_scan_bytes or source_bytes > metadata_budget.memory_bytes:
        raise ValueError("programme metadata input bodies exceed the selected source or materialized-byte budget")
    _admit_source_plan(design=design, census=census, namespace=namespace, material=root_seed_material_sha256,
        budget=metadata_budget, source_bytes=source_bytes)
    e1, populations, groups, futures, folds = _source_plan(design=design, census=census, namespace=namespace,
        root_material=root_seed_material_sha256, future_material=future_seed_material_sha256, e4_streams=e4_streams,
        e5_root_material=e5_root_seed_material_sha256, e5_future_material=e5_future_seed_material_sha256,
        checkpoint=lambda: _require_memory(metadata_budget.memory_bytes))
    design.e1_criterion.validate_allocation(e1, design.e1_factor_rule)
    for population in populations:
        scheduled._validate_allocation_members(population.coordinates, population.roots, population.scopes,
            census=census, prior_scheduled_coordinates=())
    output_bytes = 0
    with artifact_writer.verification_scope() as writer:
        template_pubs = {}
        scalar_pubs = {}
        original_files = {}
        for artifact, binding in bindings.items():
            path = _input_member(Path(request_path).parent, binding.relative_path)
            raw = read_bounded_bytes(path, maximum_bytes=artifact.size_bytes)
            if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
                raise ValueError("programme support FILE changes its exact original bytes")
            if artifact in templates:
                for assay in templates[artifact]:
                    decode_matrix_arrays(raw, assay)
            original_files[artifact] = (path, raw)
        for artifact, publication in support_publications:
            artifact.__post_init__()
            authenticate_publication(writer, publication)
            logical, material = publication.logical, publication.materialization
            if (artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes,
                    OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE) != (
                    logical.logical_artifact_id, logical.payload_schema, logical.content_sha256, logical.media_type,
                    material.size_bytes, logical.outcome_access, logical.visibility_ceiling):
                raise ValueError("programme support changes its actual complete original publication")
            raw = read_bounded_bytes(writer.root.resolve(material.relative_path, for_write=False), maximum_bytes=artifact.size_bytes)
            if (len(raw), sha256(raw).hexdigest()) != (artifact.size_bytes, artifact.sha256):
                raise ValueError("programme support changes its exact original bytes")
            if artifact in templates:
                for assay in templates[artifact]:
                    decode_matrix_arrays(raw, assay)
                template_pubs[artifact] = publication
            elif raw != scalar_records[artifact].canonical_bytes():
                raise ValueError("programme support substitutes its typed scalar definition bytes")
            else:
                definition = scalar_records[artifact]
                pin = ObjectIdentity.from_record(definition.definition_id, definition)
                selected = MatrixProgrammePublishedInput(pin, publication)
                selected.require_record(definition, pin)
                if scalar_pubs.setdefault(pin.object_id, (definition, selected)) != (definition, selected):
                    raise ValueError("programme support aliases different actual scalar definitions or custody")
        normalization_raw = original_files[normalization][1]
        normalization_request = ArtifactWriteRequest(normalization.artifact_id,
            prefix + "/publications/normalization.bin", normalization.payload_schema,
            ArtifactProfile.RAW_SOURCE_BYTES, normalization.media_type, namespace, prefix,
            normalization_raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)
        # Original Python-source custody has an installed typed byte codec.
        # Admit the selected writer before publishing any programme metadata;
        # the generic raw profile must not silently widen to replace that codec.
        writer.preflight_write(normalization_request)
        coordinates = {scheduled.coordinate_identity(co): co for co in design.training_protocol.coordinates}
        selected = dict(design.e3.role_coordinates)
        for ordinal, policy in enumerate(design.training_protocol.prefix_policies):
            project_protected_e3_protocol(specification=design.e3, nominal=coordinates[selected["CALIBRATION"]],
                nearby=coordinates[selected["TRANSFER_NEARBY"]], shifted=coordinates[selected["TRANSFER_SHIFTED"]],
                mathematical_protocol=design.training_protocol.mathematical_protocol,
                original_factor_rule=design.training_protocol.full_factor_rule, prefix_policy=policy,
                scalar_definition=design.training_protocol.scalar_definition, normalization_source=normalization,
                normalization_source_bytes=normalization_raw, record_id="projection." + namespace + "." + str(ordinal))

        def require_original_files():
            if validate_copied_inputs is not None and validate_copied_inputs() is not None:
                raise ValueError("programme copied-input validator must return None or raise")
            for artifact, (path, raw) in original_files.items():
                current_path = _input_member(Path(request_path).parent, bindings[artifact].relative_path)
                if (current_path != path or read_bounded_bytes(current_path, maximum_bytes=artifact.size_bytes) != raw):
                    raise ValueError("programme support FILE changed during dependent publication")

        # All allocation, mathematical projection and FILE checks precede the
        # first write. Scalars are current mathematical records, not old issues.
        support_writes = []
        missing_support = expected - provided
        for artifact in sorted(missing_support, key=lambda row: row.artifact_id):
            raw = original_files[artifact][1] if artifact in templates else scalar_records[artifact].canonical_bytes()
            support_writes.append(ArtifactWriteRequest(artifact.artifact_id,
                prefix + "/support/" + artifact.sha256 + (".npz" if artifact in templates else ".json"),
                artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ if artifact in templates else ArtifactProfile.CANONICAL_JSON,
                artifact.media_type, namespace + ".support", prefix + "/support", raw,
                VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
        support_size = sum(len(row.payload) for row in support_writes)
        if support_size > metadata_budget.output_bytes or support_size + source_bytes > metadata_budget.memory_bytes:
            raise ValueError("programme support publication exceeds the selected metadata resources")
        require_original_files()
        if support_writes:
            publications = writer.write_batch(tuple(support_writes))
            output_bytes += support_size
            for result in publications:
                publication = _publication_from_manifest(writer, writer.read_manifest(result.materialization.relative_path))
                artifact, = (row for row in missing_support if row.artifact_id == publication.logical.logical_artifact_id)
                if artifact in templates:
                    template_pubs[artifact] = publication
                else:
                    definition = scalar_records[artifact]
                    pin = ObjectIdentity.from_record(definition.definition_id, definition)
                    value = MatrixProgrammePublishedInput(pin, publication)
                    value.require_record(definition, pin)
                    if scalar_pubs.setdefault(pin.object_id, (definition, value)) != (definition, value):
                        raise ValueError("programme support aliases different scalar definitions")

        def write(request):
            nonlocal output_bytes
            _require_memory(metadata_budget.memory_bytes)
            _metadata_record_size(writer, len(request.payload))
            output_bytes += len(request.payload)
            if output_bytes > metadata_budget.output_bytes or source_bytes + len(request.payload) > metadata_budget.memory_bytes:
                raise ValueError("programme metadata exceeds selected actual output or materialized-byte limits")
            writer.write(request)
            return _publication_from_manifest(writer, writer.read_manifest(request.relative_path))

        def publication_request(key, record):
            _require_memory(metadata_budget.memory_bytes)
            raw = record.canonical_bytes()
            _require_memory(metadata_budget.memory_bytes)
            return ArtifactWriteRequest(namespace + "." + key, prefix + "/publications/" + key + ".json",
                record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", namespace, prefix,
                raw, VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND)

        def publish(key, record, *, identity=None):
            publication = write(publication_request(key, record))
            pin = scheduled.identity(record) if identity is None else identity
            result = MatrixProgrammePublishedInput(pin, publication)
            result.require_record(record, pin)
            return result

        design_pub = publish("design", design)
        census_pub = publish("census", census, identity=census.identity)
        audit = ScheduledExposureAudit("audit." + namespace, census, (), (census_pub.publication,))
        audit_pub = publish("audit", audit)
        provenance_pub = publish("producing-provenance", provenance, identity=provenance.identity)
        normalization_pub = write(normalization_request)
        exposure = scheduled.ScheduledExposure("exposure." + namespace, census, (), corpus_artifact(audit_pub.publication))
        e1_reservation = E1AllocationReservation("reservation." + namespace + ".e1", e1, publish("e1.allocation", e1).publication)
        e1_pub = publish("e1.reservation", e1_reservation)
        phases = {"e1": ResolvedMatrixProgrammePhaseInputs("e1", e1_reservation, None, None)}
        references = {"e1": MatrixProgrammePhaseInputs("e1", e1_pub, None, None)}
        for population in populations:
            allocation = scheduled.ScheduledAllocation("allocation." + namespace + "." + population.name,
                population.coordinates, population.roots, population.scopes, exposure)
            reservation = scheduled.ScheduledReservation("reservation." + namespace + "." + population.name,
                allocation, publish(population.name + ".allocation", allocation).publication)
            reservation_pub = publish(population.name + ".reservation", reservation)
            selection = scheduled.ScheduledSelection("selection." + namespace + "." + population.name,
                scheduled.identity(reservation), population.numerical_design, population.prefix_policies,
                population.coordinate_policies)
            specification = scheduled.ScheduledSpecification("specification." + namespace + "." + population.name,
                selection, publish(population.name + ".selection", selection).publication)
            specification_pub = publish(population.name + ".specification", specification)
            index = ScheduledSourceIndex.from_shared(reservation=reservation, specification=specification, provenances=(provenance,))
            for role in PHASE_INPUT_ROLES[1:]:
                assigned = set(groups[role])
                roots = tuple(row for row in allocation.roots if row.root.independent_group_id in assigned)
                if not roots:
                    continue
                assay = design.e2.assay if role == "e2" else design.training_assay
                protocols = []
                panels = {}
                for row in roots:
                    source = index.resolve(index.reference(source_id="source." + row.root.root_id,
                        root_id=row.root.root_id, provenance=provenance.identity))
                    protocols.append(assay.bind(source, protocol_id="protocol." + source.root_id))
                    group = row.root.independent_group_id
                    panels[group] = (ScheduledResponsePanel("panel.common." + group, group, "COMMON_NOISE_PANEL",
                        "ORIGINAL_COMPLETED_PREFIX_GENERATOR_STATES", row.streams),
                        ScheduledResponsePanel("panel.independent." + group, group, "INDEPENDENT_FUTURE",
                            "FRESH_DECLARED_FUTURE_START_AT_CUTOFF", futures[group]))
                criterion = (design.e3_calibration_criterion if role == "e3.calibration" else
                    design.e4_calibration_criterion if role == "e4.calibration" else None)
                responses = ScheduledResponseSelection("responses." + namespace + "." + role, ObjectIdentity.from_record(allocation.allocation_id, allocation),
                    tuple(protocols), tuple(sorted(panels.items())), (template_pubs[assay.array_artifact],), criterion)
                responses.validate_allocation(allocation)
                responses_pub = publish(role + ".responses", responses)
                phases[role] = ResolvedMatrixProgrammePhaseInputs(role, reservation, specification, responses)
                references[role] = MatrixProgrammePhaseInputs(role, reservation_pub, specification_pub, responses_pub)
        clock = SystemDecisionClock()
        availability_path = writer.root.resolve(prefix + "/publications/pretrain-availability.json", for_write=False)
        if availability_path.exists():
            maximum_bytes = min(metadata_budget.source_scan_bytes - source_bytes,
                metadata_budget.memory_bytes - source_bytes, metadata_budget.output_bytes)
            if maximum_bytes < 1:
                raise ValueError("programme retained availability exceeds its selected input-byte limits")
            raw = read_bounded_bytes(availability_path, maximum_bytes=maximum_bytes)
            source_bytes += len(raw)
            availability = decode_canonical_bytes(raw, AvailabilitySpec, maximum_bytes=len(raw))
            if (availability.clock_id != clock.clock_id or availability.phase is not CausalPhase.PREPARATION
                    or availability.outcome_access is not OutcomeAccess.OUTCOME_BLIND or availability.available_at is None):
                raise ValueError("programme retained availability changes its actual preparation clock or blind access")
        else:
            if writer.root.resolve(prefix + "/publications/pretrain-availability.json.manifest.json", for_write=False).exists():
                raise ValueError("programme retained availability payload is missing; its original clock cannot be reconstructed")
            now = datetime.fromisoformat(clock.now_utc().replace("Z", "+00:00"))
            availability = AvailabilitySpec(clock.clock_id, CausalPhase.PREPARATION, OutcomeAccess.OUTCOME_BLIND,
                Decimal(int(now.timestamp())))
        # A complete payload may precede its sidecar or commit marker. Admit
        # only its exact committed custody or the writer's durable intent;
        # ordinary immutable publication then owns completion of that intent.
        # Matching unowned bytes must not establish the original availability.
        writer.preflight_write(publication_request("pretrain-availability", availability))
        availability_pin = ObjectIdentity.from_record(namespace + ".pretrain-availability", availability)
        availability_pub = publish("pretrain-availability", availability, identity=availability_pin)
        future_reservation = phases["e3.calibration"].reservation
        future_responses = tuple((role, phases[slot].responses) for role, slot in _FUTURE_ROLES)
        policy = build_e6_transport_policy(record_id="policy." + namespace + ".e6",
            candidate_specification=design.e3, future_reservation=future_reservation,
            future_response_selections=future_responses, availability=(availability_pin, availability),
            criterion=design.e6_policy.criterion)
        policy_pub = publish("e6-policy", policy)
        scalar_rows = tuple(value for _, value in sorted(scalar_pubs.items()))
        commitments = MatrixProgrammeInputCommitments(record_id="commitments." + namespace, namespace=namespace,
            scientific_design=design_pub, exposure_census=census_pub, exposure_audit=audit_pub,
            producing_provenance=provenance_pub, scalar_definitions=tuple(selected for _, selected in scalar_rows),
            support_files=((normalization, normalization_pub),),
            phases=tuple(references[role] for role in PHASE_INPUT_ROLES), revision_folds=folds,
            availability=availability_pub, e6_policy=policy_pub, e4_streams=e4_streams)
        resolved = ResolvedMatrixProgrammeInputs(commitments=commitments, scientific_design=design,
            exposure_census=census, exposure_audit=audit, producing_provenance=provenance,
            scalar_definitions=tuple(definition for definition, _ in scalar_rows),
            phases=tuple(phases[role] for role in PHASE_INPUT_ROLES), availability=availability, e6_policy=policy)
        validate_programme_input_records(resolved)
        require_admitted_target_source_current(root, admitted)
        if capture_matrix_provenance(project_root=root, _admitted_source=admitted) != provenance:
            raise ValueError("programme actual source changed before its final input commitment")
        require_original_files()
        commitment = publish("commitments", commitments)
        require_original_files()
        return PublishedMatrixProgrammeAllocations(resolved, commitment, audit, audit_pub.publication, provenance,
            output_bytes)
