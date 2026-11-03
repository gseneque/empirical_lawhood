# SPDX-License-Identifier: MPL-2.0
"""Public exposed execution custody and no-contact recovery conformance."""

from pathlib import Path
from dataclasses import replace
import os

import pytest

from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding, load_authored_wave
from empirical_lawhood.api.recursive_execution import read_recursive_wave, run_recursive_wave
from empirical_lawhood.api import numerical_provenance as provenance_owner
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import RCPrerequisiteChainConfig
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.infrastructure.artifacts import ExternalArtifactPlane, FilesystemState, GuardedExternalRoot
from empirical_lawhood.infrastructure.execution import ExecutionResourceCapacity, LocalExecutionResourceAdmitter
from empirical_lawhood.runtime.artifacts import ExternalRootContract

ROOT = Path(__file__).resolve().parents[1]


class _SelectedFixtureInspector:
    def inspect(self, contract):
        return FilesystemState(contract.canonical_path, True, True, 2**40, False)


def _plane(path):
    path.mkdir()
    contract = ExternalRootContract("recursive-software-fixture", "Exposed test custody", str(path), str(path),
                                   "empirical-lawhood/testing/recursive-custody", 1)
    from empirical_lawhood.api.integration_artifact_profiles import integration_artifact_profile_validators
    return ExternalArtifactPlane(GuardedExternalRoot(contract, _SelectedFixtureInspector()),
                                validators=integration_artifact_profile_validators())


def _draft():
    config = decode_canonical_bytes((ROOT / "programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json").read_bytes(),
                                   RCPrerequisiteChainConfig, maximum_bytes=8*1024**2)
    return rc_recursive_draft(config, unit_ids=(config.units[6].unit_id,), include_summary=False)


@pytest.mark.parametrize('worker_mode',('default-serial','detected-parallel','explicit-parallel'))
def test_public_service_preserves_adverse_census_and_recovers_without_native(tmp_path, monkeypatch, worker_mode):
    # Snapshot this software fixture's source once; concurrent editor changes are
    # tested separately by the source-substitution refusal, not numerical work.
    source = implementation_binding(ROOT)
    import empirical_lawhood.api.recursive_authoring as author
    import empirical_lawhood.api.recursive_execution as execute
    from empirical_lawhood.infrastructure import execution as scheduler_owner
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    selected_count = 1 if worker_mode == 'default-serial' else min(2,len(os.sched_getaffinity(0)))
    capacity = replace(LocalExecutionResourceAdmitter.detect_capacity(),cpu_cores=selected_count)
    monkeypatch.setattr(LocalExecutionResourceAdmitter,'detect_capacity',staticmethod(lambda: capacity))
    assess = LocalExecutionResourceAdmitter.assess
    admissions = []
    def observed_admission(self, *args, **kwargs):
        admissions.append(self.capacity)
        return assess(self, *args, **kwargs)
    monkeypatch.setattr(LocalExecutionResourceAdmitter,'assess',observed_admission)
    scheduler = scheduler_owner.LocalScheduler
    selections = []
    class ObservedScheduler(scheduler):
        def __init__(self, **kwargs):
            selections.append((kwargs['maximum_parallel_tasks'],kwargs['parallel_resource_capacity']))
            assert kwargs['maximum_parallel_tasks'] == selected_count
            assert kwargs['parallel_resource_capacity'] is (capacity if selected_count > 1 else None)
            super().__init__(**kwargs)
    monkeypatch.setattr(scheduler_owner,'LocalScheduler',ObservedScheduler)
    controls = {} if worker_mode == 'default-serial' else {'maximum_parallel_tasks':selected_count,
        'parallel_resource_capacity':capacity if worker_mode == 'explicit-parallel' else None}
    observed = provenance_owner.capture_numerical_provenance(project_root=ROOT)
    monkeypatch.setattr(author, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(execute, "implementation_binding", lambda root, **kwargs: source)
    monkeypatch.setattr(provenance_owner, "capture_numerical_provenance", lambda **kwargs: observed)
    plane = _plane(tmp_path / "selected")
    directory = tmp_path / "selected/authored"
    authored = author_recursive_wave(draft=_draft(), project_root=ROOT, artifact_writer=plane, output_dir=directory)
    assert authored["native_contact"] == "none" and authored["task_count"] == 9
    report = run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane, **controls)
    assert report["status"] == "SUCCEEDED"
    assert report["native_contact"] == "possible" and report["new_native_contact_count"] == 2
    unit = next(iter(next(iter(report["terminal_products"].values())).values()))["value"]
    assert len(unit["cases"]) == 10
    statuses = {row["value"]["variant_id"]: row["value"]["measurement_state"] for row in unit["cases"]}
    assert statuses["biased"] == "FAILED" and statuses["missing"] == "UNEVALUABLE"
    def forbidden(*args, **kwargs):
        raise AssertionError("completed native evidence was reacquired")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    retained = {**report, "native_contact": "none", "new_native_contact_count": 0}
    assert read_recursive_wave(directory=directory, artifact_writer=plane) == retained
    assert run_recursive_wave(directory=directory, project_root=ROOT, artifact_writer=plane, **controls) == retained
    assert len(selections) == 2
    assert len(admissions) == 2 and all(value is capacity for value in admissions)
    # The bytes—not an editable summary success field—remain authoritative.
    (directory / "draft.json").write_bytes(b"{}")
    with pytest.raises((ValueError, RuntimeError, OSError), match="artifact|Artifact|publication|bytes|commit"):
        load_authored_wave(directory=directory, artifact_writer=plane)


@pytest.mark.parametrize('count',(0,-1,True,False,1.5,'2',None))
def test_invalid_worker_count_refuses_before_custody_or_native_contact(monkeypatch, count):
    from empirical_lawhood.api import recursive_execution as execute, recursive_inquiry as inquiry
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid worker selection reached custody')
    monkeypatch.setattr(execute,'load_authored_wave',forbidden)
    monkeypatch.setattr(inquiry,'_read',forbidden)
    for service in (execute.run_recursive_wave,inquiry.run_inquiry_successor):
        with pytest.raises(ValueError,match='positive integer'):
            service(directory=None,project_root=None,artifact_writer=None,maximum_parallel_tasks=count)


@pytest.mark.parametrize('capacity',(1,{},object()))
def test_invalid_capacity_type_refuses_before_custody(monkeypatch, capacity):
    from empirical_lawhood.api import recursive_execution as execute, recursive_inquiry as inquiry
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid capacity reached custody')
    monkeypatch.setattr(execute,'load_authored_wave',forbidden)
    monkeypatch.setattr(inquiry,'_read',forbidden)
    for service in (execute.run_recursive_wave,inquiry.run_inquiry_successor):
        with pytest.raises(TypeError,match='ExecutionResourceCapacity'):
            service(directory=None,project_root=None,artifact_writer=None,parallel_resource_capacity=capacity)


@pytest.mark.parametrize('limit',('capacity','affinity'))
def test_excessive_worker_count_refuses_before_native_contact(monkeypatch, limit):
    from empirical_lawhood.api import recursive_execution as execute
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    def forbidden(*args, **kwargs):
        raise AssertionError('excessive worker selection reached custody or native contact')
    monkeypatch.setattr(execute,'load_authored_wave',forbidden)
    monkeypatch.setattr(LocalProcessExecutor,'execute',forbidden)
    monkeypatch.setattr(execute.os,'sched_getaffinity',lambda pid: {0} if limit == 'affinity' else {0,1})
    capacity = ExecutionResourceCapacity(1 if limit == 'capacity' else 2,2**40,0,True,True,False)
    with pytest.raises(ValueError,match='CPU capacity' if limit == 'capacity' else 'CPU affinity'):
        execute.run_recursive_wave(directory=None,project_root=None,artifact_writer=None,
            maximum_parallel_tasks=2,parallel_resource_capacity=capacity)


@pytest.mark.parametrize("lifecycle", ("run", "recover"))
def test_initial_programme_authenticates_then_refuses_a_generic_wave_before_executor(tmp_path, monkeypatch, lifecycle):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.infrastructure.execution import LocalProcessExecutor
    from empirical_lawhood.api import recursive_authoring as author, recursive_execution as execute
    plane = _plane(tmp_path / "selected")
    directory = tmp_path / "selected/authored"
    authored = author_recursive_wave(draft=_draft(), project_root=ROOT, artifact_writer=plane, output_dir=directory)
    assert authored["native_contact"] == "none"
    authenticated_load = author.load_authored_wave
    loads = []
    def observed_load(**kwargs):
        loads.append(kwargs["directory"])
        return authenticated_load(**kwargs)
    monkeypatch.setattr(author, "load_authored_wave", observed_load)
    monkeypatch.setattr(execute, "load_authored_wave", observed_load)
    def forbidden(*args, **kwargs):
        pytest.fail("wrong-lifecycle initial programme reached the executor")
    monkeypatch.setattr(LocalProcessExecutor, "execute", forbidden)
    service = ExperimentProgrammeService(ROOT, plane)
    with pytest.raises(ValueError, match="initial programme requires its exact development experiment instance"):
        getattr(service, lifecycle)(directory=directory, maximum_parallel_tasks=1)
    assert loads == [directory]


@pytest.mark.parametrize("scope", (None, 0, 1, "initial"))
def test_initial_experiment_scope_requires_boolean_before_custody(monkeypatch, scope):
    from empirical_lawhood.api import recursive_execution as execute
    def forbidden(*args, **kwargs):
        pytest.fail("untyped initial-experiment scope reached custody")
    monkeypatch.setattr(execute, "load_authored_wave", forbidden)
    with pytest.raises(TypeError, match="explicit boolean"):
        execute.run_recursive_wave(directory=None, project_root=None, artifact_writer=None,
            require_initial_experiment=scope)
