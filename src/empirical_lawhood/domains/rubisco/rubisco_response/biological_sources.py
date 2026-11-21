# SPDX-License-Identifier: MPL-2.0
"""Closed retained source census for biological support, without new observations."""

from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_combinations.source_binding import TeParentGenbankInputV1, WilsonArticleInputV1, decode_source
from empirical_lawhood.domains.rubisco.rubisco_nomination_preparation.contracts import AssayPreparationProposal
from empirical_lawhood.domains.rubisco.rubisco_portfolio_inquiry.science import CUTOFF, Candidate, SourceAudit, complete_candidate_roster
from empirical_lawhood.domains.rubisco.rubisco_portfolio_inquiry.source_manifest import INITIAL_CANDIDATE_IDS, SOURCE_MANIFEST
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import WilsonMutantPanelV1, WilsonMutantRowV1
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.nomination_reuse import NominationReuseAssessment, assess_retained_nomination, nomination_donor_rows


@dataclass(frozen=True, slots=True)
class ExposedBiologicalSources(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-response/exposed-biological-sources"
    evidence_id: str
    source_audit: ObjectIdentity
    source_members: tuple[tuple[str, str, int, str], ...]
    nomination: NominationReuseAssessment
    candidates: tuple[Candidate, ...]
    wilson_panel: WilsonMutantPanelV1
    matched_donor_rows: tuple[WilsonMutantRowV1, WilsonMutantRowV1]
    assay_proposal: AssayPreparationProposal
    original_cutoff: str = CUTOFF
    exposure: str = "EXPOSED_SOURCE_AND_NOMINATION_DEVELOPMENT_NOT_INDEPENDENT_VALIDATION"
    new_biological_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.evidence_id)
        exact(self.source_audit, ObjectIdentity)
        exact(self.nomination, NominationReuseAssessment)
        if (self.source_audit.object_schema != SourceAudit.SCHEMA
                or self.source_audit.object_version != SourceAudit.VERSION
                or self.source_members != SOURCE_MANIFEST or self.original_cutoff != CUTOFF):
            raise ValueError("biological source census changes its closed original bytes or exposure cutoff")
        if (type(self.candidates) is not tuple
                or tuple(row.candidate_id for row in self.candidates) != INITIAL_CANDIDATE_IDS):
            raise ValueError("biological source census drops an adverse, unmeasured or parent candidate")
        for row in self.candidates:
            exact(row, Candidate)
        exact(self.wilson_panel, WilsonMutantPanelV1)
        if type(self.matched_donor_rows) is not tuple or len(self.matched_donor_rows) != 2:
            raise ValueError("matched donor requires both original source rows")
        for row in self.matched_donor_rows:
            exact(row, WilsonMutantRowV1)
            if row not in self.wilson_panel.rows:
                raise ValueError("nomination donor differs from the independently decoded original panel")
        before, after = self.matched_donor_rows
        if ((before.native_rbcl_edits, after.native_rbcl_edits, before.native_rbcs_edits, after.native_rbcs_edits)
                != ("P415A", "P415A", "None", "V98M")):
            raise ValueError("donor changes the matched P415A background or isolated SSU intervention")
        for native in self.wilson_panel.rows:
            if native.te_protein_specification is None:
                continue
            row = next(row for row in self.candidates if row.candidate_id == native.sample_id)
            protein = native.te_protein_specification
            if (row.lsu_sequence != protein.large_subunit_sequence
                    or row.ssu_sequence_views != (("native", protein.small_subunit_sequence),)
                    or row.turnover_s_inv != native.endpoint("KCAT_C").mean
                    or row.specificity_dimensionless != native.endpoint("SPECIFICITY_CO").mean
                    or row.turnover_error_token != native.endpoint("KCAT_C").native_token
                    or row.specificity_error_token != native.endpoint("SPECIFICITY_CO").native_token):
                raise ValueError("projected Te source loses original construct, endpoint or standard error")
        exact(self.assay_proposal, AssayPreparationProposal)
        if (self.exposure != "EXPOSED_SOURCE_AND_NOMINATION_DEVELOPMENT_NOT_INDEPENDENT_VALIDATION"
                or type(self.new_biological_units) is not int or self.new_biological_units != 0):
            raise ValueError("source decoding or an unentered proposal cannot create validation units")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.evidence_id, self)


def read_exposed_biological_sources(source_audit, dossier, receipt, *, evidence_id):
    """Authenticate retained original inputs and rederive only their source projections.

    The existing source owner retains all 32 candidate recipes, including absent
    Gp I95M endpoints. The full nineteen-row Wilson panel retains its separate
    four Se controls, native standard errors and unresolved endpoint pairing.
    Archived source scripts and original scientific producers are never run.
    """
    exact(source_audit, SourceAudit)
    nomination = assess_retained_nomination(dossier, receipt, assessment_id=evidence_id + ".nomination")
    source = ObjectIdentity.from_record(source_audit.input_id, source_audit)
    if source != dossier.preparation.macro_source:
        raise ValueError("biological source differs from the nomination's exact original macro source")
    html, parent = (source_audit.named(name) for name in ("wilson2017-jbc.html", "te-MG000148.gb"))
    wilson, _ = decode_source(
        WilsonArticleInputV1(evidence_id + ".wilson", sha256(html).hexdigest(), html.decode()),
        TeParentGenbankInputV1(evidence_id + ".te-parent", sha256(parent).hexdigest(), parent.decode()))
    return ExposedBiologicalSources(evidence_id, source, SOURCE_MANIFEST, nomination,
        complete_candidate_roster(source_audit), wilson, nomination_donor_rows(dossier), dossier.preparation.assay)
