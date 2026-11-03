# SPDX-License-Identifier: MPL-2.0
"""Current authoring permission is an operation-local precondition, never a seal."""
from types import SimpleNamespace

import pytest

from empirical_lawhood.api import experiment_preparation as owner,recursive_authoring
from empirical_lawhood.runtime.experiment_preparation import ExperimentRuntimeBinding


@pytest.mark.parametrize('verdict',(False,True,0,(),{}))
def test_authoring_validator_cannot_return_a_reusable_permission_verdict(verdict):
    guard=owner._authoring_access_guard(preparation=SimpleNamespace(prospective_spec=None),
        binding=SimpleNamespace(validate_authoring_read_access=lambda **values:verdict,
            bootstrap_prospective_input_access=None),
        artifact_writer=object(),read_access=object())
    with pytest.raises(ValueError,match='return None or raise'):
        guard()


@pytest.mark.parametrize('prospective',(False,True))
def test_unsupported_or_prospective_authoring_refuses_operational_access_without_callback(prospective):
    with pytest.raises(ValueError,match='does not support'):
        owner._authoring_access_guard(preparation=SimpleNamespace(prospective_spec=object() if prospective else None),
            binding=None,artifact_writer=object(),read_access=object())


def test_authoring_access_requires_an_ordinary_development_owner():
    with pytest.raises(TypeError,match='ordinary development'):
        ExperimentRuntimeBinding('protocol.disclosed',lambda **values:None,
            prepare_authoring=lambda **values:None,validate_authoring_read_access=lambda **values:None)


@pytest.mark.parametrize('guard',(object(),False))
def test_recursive_author_refuses_noncallable_access_before_source_or_output_io(guard):
    with pytest.raises(TypeError,match='must be callable'):
        recursive_authoring.author_recursive_wave(draft=object(),project_root=object(),artifact_writer=object(),
            output_dir=object(),_input_access_guard=guard)


@pytest.mark.parametrize('verdict',(False,True))
def test_recursive_author_refuses_access_verdict_before_source_or_output_io(verdict):
    with pytest.raises(ValueError,match='return None or raise'):
        recursive_authoring.author_recursive_wave(draft=object(),project_root=object(),artifact_writer=object(),
            output_dir=object(),_input_access_guard=lambda:verdict)
