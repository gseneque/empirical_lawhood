# SPDX-License-Identifier: MPL-2.0
"""Cold controller refusal tests; no policy selection or native acquisition."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as N

import pytest


def launcher():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_battery_refined_programme.py'
    spec = importlib.util.spec_from_file_location('exposed_refined_programme', path)
    module = importlib.util.module_from_spec(spec)
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = previous
    return module


def test_cold_help_and_missing_entry_flag_do_not_construct_services_or_import_native():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_battery_refined_programme.py'
    probe = '''
import importlib.abc,runpy,sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]=='pybamm': raise AssertionError('controller imported native')
sys.meta_path.insert(0,RefuseNative())
sys.path.insert(0,sys.argv[1])
import run_applied_el_broad_programme as broad
broad.SelectedProgramme=lambda *a: (_ for _ in ()).throw(AssertionError('cold path constructed custody'))
path=sys.argv[2]
sys.argv=[path,*sys.argv[3:]]
runpy.run_path(path,run_name='__main__')
'''
    help_result = subprocess.run([sys.executable, '-c', probe, str(path.parent), str(path), '--help'],
                                 capture_output=True, text=True)
    assert help_result.returncode == 0
    assert '--run-selected-refined-programme' in help_result.stdout
    for name in ('working-root', 'logs-root', 'durable-root', 'custody-mount', 'custody-filesystem', 'custody-profile'):
        assert '--' + name in help_result.stdout
    flags = ('project-root', 'source-preflight', 'prior-root', 'prior-report', 'prior-cost', 'numerical-selection',
             'label', 'prior-report-sha256', 'prior-cost-sha256', 'storage-root-id', 'source-id',
             'working-root', 'logs-root', 'durable-root', 'custody-mount', 'custody-filesystem', 'custody-profile')
    refused = subprocess.run([sys.executable, '-c', probe, str(path.parent), str(path),
                             *(value for name in flags for value in ('--' + name, 'unselected'))],
                            capture_output=True, text=True)
    assert refused.returncode == 2
    assert 'native entry requires --run-selected-refined-programme' in refused.stderr


def test_selection_must_be_inside_selected_checkout_and_exact_archived_bytes(tmp_path):
    module = launcher()
    project = tmp_path / 'selected-project'
    project.mkdir()
    selected = project / 'numerical-selection.json'
    raw = b'archive-bound explicit selection fixture'
    selected.write_bytes(raw)
    programme = N(project=project, preflight={'members': [{'path': selected.name, 'bytes': len(raw),
                                                        'sha256': sha256(raw).hexdigest()}]})
    assert module.archived_bytes(programme, selected) == raw
    selected.write_bytes(raw + b' altered')
    with pytest.raises(ValueError, match='complete producing archive'):
        module.archived_bytes(programme, selected)
    outside = tmp_path / 'outside.json'
    outside.write_bytes(raw)
    with pytest.raises(ValueError):
        module.archived_bytes(programme, outside)


@pytest.mark.parametrize('damage', ('report-digest', 'cost-digest', 'in-progress', 'wrong-domain', 'copy-unverified',
                                  'unrelated-custody', 'unrelated-native-count', 'short-cpu', 'short-wall', 'nonfinite-cost'))
def test_controller_refuses_unfinished_or_substituted_actual_diagnostic(tmp_path, damage):
    module = launcher()
    report = {'status': 'SELECTED_COMPONENT_PRECISION_DIAGNOSTIC_COMPLETED',
              'domain': 'battery-dfn-precision-diagnostic', 'custody_members': {'original.json': {'bytes': 31}},
              'native_contacts': 1, 'measured_through_pre_copy': {'cpu_seconds': 3.0, 'wall_seconds': 7.0}}
    cost = {'full_durable_copy_exact': True, 'operational_member_count': 1, 'operational_retained_bytes': 31,
            'native_contacts': 1, 'cpu_seconds': 4.0, 'wall_seconds': 8.0}
    if damage == 'in-progress':
        report['status'] = 'ENTERED'
    elif damage == 'wrong-domain':
        report['domain'] = 'battery-thermal-inquiry'
    elif damage == 'copy-unverified':
        cost['full_durable_copy_exact'] = False
    elif damage == 'unrelated-custody':
        cost['operational_retained_bytes'] = 32
    elif damage == 'unrelated-native-count':
        cost['native_contacts'] = 0
    elif damage == 'short-cpu':
        cost['cpu_seconds'] = 2.0
    elif damage == 'short-wall':
        cost['wall_seconds'] = 6.0
    elif damage == 'nonfinite-cost':
        cost['cpu_seconds'] = float('nan')
    raw_report, raw_cost = json.dumps(report).encode(), json.dumps(cost).encode()
    report_path, cost_path = tmp_path / 'programme-report.json', tmp_path / 'invocation-cost.json'
    report_path.write_bytes(raw_report)
    cost_path.write_bytes(raw_cost)
    args = N(prior_report=report_path, prior_report_sha256=sha256(raw_report).hexdigest(),
             prior_cost=cost_path, prior_cost_sha256=sha256(raw_cost).hexdigest())
    if damage == 'report-digest':
        args.prior_report_sha256 = 'f' * 64
    elif damage == 'cost-digest':
        args.prior_cost_sha256 = 'f' * 64
    with pytest.raises(ValueError):
        module.prior_documents(args)


def test_custody_relocation_refuses_omitted_or_tampered_original_member_before_copy(tmp_path):
    module = launcher()
    prior, selected = tmp_path / 'prior', tmp_path / 'selected'
    prior.mkdir()
    selected.mkdir()
    member = prior / 'retained-receipt.json'
    member.write_bytes(b'original exposed custody fixture')
    expected = module.census(prior)
    member.write_bytes(b'substituted exposed custody fixture')
    programme = N(root=selected)
    with pytest.raises(ValueError, match='prior complete custody'):
        module.retain_prior(programme, N(prior_root=prior), {'custody_members': expected})
    assert not tuple(selected.iterdir())


@pytest.mark.parametrize('damage', ('report-native', 'cost-native', 'cost-members', 'cost-bytes',
                                  'failed-attempt', 'changed-run', 'extra-task'))
def test_prior_census_refuses_inconsistent_actual_invocation_before_marker_read(monkeypatch, damage):
    module = launcher()
    import empirical_lawhood.infrastructure.native_effect_custody as custody
    monkeypatch.setattr(custody.ExternalNativeEffectContactStore, 'read',
                        lambda *args: pytest.fail('inconsistent prior census reached marker access'))
    actual = {key: 'exposed.' + key for key in ('run_id', 'status', 'packet_sha256', 'draft_sha256',
                                              'execution_plan_sha256', 'producing_code_sha256')}
    census = [{'operational_status': 'SUCCEEDED'}]
    report = {'native_contacts': 1, 'custody_members': {'original.json': {'bytes': 31}},
              'waves': {'precision-diagnostic': {'report': dict(actual), 'operational_census': [dict(census[0])]}}}
    cost = {'native_contacts': 1, 'operational_member_count': 1, 'operational_retained_bytes': 31}
    products = {'receipts': {'task.exposed': object()}, 'operational_census': census}
    plan = N(tasks=(N(task_id='task.exposed'),))
    if damage == 'report-native':
        report['native_contacts'] = 0
    elif damage == 'cost-native':
        cost['native_contacts'] = 0
    elif damage == 'cost-members':
        cost['operational_member_count'] = 2
    elif damage == 'cost-bytes':
        cost['operational_retained_bytes'] = 32
    elif damage == 'failed-attempt':
        census[0]['operational_status'] = 'FAILED'
    elif damage == 'changed-run':
        actual['run_id'] = 'run.substituted'
    else:
        plan.tasks = (*plan.tasks, N(task_id='extra.unselected'))
    with pytest.raises(ValueError):
        module.validate_prior_census(report, cost, actual, products, plan, None)


@pytest.mark.parametrize("kind", ("diagnostic-result", "operational-obstruction"))
def test_explicit_history_kind_refuses_the_other_terminal_scope(tmp_path, kind):
    module = launcher()
    report = {"status":"RETAINED_ADVERSE_ATTEMPT" if kind == "diagnostic-result" else "SELECTED_COMPONENT_PRECISION_DIAGNOSTIC_COMPLETED",
              "domain":"battery-dfn-precision-diagnostic", "custody_members": {"old.json":{"bytes":1}},
              "native_contacts":1,"measured_through_pre_copy":{"cpu_seconds":1,"wall_seconds":1}}
    cost = {"full_durable_copy_exact":True,"operational_member_count":1,"operational_retained_bytes":1,
            "native_contacts":1,"cpu_seconds":2,"wall_seconds":2}
    raw_report,raw_cost=json.dumps(report).encode(),json.dumps(cost).encode()
    report_path,cost_path=tmp_path/"report.json",tmp_path/"cost.json"
    report_path.write_bytes(raw_report);cost_path.write_bytes(raw_cost)
    args=N(prior_history_kind=kind,prior_report=report_path,prior_report_sha256=sha256(raw_report).hexdigest(),
           prior_cost=cost_path,prior_cost_sha256=sha256(raw_cost).hexdigest())
    with pytest.raises(ValueError):module.prior_documents(args)


@pytest.mark.parametrize("kind,source", (("operational-obstruction",None),("diagnostic-result","unselected.json")))
def test_history_mode_source_pair_refuses_before_custody_construction(monkeypatch,kind,source):
    module=launcher()
    flags=("project-root","source-preflight","prior-root","prior-report","prior-cost","numerical-selection",
           "label","prior-report-sha256","prior-cost-sha256","storage-root-id","source-id")
    argv=["refined","--run-selected-refined-programme","--prior-history-kind",kind,
          *(value for name in flags for value in ("--"+name,"unselected"))]
    argv.extend(value for name in ("working-root", "logs-root", "durable-root", "custody-mount",
                                  "custody-filesystem", "custody-profile")
                for value in ("--" + name, "unselected"))
    if source:argv.extend(("--obstruction-source",source))
    monkeypatch.setattr(sys,"argv",argv)
    monkeypatch.setattr(module,"SelectedProgramme",lambda *_:pytest.fail("invalid history mode constructed custody"))
    with pytest.raises(SystemExit) as error:module.main()
    assert error.value.code == 2


@pytest.mark.parametrize("damage", ("partial", "overlap"))
def test_explicit_custody_paths_retain_shared_pre_effect_refusals(monkeypatch, tmp_path, damage):
    module = launcher()
    flags=("project-root","source-preflight","prior-root","prior-report","prior-cost","numerical-selection",
           "label","prior-report-sha256","prior-cost-sha256","storage-root-id","source-id")
    argv=["refined","--run-selected-refined-programme",
          *(value for name in flags for value in ("--"+name,"unselected")),
          "--working-root",str(tmp_path/"working")]
    if damage == "overlap":
        argv.extend(("--logs-root",str(tmp_path/"working"/"logs"),"--durable-root",str(tmp_path/"durable"),
                     "--custody-mount",str(tmp_path),"--custody-filesystem","exposed-vfat", "--custody-profile","exposed-profile"))
    def before_effects(args):
        import run_applied_el_broad_programme as broad
        broad.selected_locations(args)
        pytest.fail("invalid explicit custody escaped shared location guards")
    monkeypatch.setattr(sys,"argv",argv)
    monkeypatch.setattr(module,"SelectedProgramme",before_effects)
    if damage == "partial":
        with pytest.raises(SystemExit) as error:
            module.main()
        assert error.value.code == 2
    else:
        with pytest.raises(ValueError, match="must be disjoint"):
            module.main()
    assert not tuple(tmp_path.iterdir())
