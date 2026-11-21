# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from hashlib import sha256

from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration

from empirical_lawhood.adapters.isolated_native_starter import experiment
from empirical_lawhood.adapters.isolated_native_starter.bindings import operation_declaration
from empirical_lawhood.adapters.isolated_native_starter.records import MAX_SOURCE_BYTES, NAMESPACE, PROTOCOL_ID, SquareInput, SquareSpecification
from empirical_lawhood.adapters.isolated_native_starter.workflow import WORKFLOW_DECLARATIONS as _WORKFLOWS

MANIFEST = operation_declaration().manifest()
REGISTRATION = CandidateCapabilityRegistration(MANIFEST, "recursive.provider." + MANIFEST.capability_key,
    "1.0.0", "application/json", None)
WORKFLOW_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".workflow",
    NAMESPACE + ".workflow", "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes((MANIFEST.fingerprint(),))).hexdigest())
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), (MANIFEST,), (REGISTRATION,), (), (WORKFLOW_PROFILE,), (), (), (), (), (), False, False)
_PROTOCOLS = (ExperimentProtocolDeclaration(PROTOCOL_ID, SquareSpecification,
    experiment.prepare, NAMESPACE + "-experiment", maximum_config_bytes=MAX_SOURCE_BYTES,
    input_record_types=(SquareInput, NumericalProducingProvenance), bind_inputs=experiment.bind_inputs,
    validate_instance=experiment.validate_instance,
    configuration_inputs=(ExperimentInputConfigurationDeclaration(NAMESPACE + "-operand", SquareInput, MAX_SOURCE_BYTES),)),)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.

from empirical_lawhood.adapters.isolated_native_starter.bindings import operation_declaration
from empirical_lawhood.adapters.isolated_native_starter.records import NAMESPACE

_EXECUTABLE_FACTORIES = (operation_declaration().provider_factory(),)
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
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
