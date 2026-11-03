# SPDX-License-Identifier: MPL-2.0
"""Actual prior native TRAIN facts; no issue or scientific qualification.

The declared exposure census remains a scientific input. Authentication preserves
its complete original corpus and actual committed publications; it does not turn
an asserted exclusion, new identifier or seed into a freshness assessment.
"""

from .native_training_records import (NativeTrainingAcquisitionRequest, future_response_support, validate_future_response_selections)
from .configured_protected_originals import _authenticate_artifact
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication


def _manifest_publications(manifest):
    """Select the unchanged complete corpus behind one source manifest."""
    audit = manifest.audit
    yield manifest.reservation.publication, manifest.reservation.allocation
    yield manifest.reservation_publication, manifest.reservation
    yield manifest.native_specification.publication, manifest.native_specification.selection
    yield manifest.audit_publication, audit
    yield manifest.scalar_definition_publication, manifest.scalar_definition
    originals = (audit.census, *audit.prior_scheduled_coordinates)
    for publication in audit.prior_corpus:
        records = tuple(value for value in originals if (value.SCHEMA, value.fingerprint()) ==
            (publication.logical.payload_schema, publication.logical.content_sha256))
        if len(records) != 1:
            raise PermissionError("native TRAIN audit omits its exact complete original corpus")
        yield publication, records[0]



def authenticate_programme_commitment(plane, request):
    """Authenticate the whole original known-input closure at this boundary."""
    from empirical_lawhood.infrastructure.matrix_programme_inputs import authenticate_programme_inputs
    if type(request) is not NativeTrainingAcquisitionRequest:
        raise TypeError("native TRAIN programme custody requires its exact current request")
    request.__post_init__()
    resolved = authenticate_programme_inputs(writer=plane, commitment=request.input_commitments,
        maximum_source_bytes=request.resources.for_operation("entry").source_scan_bytes)
    validate_request_programme_inputs(request, resolved)
    return resolved


def validate_request_programme_inputs(request, resolved):
    """Join actual TRAIN operands to C, without replacing its original parents."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.input_records import ResolvedMatrixProgrammeInputs
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    if type(request) is not NativeTrainingAcquisitionRequest or type(resolved) is not ResolvedMatrixProgrammeInputs:
        raise TypeError("native TRAIN programme join requires its exact current request and resolved original inputs")
    request.__post_init__()
    original, design = resolved.commitments, resolved.scientific_design
    train = resolved.phase("train")
    future = resolved.phase("e3.calibration")
    scalar = design.training_protocol.scalar_definition
    scalar_pin = ObjectIdentity.from_record(scalar.definition_id, scalar)
    scalar_rows = tuple(value for value in original.scalar_definitions if value.record == scalar_pin)
    if (original.identity != request.input_commitments.record or len(scalar_rows) != 1
            or request.candidate_specification != design.e3
            or request.mathematical_protocol != design.training_protocol.mathematical_protocol
            or request.train_manifest.reservation != train.reservation
            or request.train_manifest.native_specification != train.native_specification
            or request.future_manifest.reservation != future.reservation
            or request.future_manifest.native_specification != future.native_specification
            or request.protocols != train.responses.protocols
            or tuple(source.identity for source in request.sources) !=
                tuple(protocol.public_source.source for protocol in train.responses.protocols)
            or request.panels != tuple(sorted((panel for _, values in train.responses.panels for panel in values),
                key=lambda value: value.panel_id))
            or request.template_publications != train.responses.template_publications):
        raise PermissionError("native TRAIN substitutes the whole programme's original candidate, source or panel commitments")
    for manifest, slot in ((request.train_manifest, "train"), (request.future_manifest, "e3.calibration")):
        if (manifest.provenances != (resolved.producing_provenance,)
                or manifest.audit != resolved.exposure_audit
                or manifest.audit_publication != original.exposure_audit.publication
                or manifest.reservation_publication != original.phase(slot).reservation.publication
                or manifest.scalar_definition != scalar
                or manifest.scalar_definition_publication != scalar_rows[0].publication):
            raise PermissionError("native TRAIN substitutes actual original audit, scalar or producing provenance custody")
    slots = ("e3.calibration", "e3.confirmation", "e6.nearby", "e6.shifted")
    expected = tuple(sorted((request.input_commitments.record, original.availability.record, original.e6_policy.record,
        *(original.phase(slot).responses.record for slot in slots)), key=lambda value: value.object_id))
    if request.campaign.evidence_state != expected:
        raise PermissionError("native TRAIN changes its complete original pre-acquisition programme evidence census")
    selected_publications = (request.input_commitments, original.availability, original.e6_policy,
        *(original.phase(slot).responses for slot in slots))
    support = {reference: publication for reference, _, publication in future_response_support(request)}
    if support != {selected.record: selected.publication for selected in selected_publications}:
        raise PermissionError("native TRAIN substitutes exact original programme/future publication custody")


def authenticate_future_response_selections(plane, request, *, programme_inputs=None):
    """Authenticate current C once, then join every actual original future role."""
    resolved = authenticate_programme_commitment(plane, request) if programme_inputs is None else programme_inputs
    validate_request_programme_inputs(request, resolved)
    roles = (("CALIBRATION", "e3.calibration"), ("EVALUATION", "e3.confirmation"),
        ("TRANSFER_NEARBY", "e6.nearby"), ("TRANSFER_SHIFTED", "e6.shifted"))
    result = validate_future_response_selections(request,
        tuple(resolved.phase(slot).responses for _, slot in roles), resolved.availability)
    if result != tuple((role, resolved.phase(slot).responses) for role, slot in roles):
        raise PermissionError("native TRAIN substitutes or reorders actual original future roles")
    return result


def authenticate_e6_transport_policy(plane, request, policy, *, future_selections=None, programme_inputs=None):
    """Fresh exact pre-TRAIN policy and availability custody, without authority.

    Internal request authentication passes ``None`` to load its committed policy.
    A downstream consumer supplies its actual policy and must match that same pin.
    Supplied future selectors are already-authenticated boundary-local operands;
    their complete scientific joins are repeated against fresh availability.
    """
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import validate_e6_transport_policy
    if type(request) is not NativeTrainingAcquisitionRequest:
        raise TypeError("E6 transport custody requires its exact original native TRAIN request")
    if policy is not None and type(policy) is not MatrixE6EmpiricalTransportPolicy:
        raise TypeError("E6 transport custody requires its exact declared empirical policy")
    resolved = authenticate_programme_commitment(plane, request) if programme_inputs is None else programme_inputs
    validate_request_programme_inputs(request, resolved)
    actual, availability = resolved.e6_policy, resolved.availability
    if policy is not None and actual != policy:
        raise PermissionError("E6 transport policy differs from the actual pre-TRAIN commitment")
    selections = (authenticate_future_response_selections(plane, request, programme_inputs=resolved)
        if future_selections is None else future_selections)
    if (type(selections) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in selections)):
        raise TypeError("E6 transport requires the complete original role/selector tuple")
    validated = validate_future_response_selections(request, tuple(value for _, value in selections), availability)
    if validated != selections:
        raise PermissionError("E6 transport reorders or substitutes original future selection roles")
    validate_e6_transport_policy(actual, candidate_specification=request.candidate_specification,
        future_reservation=request.future_manifest.reservation, future_response_selections=validated,
        availability=(resolved.commitments.availability.record, availability))
    return actual


def authenticate_request(plane, request):
    """Authenticate actual pre-access publications, never publish replacements."""
    if type(request) is not NativeTrainingAcquisitionRequest:
        raise TypeError("native TRAIN publication custody requires its exact request")
    request.__post_init__()
    programme_inputs = authenticate_programme_commitment(plane, request)
    # The census/coordinate records do not authenticate the supporting audit or
    # current census metadata. Require the complete explicit original byte
    # custody, including FILE bounds/identity or actual publication commitment.
    committed = {artifact for _, artifact, _ in future_response_support(request)}
    for artifact, custody in request.exposure_support:
        if artifact not in committed:
            _authenticate_artifact(plane, artifact, custody)
    future_selections = authenticate_future_response_selections(plane, request, programme_inputs=programme_inputs)
    authenticate_e6_transport_policy(plane, request, None, future_selections=future_selections,
        programme_inputs=programme_inputs)
    # Deduplication is local to this boundary. It conveys no reusable authority.
    selected = {}
    for manifest in (request.train_manifest, request.future_manifest):
        for publication, record in _manifest_publications(manifest):
            path = publication.materialization.relative_path
            prior = selected.setdefault(path, (publication, record))
            if prior != (publication, record):
                raise PermissionError("native TRAIN prior publications alias different original facts")
    for publication in request.template_publications:
        path = publication.materialization.relative_path
        prior = selected.setdefault(path, (publication, None))
        if prior != (publication, None):
            raise PermissionError("native TRAIN template aliases another original publication")
    # Existing publication authentication checks the actual guarded member,
    # sidecar and committed batch, including the original canonical bytes.
    for _, (publication, record) in sorted(selected.items()):
        authenticate_publication(plane, publication, record)
    return future_selections


def authenticate_training_publications(plane, config_inputs):
    """Registered once-per-entry predicate at author, load, read and transport."""
    from .native_training_bindings import NativeTrainingEntryConfig
    from .native_training_records import validate_request

    entries = tuple(row.record for row in config_inputs if type(row.record) is NativeTrainingEntryConfig)
    if len(entries) != 1:
        raise PermissionError("native TRAIN needs one exact complete pre-acquisition entry")
    entry, = entries
    entry.__post_init__()
    validate_request(entry.specification, entry.request)
    authenticate_request(plane, entry.request)
