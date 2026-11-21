# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from hashlib import sha256
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.domains.matrix.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.bindings import operation_declarations
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import experiment
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import NAMESPACE

MANIFESTS = tuple(sorted((d.manifest() for d in operation_declarations()), key=lambda m: m.registry_id))
REGISTRATIONS = tuple(CandidateCapabilityRegistration(m, 'recursive.provider.'+m.capability_key, '1.0.0', 'application/json', None) for m in MANIFESTS)
WORKFLOW_PROFILE = ExtensionProfileRegistration('profile-registration.'+NAMESPACE+'.workflow', NAMESPACE+'.workflow', '1.0.0',
    ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA, sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(m.fingerprint() for m in MANIFESTS))).hexdigest())
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution('method.'+NAMESPACE, '1.0.0', ExtensionContributionKind.METHOD,
    (), MANIFESTS, REGISTRATIONS, (), (WORKFLOW_PROFILE,), (), (), (), (), (), False, False)
_PROTOCOLS = (ExperimentProtocolDeclaration(experiment.PROTOCOL_ID, experiment.BridgeSpecification,
    experiment.prepare, 'matrix-sci02d-paired-equilibrium', input_record_types=experiment.input_record_types(),
    bind_inputs=experiment.bind_inputs, validate_instance=experiment.validate_instance, input_storage_codecs=MATRIX_STORAGE_CODECS),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.bindings import operation_declarations
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import NAMESPACE
_EXECUTABLE_FACTORIES = tuple(d.provider_factory() for d in operation_declarations())
_EXECUTABLE_ID = 'executable-contribution.'+NAMESPACE
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
