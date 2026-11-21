"""Code-owned hosted environment declarations; selecting one contacts no device.

Native effects still belong to the selected prepared operation. These profiles
choose only installer requirements, import checks and environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from empirical_lawhood.execution.compute_backend import JAX_TORAX_BACKEND


@dataclass(frozen=True, slots=True)
class HostedWorkerProfile:
    profile_id: str
    required_versions: tuple[tuple[str, str | None], ...]
    import_modules: tuple[str, ...]
    include_cutensor_path: bool
    environment: tuple[tuple[str, str], ...] = ()

    def validate_versions(self, versions: Mapping[str, str]) -> None:
        missing = sorted(name for name, _ in self.required_versions if name not in versions)
        if missing:
            raise ValueError(f"HOSTED_WORKER_PROFILE_UNSUPPORTED: {self.profile_id} bootstrap requires "
                             + ", ".join(missing) + " in its exact installed-version declaration")
        mismatches = [f"{name}=={expected} (declared {versions[name]})"
                      for name, expected in self.required_versions if expected is not None and versions[name] != expected]
        if mismatches:
            raise ValueError(f"HOSTED_WORKER_PROFILE_UNSUPPORTED: {self.profile_id} pinned version differs: "
                             + ", ".join(mismatches))


PERIODIC_WORKER = HostedWorkerProfile(
    "periodic-cuda-pyscf-openmm", (("openmm", None), ("pyscf", None)),
    ("pyscf", "openmm"), True,
)

# Exact CUDA12 closure selected by the repository's uv.lock open-simulators-gpu
# group. This table is checked against that lock by a pure metadata contract test;
# neither importing it nor selecting it imports JAX or initializes CUDA.
JAX_TORAX_WORKER = HostedWorkerProfile(
    "jax-cuda12-torax-float64",
    (
        ("gymtorax", "1.1.1"), ("jax", "0.10.2"), ("jax-cuda12-pjrt", "0.10.2"),
        ("jax-cuda12-plugin", "0.10.2"), ("jaxlib", "0.10.2"),
        ("numpy", "2.4.6"), ("scipy", "1.17.1"), ("torax", "1.4.2"), ("xarray", "2026.7.0"),
        ("nvidia-cublas-cu12", "12.9.2.10"), ("nvidia-cuda-cccl-cu12", "12.9.27"),
        ("nvidia-cuda-cupti-cu12", "12.9.79"), ("nvidia-cuda-nvcc-cu12", "12.9.86"),
        ("nvidia-cuda-nvrtc-cu12", "12.9.86"), ("nvidia-cuda-runtime-cu12", "12.9.79"),
        ("nvidia-cudnn-cu12", "9.26.0.51"), ("nvidia-cufft-cu12", "11.4.1.4"),
        ("nvidia-cusolver-cu12", "11.7.5.82"), ("nvidia-cusparse-cu12", "12.5.10.65"),
        ("nvidia-nccl-cu12", "2.32.3"), ("nvidia-nvjitlink-cu12", "12.9.86"),
        ("nvidia-nvshmem-cu12", "3.8.0"),
    ),
    ("jax", "jaxlib", "gymtorax", "torax"), False,
    (("JAX_ENABLE_X64", "true"), ("JAX_PLATFORMS", "cuda"), ("XLA_PYTHON_CLIENT_PREALLOCATE", "false")),
)


def hosted_worker_profile(numerical_backend: str | None) -> HostedWorkerProfile:
    """Resolve only explicitly implemented backend environments, failing closed."""
    if numerical_backend == JAX_TORAX_BACKEND.accelerated_backend:
        return JAX_TORAX_WORKER
    if numerical_backend in {None, "gpu4pyscf.periodic-direct.openmm-cuda-double",
                             "gpu4pyscf.periodic-direct.openmm-reference"}:
        return PERIODIC_WORKER
    raise ValueError("HOSTED_WORKER_PROFILE_UNSUPPORTED: selected numerical backend has no implemented hosted profile")
