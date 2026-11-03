# SPDX-License-Identifier: MPL-2.0
"""Dry coordinator checks with exposed receiver fixtures; no native entry."""
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from empirical_lawhood.adapters.methods.battery_thermal_inquiry import recursive_translation as drafts
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import BatteryInquirySource
from tests.battery_source_stock_fixtures import stock_distribution, unpack_source_stock
from tests.test_battery_thermal_inquiry_binding import episode as _episode, _products


@pytest.fixture
def episode(monkeypatch):
    return _episode.__wrapped__(monkeypatch)


def launcher():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_applied_el_broad_programme.py'
    spec = importlib.util.spec_from_file_location('exposed_battery_broad_programme', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExposedProgramme:
    def __init__(self, root, records):
        self.root, self.plane = root, None
        self.records, self.drafts, self.products = records, {}, {}
        self.report = {'native_contacts': 0, 'waves': {}}
        self.events = []

    def measured(self, name, call):
        return call()

    def wave(self, name, draft, records, **kwargs):
        self.events.append(('wave', name))
        if name != 'battery-supply':
            assert kwargs['decision'] is not None and kwargs['contribution'] is not None
            assert len(records) == 1  # original supplier is authenticated parent, not fresh SOURCE
        self.drafts[name] = draft
        self.products[name] = _products(draft, self.records[name])
        self.report['native_contacts'] += 1  # mocked entry markers only
        self.report['waves'][name] = {'operational_census': ({'attempt_id': 'exposed.'+name},),
            'receipt_identities': {'exposed.'+name: {'exposed': True}}}
        return self.root / name, self.products[name], {}

    def decision(self, name, directory, result, **kwargs):
        self.events.append(('decision', name, 'ACT' if kwargs['next_draft'] is not None else 'STOP'))
        return self.root / (name + '-decision')

    def contribution(self, name, directory):
        assert self.events[-1] == ('decision', directory.name, 'ACT')
        self.events.append(('export', directory.name))
        parent = drafts.describe_contributions(self.drafts[directory.name], self.products[directory.name])[0]
        return self.root / name, parent


def install_dry_ports(monkeypatch, module, programme):
    import empirical_lawhood.api.recursive_authoring as authoring
    import empirical_lawhood.api.recursive_inquiry as inquiry
    monkeypatch.setattr(module, '_battery_source_intake', lambda p: BatteryInquirySource())
    monkeypatch.setattr(authoring, 'load_authored_wave', lambda *, directory, **kw:
                        (None, programme.drafts[directory.name], None, None))

    def preview(*, supplier_directory, **kwargs):
        draft, products = programme.drafts[supplier_directory.name], programme.products[supplier_directory.name]
        return drafts.next_wave_builder(draft, drafts.describe_contributions(draft, products)[0], products)
    monkeypatch.setattr(inquiry, 'preview_inquiry_successor', preview)


def test_three_actual_product_steps_act_before_export_exact_prior_and_shared_costs(episode, tmp_path, monkeypatch):
    supplier, later, reused, _ = episode
    module = launcher()
    programme = ExposedProgramme(tmp_path, {'battery-supply': supplier, 'battery-use': later, 'battery-reuse': reused})
    install_dry_ports(monkeypatch, module, programme)
    assert module.run_battery(programme) == (later, reused)
    assert programme.events == [('wave', 'battery-supply'), ('decision', 'battery-supply', 'ACT'),
        ('export', 'battery-supply'), ('wave', 'battery-use'), ('decision', 'battery-use', 'ACT'),
        ('export', 'battery-use'), ('wave', 'battery-reuse'), ('decision', 'battery-reuse', 'STOP')]
    assert programme.report['battery_terminal']['remaining_selected_phases'] == ()
    account = programme.report['battery_native_accounting']
    assert account['observed_native_effect_entry_count'] == 3
    assert account['retained_native_operation_attempts'] == account['retained_attempt_receipts'] == 3
    assert account['charging_forecast_provider_attempts'] == 60
    expected_subcalls = sum(trace.backend_solve_calls for trace in (*supplier.traces, *later.assessment.traces, *reused.assessment.traces))
    assert account['charging_solve_step_subcalls'] == expected_subcalls
    assert account['charging_subcall_scope'] == 'MAIN_CHARGING_SUBSOLVES_ONLY'
    assert account['initial_soc_soh_solve_calls'] == 60
    assert account['initializer_scope'] == 'INITIAL_SOC_SOH_SOLVE_CALLS'
    assert not account['initializer_subwindows_are_additive_with_trace_expense']
    assert not account['charging_subwindows_are_additive_with_trace_expense']
    assert not programme.report['battery_scientific_summary']['exact_pointwise_ideal_cccv_established']
    allocations = programme.report['battery_shared_cost_allocations']
    assert [row['value']['native_provider_attempts'] for row in allocations] == [60, 60, 30]
    assert all(row['value']['complete_total_cost_superiority'] == 'UNEVALUABLE' for row in allocations)
    assert programme.report['battery_scientific_summary']['physical_independent_units'] == 0
    assert next(row for row in programme.drafts['battery-reuse'].external_inputs if row.input_id.endswith('.supplier')).scientific_role == 'OUTCOME'


def test_negative_supplier_is_committed_stop_without_export_or_unentered_native_use(tmp_path, monkeypatch):
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry import native, science
    from tests.test_battery_thermal_inquiry import _exposed_trace
    monkeypatch.setattr(native, 'acquire', lambda config: _exposed_trace(config, technical=config.model_view == 'oregan-dfn-refined'))
    supplier = science.supply(BatteryInquirySource())
    module = launcher()
    programme = ExposedProgramme(tmp_path, {'battery-supply': supplier})
    install_dry_ports(monkeypatch, module, programme)
    assert module.run_battery(programme) == ()
    assert programme.events == [('wave', 'battery-supply'), ('decision', 'battery-supply', 'STOP')]
    assert programme.report['battery_terminal']['remaining_selected_phases'] == ('use', 'reuse')
    assert programme.report['battery_terminal']['remaining_phases_status'] == 'NONATTEMPT'
    assert programme.report['battery_native_accounting']['charging_forecast_provider_attempts'] == 36


def test_source_intake_authenticates_protocol_before_native_import_or_distribution_access(tmp_path, monkeypatch):
    module = launcher()
    project = tmp_path / 'project'
    protocol = project / 'programmes/energy/battery-charging/records/battery-thermal-inquiry-selection.json'
    protocol.parent.mkdir(parents=True)
    protocol.write_bytes(b'changed original protocol')
    root = tmp_path / 'custody'; root.mkdir()
    programme = N(root=root, project=project, report={})
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: (_ for _ in ()).throw(AssertionError('unverified source cannot discover provider')))
    with pytest.raises(ValueError, match='original source differs before native entry'):
        module._battery_source_intake(programme)


def test_complete_original_source_intake_copies_exact_installed_bytes_without_native_import(tmp_path, monkeypatch):
    import builtins
    import importlib.metadata
    from hashlib import sha256
    from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import SOURCE_MEMBERS
    stock = unpack_source_stock(tmp_path / 'exposed-stock')
    # Only the metadata port is exposed. Every supplied provider byte is genuine
    # retained stock; this test does not claim an installed scientific engine.
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: stock_distribution(stock)
                        if name == 'pybamm' else pytest.fail('unexpected distribution discovery'))
    module = launcher()
    programme = N(root=tmp_path, project=Path(__file__).resolve().parents[1], report={})
    ordinary_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name == 'pybamm' or name.startswith('pybamm.'):
            raise AssertionError('metadata source intake cannot import native provider')
        return ordinary_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded_import)
    source = module._battery_source_intake(programme, manufacturer_source_path=stock / 'm50-original.pdf')
    register = programme.report['battery_source_intake']
    assert register['source_sha256'] == source.fingerprint()
    assert len(register['members']) == len(SOURCE_MEMBERS) + 2
    assert register['installed_native_source_members'] == len(SOURCE_MEMBERS)
    assert register['native_imports_or_contacts'] == 0
    for row in register['members']:
        raw = (tmp_path / 'battery-source-originals' / row['path']).read_bytes()
        assert len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256']


@pytest.mark.parametrize('change', ('member', 'manufacturer', 'version', 'manufacturer-link'))
def test_exact_source_intake_refuses_changed_stock_or_metadata(tmp_path, monkeypatch, change):
    import importlib.metadata
    stock = unpack_source_stock(tmp_path / 'exposed-stock')
    original = stock / 'm50-original.pdf'
    version = '26.6.2.0'
    if change == 'member':
        (stock / 'pybamm/solvers/solution.py').write_bytes(b'changed exact source')
    elif change == 'manufacturer':
        original.write_bytes(b'changed original manufacturer')
    elif change == 'version':
        version = 'different-source-version'
    else:
        original = stock / 'linked-original.pdf'
        original.symlink_to(stock / 'm50-original.pdf')
    monkeypatch.setattr(importlib.metadata, 'distribution', lambda name: stock_distribution(stock, version=version))
    programme = N(root=tmp_path, project=Path(__file__).resolve().parents[1], report={})
    with pytest.raises(ValueError, match='source.*differs|source is missing or a link|distribution version differs'):
        launcher()._battery_source_intake(programme, manufacturer_source_path=original)
    assert programme.report == {}


def test_exact_source_intake_in_cold_process_uses_only_exposed_metadata(tmp_path):
    script = '''
import importlib.abc
import importlib.metadata
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
class NoNative(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'pybamm':
            raise AssertionError('PURE metadata source intake imported native engine')
sys.meta_path.insert(0, NoNative())
from tests.battery_source_stock_fixtures import stock_distribution, unpack_source_stock
repo, root = map(Path, sys.argv[1:])
stock = unpack_source_stock(root / 'exposed-stock')
discovery = []
def distribution(name):
    assert name == 'pybamm'
    discovery.append(name)
    return stock_distribution(stock)
importlib.metadata.distribution = distribution
spec = importlib.util.spec_from_file_location('pure_battery_launcher', repo / 'scripts/run_applied_el_broad_programme.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
programme = SimpleNamespace(root=root, project=repo, report={})
source = module._battery_source_intake(programme, manufacturer_source_path=stock / 'm50-original.pdf')
assert discovery == ['pybamm'] and 'pybamm' not in sys.modules
assert programme.report['battery_source_intake']['source_sha256'] == source.fingerprint()
assert programme.report['battery_source_intake']['native_imports_or_contacts'] == 0
'''
    subprocess.run([sys.executable, '-c', script, str(Path(__file__).resolve().parents[1]), str(tmp_path)],
                   check=True, cwd=Path(__file__).resolve().parents[1])
