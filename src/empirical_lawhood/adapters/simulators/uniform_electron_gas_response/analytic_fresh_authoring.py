"""One-CLI uniform electron gas analytic candidate packet and pure preissue plan projection."""

from empirical_lawhood.domains.materials.electron_gas.authoring_profile import UniformElectronGasAnalyticAuthoringProfile as _ueg_UniformElectronGasAnalyticAuthoringProfile
from pathlib import Path

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.design.experiment_entry import ExecutableStudyDefinition
from empirical_lawhood.design.study_issue import ImplementationSourceClosure

from empirical_lawhood.domains.materials.electron_gas.analytic_authoring import UniformElectronGasAnalyticAuthoringBundle, build_uniform_electron_gas_analytic_authoring
from empirical_lawhood.domains.materials.electron_gas.native_quickstart import UniformElectronGasAnalyticReferenceConfig

_MAX_CONFIG_BYTES = 128 * 1024
_MAX_PACKET_BYTES = 16 * 1024 * 1024





def load_uniform_electron_gas_analytic_config(path: Path) -> UniformElectronGasAnalyticReferenceConfig:
    return decode_canonical_bytes(
        read_bounded_bytes(path, maximum_bytes=_MAX_CONFIG_BYTES),
        UniformElectronGasAnalyticReferenceConfig,
        maximum_bytes=_MAX_CONFIG_BYTES,
    )


def load_uniform_electron_gas_analytic_authoring_bundle(directory: Path) -> UniformElectronGasAnalyticAuthoringBundle:
    """Recompute the exact installed uniform electron gas graph from bounded packet records."""

    profile = decode_canonical_bytes(
        read_bounded_bytes(directory / "profile.json", maximum_bytes=_MAX_CONFIG_BYTES),
        _ueg_UniformElectronGasAnalyticAuthoringProfile,
        maximum_bytes=_MAX_CONFIG_BYTES,
    )
    config = load_uniform_electron_gas_analytic_config(directory / "config.json")
    if profile.config_sha256 != config.fingerprint():
        raise ValueError("uniform electron gas packet config differs from frozen profile")
    closure = decode_canonical_bytes(
        read_bounded_bytes(
            directory / "source-closure.json", maximum_bytes=_MAX_CONFIG_BYTES
        ),
        ImplementationSourceClosure,
        maximum_bytes=_MAX_CONFIG_BYTES,
    )
    expected = decode_canonical_bytes(
        read_bounded_bytes(
            directory / "authoring.json", maximum_bytes=_MAX_PACKET_BYTES
        ),
        ExecutableStudyDefinition,
        maximum_bytes=_MAX_PACKET_BYTES,
    )
    bundle = build_uniform_electron_gas_analytic_authoring(
        config=config,
        experiment_id=profile.experiment_id,
        implementation_sha256=closure.implementation_sha256,
    )
    if bundle.authoring != expected:
        raise ValueError("uniform electron gas packet authoring differs from installed science")
    return bundle


__all__ = [
    "load_uniform_electron_gas_analytic_config",
    "load_uniform_electron_gas_analytic_authoring_bundle",
]
