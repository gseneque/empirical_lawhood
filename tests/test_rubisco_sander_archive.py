# SPDX-License-Identifier: MPL-2.0
"""Controls for historical failures, original byte custody and replayed restart settings."""

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import SanderArchiveSelection, read_sander_release_archive
from empirical_lawhood.adapters.rubisco.rubisco_response import sander_returns


def write(path, data):
    raw = data if isinstance(data, bytes) else json.dumps(data, sort_keys=True).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return sha256(raw).hexdigest()


@pytest.fixture
def failed_job(tmp_path):
    engine = tmp_path / "engine"
    original = write(engine / "manifest.json", b"original installation")
    binary = write(engine / "bin/sander", b"fixture executable")
    (engine / "bin/sander").chmod(0o755)
    manifest = tmp_path / "installation.json"
    seal = write(manifest, dict(schema="empirical-lawhood/native-installation-manifest", version="1.0.0", platform="linux-x86_64",
        executable="bin/sander", original_installation_manifest_sha256=original,
        files=[dict(path="bin/sander", size_bytes=18, executable=True, sha256=binary),
               dict(path="manifest.json", size_bytes=21, executable=False, sha256=original)]))
    root = tmp_path / "original"
    case, origin = "material-a", "coupled"
    topology, mapping = tmp_path / "model.prmtop", tmp_path / "atom-map.json"
    selected = root / case
    directory = selected / origin / "conditioning"
    start = selected / origin / "start.rst7"
    source = write(start, b"issued start")
    restraint = write(start.with_name("conditioning.RST"), b"selected restraint")
    qm = list(range(121))
    spec = dict(case=case, atom_count=125, labels={"ligand.HO3":4}, topology=str(topology), atom_map=str(mapping),
        parent=dict(case=case, checked_inputs={str(topology): write(topology, b"topology"), str(mapping): write(mapping, b"map")}),
        export_sha256=write(mapping.with_name("export.json"), b"export"), all_water_oxygens_sha256=write(selected/"all_water_oxygens.npy", b"waters"),
        inputs={}, conditioning_files={origin: {"start.rst7":source, "conditioning.RST":restraint}}, QM_native_zero_based=qm)
    material = write(selected/"selection.json", spec)
    mdin = ("&cntrl ntb=1, ifqnt=1, cut=8, ntpr=2, ntx=1, irest=0, imin=1, nmropt=1, maxcyc=4,/\n"
            "&qmmm qm_theory='DFTB3', qmcharge=-2, spin=1, qmshake=0, qm_ewald=1, qm_pme=1, qmcut=8., dftb_maxiter=200, iqmatoms="
            + ",".join(str(i+1) for i in qm) + ",/\n").encode()
    record = dict(stage="condition", seed=53, case=case, origin=origin, steps=4, stride=2, continuation=False,
                  start=str(start), start_sha256=source, topology_sha256=spec["parent"]["checked_inputs"][str(topology)],
                  engine_manifest_sha256=original, material_sha256=material, native_exit=1, exit=1,
                  started_unix=10., ended_unix=11., actual_cpu_s=0.25, peak_RSS_KiB=50, wall_s=1.,
                  files={n:write(directory/n,v) for n,v in {"mdin":mdin, "mdout":b"native entry failed",
                         "conditioning.RST":b"selected restraint", "resources":b"0.2 0.05 50 1.0\n"}.items()})
    ledger = tmp_path / "ledger.json"
    document = dict(native_root=str(root), selection_bindings={case: dict(selection=spec, sha256=material)},
        issued_native_receipts=[dict(record, directory=str(directory.relative_to(root)), receipt_sha256=write(directory/"receipt.json", record))],
        by_stage={"condition":{"calls":1}}, total_native_cpu_s=0.25, total_summed_native_wall_s=1.)
    return SanderArchiveSelection(ledger,write(ledger,document),root,tmp_path,engine,manifest,seal), directory


def test_zero_frame_native_failure_retains_scope_and_cost(failed_job):
    selection, _ = failed_job
    report = read_sander_release_archive(selection)
    assert report["new_native_calls"] == 0 and report["cpu_seconds"] == 0.25
    assert [r["status"] for r in report["jobs"].values()] == ["native failure"]
    with pytest.raises(ValueError, match="storage root"):
        read_sander_release_archive(replace(selection, native_root=selection.native_root.parent))


@pytest.mark.parametrize("raises", [False, True])
def test_source_is_rechecked_after_consumption_including_exceptions(failed_job, monkeypatch, raises):
    selection, directory = failed_job
    reader = sander_returns.read_sander_jobs

    def consume(*args):
        result = reader(*args)
        (directory/"mdout").write_bytes(b"edited after read")
        if raises:
            raise RuntimeError("interrupted numerical observation")
        return result

    monkeypatch.setattr(sander_returns, "read_sander_jobs", consume)
    with pytest.raises(ValueError, match="original source changed"):
        read_sander_release_archive(selection)


def test_unissued_failure_or_additional_native_member_refuses_the_whole_census(failed_job):
    selection, directory = failed_job
    (directory/"unrecorded").write_bytes(b"unknown")
    with pytest.raises(ValueError, match="member census"):
        read_sander_release_archive(selection)
    (directory/"unrecorded").unlink()
    write(directory.parent/"unissued"/"receipt.json", {})
    with pytest.raises(ValueError, match="receipt census"):
        read_sander_release_archive(selection)


def _chain(tmp_path):
    folder, previous = tmp_path/"material"/"coupled"/"segment", tmp_path/"material"/"coupled"/"parent"
    topology = "/source/model.prmtop"
    spec = dict(topology=topology, parent={"checked_inputs":{topology:"t"}}, conditioning_files={"coupled":{}})
    parent = dict(stage="release_mmshake", case="material", origin="coupled", engine_manifest_sha256="e",
                  material_sha256="m", topology_sha256="t", seed=53, stride=2, steps=6, exit=0, ended_unix=4.,
                  files={"final.ncrst":"restart"}, electronic_temperature_K=1000.)
    child = dict(parent, continuation=True, start=str(previous/"final.ncrst"), start_sha256="restart",
                 thermostat_seed=100062, cumulative_steps=12, started_unix=5.)
    jobs = {previous:parent, folder:child}
    settings = {previous:({"ig":"53","dt":"0.0005","ntpr":"2"},{"qm_theory":"DFTB3"}),
                folder:({"ig":"100062","dt":"0.0005","ntpr":"2"},{"qm_theory":"DFTB3"})}
    return folder,child,jobs,settings,spec


@pytest.mark.parametrize(("field","value"), [("engine_manifest_sha256","altered"), ("material_sha256","altered"),
    ("topology_sha256","altered"),("origin","outer"),("case","another"),("stage","release"),("seed",54),
    ("stride",3),("thermostat_seed",53),("cumulative_steps",11),("electronic_temperature_K",0.),("start_sha256","other")])
def test_continuation_authenticates_every_parent_and_numerical_setting(tmp_path, field, value):
    path,job,jobs,settings,spec = _chain(tmp_path)
    assert sander_returns._restart(path,job,jobs,settings,spec,tmp_path,"e","m") == 6
    with pytest.raises(ValueError):
        sander_returns._restart(path,dict(job, **{field:value}),jobs,settings,spec,tmp_path,"e","m")


def test_changed_native_control_refused_even_with_same_receipt_scalars(tmp_path):
    path,job,jobs,settings,spec = _chain(tmp_path)
    settings[path][0]["dt"] = "0.001"
    with pytest.raises(ValueError, match="numerical settings"):
        sander_returns._restart(path,job,jobs,settings,spec,tmp_path,"e","m")


def test_force_diagnostic_can_finish_inside_an_original_failed_wrapper(tmp_path):
    write(tmp_path/"mdout", b"NUMERICAL, ANALYTICAL FORCES (diff) from atom 5\nRMS force error = 0.232E-03")
    write(tmp_path/"resources",b"0.2 0.05 50 1.0\n")
    record = dict(stage="forcecheck",files={},native_exit=0,exit=1,actual_cpu_s=0.25,wall_s=1.,peak_RSS_KiB=50)
    _, diagnostic = sander_returns._completion(tmp_path,record,{"labels":{"ligand.HO3":4}})
    assert record["exit"] == 1 and diagnostic == {"atom_one_based":5,"relative_rms_error":.000232,"force_check_passed":True,"components_numeric_analytic_difference":[]}


def test_truncation_before_first_grid_point_keeps_the_entry_and_issued_failure(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import sander_trajectory
    job = dict(exit=1, start=str(tmp_path/"start.rst7"), steps=40, stride=4, files={"trajectory.nc":"partial"})
    frame = {"precursor":True,"water_intact":True,"maximum_contact_A":2.6,"protons_A":[],"other_proton_partners":[]}
    monkeypatch.setattr(sander_trajectory, "_restart_geometry", lambda *args: frame)
    native = ("nquant = 121 nlink = 7 qmcharge = -2 qmshake = 0 qm_ewald = 1 qm_pme = True DFTB3 method citation "
              "qmqmdx = Analytical nmropt = 0 ibelly = 0, ntr = 0\nNSTEP = 0 TIME(PS) = 0.0 TEMP(K) = 298.15\n"
              "Convergence could not be achieved")
    result = sander_trajectory.read_release(tmp_path,job,native,{},[],[],prefix=None,prior_steps=0)
    assert result["status"] == "truncated" and result["segment_observed_steps"] == 0
    assert result["frames"] == [dict(frame,time_fs=0)] and result["temperature_K"] == []
    assert result["cutoffs_A"]["2.7"]["frames"] == 0


@pytest.fixture
def released_parent(failed_job):
    from scipy.io import netcdf_file
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import SanderContinuation

    selection, directory = failed_job
    ledger = json.loads(selection.ledger.read_bytes())
    record = json.loads((directory / "receipt.json").read_bytes())
    spec = ledger["selection_bindings"][record["case"]]["selection"]
    spec["box_A"] = [40.0, 40.0, 40.0]
    spec_digest = write(directory.parent.parent / "selection.json", spec)
    ledger["selection_bindings"][record["case"]]["sha256"] = spec_digest
    record.update(stage="release", exit=0, native_exit=0, material_sha256=spec_digest)
    before = (directory / "mdin").read_text().split("&qmmm")[1]
    controls = ("&cntrl ntb=1, ifqnt=1, cut=8, ntpr=2, ntx=1, irest=0, imin=0, dt=0.0005, ntc=1, ntf=1, "
                "ioutfm=1, nstlim=4, ntwx=2, ntt=3, gamma_ln=2, tempi=298.15, temp0=298.15, nmropt=0, "
                "ntr=0, ntwf=4, ig=53, /\n&qmmm" + before)
    record["files"]["mdin"] = write(directory / "mdin", controls.encode())
    record["files"]["mdout"] = write(directory / "mdout", b"5.  TIMINGS")
    path = directory / "final.ncrst"
    with netcdf_file(path, "w") as nc:
        nc.Conventions = "AMBERRESTART"
        nc.createDimension("atom", spec["atom_count"])
        nc.createDimension("xyz", 3)
        clock = nc.createVariable("time", "d", ())
        clock.units = "picosecond"
        clock[...] = 0.002
        for name, units in (("coordinates", "angstrom"), ("velocities", "angstrom/picosecond")):
            field = nc.createVariable(name, "d", ("atom", "xyz"))
            field.units = units
            field[:] = 0
        for name, units, values in (("cell_lengths", "angstrom", spec["box_A"]), ("cell_angles", "degree", [90.] * 3)):
            field = nc.createVariable(name, "d", ("xyz",))
            field.units = units
            field[:] = values
    restart = record["files"]["final.ncrst"] = sha256(path.read_bytes()).hexdigest()
    receipt = write(directory / "receipt.json", record)
    name = str(directory.relative_to(selection.native_root))
    ledger["issued_native_receipts"] = [dict(record, directory=name, receipt_sha256=receipt)]
    ledger["by_stage"] = {"release": {"calls": 1}}
    return replace(selection, ledger_sha256=write(selection.ledger, ledger)), SanderContinuation(name, receipt, restart, 6)


def test_continuation_inherits_original_clock_and_physically_validated_restart(released_parent):
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import prepare_sander_continuation
    selection, request = released_parent
    info = prepare_sander_continuation(selection, request)
    assert (info["seed"], info["thermostat_seed"], info["stride"], info["initial_step"],
            info["cumulative_steps"], info["new_native_calls"]) == (53, 100060, 2, 4, 10, 0)


@pytest.mark.parametrize("changes", [{"parent_receipt_sha256": "0" * 64}, {"parent_restart_sha256": "0" * 64},
                                      {"parent_directory": "material-a/coupled/unissued"}, {"steps": 1}])
def test_continuation_refuses_wrong_parent_before_allocating_output(released_parent, tmp_path, changes):
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import run_sander_continuation
    selection, request = released_parent
    output = tmp_path / "fresh"
    with pytest.raises(ValueError):
        run_sander_continuation(selection, replace(request, **changes), output=output, timeout_seconds=1)
    assert not output.exists()


@pytest.mark.parametrize("raises", [False, True])
def test_continuation_rechecks_native_inputs_through_unwinding(released_parent, tmp_path, monkeypatch, raises):
    from empirical_lawhood.adapters.rubisco.rubisco_response import sander_execution
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import run_sander_continuation
    selection, request = released_parent
    def mutate(info, control, material, restart, engine, directory, timeout_seconds):
        restart.write_bytes(b"substituted during the native call")
        if raises:
            raise RuntimeError("interrupted work")
        return dict(status="complete")
    monkeypatch.setattr(sander_execution, "execute_continuation", mutate)
    output = tmp_path / "fresh"
    with pytest.raises(ValueError, match="original source changed"):
        run_sander_continuation(selection, request, output=output, timeout_seconds=1)
    assert json.loads((output / "return.json").read_bytes())["status"] == "failed"


def test_failed_continuation_preserves_zero_return_census(released_parent, tmp_path, monkeypatch):
    from empirical_lawhood.adapters.rubisco.rubisco_response import sander_execution
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import run_sander_continuation
    from empirical_lawhood.execution.local.bounded_process import BoundedProcessResult
    selection, request = released_parent
    monkeypatch.setattr(sander_execution, "run_bounded_command", lambda *a, **k: BoundedProcessResult(1, b"", b"native failure"))
    output = tmp_path / "fresh"
    report = run_sander_continuation(selection, request, output=output, timeout_seconds=3)
    assert report == json.loads((output / "return.json").read_bytes())
    assert (report["status"], report["native_exit"], report["returned_coordinate_frames"], report["expected_coordinate_frames"],
            report["returned_force_frames"], report["expected_force_frames"]) == ("failed", 1, 0, 3, 0, 1)
    with pytest.raises(FileExistsError):
        run_sander_continuation(selection, request, output=output, timeout_seconds=3)


def _precursor_path(seed, states, *, assigned=None, status="complete"):
    from empirical_lawhood.domains.rubisco.rubisco_response.precursor_occupancy import PrecursorReleasePath

    frames = [dict(time_fs=2 * i, maximum_contact_A=2.1 if state else 4.4, nearest_water_A=2.1 if state else 4.4,
                   precursor=True, water_intact=True, protons_A=[1.] * 3, other_proton_partners=[[2, 2.]] * 3)
              for i, state in enumerate(states)]
    return PrecursorReleasePath.from_release(dict(seed=seed, assigned_post_entry_frames=assigned or len(frames) - 1,
                                                  status=status, frame_interval_fs=2., frames=frames))


def test_two_gas_free_origins_and_nested_seeds_bound_only_conditional_occupancy():
    from empirical_lawhood.domains.rubisco.rubisco_response.precursor_occupancy import assess_precursor_origins

    seeds = (11031, 22063)
    coupled = tuple(_precursor_path(seed, [True] * 5) for seed in seeds)
    outer = tuple(_precursor_path(seed, [False, False, True, False, False]) for seed in seeds)
    result = assess_precursor_origins("V1-WT", seeds=seeds, coupled=coupled, outer=outer)
    assert result["observed_mixture_range"] == [0.25, 1.]
    assert result["histories"]["outer"]["passages"][0]["first_entry_fs"] == 4
    assert result["histories"]["outer"]["passages"][0]["sustained_entry_fs"] is None
    assert result["histories"]["coupled"]["first_change_from_initial"]["independent_roots"] == 1
    assert result["independent_assemblies"] == 1 and result["exchange_screen_evaluable"]
    assert not result["exchange_screen_passed"] and result["candidate_model_joint_weight_if_mixed"] is None

    states = [i // 4 % 2 == 0 for i in range(65)]
    coupled = tuple(_precursor_path(seed, states) for seed in seeds)
    outer = tuple(_precursor_path(seed, [not v for v in states]) for seed in seeds)
    mixed = assess_precursor_origins("V1-WT", seeds=seeds, coupled=coupled, outer=outer)
    assert mixed["exchange_screen_passed"] and mixed["candidate_model_joint_weight_if_mixed"] == 0.5
    assert mixed["biological_natural_weight_identified_set"] == result["biological_natural_weight_identified_set"] == [0., 1.]
    assert sum(map(sum, mixed["observed_transitions"]["shell_pairs"])) == 4 * 64


def test_censored_occupancy_uses_each_assignment_and_preserves_failure_prefixes():
    from empirical_lawhood.domains.rubisco.rubisco_response.precursor_occupancy import assess_precursor_origins

    coupled = (_precursor_path(1, [True] * 4, assigned=10, status="native failure"),
               _precursor_path(2, [], assigned=20, status="native failure"))
    outer = (_precursor_path(1, [False], assigned=10, status="truncated"),
             _precursor_path(2, [False], assigned=20, status="truncated"))
    report = assess_precursor_origins("M1-WT", seeds=(1, 2), coupled=coupled, outer=outer)
    assert report["histories"]["coupled"]["conditional_completion_bounds"] == [3 / 30, 1.]
    assert report["histories"]["outer"]["conditional_completion_bounds"] == [0., 1.]
    assert report["histories"]["coupled"]["outcome_census"] == {"native failure": 2}
    assert report["histories"]["coupled"]["prefix_frames"] == 3
    assert not report["exchange_screen_evaluable"]
    assert report["observed_transitions"] is None and report["candidate_model_joint_weight_if_mixed"] is None
    with pytest.raises(ValueError, match="seed roster"):
        assess_precursor_origins("M1-WT", seeds=(1, 2), coupled=coupled, outer=outer[:1])
    with pytest.raises(ValueError, match="original sampling clock"):
        replace(coupled[0], interval_fs=1.)
    with pytest.raises(ValueError, match="assigned grid"):
        replace(coupled[0], status="complete")


def test_uncoupled_time_grids_keep_measured_histories_and_withhold_exchange():
    from empirical_lawhood.domains.rubisco.rubisco_response.precursor_occupancy import assess_precursor_origins

    result = assess_precursor_origins("V1-WT", seeds=(1,), coupled=(_precursor_path(1, [True] * 4),),
                                      outer=(_precursor_path(1, [False] * 5),))
    assert result["histories"]["coupled"]["conditional_completion_bounds"] == [1., 1.]
    assert result["histories"]["outer"]["conditional_completion_bounds"] == [0., 0.]
    assert not result["exchange_screen_evaluable"] and result["observed_mixture_range"] == [0., 1.]


def test_precursor_selection_preserves_exact_jobs_and_refuses_mixed_physics(tmp_path):
    from empirical_lawhood.api.domain_composition.rubisco_response.sander_archive import SanderPrecursorPanel, _assess_panel

    doc = dict(panel_id="material.nominal", material="M1-WT", seeds=[1], coupled_jobs=["coupled/job"], outer_jobs=["outer/job"])
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(doc))
    panel = SanderPrecursorPanel.from_file(path)
    rows = {f"{name}/job": dict(case=panel.material, origin=name, seed=1, stage="release", release_settings_sha256="d" * 64,
                               assigned_post_entry_frames=10, frame_interval_fs=2, status="native failure", frames=[])
            for name in ("coupled", "outer")}
    report = _assess_panel(panel, rows)
    assert report["coupled_jobs"] == ["coupled/job"] and report["outer_jobs"] == ["outer/job"]
    assert not report["exchange_screen_evaluable"]
    with pytest.raises(ValueError, match="reuse an issued job"):
        replace(panel, outer_jobs=panel.coupled_jobs)
    with pytest.raises(ValueError, match="issued material"):
        _assess_panel(replace(panel, seeds=(2,)), rows)
    with pytest.raises(ValueError, match="numerical settings"):
        _assess_panel(panel, {**rows, "outer/job": {**rows["outer/job"], "release_settings_sha256": "a" * 64}})
    with pytest.raises(ValueError, match="issued material"):
        _assess_panel(panel, {**rows, "outer/job": {**rows["outer/job"], "stage": "condition"}})
