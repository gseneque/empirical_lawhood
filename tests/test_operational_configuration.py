# SPDX-License-Identifier: MPL-2.0
"""Public operational choices preserve storage/science and invocation custody."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from empirical_lawhood.api.configuration import ConfigurationError, load_configuration_record
from empirical_lawhood.cli.app import app
from empirical_lawhood.execution.operational_configuration import ArtifactVerificationMode, OperationalConfiguration


ROOT = Path(__file__).resolve().parents[1]


def test_public_configuration_owns_reduced_default_and_explicit_strict(tmp_path):
    assert OperationalConfiguration().artifact_verification is ArtifactVerificationMode.REDUCED
    example = ROOT / 'configs/operational.example.yaml'
    selected = load_configuration_record(example, consumer='operational-configuration')
    assert selected == OperationalConfiguration()
    strict = tmp_path / 'strict.yaml'
    strict.write_text(example.read_text().replace('reduced', 'strict'))
    assert load_configuration_record(strict, consumer='operational-configuration').artifact_verification is ArtifactVerificationMode.STRICT
    strict.write_text(example.read_text().replace('reduced', 'off'))
    with pytest.raises(ConfigurationError):
        load_configuration_record(strict, consumer='operational-configuration')


def test_reconstruction_is_independent_default_off_and_preserves_legacy_bytes(tmp_path):
    from empirical_lawhood.execution.operational_configuration import OperationalConfigurationV1, ScientificReconstructionMode, scientific_reconstruction_enabled, scientific_reconstruction_operation
    assert OperationalConfiguration().scientific_reconstruction is ScientificReconstructionMode.OFF
    assert not scientific_reconstruction_enabled()
    with scientific_reconstruction_operation('full'):
        assert scientific_reconstruction_enabled()
        with scientific_reconstruction_operation():
            assert not scientific_reconstruction_enabled()
        assert scientific_reconstruction_enabled()
    assert not scientific_reconstruction_enabled()
    original = OperationalConfigurationV1(ArtifactVerificationMode.STRICT).canonical_bytes()
    path = tmp_path / 'old.json'
    path.write_bytes(original)
    value = load_configuration_record(path, consumer='operational-configuration')
    assert value.artifact_verification is ArtifactVerificationMode.STRICT
    assert value.scientific_reconstruction is ScientificReconstructionMode.OFF
    assert path.read_bytes() == original


@pytest.mark.parametrize('revision', ('1.0.0', '2.0.0', '3.0.0'))
def test_acceleration_defaults_false_without_rewriting_original_selection(tmp_path, revision):
    from empirical_lawhood.execution.operational_configuration import OperationalConfigurationV1, OperationalConfigurationV2, ScientificReconstructionMode
    owners = {'1.0.0': OperationalConfigurationV1, '2.0.0': OperationalConfigurationV2,
              '3.0.0': OperationalConfiguration}
    kwargs = {'artifact_verification': ArtifactVerificationMode.STRICT}
    if revision != '1.0.0':
        kwargs['scientific_reconstruction'] = ScientificReconstructionMode.FULL
    document = owners[revision](**kwargs).to_document()
    document['value'].pop('accelerated_compute', None)
    original = json.dumps(document).encode()
    path = tmp_path / 'selection.json'
    path.write_bytes(original)
    value = load_configuration_record(path, consumer='operational-configuration')
    assert value.accelerated_compute is False
    assert value.artifact_verification is ArtifactVerificationMode.STRICT
    assert value.scientific_reconstruction is (
        ScientificReconstructionMode.OFF if revision == '1.0.0' else ScientificReconstructionMode.FULL)
    assert path.read_bytes() == original


@pytest.mark.parametrize('value', (0, 1, 'true', 'false', None, [], {}))
def test_acceleration_rejects_non_booleans_through_owner_and_public_parser(tmp_path, value):
    with pytest.raises(TypeError, match='boolean'):
        OperationalConfiguration(accelerated_compute=value)
    document = OperationalConfiguration().to_document()
    document['value']['accelerated_compute'] = value
    path = tmp_path / 'selection.json'
    path.write_text(json.dumps(document))
    with pytest.raises(ConfigurationError):
        load_configuration_record(path, consumer='operational-configuration')


@pytest.mark.parametrize('enabled', (False, True))
def test_cli_records_acceleration_selection_and_restores_invocation(tmp_path, monkeypatch, enabled):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    from empirical_lawhood.execution.operational_configuration import accelerated_compute_enabled
    calls = []
    def compute(_):
        calls.append(accelerated_compute_enabled())
        return {'status': 'SOFTWARE_CONTROL'}
    monkeypatch.setattr(native_quickstart, 'check_native_model', compute)
    config = tmp_path / 'operational.json'
    config.write_bytes(OperationalConfiguration(accelerated_compute=enabled).canonical_bytes())
    output = tmp_path / 'attempt'
    result = CliRunner().invoke(app, ['--operational-config', str(config),
        'campaign', 'rc-ladder-native-check', '--config', str(ROOT /
        'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json'),
        '--output-dir', str(output)])
    assert result.exit_code == 0, result.output
    assert calls == [enabled]
    invocation = json.loads((output / 'invocation.json').read_bytes())
    assert invocation['operational_configuration']['value']['accelerated_compute'] is enabled
    assert not accelerated_compute_enabled()


@pytest.mark.parametrize('selected,override,expected', (('off', None, False), ('full', None, True),
    ('full', 'off', False), ('off', 'full', True)))
def test_cli_explicit_reconstruction_uses_and_records_one_invocation(tmp_path, monkeypatch, selected, override, expected):
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    from empirical_lawhood.execution.operational_configuration import scientific_reconstruction_enabled
    calls = []
    def compute(_):
        calls.append(scientific_reconstruction_enabled())
        return {'status': 'SOFTWARE_CONTROL'}
    monkeypatch.setattr(native_quickstart, 'check_native_model', compute)
    config = tmp_path / 'operational.yaml'
    config.write_text((ROOT / 'configs/operational.example.yaml').read_text().replace(
        "scientific_reconstruction: 'off'", "scientific_reconstruction: '" + selected + "'"))
    arguments = ['--operational-config', str(config)]
    if override is not None:
        arguments += ['--scientific-reconstruction', override]
    output = tmp_path / 'attempt'
    result = CliRunner().invoke(app, [*arguments, 'campaign', 'rc-ladder-native-check',
        '--config', str(ROOT / 'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json'), '--output-dir', str(output)])
    assert result.exit_code == 0, result.output
    assert calls == [expected]
    invocation = json.loads((output / 'invocation.json').read_bytes())
    assert invocation['operational_configuration']['value']['scientific_reconstruction'] == ('full' if expected else 'off')
    assert not scientific_reconstruction_enabled()


@pytest.mark.parametrize('selection,expected', (('default', 'reduced'), ('config', 'strict'),
    ('override', 'reduced'), ('flag', 'strict')))
def test_cli_records_selected_mode_without_changing_scientific_output(tmp_path, monkeypatch, selection, expected):
    from empirical_lawhood.cli import attempts, platform
    from empirical_lawhood.adapters.simulators.rc_ladder_response import native_quickstart
    calls = []
    report = {'verdict': 'UNEVALUABLE', 'independent_units': 1, 'scientific_qualification': 'NOT_ESTABLISHED'}
    def compute(path):
        calls.append(path.read_bytes())
        assert platform.CLI_ARTIFACT_VERIFICATION == expected
        assert attempts._operational_configuration.get().artifact_verification == expected
        return report
    monkeypatch.setattr(native_quickstart, 'check_native_model', compute)
    before = []
    if selection in ('config', 'override'):
        config = tmp_path / 'operational.yaml'
        config.write_text((ROOT / 'configs/operational.example.yaml').read_text().replace('reduced', 'strict'))
        before += ['--operational-config', str(config)]
    if selection in ('override', 'flag'):
        before += ['--artifact-verification', expected]
    model = ROOT / 'programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json'
    destination = tmp_path / 'attempt'
    previous = attempts._operational_configuration.get(), platform.CLI_ARTIFACT_VERIFICATION
    result = CliRunner().invoke(app, [*before, 'campaign', 'rc-ladder-native-check',
        '--config', str(model), '--output-dir', str(destination)])
    assert result.exit_code == 0, result.output
    assert calls == [model.read_bytes()]
    assert json.loads(result.stdout) == report
    invocation = json.loads((destination / 'invocation.json').read_bytes())
    assert invocation['operational_configuration']['value']['artifact_verification'] == expected
    assert invocation['scientific_adjudication'] == 'NOT_PERFORMED'
    assert len(invocation['inputs']) == (2 if selection in ('config', 'override') else 1)
    assert (attempts._operational_configuration.get(), platform.CLI_ARTIFACT_VERIFICATION) == previous
