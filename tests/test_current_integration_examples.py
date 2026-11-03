# SPDX-License-Identifier: MPL-2.0
"""Current exposed projections retain science without a historical input chain."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from empirical_lawhood.api.configuration import load_configuration_record
from empirical_lawhood.api.finite_operands import current_preparation_code_sources_sha256
from empirical_lawhood.api.matrix_geometry import matrix_scientific_code_sha256

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("integration_example_generator", ROOT / "scripts/generate_integration_examples.py")
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)

# Complete scientific operands of the previously exposed examples, excluding
# only producing/configuration identities. The exact old bytes remain archival;
# no old input decoder or historical file is needed to regenerate current inputs.
OPERANDS = {
    'programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json': ('preparation-source', '4b7994705333419d4785101ec1807be9e32c205d752f7d7a61cdd0b8805a0733'),
    'programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json': ('matrix-source', 'f4c4285794d0bde9c18d555e136d46a2d70481d12012d0a633c11277fd395728'),
    'programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json': ('matrix-geometry', 'c2eea1241dfa4f559fc4331dae2c462bacf4e9964b70f5019b189f7366a15826'),
    'programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json': ('selected-parent', '801dee039780e158c03f1bc9b7393afa33403df2c75b9e2a34bfc2b44692763c'),
    'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json': ('matrix-history-source', '55f44af14af2cd33ea1cf57516db94d6dbd0aeb972983be8b38ea18c4f1c88db'),
    'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json': ('matrix-history-analysis', '78b81d514c162f33b799a88c3716740f3fce0360a1e945844d7fbe261e60c814'),
    'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json': ('matrix-history-analysis', '13304471d5e1b0d4c5aa528dda0ed7a4a0e834638f5a431f37dd3a4470e96b65'),
    'programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json': ('matrix-tangent', 'a3453fca22ecc4ced41130a1fb3ef838d19caafc9762f28cef5bf001cb2b701f'),
}


@pytest.fixture(scope='module')
def generated():
    return GENERATOR.examples()


def _without_producing_identity(value):
    if isinstance(value, dict):
        return {key: _without_producing_identity(item) for key, item in value.items()
                if key not in {'config_id', 'code_sources_sha256', 'scientific_code_sha256',
                               'dependency_lock_sha256', 'environment_lock_sha256'}}
    if isinstance(value, list):
        return [_without_producing_identity(item) for item in value]
    return value


@pytest.mark.parametrize('path,operand', tuple(OPERANDS.items()))
def test_complete_scientific_operands_and_strict_current_consumer(path, operand, generated, tmp_path):
    consumer, expected_digest = operand
    payload = generated[path]
    science = json.dumps(_without_producing_identity(json.loads(payload)), sort_keys=True, separators=(',', ':')).encode()
    assert sha256(science).hexdigest() == expected_digest
    selected = tmp_path / 'current-selector.json'
    selected.write_bytes(payload)
    assert load_configuration_record(selected, consumer=consumer).canonical_bytes() == payload


def test_current_projections_bind_actual_producing_source_and_lock(generated):
    package_digest = current_preparation_code_sources_sha256()
    native_digest = matrix_scientific_code_sha256()
    lock_digest = sha256((ROOT / 'uv.lock').read_bytes()).hexdigest()
    for path in OPERANDS:
        current = json.loads(generated[path])['value']
        if 'source' in current and 'code_sources_sha256' in current['source'].get('value', {}):
            current = current['source']['value']
        if 'code_sources_sha256' in current:
            assert current['code_sources_sha256'] == package_digest
            assert current['dependency_lock_sha256'] == lock_digest
        else:
            assert current['scientific_code_sha256'] == native_digest
            assert current['environment_lock_sha256'] == lock_digest


def test_regeneration_updates_development_projection_without_numbered_successors(tmp_path):
    current = tmp_path / 'source-current.json'
    current.write_bytes(b'previous development projection')
    GENERATOR.write_examples({'source-current.json': b'new development projection'}, root=tmp_path, check=False)
    assert current.read_bytes() == b'new development projection'
    assert list(tmp_path.iterdir()) == [current]


def test_check_mode_performs_no_repair_or_publication(tmp_path):
    current = tmp_path / 'source-current.json'
    current.write_bytes(b'current development projection')
    with pytest.raises(SystemExit, match='Integration example drifted'):
        GENERATOR.write_examples({'source-current.json': b'changed projection', 'missing.json': b'new projection'}, root=tmp_path, check=True)
    assert current.read_bytes() == b'current development projection'
    assert list(tmp_path.iterdir()) == [current]
