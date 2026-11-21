# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.

from hashlib import sha256

from empirical_lawhood.science.records.serialization import canonical_json_bytes
from empirical_lawhood.design.inquiry_methods import DependentAssessmentContract
from empirical_lawhood.execution.candidate_composition import CandidateCapabilityRegistration
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind, ExtensionProfileKind, ExtensionProfileRegistration

from empirical_lawhood.methods.assigned_opportunity_assessment.bindings import operation_declarations
from empirical_lawhood.methods.assigned_opportunity_assessment.records import NAMESPACE


MANIFESTS = tuple(sorted((d.manifest() for d in operation_declarations()), key=lambda m: m.registry_id))
REGISTRATIONS = tuple(CandidateCapabilityRegistration(m, "recursive.provider." + m.capability_key,
    "1.0.0", "application/json", None) for m in MANIFESTS)
ASSESSMENT_PROFILE = ExtensionProfileRegistration("profile-registration." + NAMESPACE + ".assessment",
    NAMESPACE + ".assessment", "1.0.0", ExtensionProfileKind.OBJECTIVE_TERMINAL, DependentAssessmentContract.SCHEMA,
    sha256(DependentAssessmentContract.SCHEMA.encode()).hexdigest(),
    sha256(canonical_json_bytes(tuple(m.fingerprint() for m in MANIFESTS))).hexdigest())
_DISCOVERY_CONTRIBUTION = ExtensionBundleContribution("method." + NAMESPACE, "1.0.0", ExtensionContributionKind.METHOD,
    (), MANIFESTS, REGISTRATIONS, (), (ASSESSMENT_PROFILE,), (), (), (), (), (), False, False)


# SPDX-License-Identifier: MPL-2.0
# Executable roles.


from empirical_lawhood.methods.assigned_opportunity_assessment.bindings import operation_declarations
from empirical_lawhood.methods.assigned_opportunity_assessment.records import NAMESPACE


_EXECUTABLE_FACTORIES = tuple(d.provider_factory() for d in operation_declarations())
_EXECUTABLE_ID = "executable-contribution." + NAMESPACE
_EXECUTABLE_VERSION = "1.0.0"
_ISSUED_RECORD_TYPES = ()


from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    executable_id=_EXECUTABLE_ID, executable_version=_EXECUTABLE_VERSION,
    factories=_EXECUTABLE_FACTORIES, record_types=_ISSUED_RECORD_TYPES,
)

__all__ = ['EXTENSION']
