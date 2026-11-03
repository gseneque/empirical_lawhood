# SPDX-License-Identifier: MPL-2.0
"""Selected E3 mathematical projections over supplied immutable originals.

No I/O, source qualification or authority is performed here. In particular the
historical full factor rule remains exposed mathematics; the prefix projection
neither relabels that rule nor widens its historical compatibility contract.
"""

from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from dataclasses import dataclass, fields
from hashlib import sha256
import json
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_factor_lifetime.records import FactorEventSpec
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import ScheduledPrefixPolicy, physical_key, identity as source_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import ScheduledResponsePanel, ScheduledResponseProtocol
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_record
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.artifacts import ArtifactProfile

from .experiment_preparation import _protocol_errors, _unique_object
from .experiment_specification import MatrixResponseErrorSpecification
from .protected_source_records import (
    ProtectedE3NativeSourceManifest, ProtectedE3ResponseSelection, _reference, _selected, identity,
)
from .response_frontier import MatrixResponseFrontierProtocol

# This reviewed original operand owns the published geometric normalization.
# Its imported numerical dependencies remain covered by producing provenance.
ORIGINAL_SCALAR_SOURCE_SHA256 = "701d7c5a1157d5d4f29c2a4cc82630e7fff70dc5ade042339009d92934fc31c9"
ORIGINAL_SCALAR_SOURCE_BYTES = 20101
PROJECTION_MEANING = "PREFIX_RESTRICTION_AND_ORIGINAL_Q2_SCALAR_GEOMETRY_NO_SOURCE_QUALIFICATION"


@dataclass(frozen=True, slots=True)
class ProtectedE3ProtocolProjection(CanonicalRecord):
    """Derived mathematical joins, not an eligibility or custody certificate."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-protocol-projection"
    record_id: str
    specification: ObjectIdentity
    candidate_sha256: str
    candidate_size_bytes: int
    mathematical_protocol: ObjectIdentity
    original_factor_rule: ObjectIdentity
    prefix_policy: ObjectIdentity
    prefix_rule: ObjectIdentity
    scalar_definition: ObjectIdentity
    original_normalization: ArtifactIdentity
    typed_normalization: ArtifactIdentity
    nominal: ObjectIdentity
    nearby: ObjectIdentity
    shifted: ObjectIdentity
    cutoff_tick: int
    meaning: str = PROJECTION_MEANING

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1FactorRule
        validate_stable_id(self.record_id)
        validate_sha256(self.candidate_sha256)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification),
                (self.mathematical_protocol, MatrixResponseFrontierProtocol), (self.original_factor_rule, FactorEventSpec),
                (self.prefix_policy, ScheduledPrefixPolicy), (self.prefix_rule, E1FactorRule),
                (self.scalar_definition, MatrixParameterScalarDefinition), (self.nominal, MatrixParameterCoordinate),
                (self.nearby, MatrixParameterCoordinate), (self.shifted, MatrixParameterCoordinate)):
            _reference(value, kind)
        if (type(self.candidate_size_bytes) is not int or self.candidate_size_bytes < 1
                or type(self.cutoff_tick) is not int or self.cutoff_tick < 1 or self.meaning != PROJECTION_MEANING
                or type(self.original_normalization) is not ArtifactIdentity
                or type(self.typed_normalization) is not ArtifactIdentity
                or self.original_normalization == self.typed_normalization
                or (self.original_normalization.payload_schema, self.original_normalization.media_type,
                    self.original_normalization.sha256, self.original_normalization.size_bytes) !=
                   ("empirical-lawhood/source/checksummed-uninterpreted-public-bytes", "text/x-python",
                    ORIGINAL_SCALAR_SOURCE_SHA256, ORIGINAL_SCALAR_SOURCE_BYTES)
                or (self.typed_normalization.payload_schema, self.typed_normalization.media_type) !=
                   (MatrixParameterScalarDefinition.SCHEMA, "application/json")
                or self.typed_normalization.sha256 != self.scalar_definition.object_fingerprint):
            raise ValueError("protected E3 projection changes its exact original scalar owners or mathematical meaning")
        self.original_normalization.__post_init__()
        self.typed_normalization.__post_init__()


def _candidate_document(specification, raw):
    _selected(specification)
    errors = _protocol_errors(specification, raw)
    if errors:
        raise ValueError("protected E3 candidate: " + "; ".join(errors))
    return json.loads(raw, object_pairs_hook=_unique_object,
        parse_float=lambda _: (_ for _ in ()).throw(ValueError("binary fractional candidate number")),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite candidate number")))


def _candidate_coordinate(metadata, coordinate):
    if type(coordinate) is not MatrixParameterCoordinate:
        raise TypeError("protected E3 requires actual complete typed coordinates")
    coordinate.__post_init__()
    if (metadata["schema"], metadata["object_id"], metadata["sha256"], metadata["bytes"]) != (
            coordinate.SCHEMA, coordinate.coordinate_id, coordinate.fingerprint(), len(coordinate.canonical_bytes())):
        raise ValueError("protected E3 coordinate differs from selected complete candidate identity/bytes")
    if metadata["full_physical_key"] != [str(value) for value in physical_key(coordinate)]:
        raise ValueError("protected E3 candidate contradicts its exact coordinate physical description")


def project_protected_e3_protocol(*, specification: MatrixResponseErrorSpecification, candidate_bytes: bytes,
        nominal: MatrixParameterCoordinate, nearby: MatrixParameterCoordinate, shifted: MatrixParameterCoordinate,
        mathematical_protocol: MatrixResponseFrontierProtocol, original_factor_rule: FactorEventSpec,
        prefix_policy: ScheduledPrefixPolicy, scalar_definition: MatrixParameterScalarDefinition,
        normalization_source: ArtifactIdentity, normalization_source_bytes: bytes,
        record_id: str) -> ProtectedE3ProtocolProjection:
    """Check exact candidate, prefix restriction and reviewed scalar equation.

    Original source bytes are hashed, never imported/executed. The code-owned
    normalization mapping concerns the geometric ratio on finite q2 inputs,
    not all availability behavior of the historical observer. Its upstream
    receiver/parameter dependencies still require normal producing provenance.
    """
    document = _candidate_document(specification, candidate_bytes)
    for value, kind in ((mathematical_protocol, MatrixResponseFrontierProtocol), (original_factor_rule, FactorEventSpec),
            (prefix_policy, ScheduledPrefixPolicy), (scalar_definition, MatrixParameterScalarDefinition),
            (normalization_source, ArtifactIdentity)):
        if type(value) is not kind:
            raise TypeError("protected E3 protocol projection requires exact original typed operands")
        value.__post_init__()
    try:
        _candidate_coordinate(document["population"]["nominal_coordinate"], nominal)
        metadata = document["E6_reservation_intent"]["typed_coordinates"]
        if len(metadata) != 2:
            raise ValueError("protected E3 changes its complete selected E6 coordinate pair")
        _candidate_coordinate(metadata[0], nearby)
        _candidate_coordinate(metadata[1], shifted)
        framed = decode_canonical_record(document["target"]["original_mathematical_protocol"], MatrixResponseFrontierProtocol)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("protected E3 candidate omits complete original typed operands") from error
    if framed != mathematical_protocol or framed.canonical_bytes() != mathematical_protocol.canonical_bytes():
        raise ValueError("protected E3 substitutes original framed mathematical protocol")
    if mathematical_protocol.factor_rule != original_factor_rule.identity:
        raise ValueError("protected E3 substitutes the original full factor rule")
    target_rules = tuple(c.target for c in mathematical_protocol.factor_rule_compatibilities
        if c.target.identity == original_factor_rule.identity)
    if not target_rules or any(rule.canonical_bytes() != original_factor_rule.canonical_bytes() for rule in target_rules):
        raise ValueError("protected E3 candidate lacks the exact full scalar factor-rule operand")
    rule, cutoff = prefix_policy.factor_rule, specification.measurement.origin_tick
    excluded = {"spec_id", "lattice", "scalar_closure", "exposure"}
    if (prefix_policy.cutoff_tick != cutoff or prefix_policy.origin_sector != "Y"
            or rule.lattice != tuple(t for t in original_factor_rule.lattice if t <= cutoff)
            or rule.lattice[-1] != cutoff
            or any(getattr(rule, field.name) != getattr(original_factor_rule, field.name)
                for field in fields(FactorEventSpec) if field.name not in excluded)
            or any(coordinate.q != 2 for coordinate in (nominal, nearby, shifted))):
        raise ValueError("protected E3 prefix changes selected factor admission/tracking/clock/lattice")
    original_scalar = original_factor_rule.scalar_closure
    if (original_scalar is None or original_scalar.normalization_owner != normalization_source
            or type(normalization_source_bytes) is not bytes
            or (normalization_source.sha256, normalization_source.size_bytes) !=
               (ORIGINAL_SCALAR_SOURCE_SHA256, ORIGINAL_SCALAR_SOURCE_BYTES)
            or len(normalization_source_bytes) != normalization_source.size_bytes
            or sha256(normalization_source_bytes).hexdigest() != normalization_source.sha256
            or original_scalar.threshold != scalar_definition.threshold
            or rule.scalar_closure.threshold != scalar_definition.threshold):
        raise ValueError("protected E3 scalar projection changes original source bytes or unchanged threshold")
    typed = rule.scalar_closure.normalization_owner
    if (typed.payload_schema, typed.sha256, typed.media_type, typed.size_bytes) != (
            scalar_definition.SCHEMA, scalar_definition.fingerprint(), "application/json", len(scalar_definition.canonical_bytes())):
        raise ValueError("protected E3 scalar projection lacks its actual typed normalization definition")
    return ProtectedE3ProtocolProjection(record_id, specification.identity, specification.protocol_sha256, len(candidate_bytes),
        mathematical_protocol.identity, original_factor_rule.identity, source_identity(prefix_policy), rule.identity,
        ObjectIdentity.from_record(scalar_definition.definition_id, scalar_definition), normalization_source, typed,
        coordinate_identity(nominal), coordinate_identity(nearby), coordinate_identity(shifted), cutoff)


def validate_protected_e3_manifest_population(*, specification: MatrixResponseErrorSpecification,
        manifest: ProtectedE3NativeSourceManifest, projections: tuple[ProtectedE3ProtocolProjection, ...],
        sources: tuple[ScheduledSource, ...], source_index=None) -> None:
    """Complete original future/reserved census; no TRAIN payload is needed."""
    _selected(specification)
    if type(manifest) is not ProtectedE3NativeSourceManifest:
        raise TypeError("protected E3 population requires its exact original source manifest")
    manifest.__post_init__()
    if (type(projections) is not tuple or not projections
            or any(type(p) is not ProtectedE3ProtocolProjection for p in projections)):
        raise TypeError("protected E3 population requires actual typed protocol projections")
    policies = {source_identity(p): p for p in manifest.native_specification.selection.prefix_policies}
    if {p.prefix_policy for p in projections} != set(policies) or len(projections) != len(policies):
        raise ValueError("protected E3 population drops/duplicates original prefix policies")
    first = projections[0]
    for projection in projections:
        projection.__post_init__()
        policy = policies[projection.prefix_policy]
        if (projection.specification != specification.identity or projection.candidate_sha256 != specification.protocol_sha256
                or (projection.nominal, projection.nearby, projection.shifted) != (first.nominal, first.nearby, first.shifted)
                or (projection.mathematical_protocol, projection.original_factor_rule, projection.original_normalization,
                    projection.cutoff_tick, projection.candidate_size_bytes) !=
                   (first.mathematical_protocol, first.original_factor_rule, first.original_normalization,
                    first.cutoff_tick, first.candidate_size_bytes)
                or projection.prefix_rule != policy.factor_rule.identity
                or projection.scalar_definition != ObjectIdentity.from_record(manifest.scalar_definition.definition_id, manifest.scalar_definition)
                or projection.typed_normalization != policy.factor_rule.scalar_closure.normalization_owner):
            raise ValueError("protected E3 population substitutes selected protocol/policy/scalar originals")
    allocation = manifest.reservation.allocation
    if (type(sources) is not tuple or any(type(s) is not ScheduledSource for s in sources)
            or tuple(s.root_id for s in sources) != tuple(row.root.root_id for row in allocation.roots)
            or len({s.source_id for s in sources}) != len(sources)
            or {s.provenance for s in sources} != {p.identity for p in manifest.provenances}):
        raise ValueError("protected E3 population drops/aliases complete original descriptors or producing provenance")
    index = source_index if source_index is not None else ScheduledSourceIndex.from_shared(
        reservation=manifest.reservation, specification=manifest.native_specification, provenances=manifest.provenances)
    index.require_parents(reservation=manifest.reservation, specification=manifest.native_specification,
        provenances=manifest.provenances)
    index.require_roster(sources, expected_root_ids=index.root_ids)
    manifest.audit.validate_source(index.resolve(sources[0]))
    if {coordinate_identity(c) for c in allocation.coordinates} != {first.nominal, first.nearby, first.shifted}:
        raise ValueError("protected E3 population substitutes complete candidate physical coordinates")
    role_keys = {(first.nominal, MatrixProgrammeRole.CALIBRATION): "CALIBRATION",
        (first.nominal, MatrixProgrammeRole.CONFIRMATION): "EVALUATION",
        (first.nearby, MatrixProgrammeRole.WITHHELD_TRANSFER): "TRANSFER_NEARBY",
        (first.shifted, MatrixProgrammeRole.WITHHELD_TRANSFER): "TRANSFER_SHIFTED"}
    actual = {role: [] for role in role_keys.values()}
    groups = set()
    for row in allocation.roots:
        key = (row.coordinate, row.root.role)
        if key not in role_keys or row.root.independent_group_id in groups:
            raise ValueError("protected E3 population thins/multiplies a whole group or relabels its original role")
        groups.add(row.root.independent_group_id)
        actual[role_keys[key]].append(row.root.independent_group_id)
    for role, units in actual.items():
        selected = specification.population(role)
        if (len(units) != selected.expected_units
                or selected.unit_ids is not None and tuple(sorted(units)) != selected.unit_ids):
            raise ValueError("protected E3 population changes a complete selected role denominator")
    training = specification.population("TRAIN").unit_ids
    if training is not None and groups & set(training):
        raise ValueError("protected E3 reserved groups overlap selected TRAIN units")


def validate_protected_e3_response_selection(selection: ProtectedE3ResponseSelection, *,
        specification: MatrixResponseErrorSpecification, manifest: ProtectedE3NativeSourceManifest,
        projections: tuple[ProtectedE3ProtocolProjection, ...], mathematical_protocol: MatrixResponseFrontierProtocol,
        sources: tuple[ScheduledSource, ...], protocols: tuple[ScheduledResponseProtocol, ...],
        panels: tuple[ScheduledResponsePanel, ...]) -> None:
    """Join separate members and all native streams to a reference-only census."""
    if type(selection) is not ProtectedE3ResponseSelection:
        raise TypeError("protected E3 requires its exact reference-only response selection")
    selection.__post_init__()
    index = ScheduledSourceIndex.from_shared(reservation=manifest.reservation,
        specification=manifest.native_specification, provenances=manifest.provenances)
    validate_protected_e3_manifest_population(specification=specification, manifest=manifest, projections=projections,
        sources=sources, source_index=index)
    if (selection.specification != specification.identity or selection.source_manifest != identity(manifest)
            or tuple(identity(p) for p in projections) != selection.protocol_projections
            or type(mathematical_protocol) is not MatrixResponseFrontierProtocol
            or any(p.mathematical_protocol != mathematical_protocol.identity for p in projections)
            or type(sources) is not tuple or any(type(s) is not ScheduledSource for s in sources)
            or type(protocols) is not tuple or any(type(p) is not ScheduledResponseProtocol for p in protocols)
            or type(panels) is not tuple or any(type(p) is not ScheduledResponsePanel for p in panels)):
        raise ValueError("protected E3 response selection substitutes exact selected operands")
    expected = tuple(row for row in manifest.reservation.allocation.roots
        if row.root.role in (MatrixProgrammeRole.CALIBRATION, MatrixProgrammeRole.CONFIRMATION))
    if (tuple(root for root, _ in selection.root_protocols) != tuple(row.root.root_id for row in expected)
            or tuple((p.public_source.root.root_id, ObjectIdentity.from_record(p.protocol_id, p)) for p in protocols) != selection.root_protocols):
        raise ValueError("protected E3 response selection changes complete nominal CAL/CONF protocol census")
    by_group = {}
    for panel in panels:
        panel.__post_init__()
        by_group.setdefault(panel.independent_group_id, []).append(panel)
    if tuple((group, tuple(ObjectIdentity.from_record(p.panel_id, p) for p in rows))
            for group, rows in sorted(by_group.items())) != selection.group_panels:
        raise ValueError("protected E3 response selection changes actual panel reference census")
    if set(by_group) != {row.root.independent_group_id for row in expected}:
        raise ValueError("protected E3 response selection drops/adds selected whole-group panels")
    forbidden_seeds = {s.effective_seed for row in manifest.reservation.allocation.roots for s in row.streams}
    forbidden_seeds.update(manifest.reservation.allocation.exposure.census.effective_seed_exclusions)
    owners = {}
    template_members = {}
    projections_by_policy = {p.prefix_policy: p for p in projections}
    descriptors = {s.root_id: s for s in sources}
    for protocol, root in zip(protocols, expected, strict=True):
        protocol.__post_init__()
        source = index.resolve(descriptors[root.root.root_id])
        public = protocol.public_source
        if type(public) is not ScheduledPublicSource:
            raise TypeError("protected E3 response requires its exact seedless public source")
        public.validate_source(source)
        coordinate = next(c for c in manifest.reservation.allocation.coordinates if coordinate_identity(c) == root.coordinate)
        policy_ref = dict(manifest.native_specification.selection.coordinate_policies)[root.coordinate]
        policy = next(p for p in manifest.native_specification.selection.prefix_policies if source_identity(p) == policy_ref)
        if (public.root != root.root or public.coordinate != coordinate or public.policy != policy
                or public.allocation != source_identity(manifest.reservation.allocation)
                or public.reservation != source_identity(manifest.reservation)
                or projections_by_policy[policy_ref].mathematical_protocol != protocol.criterion
                or protocol.horizon_steps != mathematical_protocol.horizon_steps or protocol.receiver_count != 48
                or protocol.receiver_gram_tolerance != mathematical_protocol.receiver_gram_tolerance
                or tuple(sorted((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in protocol.actions)) !=
                   tuple((a.role, a.amplitude, a.force_norm, a.pulse_steps) for a in mathematical_protocol.action_scales)):
            raise ValueError("protected E3 protocol changes original subject/policy/physical query/normalization")
        group_panels = by_group[root.root.independent_group_id]
        if tuple(sorted(p.role for p in group_panels)) != specification.measurement.panel_roles:
            raise ValueError("protected E3 response selection changes complete original two-panel scope")
        for panel in group_panels:
            if panel.role == "COMMON_NOISE_PANEL" and panel.streams != root.streams:
                raise ValueError("protected E3 common future panel changes original checkpoint streams")
            for stream in panel.streams:
                if panel.role == "INDEPENDENT_FUTURE" and stream.effective_seed in forbidden_seeds:
                    raise ValueError("protected E3 independent future overlaps exposed or reserved original streams")
                owner = (panel.independent_group_id, panel.role, stream.purpose)
                if owners.setdefault(stream.effective_seed, owner) != owner:
                    raise ValueError("protected E3 future stream crosses whole-group/purpose ownership")
        matches = tuple(p for p in selection.template_publications
            if p.logical.logical_artifact_id == protocol.templates.array_artifact.artifact_id)
        if len(matches) != 1:
            raise ValueError("protected E3 response selection lacks original template publication")
        publication, artifact = matches[0], protocol.templates.array_artifact
        archive = (artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.size_bytes)
        if template_members.setdefault(archive, protocol.templates.members) != protocol.templates.members:
            raise ValueError("protected E3 shared template archive has conflicting canonical member manifests")
        if (publication.logical.profile, publication.logical.payload_schema, publication.logical.content_sha256, publication.logical.media_type,
                publication.materialization.physical_sha256, publication.materialization.size_bytes,
                publication.logical.outcome_access, publication.logical.visibility_ceiling) != (
                ArtifactProfile.MATRIX_ARRAY_NPZ, artifact.payload_schema, artifact.sha256, artifact.media_type, artifact.sha256, artifact.size_bytes,
                protocol.templates.outcome_access, protocol.templates.visibility_ceiling):
            raise ValueError("protected E3 response selection substitutes original template bytes/access")
    if {p.logical.logical_artifact_id for p in selection.template_publications} != {p.templates.array_artifact.artifact_id for p in protocols}:
        raise ValueError("protected E3 response selection adds/omits original template publications")
