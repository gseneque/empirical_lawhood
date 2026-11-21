# SPDX-License-Identifier: MPL-2.0
"""Adverse raw-coordinate, engine-custody and no-effect registration controls."""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from types import SimpleNamespace

import pytest

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.contracts import FileEvidence
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberEngine
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_assessment import _residues, exclusion_signature, read_initial_coordinates, retained_bonded_signature, stereocentre_volume, keto_stereocentre_preserved
from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import authenticate_engine, operation_declaration


def coordinates(values, count=2):
    rows = ["exposed coordinate-reader control",str(count)]
    rows += ["".join(f"{D(v):12.7f}" for v in values[i:i+6]) for i in range(0,len(values),6)]
    return "\n".join(rows)+"\n"


def test_raw_coordinates_preserve_values_and_explicit_periodic_box():
    values = ("0.1234567","-5.2345678",9,1,2,3)
    raw = coordinates(values)
    xyz,box = read_initial_coordinates(raw,2,periodic=False)
    assert xyz == ((D(values[0]),D(values[1]),D(9)),(D(1),D(2),D(3))) and box == ()
    xyz2,box = read_initial_coordinates(coordinates((*values,30,40,50,90,90,90)),2,periodic=True)
    assert xyz2 == xyz and box == tuple(map(D,(30,40,50,90,90,90)))


@pytest.mark.parametrize("kind",("missing","extra","nan","wrong-count","velocities","nonorthogonal","negative-box"))
def test_missing_atoms_velocities_and_changed_cell_are_refused(kind):
    values = list(range(6))
    periodic = kind in ("nonorthogonal","negative-box")
    if periodic:values += [30,40,50,90,90,90]
    if kind == "missing":values.pop()
    elif kind == "extra":values.append(10)
    elif kind == "nan":values[0] = "NaN"
    elif kind == "velocities":values += list(range(6))
    elif kind == "nonorthogonal":values[-1] = 100
    elif kind == "negative-box":values[-6] = -30
    raw = coordinates(values,count=3 if kind=="wrong-count" else 2)
    with pytest.raises(ValueError):
        read_initial_coordinates(raw,2,periodic=periodic)


def test_duplicate_named_atoms_cannot_disappear_into_a_mapping():
    with pytest.raises(ValueError,match="duplicates"):
        _residues(dict(residue_starts=(1,),residue_names=("RUB",),atom_names=("C1","C1"),term_census={"atoms":2}))


def engine(tmp_path):
    binary = tmp_path/"toolchain/bin/teLeap"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"exposed nonexecutable engine custody control")
    for name in ("ld-linux-x86-64.so.2","libc.so.6"):
        library = tmp_path/"runtime/lib"/name
        library.parent.mkdir(parents=True,exist_ok=True)
        library.write_bytes(b"exposed nonexecutable runtime custody control")
    record = GpAmberEngine("engine.exposed-control",str(tmp_path),
        tuple(FileEvidence(p.relative_to(tmp_path).as_posix(),p.stat().st_size,sha256(p.read_bytes()).hexdigest())
              for p in sorted(tmp_path.rglob("*")) if p.is_file()))
    return binary,record


def test_engine_custody_authenticates_exact_bytes_without_running_binary(tmp_path):
    binary,record = engine(tmp_path)
    authenticate_engine(record)
    binary.write_bytes(b"changed")
    with pytest.raises(ValueError,match="differs"):
        authenticate_engine(record)


@pytest.mark.parametrize("kind",("extra","symlink","missing"))
def test_engine_census_cannot_hide_members(tmp_path,kind):
    binary,record = engine(tmp_path)
    if kind == "extra":(tmp_path/"extra").write_text("unselected")
    elif kind == "symlink":(tmp_path/"link").symlink_to(binary)
    else:binary.unlink()
    with pytest.raises((ValueError,FileNotFoundError)):
        authenticate_engine(record)


def test_engine_record_rejects_incomplete_or_duplicate_file_census(tmp_path):
    _,record = engine(tmp_path)
    with pytest.raises(ValueError):replace(record,files=())
    with pytest.raises(ValueError):replace(record,files=record.files*2)


def test_native_launch_uses_the_authenticated_runtime_loader(tmp_path):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import amber_command
    binary,record = engine(tmp_path)
    command = amber_command(record)
    assert command == [str(tmp_path/"runtime/lib/ld-linux-x86-64.so.2"),"--library-path",
        str(tmp_path/"runtime/lib"),str(binary)]
    with pytest.raises(ValueError,match="runtime loader"):
        amber_command(replace(record,files=tuple(row for row in record.files if "ld-linux" not in row.relative_path)))


def native_initial_source(tmp_path, monkeypatch, *, timeout=None):
    from empirical_lawhood.adapters.rubisco.rubisco_response import construction_engine, library_construction
    monkeypatch.setattr(construction_engine, "authenticate_numeric_engine", lambda *a, **k: None)
    monkeypatch.setattr(library_construction, "construct_i95m_sidechains", lambda text, chains, **kwargs: (text, {}))
    monkeypatch.setattr(library_construction, "relax_solvated_amber", lambda *a: None)
    _,record = engine(tmp_path/"engine")
    directory = tmp_path/"initial-gp.m1-wt";directory.mkdir()
    (directory/"complete-heavy.pdb").write_text("explicit process-control fixture, not molecular coordinates")
    model = SimpleNamespace(name="m1-wt", material=SimpleNamespace(chains=()), chain_map=())
    return SimpleNamespace(engine=record, numeric_engine=object(), models=(model,), construction_seed=20261114,
        construction_platform="CPU", construction_threads=1, per_model_timeout_seconds=timeout), directory


def test_native_call_and_operation_have_no_time_cutoff(tmp_path,monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import initial_amber_native as owner
    source, directory = native_initial_source(tmp_path, monkeypatch)
    observed=[]
    def completed(argv,**kwargs):
        observed.append(kwargs["timeout"])
        assert kwargs["check"] is True
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(owner.subprocess,"run",completed)
    assert owner.execute_initial_amber(source,directory) == (0,False)
    assert observed == [None]
    assert operation_declaration().resources.wall_time_seconds is None


@pytest.mark.parametrize("failure",("nonzero","timeout","spawn"))
def test_process_failures_reach_the_original_native_call_observer(tmp_path,monkeypatch,failure):
    import subprocess
    from empirical_lawhood.adapters.rubisco.rubisco_response import initial_amber_native as owner
    from empirical_lawhood.storage.native_subwork import ExternalNativeSubworkStore
    from empirical_lawhood.science.records.status import OperationalStatus
    from empirical_lawhood.execution.native_subwork import invoke_native_subwork
    source, directory = native_initial_source(tmp_path, monkeypatch, timeout=1)
    observed=[]
    progress = SimpleNamespace(call_entry=lambda entry,**kwargs: observed.append("entry"),
        call_return=lambda entry,**kwargs: observed.append(kwargs))
    def failed(argv,**kwargs):
        assert kwargs["check"] is True and kwargs["timeout"] == 1
        kwargs["stderr"].write(b"disclosed process failure bytes\n")
        if failure=="nonzero":raise subprocess.CalledProcessError(127,argv)
        if failure=="timeout":raise subprocess.TimeoutExpired(argv,1)
        raise OSError("disclosed spawn failure")
    monkeypatch.setattr(owner.subprocess,"run",failed)
    with pytest.raises((subprocess.CalledProcessError,subprocess.TimeoutExpired,OSError)):
        invoke_native_subwork(progress,object(),owner.execute_initial_amber,source,directory)
    assert observed[0] == "entry" and len(observed) == 2
    assert observed[1]["error_type"] == {"nonzero":"CalledProcessError","timeout":"TimeoutExpired","spawn":"OSError"}[failure]
    returned = SimpleNamespace(error_type=observed[1]["error_type"],return_code=None)
    ExternalNativeSubworkStore._validate_call_completion(object(),returned,OperationalStatus.FAILED)
    with pytest.raises(ValueError,match="confuses raw native return"):
        ExternalNativeSubworkStore._validate_call_completion(object(),returned,OperationalStatus.SUCCEEDED)
    assert (directory/"stderr.txt").read_bytes() == b"disclosed process failure bytes\n"


def test_static_registration_runs_no_engine_or_native_work(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError("metadata entered work")
    from empirical_lawhood.domains.rubisco.rubisco_response import gp_initial_topology_operation as owner
    from empirical_lawhood.adapters.rubisco.rubisco_response import initial_amber_native
    monkeypatch.setattr(owner,"authenticate_engine",forbidden)
    monkeypatch.setattr(initial_amber_native,"execute_initial_amber",forbidden)
    declared = operation_declaration()
    assert declared.execution_properties.native_effect
    assert declared.execution_properties.native_work_preparer is owner.prepare_native_work
    assert declared.registration().native_effect
    assert declared.manifest().resource_ceiling.cpu_cores == 8


def test_native_registration_requires_four_direct_models_source_and_provenance():
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology import GpAmberModelInput, GpInitialAmberInput
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import GpAmberOperationConfig
    from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
    declared = operation_declaration()
    assert declared.config_record_type is GpAmberOperationConfig
    assert declared.record_codecs[GpAmberOperationConfig.SCHEMA] is GpAmberOperationConfig
    assert GpAmberOperationConfig.VERSION == "4.0.0"
    assert "empirical-lawhood/rubisco-response/gp-amber-operation-config-v2" not in declared.record_codecs
    ports = {row.port_id: row for row in declared.input_ports}
    assert set(ports) == {"native-model", "native-source", "native-provenance"}
    assert (ports["native-model"].minimum_count,ports["native-model"].maximum_count) == (4,4)
    assert ports["native-model"].payload_schema == GpAmberModelInput.SCHEMA
    assert ports["native-source"].payload_schema == GpInitialAmberInput.SCHEMA
    assert ports["native-provenance"].payload_schema == NumericalProducingProvenance.SCHEMA


@pytest.mark.parametrize("count",(0,1,6,8))
def test_worker_refuses_incomplete_or_extra_direct_inputs_before_reading(count):
    from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import BUDGET, CAPABILITY, _decode
    from empirical_lawhood.science.evidence.evidence import OutcomeAccess
    context = SimpleNamespace(task_id=CAPABILITY, permissions=operation_declaration().manifest().permissions,
        resource_budget=BUDGET,outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,input_ports=(object(),)*count)
    with pytest.raises(ValueError,match="finite task contract"):
        _decode(context)


def test_bonded_comparison_uses_original_coefficients_and_signed_indices():
    original = {"BOND_FORCE_CONSTANT":(D(100),D(200)),"BOND_EQUIL_VALUE":(D("1.1"),D("1.2"))}
    permuted = {key:tuple(reversed(values)) for key,values in original.items()}
    left = {"indexed_bonded_terms":{"BONDS_INC_HYDROGEN":((0,3,1),)}}
    right = {"indexed_bonded_terms":{"BONDS_INC_HYDROGEN":((0,3,2),)}}
    assert retained_bonded_signature(original,left,2) == retained_bonded_signature(permuted,right,2)
    permuted["BOND_FORCE_CONSTANT"] = (D(200),D(101))
    assert retained_bonded_signature(original,left,2) != retained_bonded_signature(permuted,right,2)
    with pytest.raises(ValueError,match="boundary"):
        retained_bonded_signature(original,left,1)


@pytest.mark.parametrize("values",((2,2),(1,2),(0,2),(2,4)))
def test_bad_exclusions_cannot_survive_full_denominator_check(values):
    census = {"exclusion_counts":(2,1,1),"exclusions":(*values,0,0)}
    with pytest.raises(ValueError,match="exclusions"):
        exclusion_signature(census,3)


@pytest.mark.numerical(oracle="Reflection reverses the signed tetrahedral determinant; coincident substituents make it zero.")
def test_stereochemistry_detects_mirror_and_planar_hydrogen_geometry():
    points = {"a":(D(1),D(1),D(1)),"b":(D(1),D(-1),D(-1)),
        "c":(D(-1),D(1),D(-1)),"h":(D(-1),D(-1),D(1))}
    volume = stereocentre_volume(points,("a","b","c","h"))
    assert volume != 0
    mirror = {key:(-xyz[0],xyz[1],xyz[2]) for key,xyz in points.items()}
    assert stereocentre_volume(mirror,("a","b","c","h")) == -volume
    points["h"] = points["a"]
    assert stereocentre_volume(points,("a","b","c","h")) == 0


@pytest.mark.numerical(oracle="A signed unit tetrahedron has determinant -1 in the selected substituent order; reflection reverses it and scaling one edge by .001 drops its magnitude below the declared .01-A3 degeneracy floor.")
def test_minimized_keto_stereocentre_cannot_flip_or_collapse_despite_declared_success():
    names = ("O3", "C2", "C4", "H3")
    original = dict(zip(names, ((D(1),D(0),D(0)),(D(0),D(0),D(1)),(D(0),D(1),D(0)),(D(0),D(0),D(0))), strict=True))
    assert stereocentre_volume(original, names) == -1
    assert keto_stereocentre_preserved(original, original, names, D("0.01"))
    reflected = {name: (-xyz[0], *xyz[1:]) for name, xyz in original.items()}
    assert not keto_stereocentre_preserved(original, reflected, names, D("0.01"))
    collapsed = dict(original, O3=(D(".001"),D(0),D(0)))
    assert not keto_stereocentre_preserved(original, collapsed, names, D("0.01"))
