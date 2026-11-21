"""Pure hosted-profile/installer metadata contracts: no GPU, provider or engine.

These checks render/select bytes only. They are not remote GPU tests, native
import validation, installation acceptance or numerical qualification.
"""

from dataclasses import replace
from hashlib import sha256
import ast
import json
from pathlib import Path
import shlex
import tomllib

import pytest
import yaml

from empirical_lawhood.execution.compute_backend import JAX_TORAX_BACKEND
from empirical_lawhood.execution.remote.worker_profiles import JAX_TORAX_WORKER, PERIODIC_WORKER, hosted_worker_profile
from empirical_lawhood.execution.remote.accelerated_worker_bundle import WorkerBundle, render_worker_bootstrap


def bundle(*, versions=None):
    return WorkerBundle(base_image="docker:python:3.11.14@sha256:" + "a" * 64,
                        source_image_sha256="b" * 64, source_lock_sha256="c" * 64,
                        source_lock="uv.lock", requirements="requirements.txt", wheels="wheels",
                        uv_wheel="uv.whl", system_package="libgomp.deb",
                        installed_versions=dict(JAX_TORAX_WORKER.required_versions) if versions is None else versions)


def test_jax_backend_is_a_single_device_code_declaration():
    assert JAX_TORAX_BACKEND.selection(False)["backend"] == "jax.torax.cpu.float64"
    assert JAX_TORAX_BACKEND.selection(False)["gpu_devices"] == 0
    assert JAX_TORAX_BACKEND.selection(True)["backend"] == "jax.torax.cuda12.float64"
    assert JAX_TORAX_BACKEND.selection(True)["gpu_devices"] == 1


def test_jax_profile_versions_are_the_existing_lock_cuda12_closure():
    root = Path(__file__).resolve().parents[1]
    lock = tomllib.loads((root / "uv.lock").read_text())
    pairs = {(row["name"], row["version"]) for row in lock["package"]}
    assert all(row in pairs for row in JAX_TORAX_WORKER.required_versions)
    plugin = next(row for row in lock["package"] if row["name"] == "jax-cuda12-plugin")
    required = dict(JAX_TORAX_WORKER.required_versions)
    for dependency in plugin["optional-dependencies"]["with-cuda"]:
        assert dependency["name"] in required
        if "version" in dependency:
            assert required[dependency["name"]] == dependency["version"]
    project = tomllib.loads((root / "pyproject.toml").read_text())
    assert any("jax[cuda12]==0.10.2" in value for value in project["dependency-groups"]["open-simulators-gpu"])


def test_profile_selection_preserves_periodic_requirements_and_refuses_unknown():
    assert hosted_worker_profile(JAX_TORAX_BACKEND.accelerated_backend) is JAX_TORAX_WORKER
    assert hosted_worker_profile("gpu4pyscf.periodic-direct.openmm-cuda-double") is PERIODIC_WORKER
    with pytest.raises(ValueError, match="openmm"):
        PERIODIC_WORKER.validate_versions({"pyscf": "2.14.0"})
    with pytest.raises(ValueError, match="HOSTED_WORKER_PROFILE_UNSUPPORTED"):
        hosted_worker_profile("unknown.cuda")


@pytest.mark.parametrize("change", ["missing-pjrt", "wrong-cudnn", "periodic-environment"])
def test_jax_profile_refuses_partial_wrong_or_other_native_environment(change):
    versions = dict(JAX_TORAX_WORKER.required_versions)
    if change == "missing-pjrt":
        del versions["jax-cuda12-pjrt"]
    elif change == "wrong-cudnn":
        versions["nvidia-cudnn-cu12"] = "9.1.0.70"
    else:
        versions = {"pyscf": "2.14.0", "openmm": "8.3.1"}
    with pytest.raises(ValueError, match="HOSTED_WORKER_PROFILE_UNSUPPORTED"):
        bundle(versions=versions).require_capabilities(JAX_TORAX_BACKEND.accelerated_backend)


def test_jax_installer_is_profile_specific_and_has_no_device_probe(monkeypatch):
    import builtins
    original = builtins.__import__
    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in {"jax", "jaxlib", "gymtorax", "torax", "sky", "runpod", "cupy", "openmm", "pyscf"}:
            pytest.fail("profile rendering imported native or provider code")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_native)
    script = render_worker_bootstrap(bundle(), remote_root="/selected/bundle",
                                     numerical_backend=JAX_TORAX_BACKEND.accelerated_backend)
    assert "cutensor/lib" not in script and "import pyscf" not in script
    assert "nvidia-smi" not in script and "default_backend" not in script and ".devices(" not in script
    assert "--offline" in script and "--require-hashes" in script
    validator = shlex.split(script.splitlines()[-1])[-1]
    ast.parse(validator)  # Syntax only: the validator is deliberately not executed.
    assert "os.environ['JAX_PLATFORMS']='cpu'" in validator
    assert "import jax, jaxlib, gymtorax, torax" in validator
    assert "actual == expected" in validator


def test_periodic_installer_retains_its_original_import_and_library_policy():
    script = render_worker_bootstrap(bundle(versions={"pyscf": "2.14.0", "openmm": "8.3.1"}),
                                     remote_root="/selected/bundle",
                                     numerical_backend="gpu4pyscf.periodic-direct.openmm-cuda-double")
    assert "cutensor/lib" in script and "import pyscf, openmm" in script
    assert "JAX_PLATFORMS" not in script


def test_offline_payload_renderer_selects_jax_profile_and_environment(tmp_path, monkeypatch):
    """Only render a sealed fixture; never launch or install its dummy operands."""
    from dataclasses import asdict
    from empirical_lawhood.api.accelerated_deployment import prepare_accelerated_deployment
    from tests.test_accelerated_deployment import payload, selection
    root = payload(tmp_path)
    worker = root / "worker"
    worker.mkdir()
    (worker / "wheels").mkdir()
    for name in ("requirements.txt", "uv.whl", "libgomp.deb"):
        (worker / name).write_bytes(b"offline-profile-contract-fixture-not-installable")
    lock = b"offline-profile-contract-fixture-lock-not-native-acceptance"
    (worker / "uv.lock").write_bytes(lock)
    selected = replace(selection(), accelerator="H100-SXM", numerical_threads=1,
                       sizing_plan_sha256="d" * 64, numerical_backend=JAX_TORAX_BACKEND.accelerated_backend,
                       worker_bundle="worker/worker-bundle.json")
    specification = replace(bundle(), base_image=selected.image, source_lock_sha256=sha256(lock).hexdigest())
    (worker / "worker-bundle.json").write_text(json.dumps({"version": "1.0.0", **asdict(specification)}))
    import builtins
    original = builtins.__import__
    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in {"jax", "jaxlib", "gymtorax", "torax", "sky", "runpod", "cupy", "openmm", "pyscf"}:
            pytest.fail("offline payload preparation imported a native/provider implementation")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", no_native)
    destination = tmp_path / "prepared-jax"
    result = prepare_accelerated_deployment(selected, payload_root=root, output_directory=destination)
    assert result["status"] == "PREPARED_NOT_LAUNCHED" and result["execution_authority"] == "NONE"
    assert result["worker_distribution"]["profile"] == JAX_TORAX_WORKER.profile_id
    task = yaml.safe_load((destination / "task.yaml").read_text())
    assert task["envs"]["JAX_PLATFORMS"] == "cuda" and task["envs"]["JAX_ENABLE_X64"] == "true"
    assert task["envs"]["XLA_PYTHON_CLIENT_PREALLOCATE"] == "false"
    assert "CUPY_CACHE_DIR" not in task["envs"] and "OPENMM_CPU_THREADS" not in task["envs"]


def test_jax_hosted_preparation_requires_its_authenticated_bundle(tmp_path):
    from empirical_lawhood.api.accelerated_deployment import prepare_accelerated_deployment
    from tests.test_accelerated_deployment import payload, selection
    root = payload(tmp_path)
    selected = replace(selection(), accelerator="H100-SXM", numerical_threads=1,
                       sizing_plan_sha256="d" * 64, numerical_backend=JAX_TORAX_BACKEND.accelerated_backend)
    destination = tmp_path / "unentered"
    with pytest.raises(ValueError, match="JAX_TORAX_WORKER_BUNDLE_REQUIRED"):
        prepare_accelerated_deployment(selected, payload_root=root, output_directory=destination)
    assert not destination.exists()
