"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from secrets import token_bytes
from empirical_lawhood.storage.contracts.artifacts import ArtifactWriter
from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengeConfig, SimulatorMorphismChallengePhase
from empirical_lawhood.domains.history.simulator_morphism_challenges.numeric_inputs import (
    RCChallengeExposureCensus as _science_RCChallengeExposureCensus,
    RCChallengeNumericSource as _science_RCChallengeNumericSource,
)

from empirical_lawhood.domains.history.simulator_morphism_challenges.numeric_publications import (
    RCChallengeNumericInput as _science_RCChallengeNumericInput,
)

def allocate_numeric_source(*, source_id: str, config: SimulatorMorphismChallengeConfig,
                            exposure_census: _science_RCChallengeExposureCensus,
                            exposed_seed_hexes: tuple[str, ...] | None = None) -> _science_RCChallengeNumericSource:
    """Freeze actual numeric allocations before issue; supplied examples stay exposed."""
    from empirical_lawhood.domains.history.simulator_morphism_challenges.descriptors import deterministic_development_seed

    if config.phase is SimulatorMorphismChallengePhase.DEVELOPMENT:
        if exposed_seed_hexes is not None:
            raise ValueError("development allocations are the fixed exposed source")
        seeds = tuple(deterministic_development_seed(unit).hex() for unit in config.unit_ids)
        exposed = True
    elif config.phase is SimulatorMorphismChallengePhase.NOMINATION:
        seeds = exposed_seed_hexes if exposed_seed_hexes is not None else tuple(token_bytes(32).hex() for _ in config.unit_ids)
        exposed = exposed_seed_hexes is not None
    else:
        raise ValueError("allocate through nomination before evaluation; canary has no disorder roster")
    return _science_RCChallengeNumericSource(source_id, config.phase, config.unit_ids, seeds, exposure_census, exposed)


def authenticate_numeric_input(value: _science_RCChallengeNumericInput, writer: ArtifactWriter) -> None:
    """Use the existing external plane to verify retained payload and manifest bytes."""
    for publication in (value.receipt.source_publication, value.receipt.export_publication, value.receipt_publication):
        writer.verify(publication.materialization)
        writer.verify(publication.manifest_materialization)
    writer.verify_manifests((value.receipt.source_manifest, value.receipt.export_manifest, value.receipt_manifest))
