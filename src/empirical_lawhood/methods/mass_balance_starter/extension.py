# SPDX-License-Identifier: MPL-2.0
"""The mass-balance starter's one authoritative extension declaration."""
from hashlib import sha256

from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.evidence_profiles import ExperimentObjectiveProfile
from empirical_lawhood.execution.extension_bundles import ExtensionProfileKind, ExtensionProfileRegistration
from empirical_lawhood.execution.experiment_preparation import ExperimentInputConfigurationDeclaration, ExperimentProtocolDeclaration
from empirical_lawhood.execution.extensions import ExtensionDeclaration

from . import experiment
from .bindings import operation_declarations
from .records import MAX_BYTES, NAMESPACE, PROTOCOL_ID, MassEvidence, MassSpecification
from .workflow import WORKFLOW_DECLARATIONS

_OPERATIONS = operation_declarations()
_WORKFLOW_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".workflow",
    NAMESPACE + ".workflow", "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL, ExperimentObjectiveProfile.SCHEMA,
    sha256(ExperimentObjectiveProfile.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(operation.manifest().fingerprint() for operation in _OPERATIONS))).hexdigest())

EXTENSION = ExtensionDeclaration(
    extension_id=NAMESPACE, version="1.0.0", operations=_OPERATIONS,
    profiles=(_WORKFLOW_PROFILE,),
    protocols=(ExperimentProtocolDeclaration(PROTOCOL_ID, MassSpecification,
        experiment.prepare, NAMESPACE + "-experiment", maximum_config_bytes=MAX_BYTES,
        input_record_types=(MassEvidence,), bind_inputs=experiment.bind_inputs, validate_instance=experiment.validate_instance,
        configuration_inputs=(ExperimentInputConfigurationDeclaration(NAMESPACE + "-evidence", MassEvidence, MAX_BYTES),)),),
    workflows=WORKFLOW_DECLARATIONS,
)
# Discovery facts are projected from EXTENSION, not separately exported.
del WORKFLOW_DECLARATIONS

__all__ = ['EXTENSION']
