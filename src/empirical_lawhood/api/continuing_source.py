# SPDX-License-Identifier: MPL-2.0
"""Explicit composition of continuing-source ownership and existing custody."""

from contextlib import contextmanager
from pathlib import Path

from empirical_lawhood.storage.continuing_source import ExternalContinuingSourceStore
from empirical_lawhood.execution.continuing_source import ContinuingSourceOwner, LiveOperationReadout


def exposed_continuing_store(*, directory, artifact_plane):
    """Select original exposed history without acquiring live source permission.

    The exact guarded session publication supplies the selection. Historical
    inspection creates no actor handle, lease, source owner or effect port.
    Other evidence ceilings require their own current access composition.
    """
    from empirical_lawhood.storage.recursive_custody import read_exposed_recursive_payload
    from empirical_lawhood.science.inquiry.continuing_source import MAX_LIVE_RECORD_BYTES, ContinuingSourceSession
    from empirical_lawhood.science.records.decoding import decode_canonical_bytes
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling

    selected = Path(directory).relative_to(artifact_plane.root.contract.canonical_path)
    relative = (selected / "session.json").as_posix()
    manifest = artifact_plane.read_manifest(relative)
    if (manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.payload_schema != ContinuingSourceSession.SCHEMA
            or manifest.logical.lineage_parents):
        raise PermissionError("historical session inspection requires its exposed development publication")
    raw = read_exposed_recursive_payload(artifact_plane, manifest, maximum_bytes=MAX_LIVE_RECORD_BYTES)
    session = decode_canonical_bytes(raw, ContinuingSourceSession, maximum_bytes=MAX_LIVE_RECORD_BYTES)
    store = ExternalContinuingSourceStore(plane=artifact_plane, session=session,
        relative_root=selected.parent.as_posix())
    if store.relative_root != selected.as_posix():
        raise ValueError("historical session selection differs from its original custody location")
    store.authenticate_session()
    return store


@contextmanager
def open_continuing_source(*, session, artifact_plane, relative_root, package, package_payload,
                           clock, effect_ports, current_access, minimum_free_bytes=0):
    """Own one new source session independently of any client request lifetime.

The caller selects the guarded external plane, actual access and native ports.
This context must live in the source process/service, not a browser callback.
It never launches a source, selects scientific identities or grants authority.
    """
    current_access.require_owner(session)
    custody = ExternalContinuingSourceStore(plane=artifact_plane, session=session,
        relative_root=relative_root, minimum_free_bytes=minimum_free_bytes)
    with custody.owner_lock():
        owner = ContinuingSourceOwner(session=session, custody=custody, clock=clock,
            effect_ports=effect_ports, current_access=current_access)
        owner.start(package, package_payload)
        try:
            yield owner
        finally:
            owner.close()


def read_continuing_operation(*, session, artifact_plane, relative_root, request_id, current_access):
    """Read original finite work without a live actor, source launch or retry."""
    current_access.require_owner(session)
    custody = ExternalContinuingSourceStore(plane=artifact_plane, session=session, relative_root=relative_root)
    operation = custody.read_operation(request_id)
    if operation is None:
        raise ValueError("selected continuing-source operation is not retained")
    result = LiveOperationReadout(operation, custody.read_effect(operation), custody.has_contact(operation))
    current_access.require_owner(session)
    return result


def reconcile_continuing_operation(*, session, artifact_plane, relative_root, request_id,
                                  current_access, effect_observer, minimum_free_bytes=0):
    """Retain an actual observed original result through the read-only source port.

``effect_observer`` is the code-owned ``LiveEffectPort.observe`` callable. This
composition has no submission method and cannot repeat an uncertain effect.
    """
    current_access.require_owner(session)
    custody = ExternalContinuingSourceStore(plane=artifact_plane, session=session,
        relative_root=relative_root, minimum_free_bytes=minimum_free_bytes)
    operation = custody.read_operation(request_id)
    if operation is None or not custody.has_contact(operation):
        raise ValueError("continuing-source reconciliation requires original possible-contact custody")
    observed = effect_observer(operation)
    current_access.require_owner(session)
    if observed is not None:
        receipt, payload = observed
        custody.publish_effect(operation, receipt, payload)
    return LiveOperationReadout(operation, custody.read_effect(operation), True)
