# SPDX-License-Identifier: MPL-2.0
"""Current pooled configuration/resource refusal controls; no effects or authority."""

from dataclasses import replace
from decimal import Decimal as D
import numpy as np
import pytest
from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_pooled_bindings as pooled
from empirical_lawhood.adapters.methods.matrix_parameter_response.records import MatrixParameterResponseSource
from empirical_lawhood.adapters.methods.matrix_factor_response.response_error_prediction import STRATA
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.evidence import OutcomeAccess as Access, VisibilityCeiling as Visibility
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputBinding, WorkerInputKind, WorkerInputPort, WorkerIsolationProfile
from tests.test_matrix_factor_response import Reader


FINITE = ResourceBudget(1, 1024**3, 0, D(30), 64*1024**2, 64*1024**2)



def _blocked(*args, **kwargs):
    raise AssertionError('resource control entered scientific producer, fit, RNG or eigensolve')



def _block_effects(monkeypatch):
    from empirical_lawhood.adapters.methods.matrix_factor_response import response_error_prediction
    monkeypatch.setattr(response_error_prediction, 'fit_error_model', _blocked)
    monkeypatch.setattr(pooled, 'forecast', _blocked)
    for name in ('default_rng', 'Generator', 'PCG64', 'PCG64DXSM'):
        monkeypatch.setattr(np.random, name, _blocked)
    monkeypatch.setattr(np.linalg, 'eigh', _blocked)
    monkeypatch.setattr(np.linalg, 'eigvalsh', _blocked)



def _budget(placement):
    return pooled.BUDGET if placement == 'registered' else FINITE if placement == 'finite' else replace(FINITE,
        cpu_cores=2 if placement == 'cpu2' else 1, gpu_devices=1 if placement == 'gpu1' else 0)



def _port(record, name, *, access=Access.OUTCOME_BLIND, dependency=False, reader=None):
    raw = record.canonical_bytes()
    return WorkerInputPort(WorkerInputBinding(name, 'materialization.'+name, record.SCHEMA, 'application/json', len(raw),
        Visibility.PROSPECTIVE, access, WorkerInputKind.DEPENDENCY if dependency else WorkerInputKind.EXTERNAL), Reader(raw) if reader is None else reader)



def _context(config, task_id, manifest, ports, access, budget, receipts=()):
    if access is Access.DEVELOPMENT_VISIBLE:
        ports = tuple(replace(p, binding=replace(p.binding, visibility_ceiling=Visibility.DEVELOPMENT_ONLY)) for p in ports)
    ports = tuple(sorted(ports, key=lambda p: p.artifact_id))
    config_port = next(p for p in ports if p.payload_schema == config.SCHEMA)
    return TaskContext('run.software.resource', task_id, 'attempt.software.resource', CapabilityConfigRef(config.config_id,
        config.SCHEMA, manifest.config_schema_sha256, config.fingerprint(), config_port.artifact_id),
        tuple(p.binding for p in ports), ports, (), manifest.permissions, access, budget, WorkerIsolationProfile.TRUSTED_LOCAL, receipts)



@pytest.mark.parametrize('placement', ('registered', 'finite', 'cpu2', 'gpu1'))
@pytest.mark.parametrize('protected', (False, True))
def test_pooled_strict_config_guard_stops_before_model_or_fit(monkeypatch, placement, protected):
    _block_effects(monkeypatch)
    schema = pooled.MatrixResponseJointDesignPooled.SCHEMA
    root = 'software.pooled.root'
    config = pooled.MatrixResponseJointForecastConfigPooled('config.'+pooled.node_id(root, protected),
        ObjectIdentity('software.pooled.design', schema, '1.0.0', 'a'*64), root, 'software.pooled.group', STRATA[0],
        ObjectIdentity('software.source', MatrixParameterResponseSource.SCHEMA, '1.0.0', 'b'*64),
        tuple((n, 'software.producer.'+n) for n, _ in pooled.INPUTS), protected)
    manifest = pooled.selected_manifest(protected)
    access = Access.OUTCOME_BLIND if protected else Access.DEVELOPMENT_VISIBLE
    port = _port(config, config.config_id, access=access)
    if not protected:
        port = replace(port, binding=replace(port.binding, visibility_ceiling=Visibility.DEVELOPMENT_ONLY))
    context = _context(config, pooled.node_id(root, protected), manifest, (port,), access, _budget(placement))
    accepted = placement == 'registered' or protected and placement == 'finite'
    with pytest.raises(ValueError, match='omits actual' if accepted else 'resources'):
        pooled.MatrixResponseJointForecastRunnerPooled(protected).execute(context)
