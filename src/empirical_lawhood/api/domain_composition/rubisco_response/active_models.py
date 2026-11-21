# SPDX-License-Identifier: MPL-2.0
"""Supported complete active-state preparation and independent retained reading."""

from hashlib import sha256

from empirical_lawhood.domains.rubisco.rubisco_response.active_model_assessment import assess_catalytic_partition, assess_catalytic_seed
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import prepare_catalytic_sites
from empirical_lawhood.domains.rubisco.rubisco_response.active_state_geometry import materialize_catalytic_states
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import validate_relative_locator
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, ArtifactStreamWriteRequest


MAXIMUM_PREPARATION_BYTES = 64*2**20


def prepare_active_model(*, representation, prototype, coordinate_bytes, protocol,
                         output_relative_path, artifact_writer, observe=None):
    """Publish all eight sites and all 96 hypotheses, including adverse findings.

    The caller authenticates the original construction and input publications.
    This owner joins their typed identities and complete coordinate bytes.
    """
    validate_relative_locator(output_relative_path)
    if observe is not None and not callable(observe):
        raise ValueError('active preparation observer must be callable')
    destination = artifact_writer.root.resolve(output_relative_path, for_write=True)
    if destination.exists():
        raise ValueError('active preparation needs a fresh retained destination')
    sites = prepare_catalytic_sites(representation=representation, prototype=prototype,
        coordinate_bytes=coordinate_bytes, protocol=protocol)
    rows = []
    for site in sites:
        partition = assess_catalytic_partition(representation=representation, prototype=prototype,
            site=site, protocol=protocol, coordinate_bytes=coordinate_bytes)
        for seed in materialize_catalytic_states(representation=representation, site=site,
                protocol=protocol, coordinate_bytes=coordinate_bytes, cell=prototype.cell):
            assessment = assess_catalytic_seed(representation=representation, site=site,
                protocol=protocol, seed=seed, coordinate_bytes=coordinate_bytes, cell=prototype.cell)
            rows.append((seed, assessment))
        if observe is not None:
            observe(partition)
    rows.sort(key=lambda row: row[0].seed_id)
    digest = sha256((representation.fingerprint()+prototype.fingerprint()+protocol.fingerprint()).encode()).hexdigest()
    prepared = ActiveModelPreparation('preparation.gp-active-states.'+digest, representation.identity,
        prototype.identity, protocol, sites, tuple(s for s, _ in rows), tuple(a for _, a in rows))
    size = prepared.canonical_size_bytes()
    if size > MAXIMUM_PREPARATION_BYTES:
        raise ValueError('active preparation exceeds its declared member bound')
    def chunks():
        for chunk in prepared.canonical_chunks():
            for offset in range(0, len(chunk), 2**20):
                yield chunk[offset:offset+2**20]
    publication = artifact_writer.write_stream(ArtifactStreamWriteRequest(prepared.preparation_id,
        output_relative_path, prepared.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json',
        prepared.preparation_id, output_relative_path.rsplit('/', 1)[0], chunks(), maximum_bytes=size,
        maximum_chunk_bytes=min(size, 2**20), expected_size_bytes=size,
        expected_physical_sha256=prepared.fingerprint(), visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE))
    return {'preparation': prepared, 'path': str(destination), 'publication': publication}


def read_active_model(*, representation, prototype, coordinate_bytes,
                      relative_path, artifact_writer, observe=None):
    """Authenticate and independently assess every retained hypothesis without construction."""
    validate_relative_locator(relative_path)
    validate_periodic_probe_model(prototype, representation)
    with artifact_writer.read_context() as reader:
        manifest = reader.read_manifest(relative_path)
        if (manifest.logical.payload_schema != ActiveModelPreparation.SCHEMA
                or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('active preparation reader cannot change its schema or evidence lane')
        reader.verify_manifests((manifest,))
        raw = read_bounded_bytes(reader.root.resolve(relative_path, for_write=False),
            maximum_bytes=MAXIMUM_PREPARATION_BYTES)
        prepared = decode_canonical_bytes(raw, ActiveModelPreparation, maximum_bytes=MAXIMUM_PREPARATION_BYTES)
        if (prepared.representation != representation.identity or prepared.prototype != prototype.identity
                or prepared.fingerprint() != manifest.logical.content_sha256):
            raise ValueError('active preparation reader substitutes its complete original inputs')
        for site in prepared.sites:
            assessment = assess_catalytic_partition(representation=representation, prototype=prototype,
                site=site, protocol=prepared.protocol, coordinate_bytes=coordinate_bytes)
            if observe is not None:
                observe(assessment)
        site_map = {s.identity: s for s in prepared.sites}
        for seed, original in zip(prepared.seeds, prepared.assessments, strict=True):
            assessed = assess_catalytic_seed(representation=representation, site=site_map[seed.site],
                protocol=prepared.protocol, seed=seed, coordinate_bytes=coordinate_bytes, cell=prototype.cell)
            if assessed != original:
                raise ValueError('retained active geometry differs from independent original assessment')
    return prepared
