# SPDX-License-Identifier: MPL-2.0
"""Assemble missing publication metadata from an authenticated returned stream."""

from hashlib import sha256
from pathlib import PurePosixPath

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import CHUNK_BYTES, RAW_MAGIC, _ChunkReader, uncompressed_archive_chunks
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RawCoupledReturn
from empirical_lawhood.science.records.decoding import decode_canonical_bytes

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import definition_for, selected_request
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import MAX_RETURN, PeriodicProbeNativeReturn


def assemble_returned_control_publication(*, config, definition, read_output):
    """Authenticate the original frame and every member; run no numerical code."""
    if definition != definition_for(config, parent=definition.parent_contact,
            materialization_ids=definition.input_materialization_ids):
        raise ValueError("publication repair changes its original periodic control definition")
    chunks = read_output(definition, "files.raw", maximum_chunk_bytes=CHUNK_BYTES)
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError("returned periodic archive changes its original frame")
        size = int.from_bytes(reader.take(8), "big")
        if not 0 < size <= 2**20:
            raise ValueError("returned periodic file census exceeds its original metadata bound")
        census = decode_canonical_bytes(reader.take(size), DurableRawFileCensus, maximum_bytes=2**20)
        if sum(row.byte_count for row in census.files) > 4*2**30:
            raise ValueError("returned periodic archive exceeds its original output allowance")
        controls = {"control-point.json": config.point.fingerprint(),
            "control-protocol.json": config.protocol.fingerprint()}
        names = set()
        for row in census.files:
            path = PurePosixPath(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError("returned periodic archive changes its original unit directory")
            names.add(path.name)
            if path.name in ("native-error.txt", "engine-authentication-error.txt"):
                raise ValueError("successful publication repair cannot hide a retained native or engine error")
            remaining, digest = row.byte_count, sha256()
            while remaining:
                block = reader.take(min(remaining, CHUNK_BYTES))
                remaining -= len(block)
                digest.update(block)
            if digest.hexdigest() != row.sha256 or path.name in controls and row.sha256 != controls[path.name]:
                raise ValueError("returned periodic archive changes an original file or scientific control")
        reader.finish()
        if not set(controls) <= names:
            raise ValueError("returned periodic archive omits an original scientific control")
    finally:
        chunks.close()
    raw = bytearray()
    for block in read_output(definition, "raw.return", maximum_chunk_bytes=CHUNK_BYTES):
        raw.extend(block)
        if len(raw) > MAX_RETURN:
            raise ValueError("returned periodic metadata exceeds its original bound")
    captured = decode_canonical_bytes(bytes(raw), RawCoupledReturn, maximum_bytes=MAX_RETURN)
    returned = PeriodicProbeNativeReturn(config.point.identity, selected_request(config).identity,
        census, captured, None)
    return (("files.census", census), ("probe.return", returned))
