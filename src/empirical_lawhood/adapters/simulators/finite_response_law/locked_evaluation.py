"""Receipt-pinned continuation of an assigned evaluation after its parents were acquired."""

from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property
from typing import ClassVar

from empirical_lawhood.design.source_qualification import (
    ProspectiveRetainedContinuation,
)
from empirical_lawhood.domains.matrix.finite_response_law.assigned_contracts import (
    FiniteResponseLawAssignedEvaluationConfig,
)
from empirical_lawhood.domains.matrix.finite_response_law.control_records import (
    FiniteResponseLawRootControlLock,
    FiniteResponseLawRootForecast,
    FiniteResponseLawRootRequestReveal,
)
from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_retention import (
    FiniteResponseLawEvaluationRetention,
)
from empirical_lawhood.adapters.simulators.finite_response_law.native_artifact import (
    NATIVE_PAIR_SCHEMA,
)
from empirical_lawhood.adapters.simulators.finite_response_law.source_outputs import (
    FiniteResponseLawAssignedEvaluationTaskResult,
)
from empirical_lawhood.execution.linked_campaigns import LinkedCampaignStageEnvelope
from empirical_lawhood.execution.recovery import RunRecoveryTerminalEvent
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.science.records.serialization import (
    CanonicalRecord,
    require_sorted_unique_ids,
    validate_stable_id,
)
from empirical_lawhood.storage.contracts.artifacts import CanonicalTaskReceipt

CONTROL_RESULTS = {
    "forecast": FiniteResponseLawRootForecast,
    "reveal-request": FiniteResponseLawRootRequestReveal,
    "lock-choices": FiniteResponseLawRootControlLock,
}


@dataclass(frozen=True, slots=True)
class FiniteResponseLawRetainedChoice(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/methods/finite-response-law/retained-choice-publication"
    )
    task_id: str
    product: ArtifactIdentity
    receipt: ArtifactIdentity

    def __post_init__(self) -> None:
        validate_stable_id(self.task_id)
        cls = CONTROL_RESULTS.get(self.task_id.rsplit(".", 1)[-1])
        if (
            cls is None
            or self.product.payload_schema != cls.SCHEMA
            or self.receipt.payload_schema != CanonicalTaskReceipt.SCHEMA
            or self.product.size_bytes <= 0
            or self.receipt.size_bytes <= 0
        ):
            raise ValueError(
                "Retained choice requires its exact control product and receipt"
            )


@dataclass(frozen=True)
class FiniteResponseLawLockedEvaluationRetention(FiniteResponseLawEvaluationRetention):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/simulators/finite-response-law/locked-evaluation-retention"
    )
    CLOSEOUT_SCHEMA: ClassVar[str] = RunRecoveryTerminalEvent.SCHEMA
    parents: tuple[ProspectiveRetainedContinuation, ...]
    choices: tuple[FiniteResponseLawRetainedChoice, ...]
    issued_study: ObjectIdentity
    execution_authority: ObjectIdentity
    reveal_authority: ObjectIdentity
    terminal: ObjectIdentity

    def __post_init__(self) -> None:
        super().__post_init__()
        from empirical_lawhood.design.study_issue import StudyOperationAuthority
        from empirical_lawhood.execution.study_issue import (
            IssuedExecutableStudyManifest,
        )

        if (
            type(self.source) is not FiniteResponseLawAssignedEvaluationConfig
            or self.issued_study.object_schema != IssuedExecutableStudyManifest.SCHEMA
            or self.execution_authority.object_schema != StudyOperationAuthority.SCHEMA
            or self.reveal_authority.object_schema != StudyOperationAuthority.SCHEMA
            or self.terminal.object_schema != RunRecoveryTerminalEvent.SCHEMA
            or self.donor_closeout.sha256 != self.terminal.object_fingerprint
        ):
            raise ValueError(
                "Locked evaluation must bind its assigned source, original issue, grants and failed terminal"
            )
        require_sorted_unique_ids(
            self.choices, attribute="task_id", field_name="choices"
        )
        from empirical_lawhood.domains.matrix.finite_response_law.contracts import (
            native_invocations,
        )

        native = tuple(
            t for t in native_invocations(self.source) if t.phase == "parent"
        )
        if (
            len(self.parents) != 64
            or len(self.choices) != 192
            or {c.task_id for c in self.choices}
            != {
                f"{r.stage_unit}.{op}"
                for r in self.source.roots
                for op in CONTROL_RESULTS
            }
        ):
            raise ValueError(
                "Locked evaluation requires all original parents, forecasts, requests and choices"
            )
        prefixes = {p.physical_independent_unit_id: p for p in self.prefixes}
        for parent, invocation in zip(self.parents, native, strict=True):
            key = invocation.root.physical_unit_id
            prefix = prefixes[key]
            if (
                type(parent) is not ProspectiveRetainedContinuation
                or parent.segment_id != invocation.task_id
                or parent.physical_independent_unit_id != key
                or parent.predecessor_segment_id != prefix.segment_id
                or parent.start != prefix.end
                or parent.end != Decimal(invocation.clocks[1])
                or (parent.native_clock_id, parent.view_ids)
                != (prefix.native_clock_id, prefix.view_ids)
                or len(parent.artifacts) != 3
                or {a.payload_schema for a in parent.artifacts}
                != {
                    FiniteResponseLawAssignedEvaluationTaskResult.SCHEMA,
                    LinkedCampaignStageEnvelope.SCHEMA,
                    NATIVE_PAIR_SCHEMA,
                }
            ):
                raise ValueError(
                    "Retained parent changes its original unit, prefix, clock, views or native members"
                )

    @property
    def config_id(self) -> str:
        return f"{self.source.spec_id}.retained-locked-parents"

    @cached_property
    def native_origins(self):
        return tuple(
            sorted((*self.prefixes, *self.parents), key=lambda p: p.segment_id)
        )

    @cached_property
    def import_dependencies(self) -> dict[str, tuple[str, ...]]:
        prefixes = {p.physical_independent_unit_id: p.segment_id for p in self.prefixes}
        dependencies = {p.segment_id: () for p in self.native_origins}
        for root in self.source.roots:
            key = root.stage_unit
            dependencies[f"{key}.forecast"] = (prefixes[root.physical_unit_id],)
            dependencies[f"{key}.reveal-request"] = (f"{key}.forecast",)
            dependencies[f"{key}.lock-choices"] = (
                f"{key}.forecast",
                f"{key}.reveal-request",
            )
        return dependencies

    @cached_property
    def import_inputs(self) -> dict[str, tuple[ArtifactIdentity, ...]]:
        return {
            **{
                p.segment_id: (*p.artifacts, p.task_receipt)
                for p in self.native_origins
            },
            **{c.task_id: (c.product, c.receipt) for c in self.choices},
        }
