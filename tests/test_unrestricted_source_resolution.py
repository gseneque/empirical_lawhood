# SPDX-License-Identifier: MPL-2.0
"""Exposed custody checks for unrestricted inputs; no scientific qualification."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import ClassVar

import pytest

from empirical_lawhood.infrastructure.artifacts import FilesystemState, GuardedExternalRoot
from empirical_lawhood.infrastructure.candidate_sources import ExternalCandidateInputPublisher, ExternalContentAddressedInputResolver
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.study_authoring import SourceMaterializationRole
from empirical_lawhood.runtime.artifacts import ExternalRootContract
from empirical_lawhood.runtime.source_resolution import (
    ContentAddressedInputKind, ContentAddressedInputRequirement,
    ContentAddressedResolutionError, SourceMaterializationConfig, SourceReadMode,
)


class _ExposedInspector:
    def inspect(self, contract):
        return FilesystemState(contract.canonical_path, True, True, 100_000_000, False)


def _root(path):
    contract = ExternalRootContract("storage.exposed-unrestricted-input", "Exposed test input custody",
        str(path.resolve()), str(path.resolve()), "empirical-lawhood/testing/input-root", 0)
    return GuardedExternalRoot(contract, _ExposedInspector())


def _requirement(raw, *, maximum=None, expected_size=None):
    return ContentAddressedInputRequirement("input.exposed-software", ContentAddressedInputKind.CAPABILITY_CONFIG,
        sha256(raw).hexdigest(), "empirical-lawhood/testing/exposed-input", "application/json", maximum,
        expected_size, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)


def test_explicit_unrestricted_materialization_passes_old_cap_with_exact_custody(tmp_path):
    raw = b"x" * (16 * 1024**2 + 1)
    root = _root(tmp_path)
    publisher = ExternalCandidateInputPublisher(root)
    publication = publisher.publish(raw, maximum_bytes=None)
    assert publication.size_bytes == len(raw)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    resolver = ExternalContentAddressedInputResolver(root)
    requirement = _requirement(raw, expected_size=len(raw))
    decoded = decode_canonical_bytes(requirement.canonical_bytes(), ContentAddressedInputRequirement, maximum_bytes=None)
    resolved = resolver.resolve(decoded, materialize=True)
    assert resolved.payload == raw
    assert resolved.receipt.observed_sha256 == sha256(raw).hexdigest()
    assert resolved.receipt.observed_size_bytes == len(raw)
    assert resolved.receipt.observed_total_read_bytes == 3 * len(raw)
    assert resolved.receipt.network_bytes == resolved.receipt.external_bytes_written == 0
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="byte envelope"):
        publisher.publish(raw, maximum_bytes=len(raw) - 1)
    with pytest.raises(ContentAddressedResolutionError, match="read-work"):
        resolver.resolve(replace(requirement, maximum_bytes=len(raw) - 1, expected_size_bytes=None), materialize=True)
    with pytest.raises(ContentAddressedResolutionError, match="exact expectation"):
        resolver.resolve(replace(requirement, expected_size_bytes=len(raw) + 1), materialize=True)


@pytest.mark.parametrize("failure", ("digest", "symlink"))
def test_unrestricted_source_still_refuses_digest_substitution_and_symlinks(tmp_path, failure):
    raw = b"exposed recorded bytes"
    root = _root(tmp_path)
    resolver = ExternalContentAddressedInputResolver(root)
    requirement = _requirement(raw)
    path = resolver.install_path(tmp_path, requirement.content_sha256)
    path.parent.mkdir(parents=True)
    if failure == "digest":
        path.write_bytes(b"changed source bytes")
    else:
        target = tmp_path / "unselected-target"
        target.write_bytes(raw)
        path.symlink_to(target)
    with pytest.raises(ContentAddressedResolutionError):
        resolver.resolve(requirement, materialize=True)


def test_unrestricted_source_config_preserves_expected_size_and_exact_revision():
    config = SourceMaterializationConfig("config.exposed-source", "source.exposed-software",
        SourceMaterializationRole.NUMERICAL_CONFIGURATION, "a" * 64, 17 * 1024**2, None,
        "empirical-lawhood/testing/exposed-input", "application/json", SourceReadMode.ORDINARY_BOUNDED,
        OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY)
    assert decode_canonical_bytes(config.canonical_bytes(), SourceMaterializationConfig, maximum_bytes=None) == config
    with pytest.raises(ValueError, match="expected_size"):
        replace(config, expected_size_bytes=-1)
    with pytest.raises(ValueError, match="read envelope"):
        replace(config, maximum_bytes=1)


@dataclass(frozen=True, slots=True)
class ExposedCapabilityConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/testing/large-capability-config"
    content: str


def test_prospective_config_decoder_uses_the_admitted_registration_envelope(tmp_path):
    from empirical_lawhood.api.recursive_prospective_authoring import _ConfigDecoder
    config = ExposedCapabilityConfig("x" * (16 * 1024**2 + 1))
    raw = config.canonical_bytes()
    root = _root(tmp_path)
    ExternalCandidateInputPublisher(root).publish(raw, maximum_bytes=None)
    resolver = ExternalContentAddressedInputResolver(root)
    requirement = replace(_requirement(raw, expected_size=len(raw)), payload_schema=config.SCHEMA)
    admitted = resolver.resolve(requirement, materialize=True)
    decoder = _ConfigDecoder("provider.exposed-capacity", "1.0.0", ExposedCapabilityConfig)
    decoder.validate_config(admitted.payload, expected_schema=config.SCHEMA)
    assert decode_canonical_bytes(admitted.payload, ExposedCapabilityConfig, maximum_bytes=len(raw)) == config
    with pytest.raises(ContentAddressedResolutionError, match="read-work"):
        resolver.resolve(replace(requirement, maximum_bytes=len(raw) - 1, expected_size_bytes=None), materialize=True)
    with pytest.raises(ValueError, match="schema differs"):
        decoder.validate_config(raw, expected_schema="empirical-lawhood/testing/foreign-config")


def test_complete_e4_phase_collector_uses_the_full_programme_carrier():
    from empirical_lawhood.adapters.composition.generated_extension_bundles import GENERATED_EXTENSION_BUNDLE_AGGREGATE
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_e4_native_bindings import NAMESPACE
    catalog = GENERATED_EXTENSION_BUNDLE_AGGREGATE.candidate_capability_catalog
    assert catalog.registration(NAMESPACE + ".phase-collect", "1.0.0").maximum_config_bytes is None
    assert catalog.registration(NAMESPACE + ".phase-entry", "2.0.0").maximum_config_bytes is None
