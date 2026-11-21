# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# Scientific registration and configuration.

from hashlib import sha256

from empirical_lawhood.execution.declaration_helpers import bundle
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind

from empirical_lawhood.domains.history.simulator_morphism_challenges.authoring import simulator_morphism_challenges_registry
from empirical_lawhood.domains.history.simulator_morphism_challenges.issued_inputs import CAPABILITY_INPUT_TYPES
from empirical_lawhood.domains.history.simulator_morphism_challenges.capability_configs import CAPABILITY_CONFIG_TYPES


# This hashes the declared installed implementation descriptor, not source bytes.
# Exact current producing-code closure and independent method hashes are retained
# and verified by issued_inputs/runtime_provider and the scientific phase freezes.
INSTALLED_IMPLEMENTATION_DESCRIPTOR = (
    "rc-v3-current-four-phase-binding-v1",
    "dense-observer-independent-sparse-generator",
    "original-canonical-v3-descriptor-depth-random-fibre-pcg64",
    "unscaled-relative-svd-strict-1e-12",
    "individual-row-equilibrated-relative-svd-strict-1e-12",
    "36-disorder-blocks-3-nested-scales-108-adjudications",
    "whole-block-bootstrap-10000-seed3140159-alpha0.05-over18",
    "authenticated-current-numeric-source-export-and-prior-exposure-census",
)
INSTALLED_IMPLEMENTATION_SHA256 = sha256(canonical_json_bytes(INSTALLED_IMPLEMENTATION_DESCRIPTOR)).hexdigest()
CAPABILITIES = simulator_morphism_challenges_registry(implementation_sha256=INSTALLED_IMPLEMENTATION_SHA256).capabilities
_ASSEMBLED = tuple(
    bundle(capability.capability_key.removeprefix("simulator-morphism-challenges."),
           ExtensionContributionKind.SOURCE, capability,
           (CAPABILITY_CONFIG_TYPES[capability.capability_key], CAPABILITY_INPUT_TYPES[capability.capability_key]), None,
           namespace="simulator-morphism-challenges", maximum_config_bytes=8 * 1024**2)
    for capability in CAPABILITIES
)
EXTENSION_BUNDLE_CONTRIBUTIONS = tuple(value[0] for value in _ASSEMBLED)
COMPONENTS_BY_CAPABILITY = {capability.capability_key: value[1] for capability, value in zip(CAPABILITIES, _ASSEMBLED, strict=True)}


# Executable roles.

from dataclasses import dataclass, replace

from empirical_lawhood.execution.declaration_helpers import executable
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.capabilities import CapabilityRegistry
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import CampaignRuntimeProvider

from empirical_lawhood.domains.history.simulator_morphism_challenges.contracts import SimulatorMorphismChallengePhase

from empirical_lawhood.domains.history.simulator_morphism_challenges.issued_inputs import CAPABILITY_INPUT_TYPES, capability_port_key
from empirical_lawhood.adapters.simulator_morphism_challenges.input_custody import RCChallengeRuntimeInputPort
from empirical_lawhood.domains.history.simulator_morphism_challenges.capability_configs import CAPABILITY_CONFIG_TYPES


BINDINGS = tuple(replace(executable(capability, COMPONENTS_BY_CAPABILITY[capability.capability_key],
                                  (CAPABILITY_CONFIG_TYPES[capability.capability_key], CAPABILITY_INPUT_TYPES[capability.capability_key])),
                         required_platform_port_keys=(capability_port_key(capability.capability_key),)) for capability in CAPABILITIES)


class RCChallengeCapabilityRuntimeProvider(CampaignRuntimeProvider):
    """One factory owns one runner; shared external operands have lexical ownership."""

    def __init__(self, provider, capability_key: str) -> None:
        self.provider = provider
        self.capability_key = capability_key
        self.registry_sha256 = provider.registry_sha256
        self.capability_count = 1

    def runners(self, registry, source_records=()):
        return tuple(value for value in self.provider.runners(registry, source_records)
                     if value.manifest.capability_key == self.capability_key)

    def external_inputs(self, plan, source_records=()):
        owners = {}
        for task in plan.tasks:
            for spec in task.external_inputs:
                owners[spec.logical_artifact_id] = min(owners.get(spec.logical_artifact_id, task.capability.capability_key), task.capability.capability_key)
        return tuple(value for value in self.provider.external_inputs(plan, source_records)
                     if owners[value.logical_artifact_id] == self.capability_key)

    def output_semantic_contracts(self, registry, execution_plan=None):
        # The installed binding covers every declared output schema. A phase
        # uses a subset of these schemas; its actual output roster is the plan.
        if execution_plan is not None and execution_plan.registry_sha256 != self.registry_sha256:
            raise ValueError("RC semantic execution plan registry differs")
        return tuple(value for value in self.provider.output_semantic_contracts(registry)
                     if value.capability_key == self.capability_key)

    def scientific_adjudication_contract(self, registry, execution_plan=None):
        value = self.provider.scientific_adjudication_contract(registry, execution_plan)
        return value if value.capability_key == self.capability_key else None


@dataclass(frozen=True, slots=True)
class RCChallengeRuntimeFactory:
    binding: ExecutableCapabilityBinding

    def build_provider(self, *, registry: CapabilityRegistry,
                       records: tuple[CanonicalRecord, ...],
                       platform_ports: tuple[ExecutablePlatformPort, ...]):
        from empirical_lawhood.adapters.simulator_morphism_challenges.runtime_provider import SimulatorMorphismChallengeCampaignRuntimeProvider

        by_type = {type(record): record for record in records}
        config_type = CAPABILITY_CONFIG_TYPES[self.binding.capability_key]
        inputs_type = CAPABILITY_INPUT_TYPES[self.binding.capability_key]
        if len(records) != 2 or set(by_type) != {config_type, inputs_type}:
            raise ValueError("RC factory requires exact issued config and reconstruction inputs")
        if len(platform_ports) != 1 or platform_ports[0].port_key != capability_port_key(self.binding.capability_key) or not isinstance(platform_ports[0].port, RCChallengeRuntimeInputPort):
            raise ValueError("RC factory requires the current source/custody platform port")
        issued = by_type[inputs_type].inputs
        if by_type[config_type].config != issued.config:
            raise ValueError("RC capability config differs from its exact issued phase input")
        config = issued.config
        port = platform_ports[0].port
        port.authenticate(issued)
        packet = issued.numeric_input
        scientific = () if config.phase in (SimulatorMorphismChallengePhase.CANARY, SimulatorMorphismChallengePhase.NOMINATION) else packet.scientific_inputs(config) if packet is not None else None
        provider = SimulatorMorphismChallengeCampaignRuntimeProvider(
            registry=registry, config=config, external_records=issued.external_records(),
            source_files=port.source_files, scientific_inputs=scientific,
            injected_nomination_seeds=packet.source.seeds if packet is not None and config.phase is SimulatorMorphismChallengePhase.NOMINATION else None,
            manifest_implementation_sha256=INSTALLED_IMPLEMENTATION_SHA256,
        )
        return RCChallengeCapabilityRuntimeProvider(provider, self.binding.capability_key)


_EXECUTABLE_ID = "executable-contribution.simulator-morphism-challenges"
_EXECUTABLE_VERSION = "1.0.0"
_EXECUTABLE_FACTORIES = tuple(RCChallengeRuntimeFactory(binding) for binding in BINDINGS)
_ISSUED_RECORD_TYPES = tuple(kind for value in CAPABILITIES
    for kind in (CAPABILITY_CONFIG_TYPES[value.capability_key], CAPABILITY_INPUT_TYPES[value.capability_key]))


from empirical_lawhood.execution.extensions import ExtensionDefinition

from dataclasses import replace
_DISCOVERY_CONTRIBUTION = replace(
    EXTENSION_BUNDLE_CONTRIBUTIONS[0],
    contribution_id="extension-contribution.simulator-morphism-challenges",
    capability_manifests=tuple(sorted(
        (value for part in EXTENSION_BUNDLE_CONTRIBUTIONS for value in part.capability_manifests),
        key=lambda value: value.registry_id,
    )),
    candidate_capability_registrations=tuple(sorted(
        (value for part in EXTENSION_BUNDLE_CONTRIBUTIONS for value in part.candidate_capability_registrations),
        key=lambda value: value.registration_id,
    )),
    profile_registrations=tuple(sorted(
        (value for part in EXTENSION_BUNDLE_CONTRIBUTIONS for value in part.profile_registrations),
        key=lambda value: value.registration_id,
    )),
    config_decoders=tuple(sorted(
        (value for part in EXTENSION_BUNDLE_CONTRIBUTIONS for value in part.config_decoders),
        key=lambda value: value.object_id,
    )),
    runtime_providers=tuple(sorted(
        (value for part in EXTENSION_BUNDLE_CONTRIBUTIONS for value in part.runtime_providers),
        key=lambda value: value.object_id,
    )),
)

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['BINDINGS', 'EXTENSION', 'INSTALLED_IMPLEMENTATION_SHA256']
