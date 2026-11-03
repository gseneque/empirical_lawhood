# SPDX-License-Identifier: MPL-2.0
"""Cold entry and exact closed-nomination intake guards."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


def controller():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_rubisco_insilico.py'
    spec = importlib.util.spec_from_file_location('exposed_rubisco_insilico_programme', path)
    module = importlib.util.module_from_spec(spec)
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = previous
    return module


def test_import_and_help_do_not_construct_custody_or_import_native():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_rubisco_insilico.py'
    probe = '''
import importlib.abc,runpy,sys
class RefuseNative(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in ('openmm','pybamm','pyscf'):
            raise AssertionError('cold controller imported native')
sys.meta_path.insert(0,RefuseNative())
sys.path.insert(0,sys.argv[1])
import run_applied_el_broad_programme as broad
broad.SelectedProgramme=lambda *a: (_ for _ in ()).throw(AssertionError('cold custody entry'))
path=sys.argv[2]
sys.argv=[path,'--help']
runpy.run_path(path,run_name='__main__')
'''
    result = subprocess.run([sys.executable, '-c', probe, str(path.parent), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert '--run-selected-insilico-question' in result.stdout


@pytest.mark.parametrize('damage', (None, 'report-digest', 'cost-digest', 'in-progress',
    'domain', 'missing-prior-science', 'new-native', 'copy-unverified', 'member-count',
    'member-bytes', 'cost-native', 'short-cpu', 'short-wall', 'nonfinite-cpu'))
def test_actual_nomination_intake_refuses_incomplete_or_substituted_history(tmp_path, damage):
    module = controller()
    report = {'status': 'SELECTED_TEST_NOMINATION_PACKET_PREPARED',
        'domain': 'rubisco-nomination-preparation-terminal', 'prior_completed_nomination_operations': 1,
        'new_registered_operations': 0, 'native_contacts': 0,
        'custody_members': {'retained.json': {'bytes': 31, 'sha256': 'a' * 64}},
        'measured_through_pre_copy': {'cpu_seconds': 3, 'wall_seconds': 7}}
    cost = {'native_contacts': 0, 'full_durable_copy_exact': True, 'operational_member_count': 1,
        'operational_retained_bytes': 31, 'cpu_seconds': 4, 'wall_seconds': 8}
    if damage == 'in-progress':
        report['status'] = 'ENTERED'
    elif damage == 'domain':
        report['domain'] = 'unrelated'
    elif damage == 'missing-prior-science':
        report['prior_completed_nomination_operations'] = 0
    elif damage == 'new-native':
        report['native_contacts'] = 1
    elif damage == 'copy-unverified':
        cost['full_durable_copy_exact'] = False
    elif damage == 'member-count':
        cost['operational_member_count'] = 2
    elif damage == 'member-bytes':
        cost['operational_retained_bytes'] = 32
    elif damage == 'cost-native':
        cost['native_contacts'] = 1
    elif damage == 'short-cpu':
        cost['cpu_seconds'] = 2
    elif damage == 'short-wall':
        cost['wall_seconds'] = 6
    elif damage == 'nonfinite-cpu':
        cost['cpu_seconds'] = float('nan')
    report_raw, cost_raw = json.dumps(report).encode(), json.dumps(cost).encode()
    args = SimpleNamespace(prior_report=tmp_path / 'report.json', prior_cost=tmp_path / 'cost.json',
        prior_report_sha256=sha256(report_raw).hexdigest(), prior_cost_sha256=sha256(cost_raw).hexdigest())
    args.prior_report.write_bytes(report_raw)
    args.prior_cost.write_bytes(cost_raw)
    if damage == 'report-digest':
        args.prior_report_sha256 = '0' * 64
    elif damage == 'cost-digest':
        args.prior_cost_sha256 = '0' * 64
    if damage is None:
        assert module.prior_documents(args) == (report, cost)
    else:
        with pytest.raises(ValueError):
            module.prior_documents(args)


def test_source_selection_must_be_exact_member_of_producing_archive(tmp_path):
    module = controller()
    project = tmp_path / 'project'
    project.mkdir()
    selected = project / 'selected-source.json'
    raw = b'authored canonical source fixture'
    selected.write_bytes(raw)
    programme = SimpleNamespace(project=project,
        preflight={'members': [{'path': selected.name, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}]})
    assert module.archived_bytes(programme, selected) == raw
    selected.write_bytes(raw + b' changed')
    with pytest.raises(ValueError, match='producing archive'):
        module.archived_bytes(programme, selected)
