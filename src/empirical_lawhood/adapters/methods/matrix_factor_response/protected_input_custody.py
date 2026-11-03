# SPDX-License-Identifier: MPL-2.0
"""Exact original artifact custody and producer ports across E3 editions."""



from empirical_lawhood.runtime.execution import WorkerInputKind

from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA
from empirical_lawhood.runtime.execution import WorkerOutputPort

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import _publication
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes

from empirical_lawhood.runtime.artifacts import ArtifactProfile

from empirical_lawhood.kernel.decoding import decode_canonical_bytes

from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import authenticate_publication
from empirical_lawhood.infrastructure.bounded_io import bounded_file_sha256
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.planning.experiment_inputs import ExperimentFileInputBinding
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult


def matches_protected_e3_producer(edge, producer, output):
    """Retain declared port IDs and their compiler-owned task qualification.

    The recursive compiler prefixes an executable output with its task ID.
    Retained direct plans use the declared port ID. Neither projection changes
    the required producer; callers also authenticate its receipt/materialization.
    """
    return (edge.producer_task_id == producer
        and edge.producer_output_id in (output, producer + "." + output))


def require_original_publication_metadata(publication):
    if type(publication) is not ArtifactWriteResult:
        raise TypeError("protected E3 originals require exact publication custody")
    publication.__post_init__()
    publication.logical.__post_init__()
    publication.materialization.__post_init__()
    publication.manifest_materialization.__post_init__()


def authenticate_original_artifact(plane, artifact, custody):
    if type(artifact) is not ArtifactIdentity:
        raise TypeError("protected E3 census omits its exact original artifact identity")
    artifact.__post_init__()
    if type(custody) is ExperimentFileInputBinding:
        custody.__post_init__()
        if custody.identity != artifact:
            raise ValueError("protected E3 original FILE substitutes census audit/inventory identity")
        # The original selection's base is never inferred from an artifact ID.
        # Composition explicitly supplies this existing guarded root. A retained
        # copy preserves the original identity without becoming a past publication.
        actual = bounded_file_sha256(plane.root.resolve(custody.relative_path, for_write=False),
            maximum_bytes=artifact.size_bytes)
        if actual != (artifact.size_bytes, artifact.sha256):
            raise ValueError("protected E3 original FILE differs from its exact selected bytes")
        return
    require_original_publication_metadata(custody)
    if (custody.logical.logical_artifact_id, custody.logical.payload_schema, custody.logical.content_sha256,
            custody.logical.media_type, custody.materialization.size_bytes) != (
                artifact.artifact_id, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes):
        raise ValueError("protected E3 original publication substitutes census audit/inventory identity")
    authenticate_publication(plane, custody)


def read_protected_e3_worker_input(port, contract, kind=None):
    raw = port.read()
    digest = sha256(raw).hexdigest()
    if (len(raw) != port.size_bytes or digest != contract.logical.content_sha256 or digest != contract.physical_sha256
            or contract.logical.profile is not (ArtifactProfile.CANONICAL_JSON if kind else ArtifactProfile.MATRIX_ARRAY_NPZ)):
        raise ValueError("protected E3 PURE worker changes exact received publication bytes or codec")
    if kind is None:
        return raw
    result = decode_canonical_bytes(raw, kind, maximum_bytes=port.size_bytes)
    if raw != result.canonical_bytes():
        raise ValueError("protected E3 PURE worker substitutes original canonical record bytes")
    return result


def read_protected_e3_response_input(port, prepared, kind):
    raw = port.read()
    if len(raw) != port.size_bytes:
        raise ValueError("protected E3 response changes a delivered canonical input size")
    record = decode_canonical_bytes(raw, kind, maximum_bytes=port.size_bytes)
    if raw != record.canonical_bytes():
        raise ValueError("protected E3 response changes exact canonical input bytes")
    if prepared is not None:
        selected = next(row for row in prepared.inputs if row.artifact_id == port.artifact_id)
        digest = sha256(raw).hexdigest()
        if (selected.logical.profile is not ArtifactProfile.CANONICAL_JSON
                or selected.logical.content_sha256 != digest or selected.physical_sha256 != digest):
            raise ValueError("protected E3 response changes its prepared canonical publication")
    return record


def read_protected_e3_original_publication(plane, publication, kind):
    authenticate_publication(plane, publication)
    raw = read_bounded_bytes(plane.root.resolve(publication.materialization.relative_path, for_write=False),
        maximum_bytes=publication.materialization.size_bytes)
    record = decode_canonical_bytes(raw, kind, maximum_bytes=publication.materialization.size_bytes)
    _publication(publication, record)
    if raw != record.canonical_bytes():
        raise ValueError("protected E3 original publication is not its exact canonical bytes")
    return record


def validate_protected_e3_pure_outputs(context, phase):
    expected = {"product": (phase.product_type.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json")}
    if phase.array_output:
        expected["arrays"] = (MATRIX_ARRAY_SCHEMA, ArtifactProfile.MATRIX_ARRAY_NPZ, "application/x-npz")
    actual = {port.output_id.rsplit(".", 1)[-1]: port for port in context.output_ports}
    if (set(actual) != set(expected) or len(actual) != len(context.output_ports)
            or any(type(port) is not WorkerOutputPort or port.logical_artifact_id is None for port in context.output_ports)
            or len({port.logical_artifact_id for port in context.output_ports}) != len(expected)
            or any((port.payload_schema, port.profile, port.media_type) != expected[name] for name, port in actual.items())):
        raise ValueError("protected E3 PURE worker changes its complete ordinary output contract")


def validate_protected_e3_response_dependency(context, port, producer, output, prepared):
    receipts = tuple(row for row in context.dependency_receipts if port.materialization_id in row.output_materialization_ids)
    if (port.kind is not WorkerInputKind.DEPENDENCY or len(receipts) != 1 or receipts[0].task_id != producer):
        raise ValueError("protected E3 response loses its exact current producing task receipt")
    if prepared is not None:
        edges = tuple(row for row in prepared.execution_task_record.scientific_inputs
            if row.operational_logical_artifact_id == port.artifact_id)
        if len(edges) != 1 or not matches_protected_e3_producer(edges[0], producer, output):
            raise ValueError("protected E3 response substitutes the actual producing output port")


def validate_protected_e3_response_array(port, original, prepared):
    artifact = original.array_artifact
    if ((port.artifact_id, port.payload_schema, port.media_type, port.size_bytes,
            port.outcome_access, port.visibility_ceiling) != (artifact.artifact_id, artifact.payload_schema, artifact.media_type,
                artifact.size_bytes, original.outcome_access, original.visibility_ceiling)):
        raise ValueError("protected E3 response substitutes an actual ordinary array alias or scope")
    if prepared is not None:
        selected = next(row for row in prepared.inputs if row.artifact_id == port.artifact_id)
        if (selected.logical.profile is not ArtifactProfile.MATRIX_ARRAY_NPZ
                or selected.logical.content_sha256 != artifact.sha256 or selected.physical_sha256 != artifact.sha256):
            raise ValueError("protected E3 response substitutes exact original array publication bytes")


def protected_e3_source_operands(config):
    descriptor = config.source
    return tuple(sorted({config.specification.object_fingerprint, config.source_manifest.object_fingerprint,
        descriptor.fingerprint(), descriptor.identity.object_fingerprint, descriptor.allocation.object_fingerprint,
        descriptor.reservation.object_fingerprint, descriptor.selection.object_fingerprint,
        descriptor.specification.object_fingerprint, descriptor.provenance.object_fingerprint,
        descriptor.coordinate.object_fingerprint}))
