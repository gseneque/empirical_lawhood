"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from enum import StrEnum
from typing import ClassVar
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_sha256, validate_stable_id
from empirical_lawhood.storage.contracts.artifacts import ArtifactManifest, ArtifactWriteResult
from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengeConfig, SimulatorMorphismChallengeDenominatorDescriptor, SimulatorMorphismChallengePhase


ORIGINAL_DESCRIPTOR_SCHEMA = "icf-yolo/ipsmc/v3-denominator-descriptor/v1"


class RCChallengeOriginalNumericRecipe(StrEnum):
    GENERATED_ORIGINAL_ENVELOPE = "generated-original-envelope"
    FROZEN_EXPOSED_DEVELOPMENT_REFERENCE = "frozen-exposed-development-reference"


@dataclass(frozen=True, slots=True)
class RCChallengeSourceExportConfig(CanonicalRecord):
    """Editable request; published source/export/custody records are immutable operands."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/source-export-config"
    config_id: str
    config: SimulatorMorphismChallengeConfig
    source_id: str
    input_id: str
    publication_scope_id: str
    publication_scope_relative_root: str
    relative_root: str
    exposure_census: RCChallengeExposureCensus
    exposed_seed_hexes: tuple[str, ...] | None = None

    @property
    def phase(self) -> SimulatorMorphismChallengePhase:
        return self.config.phase

    def __post_init__(self) -> None:
        from empirical_lawhood.storage.contracts.artifacts import validate_publication_scope_root
        from empirical_lawhood.science.records.serialization import validate_relative_locator

        for field_name in ("config_id", "source_id", "input_id", "publication_scope_id"):
            validate_stable_id(getattr(self, field_name), field_name=field_name)
        if self.phase not in (SimulatorMorphismChallengePhase.NOMINATION, SimulatorMorphismChallengePhase.DEVELOPMENT):
            raise ValueError("source-export request must nominate evaluation streams or retain fixed development streams")
        validate_publication_scope_root(self.publication_scope_relative_root)
        validate_relative_locator(self.relative_root)
        if not self.relative_root.startswith(self.publication_scope_relative_root + "/"):
            raise ValueError("numeric export path lies outside its explicit publication scope")
        if self.exposed_seed_hexes is not None:
            if self.phase is not SimulatorMorphismChallengePhase.NOMINATION or len(self.exposed_seed_hexes) != 36:
                raise ValueError("exposed example requires the full nomination seed census")
            for seed in self.exposed_seed_hexes:
                validate_sha256(seed)


def exposed_source_export_example() -> RCChallengeSourceExportConfig:
    """Public editable software example; its numeric seeds are permanently exposed."""
    from empirical_lawhood.domains.history.simulator_morphism_challenges.descriptors import default_config

    return RCChallengeSourceExportConfig(
        "rc-history-challenge.exposed-source-export", default_config(SimulatorMorphismChallengePhase.NOMINATION),
        "rc-history-challenge.exposed-source", "rc-history-challenge.exposed-input",
        "rc-history-challenge.exposed-publication", "rc-history-challenge-exposed",
        "rc-history-challenge-exposed/numeric-input",
        RCChallengeExposureCensus("rc-history-challenge.exposed-complete-empty-census", (), (), True),
        tuple(sha256(f"rc-history-challenge-public-exposed-{index}".encode("ascii")).hexdigest() for index in range(36)),
    )


def exposed_phase_config_examples() -> tuple[SimulatorMorphismChallengeConfig, ...]:
    """Public software examples; the evaluation commitment carries no custody.

    Its known seeds are exposed forever. A real evaluation must consume its
    authenticated nomination commitment and current source packet instead.
    """
    from empirical_lawhood.domains.history.simulator_morphism_challenges.descriptors import default_config
    from empirical_lawhood.domains.history.simulator_morphism_challenges.workflow import build_seed_roster

    nomination = default_config(SimulatorMorphismChallengePhase.NOMINATION)
    _, commitment = build_seed_roster(nomination, injected_seeds=tuple(bytes.fromhex(seed)
        for seed in exposed_source_export_example().exposed_seed_hexes))
    return (nomination, default_config(SimulatorMorphismChallengePhase.CANARY),
        default_config(SimulatorMorphismChallengePhase.DEVELOPMENT),
        default_config(SimulatorMorphismChallengePhase.EVALUATION,
            seed_roster_commitment_sha256=commitment.fingerprint()))


@dataclass(frozen=True, slots=True)
class RCChallengeExposureCensus(CanonicalRecord):
    """Explicit complete prior source/export census; authenticate its artifacts separately."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/exposure-census"
    census_id: str
    prior_source_artifacts: tuple[ArtifactIdentity, ...]
    exposed_seed_sha256s: tuple[str, ...]
    complete_for_source_scope: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.census_id)
        if self.complete_for_source_scope is not True:
            raise ValueError("RC source requires the complete prior roster/exposure census")
        if tuple(a.artifact_id for a in self.prior_source_artifacts) != tuple(sorted({a.artifact_id for a in self.prior_source_artifacts})):
            raise ValueError("prior source artifacts must be unique and sorted")
        if self.exposed_seed_sha256s != tuple(sorted(set(self.exposed_seed_sha256s))):
            raise ValueError("exposed seed census must be unique and sorted")
        for digest in self.exposed_seed_sha256s:
            validate_sha256(digest)


@dataclass(frozen=True, slots=True)
class RCChallengeNumericSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/numeric-source"
    source_id: str
    phase: SimulatorMorphismChallengePhase
    unit_ids: tuple[str, ...]
    seed_hexes: tuple[str, ...]
    exposure_census: RCChallengeExposureCensus
    exposed_example: bool

    def __post_init__(self) -> None:
        from empirical_lawhood.domains.history.simulator_morphism_challenges.descriptors import development_unit_ids, deterministic_development_seed, evaluation_unit_ids, reserved_non_evaluation_seed_digests

        validate_stable_id(self.source_id)
        if self.phase not in (SimulatorMorphismChallengePhase.NOMINATION, SimulatorMorphismChallengePhase.DEVELOPMENT):
            raise ValueError("numeric allocation is nominated once or is the fixed exposed development source")
        expected = development_unit_ids() if self.phase is SimulatorMorphismChallengePhase.DEVELOPMENT else evaluation_unit_ids()
        if self.unit_ids != expected or len(self.seed_hexes) != len(expected):
            raise ValueError("numeric source differs from the complete fixed unit roster")
        for seed in self.seed_hexes:
            validate_sha256(seed, field_name="seed_hexes")
        digests = tuple(sha256(bytes.fromhex(seed)).hexdigest() for seed in self.seed_hexes)
        if len(set(digests)) != len(digests):
            raise ValueError("numeric source repeats an independent disorder-seed block")
        if self.phase is SimulatorMorphismChallengePhase.DEVELOPMENT:
            if self.exposed_example is not True or self.seed_hexes != tuple(deterministic_development_seed(unit).hex() for unit in expected):
                raise ValueError("development source retains its fixed exposed numerical seeds")
        elif not self.exposed_example and set(digests) & (set(self.exposure_census.exposed_seed_sha256s) | reserved_non_evaluation_seed_digests()):
            raise ValueError("new seed labels cannot make previously exposed numeric units fresh")

    @property
    def seeds(self) -> tuple[bytes, ...]:
        return tuple(bytes.fromhex(seed) for seed in self.seed_hexes)

    def require_config(self, config: SimulatorMorphismChallengeConfig) -> None:
        phases = (SimulatorMorphismChallengePhase.NOMINATION, SimulatorMorphismChallengePhase.EVALUATION) if self.phase is SimulatorMorphismChallengePhase.NOMINATION else (self.phase,)
        if config.phase not in phases or config.unit_ids != self.unit_ids:
            raise ValueError("numeric source does not bind the exact current phase/unit census")


def original_descriptor_bytes(descriptor: SimulatorMorphismChallengeDenominatorDescriptor) -> bytes:
    """Preserve original V3 field order, Decimal bytes and envelope for fibre RNG."""
    current = descriptor.canonical_bytes()
    prefix = ('{"schema":"' + descriptor.SCHEMA + '"').encode("ascii")
    if not current.startswith(prefix):
        raise ValueError("descriptor envelope differs from the frozen canonical recipe")
    return ('{"schema":"' + ORIGINAL_DESCRIPTOR_SCHEMA + '"').encode("ascii") + current[len(prefix):]


def original_numeric_definition(descriptor: SimulatorMorphismChallengeDenominatorDescriptor):
    """Retain known-case opaque original identity, or generate a new recipe identity.

    The fixed development table supplies numerical RNG definitions, never its
    historical artifact/receipt fields. Unavailable original canonical bytes
    are not claimed to have been reconstructed. Current physics is recomputed.
    """
    if descriptor.unit_id.startswith("dev."):
        from empirical_lawhood.domains.history.history_budget_fixed_scientific_inputs import _DESCRIPTOR_ROWS

        rows = tuple(row for row in _DESCRIPTOR_ROWS if row[0] == 0 and (row[1], row[2]) == (descriptor.unit_id, descriptor.scale_cells))
        if len(rows) != 1 or rows[0][3] != descriptor.seed_sha256 or rows[0][5] != descriptor.fingerprint():
            raise ValueError("fixed exposed original numeric reference differs from the exact current development descriptor")
        row = rows[0]
        original, seeds = row[4], row[6]
        expected = tuple(sha256(f"{original}:{depth}:random-fibre".encode("ascii")).hexdigest() for depth in range(36))
        if seeds != expected:
            raise ValueError("frozen original numeric reference changes its declared fibre recipe")
        return RCChallengeOriginalNumericRecipe.FROZEN_EXPOSED_DEVELOPMENT_REFERENCE, original, seeds
    original = sha256(original_descriptor_bytes(descriptor)).hexdigest()
    return RCChallengeOriginalNumericRecipe.GENERATED_ORIGINAL_ENVELOPE, original, tuple(sha256(f"{original}:{depth}:random-fibre".encode("ascii")).hexdigest() for depth in range(36))


@dataclass(frozen=True, slots=True)
class RCChallengeDescriptorNumericExport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/descriptor-numeric-export"
    descriptor: SimulatorMorphismChallengeDenominatorDescriptor
    original_numeric_recipe: RCChallengeOriginalNumericRecipe
    original_descriptor_sha256: str
    history_fibre_seed_sha256s: tuple[str, ...]

    def __post_init__(self) -> None:
        recipe, original, seeds = original_numeric_definition(self.descriptor)
        if self.original_numeric_recipe is not recipe or self.original_descriptor_sha256 != original or self.history_fibre_seed_sha256s != seeds:
            raise ValueError("numeric export changes the original descriptor/fibre RNG recipe")


@dataclass(frozen=True, slots=True)
class RCChallengeNumericExport(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/numeric-export"
    export_id: str
    source: ObjectIdentity
    scale_cells: tuple[int, ...]
    descriptors: tuple[RCChallengeDescriptorNumericExport, ...]

    def __post_init__(self) -> None:
        validate_stable_id(self.export_id)
        if self.source.object_schema != RCChallengeNumericSource.SCHEMA:
            raise ValueError("numeric export requires current numeric source identity")
        if self.scale_cells not in ((16, 32, 64), (64, 128, 256)):
            raise ValueError("numeric export retains the complete fixed phase scale census")
        keys = tuple((r.descriptor.unit_id, r.descriptor.scale_cells) for r in self.descriptors)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("numeric export descriptor coordinates repeat or differ in order")

    def require_source(self, source: RCChallengeNumericSource) -> None:
        if self.source != ObjectIdentity.from_record(source.source_id, source) or tuple((row.descriptor.unit_id, row.descriptor.scale_cells) for row in self.descriptors) != tuple((unit, scale) for unit in source.unit_ids for scale in self.scale_cells):
            raise ValueError("numeric export lacks the exact full source/unit/scale census")
        expected_scales = (16, 32, 64) if source.phase is SimulatorMorphismChallengePhase.DEVELOPMENT else (64, 128, 256)
        if self.scale_cells != expected_scales:
            raise ValueError("numeric export source phase and scale census differ")
        for unit, seed in zip(source.unit_ids, source.seeds, strict=True):
            if any(row.descriptor.seed_sha256 != sha256(seed).hexdigest() for row in self.descriptors if row.descriptor.unit_id == unit):
                raise ValueError("numeric export descriptor changes a source seed")


@dataclass(frozen=True, slots=True)
class RCChallengeNumericExportReceipt(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/simulator-morphism-challenges/numeric-export-receipt"
    receipt_id: str
    source_publication: ArtifactWriteResult
    export_publication: ArtifactWriteResult
    source_manifest: ArtifactManifest
    export_manifest: ArtifactManifest

    def __post_init__(self) -> None:
        validate_stable_id(self.receipt_id)
        if self.source_publication.logical.payload_schema != RCChallengeNumericSource.SCHEMA or self.export_publication.logical.payload_schema != RCChallengeNumericExport.SCHEMA:
            raise ValueError("numeric export receipt requires real current source/export publications")
        for result, manifest in ((self.source_publication, self.source_manifest), (self.export_publication, self.export_manifest)):
            if manifest.logical != result.logical or manifest.materialization != result.materialization or manifest.publication is None:
                raise ValueError("numeric receipt requires exact committed publication manifests")
