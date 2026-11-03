# SPDX-License-Identifier: MPL-2.0
"""Distinct prospective material/preparation and exploratory dossier identities."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition,
    ScientificConditionScope,
)
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord,
    validate_nonempty,
    validate_sha256,
    validate_stable_id,
)

NAMESPACE = "rubisco-nomination-preparation"
UNIT = NAMESPACE + ".exposed-source-and-conditional-model"
QUESTION = "Prepare an exact exploratory Gp SSU I95M test nominee using authentic prior conditional-model outcome and original material sources; what biological evidence is still missing?"
CANDIDATE_ID = "gp.i95m"
ALTERNATIVES = (
    "gp.wt",
    "nt.a369.t391i",
    "potato.ps3",
    "potato.pst",
    "wilson2017-row17",
)
TARGETS = ("specificity", "turnover")
SOURCE_ROLES = ("ASSAY", "CONSTRUCTION", "MATERIAL", "RATIONALE")
SOURCE_CENSUS = (
    ("ASSAY", "paired-assay-proposal.json"),
    ("ASSAY", "sharwood2008-radiometric-method.html"),
    ("ASSAY", "sharwood2016-maize.html"),
    ("CONSTRUCTION", "build_sequence_defined_construct.py"),
    ("CONSTRUCTION", "construct-preparation-and-paired-assay.md"),
    ("CONSTRUCTION", "gp-expression-patent.html"),
    ("CONSTRUCTION", "pUC19-M77789.2-original.embl"),
    ("CONSTRUCTION", "pcc7002-D13971.1.embl"),
    ("CONSTRUCTION", "sequence-defined-construction.json"),
    ("MATERIAL", "construct-options.json"),
    ("MATERIAL", "rbcX-Q44177.json"),
    ("RATIONALE", "conditional_witness.py"),
    ("RATIONALE", "donor-contrast-authentication.json"),
    ("RATIONALE", "exact-conditional-rationale.json"),
)
ORIGINAL_SOURCE_DIGESTS = {
    "gp-expression-patent.html": "486bbec9c1c1736d6eb92de3f7db957e3fb0a22888db4e1c10e69493ab88b61b",
    "pUC19-M77789.2-original.embl": "dbbad17ccf47e48cb16d12630fb22b023c7add9deb4fbccb32957d5c804610b9",
    "pcc7002-D13971.1.embl": "ef59a915672ad4fe95ce01527deedd55ce637ee18122dab513a3903e45646822",
    "rbcX-Q44177.json": "fed7dbe6faf25c9fc8fe848ab60792fd1e5bf0d1933d9d954a4818308b4eb0e1",
}
PROCESSING_GATE = "VERIFY_N_TERMINAL_PROCESSING_BEFORE_ENDPOINT_ASSAYS"
PROPOSAL_STATUS = "PROPOSED_NOT_ENTERED"
BIOLOGY = "UNEVALUABLE"
AMINO = frozenset("ACDEFGHIKLMNPQRSTVWY")


def identity(record):
    key = next(
        name
        for name in ("input_id", "config_id", "product_id", "assessment_id")
        if hasattr(record, name)
    )
    return ObjectIdentity.from_record(getattr(record, key), record)


def sequence(value):
    if not value or set(value) - AMINO:
        raise ValueError("nomination requires a full exact amino-acid sequence")


@dataclass(frozen=True, slots=True)
class NominationSourceMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/source-member"
    )
    role: str
    filename: str
    original_url: str
    source_sha256: str
    raw_utf8: str

    def __post_init__(self):
        if self.role not in SOURCE_ROLES or "/" in self.filename or not self.filename:
            raise ValueError(
                "nomination source role or filename is outside its exact contract"
            )
        validate_nonempty(self.original_url, field_name="original_url")
        validate_sha256(self.source_sha256)
        if sha256(self.raw_utf8.encode()).hexdigest() != self.source_sha256:
            raise ValueError("nomination source original-byte substitution")


@dataclass(frozen=True, slots=True)
class AssayPreparationProposal(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/paired-assay-proposal"
    )
    control_material_ids: tuple[str, ...]
    control_preparation: str
    expression_assembly_activation_purification: str
    temperature_ph_gas_conventions: str
    active_site_quantification: str
    independent_preparation_accounting: str
    replication_and_uncertainty: str
    inactive_failed_preparation_policy: str
    endpoints: tuple[str, ...] = TARGETS
    status: str = PROPOSAL_STATUS
    actual_assay_ids: tuple[str, ...] = ()
    physical_independent_units: int = 0

    def __post_init__(self):
        if (
            self.endpoints != TARGETS
            or self.status != PROPOSAL_STATUS
            or self.actual_assay_ids
            or self.physical_independent_units != 0
            or not self.control_material_ids
            or tuple(sorted(set(self.control_material_ids)))
            != self.control_material_ids
        ):
            raise ValueError(
                "nomination cannot omit paired targets or fabricate assay entry/physical units"
            )
        for name in self.control_material_ids:
            validate_stable_id(name)
        for name in (
            "control_preparation",
            "expression_assembly_activation_purification",
            "temperature_ph_gas_conventions",
            "active_site_quantification",
            "independent_preparation_accounting",
            "replication_and_uncertainty",
            "inactive_failed_preparation_policy",
        ):
            validate_nonempty(getattr(self, name), field_name=name)


@dataclass(frozen=True, slots=True)
class NominationPreparationSource(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-nomination-preparation/source"
    input_id: str
    macro_source: ObjectIdentity
    cycle_outcome: ObjectIdentity
    proposed_material_id: str
    source_candidate_id: str
    lsu_sequence: str
    source_ssu_view: str
    reported_ssu_sequence: str
    proposed_m1_ssu_sequence: str
    source_members: tuple[NominationSourceMember, ...]
    assay: AssayPreparationProposal
    conditional_rationale: str
    adverse_rationale: str
    decision_provenance: str
    alternative_ids: tuple[str, ...] = ALTERNATIVES
    processing_gate: str = PROCESSING_GATE
    stoichiometry: str = "PROPOSED_L8S8_NOT_REVALIDATED"
    target_biology: str = BIOLOGY
    exploratory_status: str = "EXPLORATORY_HIGH_RISK_TEST_NOMINEE_NOT_TARGET_QUALIFIED"
    measured_mutant_turnover_s_inv: Decimal | None = None
    measured_mutant_specificity: Decimal | None = None
    biological_qualification: bool = False
    submitted: bool = False

    def __post_init__(self):
        from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import (
            CycleUseProduct,
        )
        from empirical_lawhood.adapters.methods.rubisco_portfolio_inquiry.science import (
            SourceAudit,
        )

        for name in ("input_id", "proposed_material_id"):
            validate_stable_id(getattr(self, name))
        for item in (
            self.lsu_sequence,
            self.reported_ssu_sequence,
            self.proposed_m1_ssu_sequence,
        ):
            sequence(item)
        if (
            self.source_candidate_id != CANDIDATE_ID
            or self.source_ssu_view not in ("m1", "v1")
            or len(self.reported_ssu_sequence) != 138
            or len(self.proposed_m1_ssu_sequence) != 138
            or self.macro_source.object_schema != SourceAudit.SCHEMA
            or self.cycle_outcome.object_schema != CycleUseProduct.SCHEMA
            or self.proposed_m1_ssu_sequence != "M" + self.reported_ssu_sequence[1:]
            or self.alternative_ids != ALTERNATIVES
            or self.processing_gate != PROCESSING_GATE
            or self.stoichiometry != "PROPOSED_L8S8_NOT_REVALIDATED"
            or self.target_biology != BIOLOGY
            or self.exploratory_status
            != "EXPLORATORY_HIGH_RISK_TEST_NOMINEE_NOT_TARGET_QUALIFIED"
            or self.measured_mutant_turnover_s_inv is not None
            or self.measured_mutant_specificity is not None
            or self.biological_qualification
            or self.submitted
        ):
            raise ValueError(
                "nomination substitutes material view or promotes unmeasured/unqualified target biology"
            )
        if (
            tuple((m.role, m.filename) for m in self.source_members) != SOURCE_CENSUS
            or len({m.filename for m in self.source_members})
            != len(self.source_members)
            or set(m.role for m in self.source_members) != set(SOURCE_ROLES)
        ):
            raise ValueError(
                "nomination omits exact material/construction/assay/rationale source census"
            )
        self.assay.__post_init__()
        for m in self.source_members:
            m.__post_init__()
            if (
                m.filename in ORIGINAL_SOURCE_DIGESTS
                and m.source_sha256 != ORIGINAL_SOURCE_DIGESTS[m.filename]
            ):
                raise ValueError(
                    "nomination replaces selected original construction source bytes"
                )
        for name in (
            "source_ssu_view",
            "conditional_rationale",
            "adverse_rationale",
            "decision_provenance",
        ):
            validate_nonempty(getattr(self, name), field_name=name)


def scope(source):
    return ScientificConditionScope(
        "system.rubisco-nomination.gp-i95m",
        "world.rubisco-nomination.exploratory-preparation",
        source.input_id,
        ("prepared-dossier", "specificity", "turnover"),
        ("dimensionless", "dimensionless", "s^-1"),
        "receiver.exploratory-test-nomination-not-assay",
        "clock.exposed-nomination-preparation",
        "Exact proposed Gp I95M material and paired-assay proposal; exposed source and conditional mechanism evidence only, biological target admission UNEVALUABLE.",
        source_config_sha256=source.fingerprint(),
        instance_id=source.proposed_material_id,
    )


@dataclass(frozen=True, slots=True)
class NominationTargetFinding(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/target-finding"
    )
    candidate_id: str
    reference_view: str
    turnover_s_inv: Decimal | None
    specificity: Decimal | None
    turnover_ratio: Decimal | None
    specificity_ratio: Decimal | None
    historical_point_joint_pass: bool | None
    source_pairing_and_processing: str
    biological_admission: str = BIOLOGY

    def __post_init__(self):
        if self.biological_admission != BIOLOGY:
            raise ValueError(
                "historical numerical view cannot manufacture biological target admission"
            )


@dataclass(frozen=True, slots=True)
class NominationRationaleCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/conditional-rationale-case"
    )
    case_id: str
    turnover_multiplier: Decimal
    specificity_multiplier: Decimal
    conditional_turnover: Decimal
    conditional_specificity: Decimal
    target_joint_pass: tuple[tuple[str, bool], ...]
    stationary_checks: int

    def __post_init__(self):
        if self.stationary_checks != 14 or tuple(
            name for name, _ in self.target_joint_pass
        ) != ("coupled", "radiometric"):
            raise ValueError(
                "nomination rationale case drops its exact reference/check denominator"
            )
        for q in (
            self.turnover_multiplier,
            self.specificity_multiplier,
            self.conditional_turnover,
            self.conditional_specificity,
        ):
            if not q.is_finite() or q <= 0:
                raise ValueError(
                    "nomination rationale requires positive finite hypothetical quantities"
                )


@dataclass(frozen=True, slots=True)
class NominationRationaleAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/conditional-rationale-assessment"
    )
    assessment_id: str
    source_sha256: str
    cases: tuple[NominationRationaleCase, ...]
    independent_stationary_checks: int
    interpretation: str
    target_biology: str

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        validate_sha256(self.source_sha256)
        expected = (
            "donor-nominal-compatibility",
            "gp-sufficient-unmeasured-headroom",
            "gp-donor-speed-headroom-insufficient",
            "gp-oxygen-recapture-larger-specificity-loss",
            "gp-mutation-no-release-effect",
        )
        if (
            tuple(c.case_id for c in self.cases) != expected
            or self.independent_stationary_checks != 70
            or self.interpretation
            != "CONDITIONAL_MATHEMATICAL_WITNESS_NOT_MUTATION_PREDICTION"
            or self.target_biology != BIOLOGY
        ):
            raise ValueError(
                "nomination rationale omits adverse cases or promotes conditional prediction"
            )
        for c in self.cases:
            c.__post_init__()


@dataclass(frozen=True, slots=True)
class NominationDossier(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/exploratory-dossier"
    )
    product_id: str
    preparation: NominationPreparationSource
    cycle_outcome: ObjectIdentity
    target_findings: tuple[NominationTargetFinding, ...]
    prior_model_reason_codes: tuple[str, ...]
    prior_model_scope: ScientificConditionScope
    rationale_assessment: NominationRationaleAssessment
    conditional_mechanism_denominator: int
    scope: ScientificConditionScope
    disposition: AssessmentDisposition
    biological_disposition: AssessmentDisposition = AssessmentDisposition.UNEVALUABLE
    reason_codes: tuple[str, ...] = (
        "EXPLORATORY_TEST_NOMINEE_ONLY",
        "I95M_TARGET_ASSAYS_MISSING",
        "M1_PROCESSING_VERIFICATION_REQUIRED",
        "MUTATION_TO_MICRORATES_UNIDENTIFIED",
        "NO_EXTERNAL_SUBMISSION",
    )

    def __post_init__(self):
        validate_stable_id(self.product_id)
        self.preparation.__post_init__()
        self.rationale_assessment.__post_init__()
        if self.rationale_assessment.source_sha256 not in {
            m.source_sha256
            for m in self.preparation.source_members
            if m.role == "RATIONALE"
        }:
            raise ValueError(
                "nomination rationale assessment loses exact source identity"
            )
        from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import (
            UNKNOWN_REASONS,
        )

        if (
            self.prior_model_reason_codes != UNKNOWN_REASONS
            or self.conditional_mechanism_denominator != 864
        ):
            raise ValueError(
                "nomination drops original model unknowns or full conditional denominator"
            )
        if (
            self.cycle_outcome != self.preparation.cycle_outcome
            or self.scope != scope(self.preparation)
            or self.disposition is not AssessmentDisposition.SATISFIED
            or self.biological_disposition is not AssessmentDisposition.UNEVALUABLE
            or self.reason_codes
            != (
                "EXPLORATORY_TEST_NOMINEE_ONLY",
                "I95M_TARGET_ASSAYS_MISSING",
                "M1_PROCESSING_VERIFICATION_REQUIRED",
                "MUTATION_TO_MICRORATES_UNIDENTIFIED",
                "NO_EXTERNAL_SUBMISSION",
            )
        ):
            raise ValueError(
                "nomination dossier changes exact preparation or promotes biological qualification"
            )
        candidates = tuple(sorted((CANDIDATE_ID, *ALTERNATIVES)))
        if tuple(
            (r.candidate_id, r.reference_view) for r in self.target_findings
        ) != tuple((c, r) for c in candidates for r in ("coupled", "radiometric")):
            raise ValueError(
                "nomination dossier omits unknown/adverse candidate or reference denominator"
            )
        for row in self.target_findings:
            row.__post_init__()
            if row.candidate_id == CANDIDATE_ID and any(
                v is not None
                for v in (
                    row.turnover_s_inv,
                    row.specificity,
                    row.turnover_ratio,
                    row.specificity_ratio,
                    row.historical_point_joint_pass,
                )
            ):
                raise ValueError(
                    "nomination dossier fabricates I95M target measurements"
                )


@dataclass(frozen=True, slots=True)
class NominationOperationConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = (
        "empirical-lawhood/rubisco-nomination-preparation/operation-config"
    )
    config_id: str
    preparation: NominationPreparationSource
    cycle_scope: ScientificConditionScope
    operands: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (
            self.config_id != "config." + NAMESPACE + ".prepare"
            or self.operands
            != tuple(
                sorted(
                    (
                        identity(self.preparation),
                        self.preparation.macro_source,
                        self.preparation.cycle_outcome,
                    ),
                    key=lambda r: r.object_id,
                )
            )
        ):
            raise ValueError(
                "nomination config substitutes exact prepared source or prior outcome"
            )
