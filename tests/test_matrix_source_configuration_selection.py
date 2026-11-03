# SPDX-License-Identifier: MPL-2.0
"""Pure source-selection delegation; no files, source observation or native work."""

from pathlib import Path
from types import SimpleNamespace
from hashlib import sha256

import pytest

from empirical_lawhood.api import finite_operands as owner
from empirical_lawhood.adapters.methods.finite_response_law.transient_bridge import TransientBridgeSpec
from empirical_lawhood.adapters.methods.finite_response_law.transient_bridge_source_records import (
    CurrentPreparationSourceConfig, MatrixPreparationSourceConfig, MatrixPreparationSourceProtocol,
)
from empirical_lawhood.infrastructure import numerical_provenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from tests.test_matrix_operand_transport import allocation


@pytest.mark.parametrize('project_root', (None, Path('/explicit/selected-source')))
@pytest.mark.parametrize('original', (False, True))
def test_matrix_configuration_observes_selected_source_once_and_preserves_identity(monkeypatch, project_root, original):
    calls = []
    rows = (('selected/source.py', 'a' * 64),)
    code = sha256(canonical_json_bytes(rows)).hexdigest()
    def observe(selected):
        calls.append(selected)
        return rows, code, 'b' * 64, 'c' * 40, False
    monkeypatch.setattr(numerical_provenance, 'observe_implementation_source', observe)
    def redundant_observation(*args, **kwargs):
        pytest.fail('configuration repeated its selected package observation')
    monkeypatch.setattr(owner, 'current_preparation_code_sources_sha256', redundant_observation)
    monkeypatch.setattr(numerical_provenance, 'numerical_package_sources', redundant_observation)
    lower = SimpleNamespace(identity=ObjectIdentity('original.synthetic',
        'empirical-lawhood/methods/finite-response-law/original-finite-response-law', '1.0.0', 'd' * 64))
    result = owner.prepare_matrix_source_configuration(config_id='configuration.synthetic', allocation=allocation(),
        original_f=lower if original else None, project_root=project_root)
    assert calls == [project_root]
    assert result.dependency_lock_sha256 == 'b' * 64
    assert result.code_sources_sha256 == code
    if original:
        assert result.original_f == lower.identity
        expected = CurrentPreparationSourceConfig('configuration.synthetic', allocation().identity, lower.identity,
            ObjectIdentity.from_record('finite-response-law.transient-bridge-protocol', TransientBridgeSpec()),
            code, dependency_lock_sha256='b' * 64)
    else:
        expected = MatrixPreparationSourceConfig('configuration.synthetic', allocation().identity,
            MatrixPreparationSourceProtocol(), code, dependency_lock_sha256='b' * 64)
    assert result.canonical_bytes() == expected.canonical_bytes()
    assert result.identity == expected.identity


def test_selected_source_refusal_precedes_configuration_or_package_observation(monkeypatch):
    error = PermissionError('selected candidate/source does not match')
    def refuse(selected):
        assert selected is None
        raise error
    monkeypatch.setattr(numerical_provenance, 'observe_implementation_source', refuse)
    monkeypatch.setattr(owner, 'current_preparation_code_sources_sha256',
        lambda: pytest.fail('source refusal reached a package/configuration observation'))
    with pytest.raises(PermissionError) as raised:
        owner.prepare_matrix_source_configuration(config_id='configuration.synthetic', allocation=allocation())
    assert raised.value is error
