# SPDX-License-Identifier: MPL-2.0
"""Public preparation counts; exposed definitions supply no scientific evidence."""
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.configured_specification import matched_e3_estimators
from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
from empirical_lawhood.api.experiment_preparation import load_experiment_specification, prepare_experiment
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection


EXPERIMENTS = Path(__file__).parents[1] / 'programmes/foundations/emergent-structure/workflows'


@pytest.mark.parametrize('curve_primary, feature_counts', (
    (False, {'b0-features': 22, 's0-features': 22, 'shared-base-features': 18}),
    (True, {'b0-features': 24, 's0-features': 24, 'shared-base-features': 20}),
))
def test_public_matched_preparation_retains_complete_census_and_missing_inputs(curve_primary, feature_counts):
    raw = (EXPERIMENTS / 'matrix-programme/scientific-design.example.json').read_bytes()
    specification = decode_canonical_bytes(raw, MatrixProgrammeScientificDesign, maximum_bytes=None).e3
    if not curve_primary:
        specification = replace(specification, methods=matched_e3_estimators(), assessment=replace(
            specification.assessment, improvement_margin=None,
            improvement_rule='MATCHED_MEAN_K_LOSS_REDUCTION_AT_LEAST_ONE_OF_29'))
    original = specification.canonical_bytes()
    prepared = prepare_experiment(specification, scientific_inputs={}, execution=ExecutionSelection(workers=8))
    counts = dict(prepared.census.output_counts)
    assert {key: value for key, value in counts.items() if key.endswith('-features')} == feature_counts
    assert dict(prepared.census.role_counts) == {
        'train': 64, 'calibration': 64, 'evaluation': 80, 'transfer_nearby': 64, 'transfer_shifted': 64}
    assert counts['selected-tasks'] == 1446 and prepared.census.native_effect_count == 288
    assert counts['fitted-models'] == 4 and counts['minimum-primary-successes'] == 52
    assert counts['point-forecast-endpoints'] == 144 * 58 * 4
    assert counts['response-view-endpoints'] == 208 * 29 * 2
    assert not prepared.executable and prepared.draft is None
    assert 'matrix.e3.protected-selection' in {row.code for row in prepared.dependencies}
    assert specification.canonical_bytes() == original


@pytest.mark.parametrize('name', ('configured-v2.json', 'configured-protected-v2.json'))
def test_public_paired15_preparation_preserves_original_feature_census(name):
    specification = load_experiment_specification(EXPERIMENTS / 'matrix-response-experiment' / name)
    prepared = prepare_experiment(specification, scientific_inputs={}, execution=ExecutionSelection(workers=1))
    counts = dict(prepared.census.output_counts)
    assert {key: value for key, value in counts.items() if key.endswith('-features')} == {
        'all-origin-features': 21, 'spectral-features': 13}
    assert counts['fitted-models'] == 3 and specification.calibration_alpha == Decimal('.2')
    assert not prepared.executable and prepared.dependencies
