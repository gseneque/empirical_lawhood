# SPDX-License-Identifier: MPL-2.0
"""Pure adapter declarations and worker selection for optional acceleration."""

from dataclasses import dataclass

from empirical_lawhood.science.records.serialization import validate_stable_id


ACCELERATED_COMPUTE_ENV = "EMPIRICAL_LAWHOOD_ACCELERATED_COMPUTE"
GPU_WORKER_ENVIRONMENT_OPTIONAL = (
    'LD_LIBRARY_PATH', 'CUDA_PATH', 'CUPY_CACHE_DIR', 'CUDA_CACHE_PATH',
    'JAX_PLATFORMS', 'JAX_ENABLE_X64', 'JAX_COMPILATION_CACHE_DIR',
    'XLA_PYTHON_CLIENT_PREALLOCATE',
)


@dataclass(frozen=True, slots=True)
class ComputeBackendDeclaration:
    """Code-owned support; constructing this declaration never probes a device."""

    cpu_backend: str
    accelerated_backend: str | None = None
    gpu_devices: int = 0

    def __post_init__(self):
        validate_stable_id(self.cpu_backend)
        if self.accelerated_backend is not None:
            validate_stable_id(self.accelerated_backend)
        if (type(self.gpu_devices) is not int or self.gpu_devices < 0
                or (self.accelerated_backend is None) != (self.gpu_devices == 0)):
            raise ValueError("compute declaration requires its exact accelerated backend and device count")

    def selection(self, accelerated_compute: bool) -> dict:
        if type(accelerated_compute) is not bool:
            raise TypeError("accelerated_compute requires a boolean")
        used = accelerated_compute and self.accelerated_backend is not None
        return {
            "accelerated_compute": accelerated_compute,
            "backend": self.accelerated_backend if used else self.cpu_backend,
            "gpu_devices": self.gpu_devices if used else 0,
            "disposition": ("ACCELERATED" if used else "UNSUPPORTED_OPERATION"
                            if accelerated_compute else "NOT_REQUESTED"),
        }


JAX_TORAX_BACKEND = ComputeBackendDeclaration(
    "jax.torax.cpu.float64", "jax.torax.cuda12.float64", 1,
)


def worker_acceleration_selection(environment) -> bool:
    """Read the frozen worker setting, with historical omission meaning false."""
    value = dict(environment).get(ACCELERATED_COMPUTE_ENV, "false")
    if value not in ("false", "true"):
        raise ValueError("worker accelerated_compute setting requires true or false")
    return value == "true"
