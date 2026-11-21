# SPDX-License-Identifier: MPL-2.0
"""Editable, disclosed declaration/codec fixture; not a scientific starter.

The runner is deliberately unavailable. This file demonstrates selection and
exact retained verification of a contributor's code without source contact.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile
from empirical_lawhood.execution.capabilities import CapabilityKind
from empirical_lawhood.execution.extension_conformance import ConformanceCall, ConformanceCase, ConformanceProfile, ExtensionConformanceSelection
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration


@dataclass(frozen=True, slots=True)
class DisclosedValue(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/conformance-demo/value"
    record_id: str
    value: Decimal


def unavailable_runner():
    raise NotImplementedError("This codec fixture supplies no scientific calculation")


operation = RecursiveOperationDeclaration(
    capability_key="conformance-demo.codec", capability_version="1.0.0",
    implementation_id="disclosed-codec-example", kind=CapabilityKind.TRANSFORM,
    config_record_type=DisclosedValue, stage=ScientificStage.TRANSFORM,
    input_ports=(), outputs=(OutputTemplate("value", DisclosedValue.SCHEMA,
        ArtifactProfile.CANONICAL_JSON, "application/json", ".json"),),
    permissions=(), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
    outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
    resources=ResourceBudget(1, 1024**2, 0, None, 4096, 4096),
    conformance_check_ids=("conformance-demo.roundtrip",),
    runner_factory=unavailable_runner, record_codecs={DisclosedValue.SCHEMA: DisclosedValue},
    execution_properties=RecursiveExecutionProperties(requires_active_mount=False),
)
original = DisclosedValue("conformance-demo.original", Decimal("0.123456789012345678901234567890"))
CONFORMANCE_SELECTION = ExtensionConformanceSelection(
    namespace="conformance-demo", schema_prefix="empirical-lawhood/conformance-demo/",
    operations=(operation,), profile=ConformanceProfile.ORDINARY_DEVELOPMENT,
    cases=(ConformanceCase("conformance-demo.roundtrip", ConformanceCall.CODEC_ROUNDTRIP,
        {"record": original, "codec": DisclosedValue}, original),),
)
