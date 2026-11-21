# SPDX-License-Identifier: MPL-2.0
"""Offline SkyPilot task preparation and bounded, original-byte transport.

SkyPilot owns provisioning. The existing operation owns execution, admission,
receipts and recovery. This module never contacts a provider or runs a task.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import math
from pathlib import Path, PurePosixPath
import re
import shlex
import stat

from empirical_lawhood.storage.artifact_replication import _durable_bytes

from empirical_lawhood.storage import transfer_files
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.serialization import validate_sha256, validate_stable_id


from empirical_lawhood.execution.remote.accelerated_controller import SKYPILOT_VERSION, SKYPILOT_COMMIT, RUNPOD_ACCELERATOR_MEMORY_GB
from empirical_lawhood.execution.remote.accelerated_worker_bundle import WorkerBundle, RetainedWorkerBundle, render_worker_bootstrap
from empirical_lawhood.execution.remote.worker_profiles import JAX_TORAX_WORKER, hosted_worker_profile


_A100_ACCELERATORS = ('A100-80GB', 'A100-80GB-SXM')








@dataclass(frozen=True, slots=True)
class RunpodDeploymentSelection:
    """Editable operational selections, with no execution or spending authority."""

    deployment_id: str
    region: str
    zone: str
    image: str
    volume_name: str
    volume_id: str
    volume_mount: str
    remote_payload: str
    remote_output: str
    source_wheel: str
    operational_config: str
    arguments: tuple[str, ...]
    resources: ResourceBudget
    container_disk_gb: int
    maximum_files: int
    quoted_hourly_usd: str | None = None
    quote_sha256: str | None = None
    worker_bundle: str | None = None
    accelerator: str | None = None
    retained_worker_bundle: str | None = None
    numerical_threads: int | None = None
    sizing_plan_sha256: str | None = None
    numerical_backend: str | None = None

    def __post_init__(self):
        validate_stable_id(self.deployment_id)
        derived = (self.numerical_threads is not None, self.sizing_plan_sha256 is not None,
                   self.numerical_backend is not None)
        if any(derived) and not all(derived):
            raise ValueError('automatic deployment requires its plan digest, backend and frozen numerical threads together')
        if self.numerical_threads is not None:
            if (type(self.numerical_threads) is not int or self.numerical_threads < 1
                    or self.numerical_threads > self.resources.cpu_cores or self.accelerator is None):
                raise ValueError('automatic deployment preserves explicit numerical threads within its CPU allocation')
            validate_sha256(self.sizing_plan_sha256, field_name='deployment sizing plan')
            validate_stable_id(self.numerical_backend, field_name='deployment numerical backend')
        if self.accelerator is not None and (
                type(self.accelerator) is not str
                or self.accelerator not in RUNPOD_ACCELERATOR_MEMORY_GB):
            raise ValueError('deployment requires a supported explicit CUDA accelerator selection')
        for value in (self.region, self.zone, self.volume_name, self.volume_id):
            if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_-]+', value) is None:
                raise ValueError('deployment requires explicit region, zone and persistent-volume selections')
        if (type(self.image) is not str or re.fullmatch(
                r'docker:[A-Za-z0-9_./:-]+@sha256:[0-9a-f]{64}', self.image) is None):
            raise ValueError('deployment requires one digest-pinned upstream container image')
        paths = [PurePosixPath(transfer_files.normalized_absolute_path(v)) for v in (self.volume_mount, self.remote_payload, self.remote_output)]
        mount, payload, output = paths
        if (not payload.is_relative_to(mount) or payload == mount
                or not output.is_relative_to(mount) or output == mount
                or payload.is_relative_to(output) or output.is_relative_to(payload)
                or any(p.is_relative_to(mount / '.el-deployment') for p in (payload, output))):
            raise ValueError('payload and output must be disjoint children of the selected persistent mount')
        transfer_files.portable_relative_path(self.source_wheel)
        transfer_files.portable_relative_path(self.operational_config)
        if self.worker_bundle is not None:
            transfer_files.portable_relative_path(self.worker_bundle)
        if self.retained_worker_bundle is not None:
            transfer_files.portable_relative_path(self.retained_worker_bundle)
            if self.worker_bundle is not None:
                raise ValueError('select either a transferred or retained worker bundle')
            if self.accelerator is None:
                raise ValueError('retained bundle requires its explicit accelerator selection')
        if not PurePosixPath(self.source_wheel).name.startswith('empirical_lawhood-') or not self.source_wheel.endswith('.whl'):
            raise ValueError('deployment source must be the selected empirical-lawhood wheel')
        if (type(self.arguments) is not tuple or not self.arguments
                or any(type(v) is not str or not v or '\x00' in v for v in self.arguments)
                or any(v.split('=', 1)[0] == '--operational-config' for v in self.arguments)):
            raise ValueError('deployment requires one existing CLI operation and its fixed operational selection')
        if type(self.resources) is not ResourceBudget:
            raise TypeError('deployment uses the shared resource budget')
        if (type(self.resources.gpu_devices) is not int or self.resources.gpu_devices != 1 or self.resources.wall_time_seconds is not None
                or any(type(v) is not int or v <= 0 for v in (
                    self.resources.cpu_cores, self.resources.memory_bytes, self.resources.source_scan_bytes,
                    self.resources.output_bytes, self.container_disk_gb, self.maximum_files))):
            raise ValueError('deployment requires one GPU, explicit host/storage bounds and no experiment deadline')
        if (self.quoted_hourly_usd is None) != (self.quote_sha256 is None):
            raise ValueError('quote amount and original quote digest must be selected together')
        if self.quoted_hourly_usd is not None:
            if type(self.quoted_hourly_usd) is not str:
                raise TypeError('quoted spend retains its exact Decimal string')
            try:
                price = Decimal(self.quoted_hourly_usd)
            except InvalidOperation as error:
                raise ValueError('quoted hourly spend requires a Decimal string') from error
            if not price.is_finite() or price <= 0:
                raise ValueError('quoted hourly spend must be positive and finite')
            validate_sha256(self.quote_sha256, field_name='quote digest')

    @classmethod
    def from_document(cls, document):
        if type(document) is not dict or document.get('version') not in ('1.0.0', '2.0.0', '3.0.0', '4.0.0', '5.0.0', '6.0.0'):
            raise ValueError('unsupported accelerated deployment selection revision')
        if (('retained_worker_bundle' in document and document['version'] not in ('5.0.0', '6.0.0'))
                or (document['version'] == '5.0.0' and (not document.get('retained_worker_bundle')
                    or document.get('worker_bundle') is not None or document.get('accelerator') is None))):
            raise ValueError('retained bundle requires its explicit deployment revision and accelerator')
        if ((document['version'] == '1.0.0' and 'worker_bundle' in document)
                or (document['version'] == '2.0.0' and not document.get('worker_bundle'))):
            raise ValueError('worker bundle selection requires its explicit deployment revision')
        if ((document['version'] in ('1.0.0', '2.0.0') and 'accelerator' in document)
                or (document['version'] in ('3.0.0', '4.0.0') and document.get('accelerator') is None)):
            raise ValueError('accelerator selection requires its explicit deployment revision')
        if ((document['version'] == '3.0.0' and document['accelerator'] not in _A100_ACCELERATORS)
                or (document['version'] == '4.0.0' and document['accelerator'] in _A100_ACCELERATORS)):
            raise ValueError('accelerator selection does not match its deployment revision')
        if document['version'] == '6.0.0':
            if (document.get('numerical_threads') is None or document.get('sizing_plan_sha256') is None
                    or document.get('numerical_backend') is None or document.get('accelerator') is None):
                raise ValueError('automatic deployment revision requires explicit plan, threads, backend and accelerator')
        elif any(name in document for name in ('numerical_threads', 'sizing_plan_sha256', 'numerical_backend')):
            raise ValueError('automatic deployment fields require revision 6.0.0')
        values = dict(document)
        del values['version']
        if type(values.get('arguments')) is not list or type(values.get('resources')) is not dict:
            raise ValueError('deployment requires explicit command arguments and shared resources')
        values['arguments'] = tuple(values['arguments'])
        values['resources'] = ResourceBudget(**values['resources'])
        return cls(**values)

    def to_document(self):
        from dataclasses import asdict
        values = asdict(self)
        version = ('3.0.0' if self.accelerator in _A100_ACCELERATORS else '4.0.0') if self.accelerator is not None else (
            '2.0.0' if self.worker_bundle is not None else '1.0.0')
        if self.retained_worker_bundle is not None:
            version = '5.0.0'
        else:
            del values['retained_worker_bundle']
        if self.numerical_threads is not None:
            version = '6.0.0'
        else:
            del values['numerical_threads']
            del values['sizing_plan_sha256']
            del values['numerical_backend']
        if self.worker_bundle is None:
            del values['worker_bundle']
        if self.accelerator is None:
            del values['accelerator']
        return {'version': version, **values}

    @classmethod
    def for_execution_plan(cls, plan, *, payload_root, numerical_threads, backend,
                           resource_spec=None, cpu_cores=None, memory_bytes=None,
                           container_disk_gb=None, **placement):
        """Derive host/transfer reservations from an unchanged compiled plan.

        This is operational sizing, not a new scientific definition or an
        authorization to launch. The conservative CPU/RAM envelope supports any
        ready set up to the plan's declared concurrency (all tasks if unbounded).
        GPU tasks share the existing one-device scheduler. Missing memory or
        output bounds are refused, never guessed. Explicit host overrides may
        only enlarge this operational envelope; they do not change task budgets.
        """
        from empirical_lawhood.execution.resources.remote_sizing import RemotePlacementUnsupported, size_runpod_resources
        from empirical_lawhood.execution.compute_backend import ComputeBackendDeclaration
        if (type(backend) is not ComputeBackendDeclaration
                or backend.accelerated_backend is None or backend.gpu_devices != 1):
            raise RemotePlacementUnsupported('HOSTED_UNSUPPORTED_COMPUTE_BACKEND',
                'select the existing code-owned single-GPU numerical backend declaration')
        root = transfer_files.ordinary_root(payload_root)
        sizes = []
        for path in root.rglob('*'):
            info = path.lstat()
            if path.is_symlink() or path.resolve(strict=True) != path:
                raise ValueError('deployment sizing refuses linked or redirected payload members')
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('deployment sizing requires regular payload members')
            transfer_files.portable_relative_path(path.relative_to(root).as_posix())
            sizes.append(info.st_size)
        if not sizes:
            raise ValueError('deployment sizing requires a nonempty selected payload')
        sized = size_runpod_resources(plan, payload_bytes=sum(sizes),
            resource_spec=resource_spec, cpu_cores=cpu_cores, memory_bytes=memory_bytes)
        if (type(numerical_threads) is not int or numerical_threads < 1
                or numerical_threads > min(task.capability.requested_resources.cpu_cores for task in plan.tasks)):
            raise ValueError('frozen numerical threads must fit every selected task CPU allocation')
        # Two payload copies cover transient transfer plus extraction; a named
        # 10-GiB installation reserve is operational policy, not a numerical
        # requirement. Large native installations retain an explicit override.
        minimum_disk = max(10, math.ceil(2 * sum(sizes) / 2**30) + 10)
        disk = minimum_disk if container_disk_gb is None else container_disk_gb
        if type(disk) is not int or disk < minimum_disk:
            raise ValueError('container disk override is smaller than transfer and installation reserve')
        if any(name in placement for name in ('resources', 'maximum_files',
                'sizing_plan_sha256', 'numerical_threads', 'numerical_backend')):
            raise ValueError('derived deployment fields cannot be supplied twice')
        return cls(resources=sized, maximum_files=len(sizes), container_disk_gb=disk,
            numerical_threads=numerical_threads, sizing_plan_sha256=plan.fingerprint(),
            numerical_backend=backend.accelerated_backend, **placement)












def prepare_runpod_task(selection, *, payload_root, output_directory):
    """Freeze local selections and render a single upstream task, with no launch."""
    import yaml
    if type(selection) is not RunpodDeploymentSelection:
        raise TypeError('deployment preparation requires its typed selection')
    selection.__post_init__()
    worker_profile = hosted_worker_profile(selection.numerical_backend)
    payload_root = transfer_files.ordinary_root(payload_root)
    output = Path(output_directory)
    if (not output.is_absolute() or output.resolve(strict=False) != output or output.exists()
            or not output.parent.is_dir() or output.is_relative_to(payload_root)
            or payload_root.is_relative_to(output)):
        raise ValueError('deployment preparation requires a fresh separate absolute output directory')
    for name in (selection.source_wheel, selection.operational_config):
        if not (payload_root/name).is_file():
            raise ValueError('selected source wheel or operational input is absent')
    bundle = None
    retained = None
    if selection.worker_bundle is not None:
        bundle = WorkerBundle.read(payload_root/selection.worker_bundle)
        if bundle.base_image != selection.image:
            raise ValueError('worker bundle differs from the selected public base image')
        bundle.validate_files((payload_root/selection.worker_bundle).parent)
    elif selection.retained_worker_bundle is not None:
        retained = RetainedWorkerBundle.read(payload_root/selection.retained_worker_bundle, payload_root=payload_root)
        bundle = retained.bundle
        remote_root = PurePosixPath(retained.remote_root)
        mount = PurePosixPath(selection.volume_mount)
        if (not remote_root.is_relative_to(mount) or remote_root == mount
                or any(remote_root.is_relative_to(path) or PurePosixPath(path).is_relative_to(remote_root)
                    for path in (selection.remote_payload, selection.remote_output))):
            raise ValueError('retained worker bundle requires a separate child of the selected persistent volume')
        if bundle.base_image != selection.image:
            raise ValueError('retained worker bundle differs from the selected public base image')
    if bundle is not None:
        bundle.require_capabilities(selection.numerical_backend)
    elif worker_profile is JAX_TORAX_WORKER:
        raise ValueError('JAX_TORAX_WORKER_BUNDLE_REQUIRED: select an authenticated transferred or retained offline bundle')
    output.mkdir()
    manifest = transfer_files.prepare_transfer(payload_root, output,
        maximum_bytes=selection.resources.source_scan_bytes, maximum_files=selection.maximum_files)
    archive = Path(manifest['archive'])
    archive_size, archive_digest = manifest['archive_bytes'], manifest['archive_sha256']
    _durable_bytes(output/'selection.json', transfer_files.encode_document(selection.to_document()))
    control = str(PurePosixPath(selection.volume_mount) / '.el-deployment' / selection.deployment_id)
    staging = '/tmp/el-deployment-transfer/'+selection.deployment_id
    cli = '/opt/el/worker/bin/empirical-lawhood'
    remote_config = selection.remote_payload + '/' + selection.operational_config
    bootstrap = ()
    control_files = ['payload-manifest.json', 'SHA256SUMS', 'selection.json']
    if bundle is not None:
        remote_bundle = (retained.remote_root if retained is not None else
            str(PurePosixPath(selection.remote_payload, selection.worker_bundle).parent))
        raw = render_worker_bootstrap(bundle, remote_root=remote_bundle, numerical_backend=selection.numerical_backend).encode()
        _durable_bytes(output/'bootstrap-worker.sh', raw)
        control_files.append('bootstrap-worker.sh')
        bootstrap = (
            'printf %s '+shlex.quote(sha256(raw).hexdigest()+'  '+control+'/bootstrap-worker.sh\n')+' | sha256sum --check',
            shlex.join(('bash', control+'/bootstrap-worker.sh')),
        )
        if retained is not None:
            raw_check = retained.verification_script().encode()
            _durable_bytes(output/'verify-retained-worker.py', raw_check)
            control_files.append('verify-retained-worker.py')
            check = (
                'printf %s '+shlex.quote(sha256(raw_check).hexdigest()+'  '+control+'/verify-retained-worker.py\n')+' | sha256sum --check',
                shlex.join(('python3', control+'/verify-retained-worker.py')),
            )
            bootstrap = (*check, *bootstrap, *check)
    setup = '\n'.join((
        'set -eu',
        # The volume has an independent upstream lifecycle. A root-directory
        # substitute is refused; actual volume identity is checked at launch.
        'test "$(stat -c %d '+shlex.quote(selection.volume_mount)+')" != "$(stat -c %d /)"',
        'test ! -L '+shlex.quote(selection.remote_payload),
        'mkdir -p '+shlex.quote(control),
        shlex.join(('cp', *[staging+'/'+name for name in control_files], control+'/')),
        'printf %s '+shlex.quote(archive_digest+'  '+staging+'/payload.tar\n')+' | sha256sum --check',
        'if test ! -e '+shlex.quote(selection.remote_payload)+'; then',
        '  mkdir -p '+shlex.quote(selection.remote_payload),
        '  '+shlex.join(('tar', '--extract', '--file', staging+'/payload.tar', '--directory',
            selection.remote_payload, '--no-same-owner')),
        'fi',
        'cd '+shlex.quote(selection.remote_payload),
        'sha256sum --check '+shlex.quote(control+'/SHA256SUMS'),
        *bootstrap,
        shlex.join(('/opt/el/tools/bin/uv', 'pip', 'install', '--no-deps', '--python',
            '/opt/el/worker/bin/python', selection.remote_payload+'/'+selection.source_wheel)),
        shlex.join((cli, 'deployment', 'verify-files', '--root', selection.remote_payload,
            '--manifest', control+'/payload-manifest.json', '--sha256', manifest['sha256'])),
    ))
    task = {'name': selection.deployment_id, 'num_nodes': 1,
        'resources': {'infra': f'runpod/{selection.region}/{selection.zone}',
            'accelerators': (selection.accelerator or 'A100-80GB')+':1',
            'cpus': str(selection.resources.cpu_cores)+'+',
            'memory': str(math.ceil(selection.resources.memory_bytes/2**30))+'+',
            'disk_size': selection.container_disk_gb, 'use_spot': False, 'image_id': selection.image},
        'volumes': {selection.volume_mount: selection.volume_name},
        'file_mounts': {staging+'/payload.tar': str(archive),
            **{staging+'/'+name: str(output/name) for name in control_files}},
        'envs': {'CUDA_VISIBLE_DEVICES': '0', 'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
            'EL_DEPLOYMENT_PAYLOAD_SHA256': manifest['sha256'],
            'CUPY_CACHE_DIR': selection.volume_mount+'/.el-cupy-cache/'+selection.deployment_id,
            'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': str(selection.resources.cpu_cores),
            'OPENMM_CPU_THREADS': str(selection.resources.cpu_cores),
            'OPENBLAS_NUM_THREADS': str(selection.resources.cpu_cores),
            'MKL_NUM_THREADS': str(selection.resources.cpu_cores), 'NUMEXPR_NUM_THREADS': '1'},
        'setup': setup,
        'run': 'exec '+shlex.join((cli, '--operational-config', remote_config, *selection.arguments))}
    if selection.numerical_threads is not None:
        from empirical_lawhood.execution.local.worker_bootstrap import NUMERICAL_THREAD_ENV_VARS
        # Placement is not a numerical selection. New derived deployments bind
        # the original per-worker setting even when the host has many cores.
        task['envs'].update({name: str(selection.numerical_threads)
            for name in (*NUMERICAL_THREAD_ENV_VARS, 'OPENMM_CPU_THREADS')})
    task['envs'].update(dict(worker_profile.environment))
    if worker_profile is JAX_TORAX_WORKER:
        task['envs'].pop('CUPY_CACHE_DIR', None)
        task['envs'].pop('OPENMM_CPU_THREADS', None)
        task['envs']['JAX_COMPILATION_CACHE_DIR'] = selection.volume_mount+'/.el-jax-cache/'+selection.deployment_id
    _durable_bytes(output/'task.yaml', yaml.safe_dump(task, sort_keys=False).encode())
    result = {'status': 'PREPARED_NOT_LAUNCHED', 'task': str(output/'task.yaml'),
        'payload_manifest': manifest, 'controller_version': SKYPILOT_VERSION,
        'payload_archive': {'path': str(archive), 'sha256': archive_digest, 'bytes': archive_size},
        'controller_commit': SKYPILOT_COMMIT, 'volume_id': selection.volume_id,
        'quote_status': 'UNSELECTED' if selection.quote_sha256 is None else 'SELECTED_NOT_AUTHORIZED',
        'remaining_entry_requirements': ['actual-access-and-spend', 'quoted-current-offer', 'image-digest',
            'persistent-volume-identity', 'actual-host-and-device-admission', 'selected-operation-authority'],
        'execution_authority': 'NONE'}
    if selection.sizing_plan_sha256 is not None:
        result['resource_derivation'] = {
            'execution_plan_sha256': selection.sizing_plan_sha256,
            'numerical_threads': selection.numerical_threads,
            'numerical_backend': selection.numerical_backend,
            'task_scientific_settings': 'UNCHANGED',
            'host_capacity': 'REQUIRES_ACTUAL_ADMISSION',
            'container_disk_policy': 'TWO_PAYLOAD_COPIES_PLUS_10_GIB_INSTALLATION_RESERVE',
        }
    if bundle is not None:
        result['worker_distribution'] = {'profile': worker_profile.profile_id, 'kind': ('PUBLIC_BASE_AND_OFFLINE_WHEELS' if retained is None
                else 'PUBLIC_BASE_AND_VERIFIED_RETAINED_WHEELS'),
            'base_image': bundle.base_image, 'source_image_sha256': bundle.source_image_sha256,
            'source_lock_sha256': bundle.source_lock_sha256,
            'worker_bundle': selection.worker_bundle, 'private_registry_required': False}
        if retained is not None:
            result['worker_distribution'].update(retained_worker_bundle=selection.retained_worker_bundle,
                original_manifest_sha256=retained.original_manifest_sha256,
                retained_files=len(retained.files), retained_bytes=sum(row.size_bytes for row in retained.files))
    _durable_bytes(output/'preparation.json', transfer_files.encode_document(result))
    return result
