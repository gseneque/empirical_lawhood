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
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration

from empirical_lawhood.methods.mass_balance_revision import experiment
from empirical_lawhood.methods.mass_balance_revision.bindings import operation_declarations
from empirical_lawhood.methods.mass_balance_revision.records import MAX_BYTES, PROTOCOL_ID, ForecastUpgradeSource, ForecastUpgradeSpecification
from empirical_lawhood.methods.mass_balance_revision.workflow import WORKFLOW_DECLARATIONS as _WORKFLOWS

MANIFESTS = tuple(declaration.manifest() for declaration in operation_declarations())
REGISTRATIONS = tuple(CandidateCapabilityRegistration(manifest, 'recursive.provider.' + manifest.capability_key,
    '1.0.0', 'application/json', None) for manifest in MANIFESTS)
WORKFLOW_PROFILE = ExtensionProfileRegistration('profile-registration.mass-balance-record-upgrade.workflow',
    'mass-balance-record-upgrade.workflow', '1.0.0', ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(manifest.fingerprint() for manifest in MANIFESTS))).hexdigest())
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution('method.mass-balance-record-upgrade', '1.0.0',
    ExtensionContributionKind.METHOD, (), MANIFESTS, REGISTRATIONS, (), (WORKFLOW_PROFILE,), (), (), (), (), (), False, False)
_PROTOCOLS = (ExperimentProtocolDeclaration(PROTOCOL_ID, ForecastUpgradeSpecification,
    experiment.prepare, 'mass-balance-forecast-upgrade', maximum_config_bytes=MAX_BYTES,
    input_record_types=(ForecastUpgradeSource,), bind_inputs=experiment.bind_inputs, validate_instance=experiment.validate_instance,
    configuration_inputs=(ExperimentInputConfigurationDeclaration('mass-balance-upgrade-source', ForecastUpgradeSource, MAX_BYTES),)),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.

from empirical_lawhood.methods.mass_balance_revision.bindings import operation_declarations

_EXECUTABLE_FACTORIES = tuple(declaration.provider_factory() for declaration in operation_declarations())
_EXECUTABLE_ID = 'executable-contribution.mass-balance-record-upgrade'
_EXECUTABLE_VERSION = '1.0.0'
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
    protocols=_PROTOCOLS,
    workflows=_WORKFLOWS,
)

__all__ = ['EXTENSION']
