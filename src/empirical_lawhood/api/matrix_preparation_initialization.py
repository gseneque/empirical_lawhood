# SPDX-License-Identifier: MPL-2.0
"""Publish declared Matrix initial conditions after actual original custody.

Initialization is deterministic configuration construction. It consumes zero
random streams, acquires no trajectory and grants no scientific authority.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_experimental_programme import preparation_initialization as domain
from empirical_lawhood.adapters.methods.matrix_experimental_programme.preparation_initialization_science import initialize_source
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from .matrix_prepared_source_runtime import (
    _committed_e4_selections, _e4_phases, _native_training_prerequisite, _read_development_controls, _require_current_exposure_subset,
    _future_source_selections,
)
from empirical_lawhood.infrastructure.source_origin import require_selected_implementation
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling, inherited_visibility
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding, ExperimentFileInputSelection, ExperimentInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest, derived_outcome_access
from empirical_lawhood.runtime.experiment_preparation import ExperimentInputDerivationResult


@contextmanager
def authenticated_initialization_request(*, writer, request, maximum_source_bytes):
    """Keep whole C and the actual original sequence guarded through publication."""
    request.__post_init__()
    if type(maximum_source_bytes) is not int or maximum_source_bytes < 1:
        raise ValueError("initialization requires the actual selected positive source byte bound")
    limit = min(maximum_source_bytes, request.original_commitments.maximum_source_bytes)
    _, original, _, _ = _native_training_prerequisite(writer, request.original_commitments.native_training_locator)
    with _committed_e4_selections(writer, request.original_commitments.input_commitments, original,
            maximum_source_bytes=limit, native_training_locator=request.original_commitments.native_training_locator) as inputs:
        _authenticate_initialization_sources(writer=writer, request=request, original=original,
            future=_future_source_selections(inputs), e4_phases=_e4_phases(inputs), inputs=inputs)
        yield


def authenticate_initialization_request(*, writer, request, maximum_source_bytes):
    """Standalone authentication with its final complete original byte guards."""
    with authenticated_initialization_request(writer=writer, request=request, maximum_source_bytes=maximum_source_bytes):
        return None


def _authenticate_initialization_sources(*, writer, request, original, future, e4_phases, inputs):
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_originals import _authenticate_artifact
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
    sources = request.sources
    for artifact, custody in request.exposure_support:
        _authenticate_artifact(writer, artifact, custody)
    for value, publication in ((sources.reservation.allocation, sources.reservation.publication),
            (sources.specification.selection, sources.specification.publication), (sources.audit, sources.audit_publication)):
        authenticate_publication(writer, publication, value)
    records = (sources.audit.census, *sources.audit.prior_scheduled_coordinates)
    for publication in sources.audit.prior_corpus:
        matches = tuple(record for record in records if (record.SCHEMA, record.fingerprint()) ==
            (publication.logical.payload_schema, publication.logical.content_sha256))
        if len(matches) != 1:
            raise PermissionError("initialization changes original complete exposure corpus")
        authenticate_publication(writer, publication, matches[0])
    index = sources.source_index()
    selected = tuple(sources.source(descriptor, index=index) for descriptor in sources.descriptors)
    roles = {"E5_OPPORTUNITY": ("e5.development",), "E5_CONFIRMATION": ("e5.confirmation",),
        "E6_TRANSFER": ("e6.nearby", "e6.shifted")}[request.phase]
    expected = {}
    for role in roles:
        phase = inputs.phase(role)
        for protocol in phase.responses.protocols:
            public = protocol.public_source
            root, = (row for row in phase.reservation.allocation.roots if row.root.root_id == public.root.root_id)
            if public.root.root_id in expected:
                raise PermissionError("initialization C repeats an original assigned phase root")
            expected[public.root.root_id] = root, public
    if {value.root_id for value in selected} != set(expected):
        raise PermissionError("initialization changes C's complete original assigned phase roots")
    for value in selected:
        root, public = expected[value.root_id]
        if (value.root != root or value.coordinate != public.coordinate or value.policy != public.policy
                or value.source_id != public.source.object_id or value.provenance != inputs.producing_provenance):
            raise PermissionError("initialization changes C's actual groups, streams, physics or producing source")
    if request.phase == "E6_TRANSFER":
        expected = original.future_manifest
        if (sources.reservation != expected.reservation or sources.specification != expected.native_specification
                or sources.audit != expected.audit or sources.audit_publication != expected.audit_publication):
            raise PermissionError("initialization changes the exact original pre-TRAIN transfer reserve")
        protocols = tuple(protocol for role, selection in future if role in ("TRANSFER_NEARBY", "TRANSFER_SHIFTED")
            for protocol in selection.protocols)
        expected_sources = {protocol.public_source.root.root_id: protocol.public_source for protocol in protocols}
        actual_sources = {source.root_id: ScheduledPublicSource.from_source(source) for source in selected}
        if len(expected_sources) != len(protocols) or actual_sources != expected_sources:
            raise PermissionError("initialization thins or substitutes original reserved source/root/clock/provenance")
        reserved = {root.root.root_id: root for root in expected.reservation.allocation.roots
            if root.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
        if {source.root_id: source.root for source in selected} != reserved:
            raise PermissionError("initialization changes original complete reserved effective streams")
        return
    forbidden_groups, forbidden_seeds, required_exclusion_groups, required_exclusion_seeds, coordinates = set(), set(), set(), set(), {}
    for manifest in (original.train_manifest, original.future_manifest):
        forbidden_groups.update(manifest.audit.census.exposed_independent_groups)
        forbidden_seeds.update(manifest.audit.census.effective_seed_exclusions)
        required_exclusion_seeds.update(manifest.audit.census.effective_seed_exclusions)
        declared = {scheduled.coordinate_identity(value): value for value in manifest.reservation.allocation.coordinates}
        for root in manifest.reservation.allocation.roots:
            forbidden_groups.add(root.root.independent_group_id)
            forbidden_seeds.update(stream.effective_seed for stream in root.streams)
            if manifest is original.train_manifest or root.root.role in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION):
                required_exclusion_groups.add(root.root.independent_group_id)
                required_exclusion_seeds.update(stream.effective_seed for stream in root.streams)
                coordinate = declared[root.coordinate]
                coordinates[coordinate.coordinate_id] = coordinate
    forbidden_seeds.update(stream.effective_seed for panel in original.panels for stream in panel.streams)
    required_exclusion_seeds.update(stream.effective_seed for panel in original.panels for stream in panel.streams)
    for role, selection in future:
        seeds = {stream.effective_seed for _, panels in selection.panels for panel in panels for stream in panel.streams}
        forbidden_seeds.update(seeds)
        if role in ("CALIBRATION", "EVALUATION"): required_exclusion_seeds.update(seeds)
    # All committed E4 banks are exclusions, including unused reservations.
    # These sets never report those streams as actually consumed.
    for _, phase in e4_phases:
        selection, allocation = phase.responses, phase.reservation.allocation
        selection.validate_allocation(allocation)
        declared = {scheduled.coordinate_identity(value): value for value in allocation.coordinates}
        for root in allocation.roots:
            forbidden_groups.add(root.root.independent_group_id); required_exclusion_groups.add(root.root.independent_group_id)
            forbidden_seeds.update(stream.effective_seed for stream in root.streams)
            required_exclusion_seeds.update(stream.effective_seed for stream in root.streams)
            coordinate = declared[root.coordinate]; coordinates[coordinate.coordinate_id] = coordinate
        seeds = {stream.effective_seed for _, panels in selection.panels for panel in panels for stream in panel.streams}
        forbidden_seeds.update(seeds); required_exclusion_seeds.update(seeds)
    if request.development_product is not None:
        programme, _ = _read_development_controls(writer=writer, locator=request.development_product)
        # A shared original allocation may also reserve future CONF roots.
        # Actual DEV controls establish only their complete selected sources;
        # the full allocation remains an authenticated custody parent.
        from empirical_lawhood.adapters.methods.matrix_experimental_programme.selected_revision_programme import MatrixRevisionPreparedProgramme
        selected_development = (programme.source_arms() if type(programme) is MatrixRevisionPreparedProgramme
            else tuple((None, value) for value in programme.sources.sources))
        for _, source in selected_development:
            root, coordinate = source.root, source.coordinate
            forbidden_groups.add(root.root.independent_group_id); required_exclusion_groups.add(root.root.independent_group_id)
            forbidden_seeds.update(stream.effective_seed for stream in root.streams)
            required_exclusion_seeds.update(stream.effective_seed for stream in root.streams)
            coordinates[coordinate.coordinate_id] = coordinate
        seeds = {stream.effective_seed for _, panels in programme.panels for panel in panels for stream in panel.streams}
        forbidden_seeds.update(seeds); required_exclusion_seeds.update(seeds)
    allocation = original.future_manifest.reservation.allocation
    withheld = {root.coordinate for root in allocation.roots if root.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
    forbidden_physics = {scheduled.physical_key(value) for value in allocation.coordinates if scheduled.coordinate_identity(value) in withheld}
    forbidden_groups.update(sources.audit.census.exposed_independent_groups)
    forbidden_seeds.update(sources.audit.census.effective_seed_exclusions)
    if (any(source.root.root.independent_group_id in forbidden_groups or scheduled.physical_key(source.coordinate) in forbidden_physics
            for source in selected) or any(stream.effective_seed in forbidden_seeds for source in selected for stream in source.root.streams)):
        raise PermissionError("initialization consumes prior TRAIN/E3/E4/DEV groups, streams or original E6 physical keys")
    _require_current_exposure_subset(original.future_manifest.audit, sources.audit,
        effective_seeds=tuple(sorted(required_exclusion_seeds)), group_ids=tuple(sorted(required_exclusion_groups)),
        coordinates=tuple(coordinates[key] for key in sorted(coordinates)))


def publish_initialization(*, specification, request, project_root, writer, metadata_directory, output_selection_path, execution):
    """Validate all originals and values before the first selected publication."""
    from empirical_lawhood.api.matrix_numerical_provenance import capture_matrix_provenance
    from empirical_lawhood.api.recursive_authoring import implementation_binding


    root = Path(project_root).resolve(strict=True)
    require_selected_implementation(root)
    specification.__post_init__(); request.__post_init__(); execution.__post_init__()
    source_binding = implementation_binding(root)
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    if (execution.source_snapshot != ObjectIdentity.from_record("recursive-member.implementation", source_binding)
            or execution.workers is None or execution.environment_id is None or execution.output_root is None):
        raise ValueError("initialization requires the actual selected source and explicit worker/environment/output selections")
    if specification.request != request.identity:
        raise PermissionError("initialization changes its selected request")
    directory = Path(metadata_directory).resolve(strict=False)
    artifact_root = Path(writer.root.contract.canonical_path).resolve(strict=True)
    if (Path(execution.output_root).resolve(strict=True) != artifact_root
            or Path(metadata_directory) != directory):
        raise ValueError("initialization changes the exact selected canonical output root or metadata directory")
    relative = directory.relative_to(artifact_root).as_posix()
    output = Path(output_selection_path).resolve(strict=False)
    if Path(output_selection_path) != output or output != directory / "sources.json":
        raise ValueError("initialization selector must be sources.json under its explicit metadata directory")
    writer.root.resolve(relative + "/sources.json", for_write=True)
    with writer.verification_scope() as writer, authenticated_initialization_request(writer=writer, request=request,
            maximum_source_bytes=request.original_commitments.maximum_source_bytes):
        from empirical_lawhood.api.domain_composition.matrix_selected_declarative.derivation import selected_produced_input_parents
        development = () if request.development_product is None else (request.development_product,)
        parents = (() if not development else selected_produced_input_parents(writer,
            originals=(), development=development))
        ceilings = tuple(value.visibility_ceiling for value in parents)
        access = derived_outcome_access(OutcomeAccess.OUTCOME_BLIND, *(value.outcome_access for value in parents))
        visibility = inherited_visibility(ceilings, access) if parents else VisibilityCeiling.PROSPECTIVE
        def require_current_metadata():
            if development and selected_produced_input_parents(writer, originals=(), development=development) != parents:
                raise PermissionError('initialization changes its actual DEV produced-parent metadata')
            writer.require_verification_snapshot()
        provenance = capture_matrix_provenance(project_root=root)
        states, arrays = [], {}
        index = request.sources.source_index()
        for descriptor in request.sources.descriptors:
            source = request.sources.source(descriptor, index=index)
            identifier = request.namespace + ".initial." + descriptor.identity.object_fingerprint
            initial, raw = initialize_source(source, provenance, state_id=identifier, artifact_id="array." + identifier)
            states.append((descriptor.root_id, initial)); arrays[descriptor.root_id] = raw
        bank = domain.MatrixPreparationInitializationBank("initial-states." + request.fingerprint(), request, tuple(states))
        # A current-code/provenance change refuses before publication, never by
        # rewriting an original reservation or old source descriptor.
        if capture_matrix_provenance(project_root=root) != provenance or implementation_binding(root) != source_binding:
            raise PermissionError("initialization producing source changed during numerical configuration construction")
        publications = []
        def publish(name, record):
            require_current_metadata()
            result = writer.write(ArtifactWriteRequest(request.namespace + "." + name, relative + "/" + name + ".json",
                record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json", request.namespace, relative,
                record.canonical_bytes(), visibility, ceilings, access, lineage_parents=parents))

            publications.append(result)
            return ExperimentInputBinding(name, record.identity, name + ".json", result.materialization.size_bytes)
        bindings = tuple(sorted((publish("request", request), publish("initial-states", bank)), key=lambda row: row.key))
        files = []
        for index, (root_id, state) in enumerate(bank.states):
            filename = "initial-state." + str(index).zfill(5) + ".npz"
            require_current_metadata()
            result = writer.write(ArtifactWriteRequest(state.array_artifact.artifact_id, relative + "/" + filename,
                state.array_artifact.payload_schema, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz", request.namespace,
                relative, arrays[root_id], VisibilityCeiling.PROSPECTIVE, (), OutcomeAccess.OUTCOME_BLIND))
            publications.append(result)
            files.append(ExperimentFileInputBinding("initial-state." + root_id, state.array_artifact, "1.0.0", filename,
                state.array_artifact.size_bytes))
        selector = ExperimentFileInputSelection("selection." + request.namespace + ".initial-states", domain.PROTOCOL_ID, bindings, tuple(sorted(files, key=lambda row: row.key)))
        require_current_metadata()
        publications.append(writer.write(ArtifactWriteRequest(request.namespace + ".sources", relative + "/sources.json", selector.SCHEMA,
            ArtifactProfile.CANONICAL_JSON, "application/json", request.namespace, relative, selector.canonical_bytes(),
            visibility, ceilings, access, lineage_parents=parents)))
        prepared = domain.prepare(specification, execution=execution, method_inputs=(request, bank))
        payload = canonical_json_bytes({"schema": "empirical-lawhood/operational/experiment-input-requirements", "version": "1.0.0", "value": {
            "specification": specification.identity.to_document(), "initialization_bank": bank.identity.to_document(),
            "initial_state_count": len(states), "initialization": "DECLARED_DETERMINISTIC_TICK_ZERO_INITIAL_CONDITION",
            "native_contact": "NONE", "consumed_streams": (), "scientific_authority": "NONE",
            "retained_original_streams": tuple((root_id, tuple(state.root.stream_identity(stream).to_document() for stream in state.root.streams)) for root_id, state in bank.states),
            "dependencies": ()}})
        require_current_metadata()
        requirements = writer.write(ArtifactWriteRequest(request.namespace + ".requirements." + sha256(payload).hexdigest(),
            relative + "/requirements.json", "empirical-lawhood/operational/experiment-input-requirements", ArtifactProfile.CANONICAL_JSON,
            "application/json", request.namespace, relative, payload, visibility, ceilings, access, lineage_parents=parents))
        publications.append(requirements)
        require_current_metadata()
        return ExperimentInputDerivationResult(specification.identity, selector, output, prepared, tuple(publications), requirements)


def derive_inputs(*, specification, source_selection_path, project_root, artifact_writer, metadata_directory, output_selection_path, execution, read_access=None):
    from .experiment_preparation import load_experiment_inputs
    inputs = load_experiment_inputs(specification, source_selection_path, artifact_writer=artifact_writer, read_access=read_access)
    request, bank = inputs.method_inputs
    if request is None:
        raise ValueError("select the exact original commitment-bearing initialization request")
    if bank is not None:
        raise ValueError("select the original request input for initialization derivation; generated banks remain immutable")
    return publish_initialization(specification=specification, request=request, project_root=project_root, writer=artifact_writer,
        metadata_directory=metadata_directory, output_selection_path=output_selection_path, execution=execution)
