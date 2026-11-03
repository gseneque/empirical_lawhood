# SPDX-License-Identifier: MPL-2.0
"""Generated invocation contracts agree with both Click and observed refusals."""

import json
import importlib
import re
from pathlib import Path

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from empirical_lawhood.cli.app import app
from empirical_lawhood.cli.introspection import canonical_click_tree
from empirical_lawhood.cli.metadata import invocation_contracts

ROOT = Path(__file__).resolve().parents[1]


def test_every_leaf_has_exact_output_format_and_error_metadata():
    leaves = {
        fact.command: fact
        for fact in canonical_click_tree(get_command(app))
        if fact.command_kind == "command"
    }
    contracts = invocation_contracts()
    assert set(contracts) == set(leaves)
    for name, fact in leaves.items():
        has_format = any(
            "--format" in parameter.declarations for parameter in fact.parameters
        )
        assert has_format is (
            contracts[name].errors == "api"
            or name in {"workflow list", "workflow show", "config validate", "config prepare"}
        ), name


@pytest.mark.parametrize('command,api_module,entry',(
    ('recursive-development-run','recursive_execution','run_recursive_wave'),
    ('recursive-inquiry-run','recursive_inquiry','run_inquiry_successor'),
))
@pytest.mark.parametrize('workers',(None,2))
def test_recursive_run_cli_forwards_selected_workers(tmp_path, monkeypatch, command, api_module, entry, workers):
    from empirical_lawhood.cli import integrations
    module = importlib.import_module('empirical_lawhood.api.'+api_module)
    plane = object()
    monkeypatch.setattr(integrations,'_storage',lambda: (ROOT,None,plane))
    calls = []
    def selected(**kwargs):
        calls.append(kwargs)
        return {'native_contact':'none','new_native_contact_count':0}
    monkeypatch.setattr(module,entry,selected)
    args = ['campaign',command,'--authoring-dir',str(tmp_path),'--terminal-product-format','references']
    if workers is not None:
        args.extend(('--workers',str(workers)))
    result = CliRunner().invoke(app,args)
    assert result.exit_code == 0, result.output
    assert calls == [{'directory':tmp_path,'project_root':ROOT,'artifact_writer':plane,
        'terminal_product_format':'references','maximum_parallel_tasks':1 if workers is None else workers}]


@pytest.mark.parametrize('command',('recursive-development-run','recursive-inquiry-run'))
@pytest.mark.parametrize('workers',('0','-1','true','1.5'))
def test_recursive_run_cli_rejects_invalid_workers_before_storage(tmp_path, monkeypatch, command, workers):
    from empirical_lawhood.cli import integrations
    def forbidden():
        raise AssertionError('invalid worker selection reached storage')
    monkeypatch.setattr(integrations,'_storage',forbidden)
    result = CliRunner().invoke(app,['campaign',command,'--authoring-dir',str(tmp_path),'--workers',workers])
    assert result.exit_code == 2, result.output
    assert 'workers' in result.output


def test_recursive_worker_options_and_help_remain_static(monkeypatch):
    from empirical_lawhood.infrastructure.execution import LocalExecutionResourceAdmitter
    def forbidden():
        raise AssertionError('static command discovery inspected host capacity')
    monkeypatch.setattr(LocalExecutionResourceAdmitter,'detect_capacity',staticmethod(forbidden))
    facts = canonical_click_tree(get_command(app))
    owners = {fact.command for fact in facts
        if fact.command.startswith('campaign recursive-')
        and any('--workers' in p.declarations for p in fact.parameters)}
    assert owners == {'campaign recursive-development-run','campaign recursive-inquiry-run'}
    for command in owners:
        result = CliRunner().invoke(app,[*command.split(),'--help'])
        assert result.exit_code == 0, result.output
        assert 'workers' in result.output


@pytest.mark.parametrize("options", (
    ("--workers", "4"), ("--run", "run.protected"), ("--yes",), ("--reconcile-only",),
    ("--reveal-authority-id", "authority.protected"), ("--programme-request", "/unused/request.json"),
))
def test_custody_only_recovery_rejects_mixed_execution_options_before_storage(tmp_path, monkeypatch, options):
    from empirical_lawhood.cli import integrations

    def forbidden():
        pytest.fail("invalid custody-only invocation opened storage")
    monkeypatch.setattr(integrations, "_storage", forbidden)
    result = CliRunner().invoke(app, ["campaign", "experiment-recover", "--authoring-dir", str(tmp_path),
        "--custody-only", *options])
    assert result.exit_code == 2, result.output
    assert "--custody-only refuses" in result.output


@pytest.mark.parametrize("option", ("--retry-authority-id", "--source-authority-id"))
def test_recovery_rejects_retired_authority_options_before_storage(tmp_path, monkeypatch, option):
    from empirical_lawhood.cli import integrations

    def forbidden():
        pytest.fail("retired recovery option opened storage")
    monkeypatch.setattr(integrations, "_storage", forbidden)
    result = CliRunner().invoke(app, ["campaign", "experiment-recover", "--authoring-dir", str(tmp_path),
        "--custody-only", option, "authority.retired"])
    assert result.exit_code == 2, result.output
    output = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert "No such option" in output and option in output


def test_custody_only_cli_selects_the_explicit_service_mode(tmp_path, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.cli import integrations

    plane = object()
    monkeypatch.setattr(integrations, "_storage", lambda: (ROOT, None, plane))
    calls = []
    def selected(self, **kwargs):
        assert self.project_root == ROOT and self.artifact_writer is plane
        calls.append(kwargs)
        return {"native_contact": "none", "new_native_contact_count": 0}
    monkeypatch.setattr(ExperimentProgrammeService, "recover", selected)
    result = CliRunner().invoke(app, ["campaign", "experiment-recover", "--authoring-dir", str(tmp_path), "--custody-only"])
    assert result.exit_code == 0, result.output
    assert calls == [{"directory": tmp_path, "maximum_parallel_tasks": None, "custody_only": True}]


@pytest.mark.parametrize(
    ("command", "config", "reason"),
    (
        (
            "dependent-response-input-check",
            "prepared-response/prepared-dependent-refinement-input.json",
            "SOURCE_ROOT_REQUIRED",
        ),
        (
            "finite-response-stage-input-check",
            "finite-response-law/calibration-stage-input.json",
            "SOURCE_ROOT_REQUIRED",
        ),
        (
            "response-composition-input-check",
            "causal-transfer-audit/analysis-input.json",
            "SOURCE_ROOT_REQUIRED",
        ),
    ),
)
def test_conditional_parent_commands_reach_source_refusal_without_project_or_profile(
    tmp_path,
    monkeypatch,
    command,
    config,
    reason,
):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        app, ["campaign", command, "--config", str(ROOT / "programmes/foundations/emergent-structure/workflows" / config)]
    )
    assert result.exit_code == 3, result.output
    assert reason in result.output
    assert "--project-root" not in result.output
    assert list(tmp_path.iterdir()) == []


def test_native_schema_errors_use_their_documented_exit_and_stream(tmp_path):
    config = json.loads(
        (ROOT / "programmes/foundations/emergent-structure/workflows/prepared-response/prepared-canary.json").read_text()
    )
    config["value"]["unknown_field"] = "invalid"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(config))
    result = CliRunner().invoke(
        app, ["campaign", "prepared-response-native-check", "--config", str(path)]
    )
    assert result.exit_code == 3, result.output
    assert result.stdout == ""
    assert "fields differ" in result.stderr
    contract = invocation_contracts()["campaign prepared-response-native-check"]
    assert contract.errors == "refusal-3"


def test_portable_api_errors_use_common_envelope_and_argument_errors_use_click(
    tmp_path,
):
    path = tmp_path / "invalid.json"
    path.write_text('{"schema":"unsupported"}')
    result = CliRunner().invoke(
        app, ["system", "validate", "--spec", str(path), "--format", "json"]
    )
    assert result.exit_code == 2, result.output
    document = json.loads(result.stderr)
    assert document["status"] == "INVALID"
    argument = CliRunner().invoke(app, ["campaign", "prepared-response-native-check"])
    assert argument.exit_code == 2
    assert "Missing option" in argument.output


@pytest.mark.parametrize(
    ("route", "module", "entry", "contacts"),
    (
        ("prepared", "prepared_response", "prepare_native_prefix", 2),
        ("finite", "finite_response_law", "execute_native_phase", 12),
    ),
)
def test_canary_cli_observed_native_contact_and_read_only_effects(
    tmp_path,
    monkeypatch,
    route,
    module,
    entry,
    contacts,
):
    from empirical_lawhood.cli.metadata import COMMAND_METADATA

    native = importlib.import_module(
        f"empirical_lawhood.adapters.simulators.{module}.native_quickstart"
    )
    original = getattr(native, entry)
    calls = []

    def observed(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(native, entry, observed)
    monkeypatch.chdir(tmp_path)
    command = f"{route}-response-native-check"
    bundle = "prepared-response" if route == "prepared" else "finite-response-law"
    config = ROOT / "programmes/foundations/emergent-structure/workflows" / bundle / f"{route}-canary.json"
    result = CliRunner().invoke(app, ["campaign", command, "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    report = json.loads(result.stdout)
    assert report["independent_roots"] == 1
    assert report["nested_numerical_views"] == 2
    assert report["development_only"] is True
    assert report["campaign_issued"] is False
    assert len(calls) == contacts
    assert list(tmp_path.iterdir()) == []
    metadata = next(m for m in COMMAND_METADATA if m.command == f"campaign {command}")
    assert metadata.effects.startswith("read-only. Executes")
    assert metadata.native_software and "native canary" in metadata.native_status

    calls.clear()
    missing = CliRunner().invoke(app, ["campaign", command])
    assert missing.exit_code == 2 and "Missing option" in missing.stderr
    malformed = tmp_path / "invalid.json"
    document = json.loads(config.read_bytes())
    document["value"]["evidence_role"] = "PROSPECTIVE"
    malformed.write_text(json.dumps(document))
    refused = CliRunner().invoke(app, ["campaign", command, "--config", str(malformed)])
    assert refused.exit_code == 3 and refused.stdout == ""
    assert "refused" in refused.stderr
    assert calls == []
    assert list(tmp_path.iterdir()) == [malformed]


def test_native_continuation_cli_prepares_without_execution_option(tmp_path, monkeypatch):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.cli import integrations
    monkeypatch.setattr(integrations, '_storage', lambda: (ROOT, None, object()))
    calls = []
    monkeypatch.setattr(ExperimentProgrammeService, 'prepare_native_continuation',
        lambda self, **kwargs: calls.append(kwargs) or {'execution_authorized': False, 'native_tasks_started': 0})
    instruction = tmp_path/'instruction.txt'
    instruction.write_text('Prepare only; no execution.\n')
    command = ['campaign', 'experiment-prepare-native-continuation', '--authoring-dir', str(tmp_path),
        '--run', 'run.disclosed', '--output-dir', str(tmp_path/'proposal'),
        '--worker-interpreter', '/disclosed/worker/bin/python', '--worker-source-root', '/disclosed/source',
        '--preparation-instruction', str(instruction), '--pure-output-bytes', '268435456']
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 0, result.output
    selected, = calls
    assert selected['preparation_instruction_path'] == instruction
    assert selected['pure_output_bytes'] == 268435456 and selected['run_id'] == 'run.disclosed'
    assert json.loads(result.stdout)['execution_authorized'] is False
    refused = CliRunner().invoke(app, [*command, '--yes'])
    assert refused.exit_code == 2 and len(calls) == 1


@pytest.mark.parametrize('confirmed', (False, True))
def test_native_continuation_cli_requires_separate_execution_selection(tmp_path, monkeypatch, confirmed):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.cli import integrations
    monkeypatch.setattr(integrations, '_storage', lambda: (ROOT, None, object()))
    calls = []
    monkeypatch.setattr(ExperimentProgrammeService, 'continue_native',
        lambda self, **kwargs: calls.append(kwargs) or {'execution_authorized': kwargs['confirmed']})
    instruction, proposal = tmp_path/'execution.txt', tmp_path/'proposal.json'
    instruction.write_text('Separate disclosed execution selection.\n')
    proposal.write_text('{}\n')
    command = ['campaign', 'experiment-continue-native', '--authoring-dir', str(tmp_path),
        '--run', 'run.disclosed', '--proposal', str(proposal), '--execution-instruction', str(instruction), '--workers', '8']
    result = CliRunner().invoke(app, [*command, *(['--yes'] if confirmed else [])])
    assert result.exit_code == 0, result.output
    selected, = calls
    assert selected['proposal_path'] == proposal and selected['execution_instruction_path'] == instruction
    assert selected['maximum_parallel_tasks'] == 8 and selected['confirmed'] is confirmed
    assert json.loads(result.stdout)['execution_authorized'] is confirmed
    missing = CliRunner().invoke(app, command[:-4])
    assert missing.exit_code == 2 and len(calls) == 1


@pytest.mark.parametrize('repair', ('retained-e3', 'development-output', 'development-controller'))
def test_retained_e3_repair_cli_passes_explicit_installation_selection(tmp_path, monkeypatch, repair):
    from empirical_lawhood.api.experiment_programme import ExperimentProgrammeService
    from empirical_lawhood.cli import integrations
    monkeypatch.setattr(integrations, '_storage', lambda: (ROOT, None, object()))
    instruction = tmp_path / 'instruction.txt'
    instruction.write_text('Repair only the failed PURE adoption; retain completed work.\n')
    calls = []
    monkeypatch.setattr(ExperimentProgrammeService, 'recover',
        lambda self, **kwargs: calls.append(kwargs) or {'selected': True})
    selection = ['--repair-retained-e3'] if repair == 'retained-e3' else ['--repair-development-output-bytes', '16777216']
    if repair == 'development-controller':
        selection.append('--repair-development-controller')
    result = CliRunner().invoke(app, ['campaign', 'experiment-recover', '--authoring-dir', str(tmp_path),
        '--run', 'run.disclosed', '--yes', '--workers', '8', *selection,
        '--worker-interpreter', '/disclosed/worker/bin/python', '--worker-source-root', '/disclosed/source',
        '--repair-instruction', str(instruction)])
    assert result.exit_code == 0, result.output
    selected, = calls
    if repair == 'retained-e3':
        assert selected['repair_retained_e3'] is True
    else:
        assert selected['repair_development_output_bytes'] == 16777216
        assert selected.get('repair_development_controller', False) is (repair == 'development-controller')
    assert selected['request'].run_id == 'run.disclosed' and selected['request'].confirmed
    assert selected['maximum_parallel_tasks'] == 8
    assert selected['worker_interpreter'] == Path('/disclosed/worker/bin/python')
    assert selected['worker_source_root'] == Path('/disclosed/source')
    assert selected['repair_instruction_path'] == instruction


@pytest.mark.parametrize('repair', ('retained-e3', 'development-output', 'development-controller'))
@pytest.mark.parametrize('options', [[], ['--yes'], ['--yes', '--worker-interpreter', '/disclosed/python']])
def test_incomplete_retained_repair_selection_refuses_before_storage(tmp_path, monkeypatch, options, repair):
    from empirical_lawhood.cli import integrations
    monkeypatch.setattr(integrations, '_storage', lambda: pytest.fail('invalid repair opened storage'))
    selection = ['--repair-retained-e3'] if repair == 'retained-e3' else ['--repair-development-output-bytes', '16777216']
    if repair == 'development-controller':
        selection.append('--repair-development-controller')
    result = CliRunner().invoke(app, ['campaign', 'experiment-recover', '--authoring-dir', str(tmp_path),
        '--run', 'run.disclosed', *selection, *options])
    assert result.exit_code == 2, result.output
    assert selection[0] + ' requires' in result.output
