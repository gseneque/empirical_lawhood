# SPDX-License-Identifier: MPL-2.0
"""Offline shared deployment and byte transport controls, without cloud contact."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shlex
import tarfile
import subprocess
import sys

import pytest
import yaml

from empirical_lawhood.api.accelerated_deployment import prepare_accelerated_deployment
from empirical_lawhood.storage.transfer_files import seal_transfer, verify_transfer
from empirical_lawhood.execution.remote.accelerated_deployment import RunpodDeploymentSelection
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.execution.operational_configuration import OperationalConfiguration


def selection():
    return RunpodDeploymentSelection('el-exposed-control', 'CA', 'CA-MTL-1',
        'docker:example.invalid/nonexecuting@sha256:'+'1'*64, 'exposed-volume', 'exposed-volume-id',
        '/el-persistent', '/el-persistent/input/control', '/el-persistent/output/control',
        'empirical_lawhood-0.3.0-py3-none-any.whl', 'operational.json',
        ('campaign', 'rc-ladder-native-check', '--config', '/el-persistent/input/control/model.json',
            '--output-dir', '/el-persistent/output/control'),
        ResourceBudget(8, 64*2**30, 1, None, 1024*1024, 1024*1024), 40, 100)


def payload(tmp_path, *, enabled=True):
    root = tmp_path/'payload'
    root.mkdir()
    (root/selection().source_wheel).write_bytes(b'EXPOSED NONEXECUTABLE WHEEL PLACEHOLDER')
    (root/'operational.json').write_bytes(OperationalConfiguration(accelerated_compute=enabled).canonical_bytes())
    (root/'model.json').write_bytes(b'EXPOSED INPUT BYTES; NO NATIVE ENTRY')
    return root


@pytest.mark.parametrize('accelerator,expected', (
    (None, 'A100-80GB:1'), ('A100-80GB-SXM', 'A100-80GB-SXM:1'),
    ('H100', 'H100:1'), ('H100-SXM', 'H100-SXM:1'), ('H100-NVL', 'H100-NVL:1'),
    ('H200-SXM', 'H200-SXM:1'), ('B200', 'B200:1'),
    ('RTXPRO6000', 'RTXPRO6000:1'), ('RTXPRO6000-WK', 'RTXPRO6000-WK:1'),
))
def test_shared_task_preparation_preserves_complete_payload_and_never_launches(tmp_path, monkeypatch, accelerator, expected):
    import builtins
    original_import = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.split('.')[0] in ('sky', 'runpod', 'cupy', 'gpu4pyscf', 'openmm'):
            pytest.fail('offline deployment imported an optional provider or native engine')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded)
    root = payload(tmp_path)
    selected = replace(selection(), accelerator=accelerator)
    configuration = tmp_path/'selection.json'
    configuration.write_text(json.dumps(selected.to_document()))
    originals = {p.name: p.read_bytes() for p in root.iterdir()}
    output = tmp_path/'prepared'
    result = prepare_accelerated_deployment(configuration, payload_root=root, output_directory=output)
    assert result['status'] == 'PREPARED_NOT_LAUNCHED' and result['execution_authority'] == 'NONE'
    task = yaml.safe_load((output/'task.yaml').read_text())
    assert task['num_nodes'] == 1 and task['resources']['use_spot'] is False
    assert task['resources']['accelerators'] == expected
    assert task['resources']['image_id'] == selected.image
    assert task['volumes'] == {'/el-persistent': selected.volume_name}
    assert shlex.split(task['run'])[1:] == ['/opt/el/worker/bin/empirical-lawhood', '--operational-config',
        selected.remote_payload+'/operational.json', *selected.arguments]
    assert 'docker run' not in task['setup'] and 'sky launch' not in task['run']
    assert {p.name: p.read_bytes() for p in root.iterdir()} == originals
    verified = verify_transfer(root, output/'payload-manifest.json',
        expected_sha256=result['payload_manifest']['sha256'])
    assert verified['files'] == 3 and verified['native_completion'] == 'NOT_INFERRED'
    with pytest.raises(ValueError, match='fresh'):
        prepare_accelerated_deployment(configuration, payload_root=root, output_directory=output)


def test_false_deployment_selection_refuses_before_writing_or_provisioning(tmp_path):
    root = payload(tmp_path, enabled=False)
    config = tmp_path/'selection.json'
    config.write_text(json.dumps(selection().to_document()))
    with pytest.raises(ValueError, match='accelerated_compute: true'):
        prepare_accelerated_deployment(config, payload_root=root, output_directory=tmp_path/'refused')
    assert not (tmp_path/'refused').exists()


@pytest.mark.parametrize('damage', ('transient-bytes', 'omitted', 'duplicate', 'renamed'))
def test_preparation_authenticates_actual_archive_members_before_publication(tmp_path, monkeypatch, damage):
    """Restoring source files cannot make a damaged transferred archive valid."""
    root = payload(tmp_path)
    original = (root/'model.json').read_bytes()
    add = tarfile.TarFile.add

    def damaged(packed, name, arcname=None, **kwargs):
        if arcname != 'model.json':
            return add(packed, name, arcname=arcname, **kwargs)
        if damage == 'omitted':
            return None
        if damage == 'renamed':
            return add(packed, name, arcname='unselected.json', **kwargs)
        if damage == 'duplicate':
            add(packed, name, arcname=arcname, **kwargs)
            return add(packed, name, arcname=arcname, **kwargs)
        Path(name).write_bytes(b'X'*len(original))
        try:
            return add(packed, name, arcname=arcname, **kwargs)
        finally:
            Path(name).write_bytes(original)

    monkeypatch.setattr(tarfile.TarFile, 'add', damaged)
    output = tmp_path/'refused-archive'
    with pytest.raises(ValueError, match='transfer archive'):
        prepare_accelerated_deployment(selection(), payload_root=root, output_directory=output)
    assert (root/'model.json').read_bytes() == original
    assert (output/'payload.tar').exists()
    assert not (output/'preparation.json').exists()
    assert not (output/'task.yaml').exists()


def test_preparation_refuses_unselected_bytes_after_tar_terminator(tmp_path, monkeypatch):
    root = payload(tmp_path)
    close = tarfile.TarFile.close

    def appended(packed):
        append = not packed.closed and packed.mode == 'w'
        close(packed)
        if append:
            packed.fileobj.write(b'UNSELECTED TRAILING CONTENT')

    monkeypatch.setattr(tarfile.TarFile, 'close', appended)
    output = tmp_path/'refused-tail'
    with pytest.raises(ValueError, match='unselected bytes after'):
        prepare_accelerated_deployment(selection(), payload_root=root, output_directory=output)
    assert not (output/'preparation.json').exists()


def test_archive_obeys_selected_carrier_size_bound(tmp_path):
    from empirical_lawhood.storage.artifact_replication import ReplicaFile
    from empirical_lawhood.storage.bounded_io import BoundedFileIOError
    from empirical_lawhood.storage.transfer_archive import archive_transfer_files
    root = tmp_path/'bounded'
    root.mkdir()
    raw = b'ORIGINAL'
    (root/'input').write_bytes(raw)
    with pytest.raises(BoundedFileIOError, match='byte limit'):
        archive_transfer_files(root, tmp_path/'bounded.tar',
            (ReplicaFile('input', len(raw), sha256(raw).hexdigest()),), maximum_archive_bytes=100)
    assert (tmp_path/'bounded.tar').stat().st_size <= 100


def test_complete_transfer_survives_payload_ignore_rules_and_uses_real_volume_directory(tmp_path):
    root = payload(tmp_path)
    (root/'.gitignore').write_text('*\n')
    (root/'.skyignore').write_text('*\n')
    (root/'same-model.json').hardlink_to(root/'model.json')
    config = tmp_path/'selection.json'
    config.write_text(json.dumps(selection().to_document()))
    output = tmp_path/'prepared'
    result = prepare_accelerated_deployment(config, payload_root=root, output_directory=output)
    archive = Path(result['payload_archive']['path'])
    assert sha256(archive.read_bytes()).hexdigest() == result['payload_archive']['sha256']
    returned = tmp_path/'returned'
    returned.mkdir()
    with tarfile.open(archive) as packed:
        assert all(member.isfile() for member in packed.getmembers())
        packed.extractall(returned, filter='data')
    assert verify_transfer(returned, output/'payload-manifest.json',
        expected_sha256=result['payload_manifest']['sha256'])['files'] == 6
    task = yaml.safe_load((output/'task.yaml').read_text())
    assert all(Path(path).is_file() for path in task['file_mounts'].values())
    assert all(path.startswith('/tmp/') for path in task['file_mounts'])
    assert selection().remote_payload not in task['file_mounts']
    assert 'test ! -L '+selection().remote_payload in task['setup']
    assert '--directory '+selection().remote_payload in task['setup']


@pytest.mark.parametrize('damage', ('bytes', 'missing', 'extra', 'symlink', 'manifest', 'digest'))
def test_transfer_refuses_changed_or_unauthenticated_complete_custody(tmp_path, damage):
    root = payload(tmp_path)
    manifest = tmp_path/'manifest.json'
    result = seal_transfer(root, manifest, maximum_bytes=1024*1024, maximum_files=100)
    digest = result['sha256']
    if damage == 'bytes': (root/'model.json').write_bytes(b'changed')
    elif damage == 'missing': (root/'model.json').unlink()
    elif damage == 'extra': (root/'unselected.json').write_bytes(b'extra')
    elif damage == 'symlink':
        (root/'model.json').unlink()
        (root/'model.json').symlink_to(manifest)
    elif damage == 'manifest': manifest.write_bytes(manifest.read_bytes()+b' ')
    else: digest = '0'*64
    with pytest.raises((ValueError, OSError)):
        verify_transfer(root, manifest, expected_sha256=digest)


@pytest.mark.parametrize('damage', ('deadline', 'gpu-count', 'gpu-bool', 'image-tag', 'nested-output',
    'relative-mount', 'overridden-config', 'unbound-quote', 'float-price', 'invalid-price',
    'unsupported-accelerator', 'invalid-accelerator', 'unknown-field'))
def test_deployment_selection_refuses_ambiguous_resources_or_identity(damage):
    selected = selection()
    with pytest.raises((ValueError, TypeError)):
        if damage == 'deadline': replace(selected, resources=replace(selected.resources, wall_time_seconds=60))
        elif damage == 'gpu-count': replace(selected, resources=replace(selected.resources, gpu_devices=2))
        elif damage == 'gpu-bool': replace(selected, resources=replace(selected.resources, gpu_devices=True))
        elif damage == 'image-tag': replace(selected, image='docker:python:latest')
        elif damage == 'nested-output': replace(selected, remote_output=selected.remote_payload+'/out')
        elif damage == 'relative-mount': replace(selected, volume_mount='workspace')
        elif damage == 'overridden-config': replace(selected, arguments=('--operational-config=/other.json', 'doctor'))
        elif damage == 'unbound-quote': replace(selected, quoted_hourly_usd='1.2345')
        elif damage == 'float-price': replace(selected, quoted_hourly_usd=1.2345, quote_sha256='2'*64)
        elif damage == 'invalid-price': replace(selected, quoted_hourly_usd='one dollar', quote_sha256='2'*64)
        elif damage == 'unsupported-accelerator': replace(selected, accelerator='MI300X')
        elif damage == 'invalid-accelerator': replace(selected, accelerator=True)
        else: RunpodDeploymentSelection.from_document({**selected.to_document(), 'extra': True})


def test_quote_retains_exact_decimal_and_schema_requires_explicit_operands():
    selected = replace(selection(), quoted_hourly_usd='1.2345000', quote_sha256='2'*64)
    document = json.loads(json.dumps(selected.to_document()))
    assert RunpodDeploymentSelection.from_document(document) == selected
    assert document['quoted_hourly_usd'] == '1.2345000'
    example = Path(__file__).resolve().parents[1]/'configs/accelerated-compute/selection.example.json'
    with pytest.raises(ValueError, match='digest-pinned'):
        RunpodDeploymentSelection.from_document(json.loads(example.read_text()))


@pytest.mark.parametrize('bundle', (None, 'bundle/worker-bundle.json'))
def test_explicit_sxm_revision_preserves_legacy_selection_and_refuses_silent_changes(bundle):
    original = replace(selection(), worker_bundle=bundle)
    old_document = json.loads(json.dumps(original.to_document()))
    assert 'accelerator' not in old_document
    assert old_document['version'] == ('1.0.0' if bundle is None else '2.0.0')
    assert json.loads(json.dumps(RunpodDeploymentSelection.from_document(old_document).to_document())) == old_document
    selected = replace(original, accelerator='A100-80GB-SXM')
    document = json.loads(json.dumps(selected.to_document()))
    assert document['version'] == '3.0.0' and document['accelerator'] == 'A100-80GB-SXM'
    assert RunpodDeploymentSelection.from_document(document) == selected
    with pytest.raises(ValueError, match='accelerator selection'):
        RunpodDeploymentSelection.from_document({**old_document, 'accelerator': 'A100-80GB-SXM'})
    with pytest.raises(ValueError, match='accelerator selection'):
        RunpodDeploymentSelection.from_document({**old_document, 'version': '3.0.0'})


@pytest.mark.parametrize('accelerator', ('H100', 'H100-SXM', 'H100-NVL', 'H200-SXM',
    'B200', 'RTXPRO6000', 'RTXPRO6000-WK'))
def test_additional_gpu_targets_require_new_revision_and_preserve_exact_selection(accelerator):
    selected = replace(selection(), accelerator=accelerator, quoted_hourly_usd='2.490000', quote_sha256='2'*64)
    document = json.loads(json.dumps(selected.to_document()))
    assert document['version'] == '4.0.0'
    assert json.loads(json.dumps(RunpodDeploymentSelection.from_document(document).to_document())) == document
    assert document['accelerator'] == accelerator and document['quoted_hourly_usd'] == '2.490000'
    with pytest.raises(ValueError, match='accelerator selection'):
        RunpodDeploymentSelection.from_document({**document, 'version': '3.0.0'})
    with pytest.raises(ValueError, match='accelerator selection'):
        RunpodDeploymentSelection.from_document({**document, 'accelerator': 'A100-80GB'})


def test_public_base_bundle_binds_complete_offline_inputs_and_preserves_original_revision(tmp_path):
    root = payload(tmp_path)
    selected = replace(selection(), worker_bundle='bundle/worker-bundle.json')
    bundle = root/'bundle'
    bundle.mkdir()
    (bundle/'wheels').mkdir()
    for name in ('requirements.txt', 'wheels/uv.whl', 'libgomp.deb', 'uv.lock'):
        (bundle/name).write_bytes(b'EXPOSED NONEXECUTABLE INSTALLATION INPUT')
    specification = {'version':'1.0.0', 'base_image':selected.image,
        'source_image_sha256':'2'*64, 'source_lock_sha256':sha256((bundle/'uv.lock').read_bytes()).hexdigest(),
        'source_lock':'uv.lock',
        'requirements':'requirements.txt', 'wheels':'wheels', 'uv_wheel':'wheels/uv.whl',
        'system_package':'libgomp.deb', 'installed_versions':{'pyscf':'2.14.0', 'openmm':'8.3.1'}}
    (bundle/'worker-bundle.json').write_text(json.dumps(specification))
    config = tmp_path/'deployment.json'
    config.write_text(json.dumps(selected.to_document()))
    output = tmp_path/'prepared'
    result = prepare_accelerated_deployment(config, payload_root=root, output_directory=output)
    assert result['worker_distribution']['private_registry_required'] is False
    assert result['payload_manifest']['files'] == 8
    assert selected.to_document()['version'] == '2.0.0'
    assert 'worker_bundle' not in selection().to_document()
    assert RunpodDeploymentSelection.from_document(json.loads(json.dumps(selection().to_document()))) == selection()
    assert RunpodDeploymentSelection.from_document(json.loads(json.dumps(selected.to_document()))) == selected
    task = yaml.safe_load((output/'task.yaml').read_text())
    setup = task['setup']
    assert setup.index('sha256sum --check') < setup.index('bash ') < setup.index('uv pip install')
    bootstrap = (output/'bootstrap-worker.sh').read_text()
    assert '--offline --no-cache --no-index --require-hashes' in bootstrap
    assert task['resources']['image_id'] == selected.image
    assert task['run'].startswith('exec /opt/el/worker/bin/empirical-lawhood ')
    # Original byte verification covers the wheel inputs, not just their names.
    (bundle/'wheels/uv.whl').write_bytes(b'changed')
    with pytest.raises(ValueError, match='original file census'):
        verify_transfer(root, output/'payload-manifest.json',
            expected_sha256=result['payload_manifest']['sha256'])
    specification['base_image'] = selected.image.replace('1'*64, '4'*64)
    (bundle/'worker-bundle.json').write_text(json.dumps(specification))
    with pytest.raises(ValueError, match='public base image'):
        prepare_accelerated_deployment(config, payload_root=root, output_directory=tmp_path/'refused')
    assert not (tmp_path/'refused').exists()


def test_public_cli_prepares_and_verifies_original_payload_and_reports_refusal(tmp_path):
    from typer.testing import CliRunner
    from empirical_lawhood.cli.app import app
    root = payload(tmp_path)
    config = tmp_path/'deployment.json'
    config.write_text(json.dumps(selection().to_document()))
    output = tmp_path/'prepared'
    runner = CliRunner()
    result = runner.invoke(app, ['deployment', 'prepare', '--selection', str(config),
        '--payload', str(root), '--output-dir', str(output)])
    assert result.exit_code == 0, result.output
    document = json.loads(result.stdout)
    assert document['status'] == 'PREPARED_NOT_LAUNCHED'
    arguments = ['deployment', 'verify-files', '--root', str(root), '--manifest',
        str(output/'payload-manifest.json'), '--sha256', document['payload_manifest']['sha256']]
    verified = runner.invoke(app, arguments)
    assert verified.exit_code == 0 and json.loads(verified.stdout)['files'] == 3
    (root/'model.json').write_bytes(b'changed')
    refused = runner.invoke(app, arguments)
    assert refused.exit_code == 2 and 'complete original file census' in refused.output


@pytest.mark.parametrize('damage', (None, 'changed', 'missing', 'extra', 'linked'))
def test_retained_worker_bundle_is_verified_before_reuse_without_retransfer(tmp_path, damage):
    from empirical_lawhood.execution.remote.accelerated_worker_bundle import RetainedWorkerBundle
    original = tmp_path/'prior-payload'
    bundle = original/'worker-bundle'
    bundle.mkdir(parents=True)
    (bundle/'wheels').mkdir()
    for name in ('uv.lock', 'requirements.txt', 'wheels/uv.whl', 'libgomp.deb'):
        (bundle/name).write_bytes(b'EXPOSED ORIGINAL INSTALLATION BYTES')
    specification = {'version': '1.0.0', 'base_image': selection().image, 'source_image_sha256': '2'*64,
        'source_lock_sha256': sha256((bundle/'uv.lock').read_bytes()).hexdigest(), 'source_lock': 'uv.lock',
        'requirements': 'requirements.txt', 'wheels': 'wheels', 'uv_wheel': 'wheels/uv.whl',
        'system_package': 'libgomp.deb', 'installed_versions': {'pyscf': '2.14.0', 'openmm': '8.3.1'}}
    (bundle/'worker-bundle.json').write_text(json.dumps(specification))
    original_manifest = tmp_path/'prior-manifest.json'
    prior = seal_transfer(original, original_manifest, maximum_bytes=10000, maximum_files=10)
    root = payload(tmp_path)
    (root/'original-manifest.json').write_bytes(original_manifest.read_bytes())
    (root/'original-bundle.json').write_bytes((bundle/'worker-bundle.json').read_bytes())
    reference = {'version': '1.0.0', 'remote_root': str(bundle), 'original_prefix': 'worker-bundle',
        'original_manifest': 'original-manifest.json', 'original_manifest_sha256': prior['sha256'],
        'bundle_specification': 'original-bundle.json'}
    (root/'reuse.json').write_text(json.dumps(reference))
    retained = RetainedWorkerBundle.read(root/'reuse.json', payload_root=root)
    verification_script = tmp_path/'verify-retained.py'
    verification_script.write_text(retained.verification_script())
    if damage == 'changed': (bundle/'wheels/uv.whl').write_bytes(b'CHANGED')
    if damage == 'missing': (bundle/'wheels/uv.whl').unlink()
    if damage == 'extra': (bundle/'extra').write_bytes(b'EXTRA')
    if damage == 'linked':
        (bundle/'uv.lock').unlink()
        (bundle/'uv.lock').symlink_to(original_manifest)
    checked = subprocess.run([sys.executable, str(verification_script)], capture_output=True, text=True)
    assert (checked.returncode == 0) == (damage is None), checked.stderr
    # Prepare for a real mount destination, but never execute the installer.
    reference['remote_root'] = '/el-persistent/old-payload/worker-bundle'
    (root/'reuse.json').write_text(json.dumps(reference))
    selected = replace(selection(), accelerator='H100-SXM', retained_worker_bundle='reuse.json')
    config = tmp_path/'selection.json'
    config.write_text(json.dumps(selected.to_document()))
    assert selected.to_document()['version'] == '5.0.0'
    output = tmp_path/'prepared'
    result = prepare_accelerated_deployment(config, payload_root=root, output_directory=output)
    assert result['worker_distribution']['retained_files'] == 5
    with tarfile.open(output/'payload.tar') as archive:
        assert not any(row.name.endswith('uv.whl') for row in archive)
    setup = yaml.safe_load((output/'task.yaml').read_text())['setup']
    assert setup.index('python3 ') < setup.index('bash ') < setup.rindex('python3 ')
    with pytest.raises(ValueError, match='explicit deployment revision'):
        RunpodDeploymentSelection.from_document({**selected.to_document(), 'version': '4.0.0'})
    (root/'original-bundle.json').write_text('{}')
    with pytest.raises(ValueError, match='original sealed bytes'):
        prepare_accelerated_deployment(config, payload_root=root, output_directory=tmp_path/'refused')
    assert not (tmp_path/'refused').exists()
