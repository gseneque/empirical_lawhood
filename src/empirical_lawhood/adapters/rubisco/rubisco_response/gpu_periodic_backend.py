# SPDX-License-Identifier: MPL-2.0
"""Explicit double-precision GPU backend for the complete periodic operator.

The upstream periodic wrapper remains experimental. This owner restores the
selected charged-background convention without modifying installed packages.
Numerical acceptance is supplied by independent CPU and finite-difference reads.
"""

from hashlib import sha256
from pathlib import Path
from types import MethodType

from empirical_lawhood.execution.compute_backend import ComputeBackendDeclaration
from empirical_lawhood.methods import electrostatics


BACKEND = ComputeBackendDeclaration("pyscf.periodic-direct.openmm-reference",
    "gpu4pyscf.periodic-direct.openmm-cuda-double", 1)
REFERENCE_MM_BACKEND = ComputeBackendDeclaration("pyscf.periodic-direct.openmm-reference",
    "gpu4pyscf.periodic-direct.openmm-reference", 1)
GPU4PYSCF_VERSION = "1.8.1"
PERIODIC_SOURCE_SHA256 = "140aef15b0318b9e6e1da4ca443e8d4eecdb69852761adb076929613195fb266"
MM_SOURCE_SHA256 = "9d2d7764b63294915404fb49b48b6e1f5f8b2a6b42e78fd4bc6cac9b6b24254e"


def bind_charged_background(mean_field):
    """Instance-local correction; preserve upstream SCF and all gradient components."""
    if getattr(mean_field, "_el_charged_background", False):
        raise ValueError("periodic charged background was already bound")
    original = mean_field.energy_ewald

    def energy_ewald(self, dm=None, mm_ewald_pot=None, qm_ewald_pot=None):
        eta, _ = self.mm_mol.get_ewald_params()
        correction = electrostatics.charged_background_energy(qm_charge=self.mol.charge,
            mm_charge=sum(float(q) for q in self.mm_mol.atom_charges()),
            volume_bohr3=self.mm_mol.vol, eta_inverse_bohr=eta)
        return original(dm=dm, mm_ewald_pot=mm_ewald_pot, qm_ewald_pot=qm_ewald_pot) + correction

    mean_field.energy_ewald = MethodType(energy_ewald, mean_field)
    mean_field._el_charged_background = True
    return mean_field


def bind_full_density_potential(mean_field, *, observe):
    """Rebuild each potential from its complete density without accumulated updates.

    GPU4PySCF 1.8.1 RKS/UKS select incremental J/K from the previous potential's
    tags. Rebuilding through the same public method retains the selected direct
    integrals, XC grid and periodic correction. It changes no SCF tolerance.
    """
    if getattr(mean_field, "_el_full_density_potential", False):
        raise ValueError("full-density GPU potential was already bound")
    original = mean_field.get_veff

    def get_veff(self, mol=None, dm=None, dm_last=0, vhf_last=0, hermi=1, **kwargs):
        return original(mol=mol, dm=dm, dm_last=None, vhf_last=None, hermi=hermi, **kwargs)

    mean_field.get_veff = MethodType(get_veff, mean_field)
    mean_field._el_full_density_potential = True
    observe(dict(event="gpu-scf-potential-policy", density="COMPLETE_CURRENT_DENSITY",
        incremental_jk=False, numerical_tolerances_changed=False))
    return mean_field


def available_device_memory(cp, *, required_bytes):
    """Release only unused pool blocks before admitting another cold operator.

    Successive electronic states share a process. A previous complete call's
    idle CuPy cache is reclaimable stock, while live arrays and OpenMM contexts
    still consume the actual observed allocation. Never retry a native call.
    """
    import gc
    free, total = cp.cuda.runtime.memGetInfo()
    before = int(free)
    if required_bytes > free:
        gc.collect()
        cp.cuda.runtime.deviceSynchronize()
        cp.get_default_memory_pool().free_all_blocks()
        free, total = cp.cuda.runtime.memGetInfo()
    return int(free), int(total), before


def preflight_gpu_backend(*, device_memory_bytes, molecular_platform='CUDA'):
    """Observe actual libraries, one selected device and memory before scientific entry."""
    if type(device_memory_bytes) is not int or device_memory_bytes <= 0:
        raise ValueError("GPU execution requires an explicit positive device-memory allocation")
    if molecular_platform not in ('CUDA', 'Reference'):
        raise ValueError('GPU electronic execution requires its explicit CUDA or Reference MM platform')
    from empirical_lawhood.execution.resources.accelerated_compute import observe_cuda_devices
    devices = observe_cuda_devices()
    if len(devices) != 1:
        raise RuntimeError("GPU backend requires exactly one explicitly visible whole CUDA device")
    device = devices[0]
    if int(device.compute_capability.split('.')[0]) < 7:
        raise RuntimeError("selected GPU4PySCF binary does not support this pre-Volta CUDA device")
    try:
        import cupy as cp
        import gpu4pyscf
        from gpu4pyscf.qmmm.pbc import itrf, mm_mole
        import openmm
    except (ImportError, OSError) as error:
        raise RuntimeError("selected GPU backend requires its pinned CuPy, GPU4PySCF and OpenMM environment") from error
    if gpu4pyscf.__version__ != GPU4PYSCF_VERSION:
        raise RuntimeError("GPU periodic wrapper requires the selected GPU4PySCF 1.8.1 source")
    for module, expected in ((itrf, PERIODIC_SOURCE_SHA256), (mm_mole, MM_SOURCE_SHA256)):
        if sha256(Path(module.__file__).read_bytes()).hexdigest() != expected:
            raise RuntimeError("GPU periodic wrapper source differs from its assessed upstream selection")
    if cp.cuda.runtime.getDeviceCount() != 1:
        raise RuntimeError("GPU backend requires exactly one explicitly visible whole CUDA device")
    cp.cuda.Device(0).use()
    properties = cp.cuda.runtime.getDeviceProperties(0)
    if int(properties["major"]) < 7:
        raise RuntimeError("selected GPU4PySCF binary does not support this pre-Volta CUDA device")
    free, total, before = available_device_memory(cp, required_bytes=device_memory_bytes)
    if device_memory_bytes > free:
        raise RuntimeError("selected device-memory allocation exceeds currently available GPU memory")
    platform = openmm.Platform.getPlatformByName(molecular_platform)
    required = {"Precision", "DeviceIndex", "DeterministicForces"}
    if molecular_platform == 'CUDA' and not required.issubset(platform.getPropertyNames()):
        raise RuntimeError("OpenMM CUDA platform lacks the selected double-precision properties")
    name = properties["name"]
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    backend = BACKEND if molecular_platform == 'CUDA' else REFERENCE_MM_BACKEND
    return dict(backend=backend.accelerated_backend, gpu4pyscf=gpu4pyscf.__version__,
        cupy=cp.__version__, openmm=openmm.__version__, device_index=0, device_name=name,
        device_uuid=device.uuid, physical_device_index=device.physical_index,
        compute_capability=f'{properties["major"]}.{properties["minor"]}',
        cuda_driver_version=cp.cuda.runtime.driverGetVersion(),
        cuda_runtime_version=cp.cuda.runtime.runtimeGetVersion(),
        device_total_bytes=int(total), device_free_bytes=int(free),
        device_free_before_idle_pool_release_bytes=before,
        device_allocation_bytes=device_memory_bytes, precision="float64", density_fitting=False,
        openmm_nonbonded_parameter_storage='UPSTREAM_FLOAT32' if molecular_platform == 'CUDA' else 'BINARY64',
        grid_response=True, periodic_source_sha256=PERIODIC_SOURCE_SHA256,
        mm_source_sha256=MM_SOURCE_SHA256)


class GpuPeriodicBackend:
    """One selected device, direct integrals, explicit boundary transfers and returns."""

    def __init__(self, *, device_memory_bytes, observe, molecular_platform='CUDA', host_memory_bytes=None):
        self.observation = preflight_gpu_backend(device_memory_bytes=device_memory_bytes,
            molecular_platform=molecular_platform)
        self.molecular_platform = molecular_platform
        self.host_memory_bytes = host_memory_bytes
        import cupy as cp
        from gpu4pyscf import dft
        from gpu4pyscf.qmmm.pbc import itrf
        self.cp, self.dft, self.electronic = cp, dft, itrf
        self.observe = observe
        self.transfers_to_device = self.transfers_to_host = 0
        self.peak_pool_bytes = 0
        self.minimum_free_bytes = self.observation["device_free_bytes"]
        # This limit owns CuPy pool allocations. OpenMM/driver allocations are
        # outside that pool and are observed separately, not falsely bounded.
        cp.get_default_memory_pool().set_limit(size=device_memory_bytes)
        self.observe(dict(event="compute-backend", accelerated_compute=True,
            **self.observation, memory_limit_scope="CUPY_POOL_ONLY",
            transfer_counter_scope="EXPLICIT_ADAPTER_BOUNDARIES"))

    def synchronize(self):
        self.cp.cuda.runtime.deviceSynchronize()

    def begin(self):
        self.synchronize()
        self.started = self.cp.cuda.Event()
        self.started.record()

    def measurement(self):
        self.synchronize()
        pool = self.cp.get_default_memory_pool()
        free, _ = self.cp.cuda.runtime.memGetInfo()
        self.peak_pool_bytes = max(self.peak_pool_bytes, pool.total_bytes())
        self.minimum_free_bytes = min(self.minimum_free_bytes, int(free))
        return dict(cupy_pool_reserved_bytes=pool.total_bytes(), cupy_pool_used_bytes=pool.used_bytes(),
            observed_peak_pool_bytes=self.peak_pool_bytes, device_free_bytes=int(free),
            observed_minimum_device_free_bytes=self.minimum_free_bytes,
            explicit_host_to_device_bytes=self.transfers_to_device,
            explicit_device_to_host_bytes=self.transfers_to_host)

    def finish(self, *, evaluation, failed):
        self.synchronize()
        ended = self.cp.cuda.Event()
        ended.record()
        ended.synchronize()
        self.observe(dict(event="gpu-evaluation-cost", evaluation=evaluation, failed=failed,
            synchronized_device_interval_ms=float(self.cp.cuda.get_elapsed_time(self.started, ended)),
            interval_scope="ELAPSED_DEVICE_TIMELINE_INCLUDING_HOST_GAPS",
            **self.measurement()))

    def to_host(self, value):
        import numpy as np
        if isinstance(value, self.cp.ndarray):
            self.transfers_to_host += value.nbytes
            result = self.cp.asnumpy(value)
            self.synchronize()
            return result
        return np.asarray(value)

    def density_to_device(self, value):
        if value is None or isinstance(value, self.cp.ndarray):
            return value
        self.transfers_to_device += value.nbytes
        return self.cp.asarray(value, dtype=self.cp.float64, order="C")

    def norm(self, value):
        return float(self.cp.linalg.norm(value))

    def couple(self, base, *args, **kwargs):
        from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_ewald import bind_bounded_ewald
        from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_point_gradient import bind_point_charge_potential
        if getattr(base, "with_df", None) is not None:
            raise ValueError("reference GPU backend refuses undeclared density fitting")
        mean_field = bind_charged_background(self.electronic.add_mm_charges(base, *args, **kwargs))
        mean_field = bind_bounded_ewald(mean_field,
            device_memory_bytes=self.observation["device_allocation_bytes"], observe=self.observe)
        mean_field = bind_point_charge_potential(mean_field, observe=self.observe)
        return bind_full_density_potential(mean_field, observe=self.observe)

    def gradient(self, mean_field):
        from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_ewald import bind_bounded_ewald_gradient
        from empirical_lawhood.adapters.rubisco.rubisco_response.gpu_periodic_point_gradient import bind_point_charge_gradient
        # Upstream QMMM overrides Gradients, not every CPU-style alias.
        derivative = mean_field.Gradients()
        derivative.grid_response = True
        derivative = bind_bounded_ewald_gradient(derivative)
        return bind_point_charge_gradient(derivative, observe=self.observe)

    def openmm_context(self, system, integrator, mm):
        platform = mm.Platform.getPlatformByName(self.molecular_platform)
        properties = ({"Precision": "double", "DeviceIndex": "0", "DeterministicForces": "true"}
            if self.molecular_platform == 'CUDA' else {})
        context = mm.Context(system, integrator, platform, properties)
        if self.molecular_platform == 'CUDA':
            from empirical_lawhood.domains.rubisco.rubisco_response.gpu_openmm_limits import admit_cuda_mm_context
            admit_cuda_mm_context(system, context, mm)
        else:
            from empirical_lawhood.domains.rubisco.rubisco_response.gpu_openmm_limits import admit_reference_mm_context
            admission = admit_reference_mm_context(system, context, mm, host_memory_bytes=self.host_memory_bytes)
            self.observe(dict(event='openmm-pme-admission', platform='Reference', **admission))
        actual = {key: platform.getPropertyValue(context, key) for key in properties}
        if actual != properties:
            raise RuntimeError("OpenMM context changed its requested CUDA platform properties")
        self.observe(dict(event="openmm-platform", platform=context.getPlatform().getName(), properties=actual))
        return context
