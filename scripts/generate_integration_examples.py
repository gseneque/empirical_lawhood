# SPDX-License-Identifier: MPL-2.0
"""Generate explicit exposed integration inputs; never create current authority."""

import argparse
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from empirical_lawhood.adapters.composition.finite_response_law.assignment import proposed_scientific_seeds
from empirical_lawhood.adapters.composition.finite_response_law.rerun_input import FiniteResponseLawCurrentAllocation, FiniteResponseLawCurrentExposure, FiniteResponseLawRerunInput, PUBLIC_CALIBRATION_MASTER_SEED, PUBLIC_EVALUATION_MASTER_SEED, original_development_exposure, public_rerun_sample_exposure
from empirical_lawhood.adapters.methods.finite_response_law.nominated_package import current_nomination_from_sources
from empirical_lawhood.adapters.methods.finite_response_law.original_f import original_f_source_identities, authenticate_original_f_sources, original_f_from_bytes
from empirical_lawhood.adapters.methods.finite_response_law.science import FiniteResponseLawScienceSpec
from empirical_lawhood.adapters.methods.finite_response_law.transient_bridge_source_records import CurrentPreparationSourceConfig, MatrixPreparationSourceConfig, MatrixPreparationSourceProtocol
from empirical_lawhood.adapters.methods.constructed_preparation_applicability.config import FIXED_PROBE_SEED
from empirical_lawhood.adapters.simulator_morphism_challenges.numeric_inputs import exposed_source_export_example, exposed_phase_config_examples
from empirical_lawhood.api.finite_operands import ORIGINAL_F_FILENAMES, _public_bytes, current_preparation_code_sources_sha256, current_preparation_protocol_identity
from empirical_lawhood.kernel.matrix_inputs import MATRIX_NATIVE_PURPOSES, MatrixAllocation, MatrixRootAllocation, MatrixPurposeSeed

ROOT = Path(__file__).resolve().parents[1]

# These files are editable exposed development projections of current owners.
# Retained scientific input/evidence bytes live in their original custody, not
# a numbered regeneration chain required by this generator or the release.


def _root(index: int, cohort: str, label: str):
    seeds = []
    for purpose in sorted(MATRIX_NATIVE_PURPOSES):
        digest = sha256(f'public-exposed-matrix-input|{label}|{index}|{purpose}'.encode()).digest()
        seeds.append(MatrixPurposeSeed(purpose, int.from_bytes(digest[:16], 'big')))
    conditioning = ()
    if cohort == 'constructed':
        conditioning = (MatrixPurposeSeed('passive-probes', FIXED_PROBE_SEED, 'PCG64DXSM'),)
    else:
        seeds.append(MatrixPurposeSeed('passive-probes', int.from_bytes(sha256(f'public-exposed-matrix-probe|{label}|{index}'.encode()).digest(), 'big'), 'PCG64DXSM'))
    return MatrixRootAllocation(f'example.exposed.{label}.root-{index:03d}', cohort, tuple(sorted(seeds, key=lambda seed: seed.purpose_id)), conditioning_seeds=conditioning)


def examples() -> dict[str, bytes]:
    sources = _public_bytes('original_f', ORIGINAL_F_FILENAMES, (37921, 3919, 1428, 17166, 522736))
    identities = original_f_source_identities(tuple(f'example.original-f.source.{index}' for index in range(5)))
    authenticate_original_f_sources(identities, sources)
    lower = original_f_from_bytes(sources[0], payload_id='example.original-f', source_identities=identities)
    nomination, _ = current_nomination_from_sources('example.original-nomination', _public_bytes('nomination', ('development-report.json', 'coefficients.transport.json', 'development-manifest.json'), (32160, 763803, 227387)))
    allocation = MatrixAllocation('example.exposed.matrix-allocation', tuple(_root(index, 'q2' if index < 8 else 'cir1', 'preparation') for index in range(24)))
    conformance = MatrixAllocation('example.exposed.native-conformance-allocation', tuple(_root(index, cohort, 'conformance') for index, cohort in enumerate(('q2', 'cir1', 'constructed'))))
    lock_sha256 = sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    code_sha256 = current_preparation_code_sources_sha256()
    source = CurrentPreparationSourceConfig('example.exposed.preparation-source.current', allocation.identity, lower.identity, current_preparation_protocol_identity(), code_sha256, dependency_lock_sha256=lock_sha256)
    generic = MatrixPreparationSourceConfig('example.exposed.matrix-source.current', allocation.identity, MatrixPreparationSourceProtocol(), code_sha256, dependency_lock_sha256=lock_sha256)
    original_units, original_seeds = original_development_exposure()
    sample_units, sample_seeds = public_rerun_sample_exposure()
    exposure = FiniteResponseLawCurrentExposure('example.original-and-public-exposure', tuple(sorted(set(original_units) | set(sample_units))), tuple(sorted(set(original_seeds) | set(sample_seeds))))
    allocations = tuple(FiniteResponseLawCurrentAllocation(stage, f'empirical-lawhood.finite-response-law.{stage}.public-sample', FiniteResponseLawScienceSpec().plan_sha256, count, 'EXPOSED_DEVELOPMENT_NONPROMOTABLE', proposed_scientific_seeds(stage, master)) for stage, count, master in (('calibration', 32, PUBLIC_CALIBRATION_MASTER_SEED), ('prospective-evaluation', 64, PUBLIC_EVALUATION_MASTER_SEED)))
    rerun = FiniteResponseLawRerunInput('example.exposed.finite-calibration', 'calibration', allocations[0], nomination, original_units, original_seeds)
    records = {
        'programmes/foundations/emergent-structure/workflows/matrix-inputs/allocation.json': allocation,
        'programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json': source,
        'programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json': generic,
        'programmes/foundations/emergent-structure/workflows/preparation-applicability/conformance-allocation.json': conformance,
        'programmes/foundations/measurement-and-response/workflows/rc-challenges/source-export.json': exposed_source_export_example(),
        'programmes/foundations/emergent-structure/workflows/finite-response-law/current-calibration-allocation.json': allocations[0],
        'programmes/foundations/emergent-structure/workflows/finite-response-law/current-evaluation-allocation.json': allocations[1],
        'programmes/foundations/emergent-structure/workflows/finite-response-law/current-exposure.json': exposure,
        'programmes/foundations/emergent-structure/workflows/finite-response-law/rerun-calibration.json': rerun,
    }
    records.update({f'programmes/foundations/measurement-and-response/workflows/rc-challenges/{config.phase.value.lower()}.json': config for config in exposed_phase_config_examples()})
    from empirical_lawhood.api.matrix_geometry import matrix_geometry_example_input
    from empirical_lawhood.api.selected_events import selected_parent_example_input
    from empirical_lawhood.api.matrix_history_analysis import matrix_history_example_records
    records["programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json"] = replace(matrix_geometry_example_input(environment_lock_sha256=lock_sha256), config_id="matrix-geometry.exposed-example.current")
    records["programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json"] = replace(selected_parent_example_input(environment_lock_sha256=lock_sha256), config_id="selected-parent.exposed-paper-context.current")
    history = matrix_history_example_records(ROOT)
    history_source = replace(history["source.json"], config_id="public.matrix-history.source.current")
    records["programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json"] = history["allocation.json"]
    records["programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json"] = history_source
    for mode in ("algebra", "passive"):
        records[f"programmes/foundations/emergent-structure/workflows/matrix-history-analysis/{mode}-current.json"] = replace(history[f"{mode}.json"], config_id=f"public.matrix-history.{mode}.current", source=history_source)
    from empirical_lawhood.adapters.methods.matrix_history_analysis.experiment_preparation import (
        MatrixHistoryProgrammeSpecification, PROTOCOL_ID as history_protocol,
    )
    from empirical_lawhood.kernel.provenance import ObjectIdentity
    from empirical_lawhood.planning.experiment_inputs import ExperimentInputBinding, ExperimentInputSelection
    history_allocation = history['allocation.json']
    history_analysis = records['programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json']
    analysis_identity = ObjectIdentity.from_record(history_analysis.config_id, history_analysis)
    records['programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json'] = MatrixHistoryProgrammeSpecification(
        'experiment.disclosed-e2-retained-result', history_allocation.identity, analysis_identity, (),
        'matrix-history/replace-with-retained-result', 'READ_RETAINED')
    records['programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme-sources.json'] = ExperimentInputSelection(
        'sources.disclosed-e2-originals', history_protocol, (
            ExperimentInputBinding('allocation', history_allocation.identity, 'allocation.json',
                len(history_allocation.canonical_bytes())),
            ExperimentInputBinding('analysis', analysis_identity, 'algebra-current.json',
                len(history_analysis.canonical_bytes())),
        ))
    from empirical_lawhood.api.matrix_preparation_analysis import tangent_preparation_configuration
    from empirical_lawhood.adapters.methods.matrix_preparation_analysis.records import TransientAnalysisConfig, BaselineSupportConfig
    records["programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json"] = tangent_preparation_configuration(config_id="example.matrix-tangent.exposed.current", namespace="example.matrix-tangent.exposed", master_seed=70409, project_root=ROOT)
    records["programmes/foundations/emergent-structure/workflows/matrix-transient/input.json"] = TransientAnalysisConfig("example.matrix-transient.exposed")
    records["programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json"] = BaselineSupportConfig("example.matrix-baseline.exposed")
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import default_chain_config
    records["programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json"] = default_chain_config()
    payloads = {name: record.canonical_bytes() for name, record in records.items()}
    return payloads


def write_examples(payloads: dict[str, bytes], *, root: Path, check: bool) -> None:
    # Check mode compares current projections without repairing them. Regeneration
    # updates development examples; it does not edit retained scientific inputs.
    for relative, payload in payloads.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != payload:
                raise SystemExit(f'Integration example drifted: {relative}')
    if not check:
        for relative, payload in payloads.items():
            path = root / relative
            if path.is_file() and path.read_bytes() == payload:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    write_examples(examples(), root=ROOT, check=args.check)


if __name__ == '__main__':
    main()
