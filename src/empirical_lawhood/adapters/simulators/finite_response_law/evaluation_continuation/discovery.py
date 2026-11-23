"""Only the native continuation and receipt-import owners are new."""

from dataclasses import replace
from hashlib import sha256

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess
from empirical_lawhood.design.source_qualification import ProspectiveRetainedSourceUse
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.extension_bundles import ExtensionContributionKind
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.source_qualification import ProspectiveRetainedSourceUseBinding
from empirical_lawhood.execution.declaration_helpers import manifest, bundle
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation.discovery import SOURCE_CAPABILITY as ORIGINAL_SOURCE, SOURCE_COMPONENTS as ORIGINAL_COMPONENTS
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import FiniteResponseLawAssignedEvaluationConfig
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_retention import FiniteResponseLawEvaluationRetention
from empirical_lawhood.adapters.simulators.finite_response_law.source_outputs import FiniteResponseLawAssignedEvaluationTaskResult
from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import NATIVE_PAIR_SCHEMA

from empirical_lawhood.adapters.simulators.finite_response_law.locked_evaluation import CONTROL_RESULTS, FiniteResponseLawLockedEvaluationRetention

NAMESPACE = "finite-response-law.evaluation-continuation"
SOURCE_CAPABILITY = replace(
    ORIGINAL_SOURCE,
    capability_key=f"{NAMESPACE}.source",
    runtime_id=f"{NAMESPACE}.source",
    implementation_sha256=sha256(b'finite-response-law-retained-prefix-native-continuation').hexdigest(),
    conformance_check_ids=(
        "exact-original-native-source-compatibility",
        "no-prefix-reacquisition",
        "unchanged-pre-parent-control-guards",
    ),
)
IMPORT_CAPABILITY = manifest(
    "prefix-import",
    FiniteResponseLawEvaluationRetention,
    CapabilityKind.TRANSFORM,
    (
        FiniteResponseLawEvaluationRetention.SCHEMA,
        CanonicalTaskReceipt.SCHEMA,
        FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA,
        NATIVE_PAIR_SCHEMA,
        LinkedCampaignStageEnvelope.SCHEMA,
    ),
    (FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA, NATIVE_PAIR_SCHEMA, LinkedCampaignStageEnvelope.SCHEMA),
    EvidenceCeiling.MEASUREMENT,
    OutcomeAccess.OUTCOME_BLIND,
    30,
    namespace=NAMESPACE,
    resources=ResourceBudget(
        1, 1024**3, 0, 30, 64 * 1024**2, ORIGINAL_SOURCE.resource_ceiling.output_bytes
    ),
    implementation_id="receipt-authenticated-byte-identical-prefix-import",
    conformance_ids=(
        "all-64-donor-prefixes",
        "outcome-blind-receipted-import",
        "zero-native-launches",
    ),
    read_permission=(CapabilityPermission.READ_OUTCOME_VISIBLE if 'prefix-import' == "evaluation" else CapabilityPermission.READ_SEALED_OUTCOMES),
)
IMPORT_CAPABILITY = replace(
    IMPORT_CAPABILITY,
    permissions=tuple(
        p
        for p in IMPORT_CAPABILITY.permissions
        if p is not CapabilityPermission.READ_SEALED_OUTCOMES
    ),
)
_locked_outputs = (*IMPORT_CAPABILITY.output_schema_ids, *(cls.SCHEMA for cls in CONTROL_RESULTS.values()))
LOCKED_IMPORT_CAPABILITY = manifest(
    "locked-parent-import", FiniteResponseLawLockedEvaluationRetention, CapabilityKind.TRANSFORM,
    (FiniteResponseLawLockedEvaluationRetention.SCHEMA, CanonicalTaskReceipt.SCHEMA, *_locked_outputs),
    _locked_outputs, EvidenceCeiling.MEASUREMENT, OutcomeAccess.OUTCOME_BLIND, 60,
    namespace=NAMESPACE, resources=ResourceBudget(1, 2 * 1024**3, 0, 60, 128 * 1024**2, 16 * 1024**2),
    implementation_id="original-locked-choices-and-acquired-native-parents",
    conformance_ids=("no-native-acquisition", "original-receipt-and-complete-members", "prepared-choice-continuity"),
    read_permission=CapabilityPermission.READ_SEALED_OUTCOMES,
)
LOCKED_IMPORT_CAPABILITY = replace(LOCKED_IMPORT_CAPABILITY, permissions=tuple(
    perm for perm in LOCKED_IMPORT_CAPABILITY.permissions if perm is not CapabilityPermission.READ_SEALED_OUTCOMES))
_locked, LOCKED_IMPORT_COMPONENTS = bundle(
    "locked-parent-import", ExtensionContributionKind.METHOD, LOCKED_IMPORT_CAPABILITY,
    (FiniteResponseLawLockedEvaluationRetention,), NATIVE_PAIR_SCHEMA, namespace=NAMESPACE)

_source, SOURCE_COMPONENTS = bundle(
    "source",
    ExtensionContributionKind.SOURCE,
    SOURCE_CAPABILITY,
    (
        FiniteResponseLawAssignedEvaluationConfig,
        ProspectiveRetainedSourceUse,
        ProspectiveRetainedSourceUseBinding,
        FiniteResponseLawEvaluationRetention,
    ),
    NATIVE_PAIR_SCHEMA,
    namespace=NAMESPACE,
)
_import, IMPORT_COMPONENTS = bundle(
    "prefix-import",
    ExtensionContributionKind.METHOD,
    IMPORT_CAPABILITY,
    (FiniteResponseLawEvaluationRetention,),
    NATIVE_PAIR_SCHEMA,
    namespace=NAMESPACE,
)
# Reuse exact existing decoder identities instead of registering another decoder
# for an immutable source schema or for the shared retention record.
_original_decoder = ORIGINAL_COMPONENTS[0]
_discarded_source_decoder = SOURCE_COMPONENTS[0]
SOURCE_COMPONENTS = (_original_decoder, *SOURCE_COMPONENTS[1:])
_source = replace(
    _source,
    config_decoders=tuple(
        v
        for v in _source.config_decoders
        if v.object_id != _discarded_source_decoder.registration_id
    ),
)
IMPORT_COMPONENTS = (SOURCE_COMPONENTS[3], *IMPORT_COMPONENTS[1:])
_import = replace(_import, config_decoders=())
EXTENSION_BUNDLE_CONTRIBUTION = replace(
    _source,
    contribution_id=f"extension-contribution.{NAMESPACE}",
    capability_manifests=tuple(
        sorted(
            (*_source.capability_manifests, *_import.capability_manifests, *_locked.capability_manifests),
            key=lambda v: v.registry_id,
        )
    ),
    candidate_capability_registrations=tuple(
        sorted(
            (
                *_source.candidate_capability_registrations,
                *_import.candidate_capability_registrations, *_locked.candidate_capability_registrations,
            ),
            key=lambda v: v.registration_id,
        )
    ),
    profile_registrations=tuple(
        sorted(
            (*_source.profile_registrations, *_import.profile_registrations, *_locked.profile_registrations),
            key=lambda v: v.registration_id,
        )
    ),
    config_decoders=tuple(
        sorted(
            {v.object_id: v for p in (_source, _import, _locked) for v in p.config_decoders}.values(),
            key=lambda v: v.object_id,
        )
    ),
    runtime_providers=tuple(
        sorted((*_source.runtime_providers, *_import.runtime_providers, *_locked.runtime_providers), key=lambda v: v.object_id)
    ),
    artifact_validators=tuple(
        sorted(
            (*_source.artifact_validators, *_import.artifact_validators, *_locked.artifact_validators), key=lambda v: v.object_id
        )
    ),
)
