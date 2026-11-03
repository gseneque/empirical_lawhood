# SPDX-License-Identifier: MPL-2.0
"""Source-bound finalist challenge and paired-test proposition, without nomination."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar
from xml.etree import ElementTree

from empirical_lawhood.adapters.methods.rubisco_cycle_constraints.contracts import CycleUseProduct
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition
from empirical_lawhood.kernel.serialization import CanonicalRecord
from .science import REFERENCES, PortfolioAssessment, PortfolioSupply, assess, authentic_candidate

FINALIST_IDS = ('gp.wt', 'nt.a369.t391i', 'potato.ps3', 'potato.pst', 'wilson2017-row17')
YAMORI_BYTES = 139555
YAMORI_SHA256 = '41c3ee13edb2d0cb55287d2852ce849910f9c238ceade7968883f7d6b809aaa5'


@dataclass(frozen=True, slots=True)
class FinalistCase(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/finalist-case'
    candidate_id: str
    candidate: ObjectIdentity
    lsu_sha256: str
    ssu_sequence_views: tuple[tuple[str, str], ...]
    conditional_margins: tuple[tuple[str, Decimal, Decimal], ...]
    finite_release_supporting_families: tuple[tuple[str, int, int], ...]
    observed_recipe_scope: str
    unresolved_preparation: str
    decisive_missing_evidence: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PairedAssayProposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/paired-assay-proposition'
    proposal_id: str
    candidate_ids: tuple[str, ...]
    prospective_materials: tuple[str, ...]
    working_conditions: tuple[str, ...]
    experimental_units: tuple[str, ...]
    endpoints: tuple[str, ...]
    decision_rule: str
    status: str = 'PROPOSED_NOT_ENTERED'

    def __post_init__(self):
        if (self.proposal_id != 'proposal.rubisco-finalists.matched-biochemical-assays'
                or self.candidate_ids != FINALIST_IDS or self.status != 'PROPOSED_NOT_ENTERED'
                or not self.prospective_materials or not self.working_conditions
                or not self.experimental_units or not self.endpoints or not self.decision_rule):
            raise ValueError('paired-test proposition cannot change selected scope or claim entered assays')


@dataclass(frozen=True, slots=True)
class FinalistChallenge(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/finalist-challenge'
    challenge_id: str
    portfolio: ObjectIdentity
    kinetic_uses: tuple[ObjectIdentity, ...]
    cases: tuple[FinalistCase, ...]
    new_primary_source: tuple[str, int, str]
    adverse_findings: tuple[str, ...]
    assay_proposition: PairedAssayProposition
    disposition: AssessmentDisposition
    biological_disposition: AssessmentDisposition = AssessmentDisposition.UNEVALUABLE
    nomination: str = 'BOUNDED_SHORTLIST_NO_JOINTLY_SUPPORTED_NOMINEE'
    nominee: str | None = None
    new_biological_units: int = 0

    def __post_init__(self):
        if (self.challenge_id != 'challenge.rubisco-five-finalists.source-and-mechanism'
                or tuple(row.candidate_id for row in self.cases) != FINALIST_IDS
                or len(self.kinetic_uses) != 2
                or self.new_primary_source != ('10.1038/s41467-026-73783-w', YAMORI_BYTES, YAMORI_SHA256)
                or self.disposition is not AssessmentDisposition.SATISFIED
                or self.biological_disposition is not AssessmentDisposition.UNEVALUABLE
                or self.nomination != 'BOUNDED_SHORTLIST_NO_JOINTLY_SUPPORTED_NOMINEE'
                or self.nominee is not None or self.new_biological_units != 0):
            raise ValueError('source/model challenge cannot manufacture nomination or biological qualification')
        self.assay_proposition.__post_init__()


def challenge_finalists(
    supplier: PortfolioSupply, assessment: PortfolioAssessment,
    kinetic_uses: tuple[CycleUseProduct, ...], yamori_original: bytes,
) -> FinalistChallenge:
    """Challenge saved, actually assessed source/model products at their scope.

    Primary-source methods establish an adverse evidence-role distinction. They
    do not provide new paired biochemical labels or calibration of latent rates.
    """
    if assessment != assess(supplier, authentic_candidate(supplier)):
        raise ValueError('finalist challenge requires the exact authentic assessed portfolio')
    if (len(yamori_original) != YAMORI_BYTES
            or sha256(yamori_original).hexdigest() != YAMORI_SHA256):
        raise ValueError('new primary-source bytes differ from the frozen inquiry input')
    article = ElementTree.fromstring(yamori_original)
    doi = tuple(''.join(n.itertext()) for n in article.findall('.//article-id')
                if n.get('pub-id-type') == 'doi')
    paragraphs = tuple(' '.join(''.join(n.itertext()).split()) for n in article.findall('.//p'))
    methods = tuple(p for p in paragraphs if 'To determine in vivo Rubisco' in p)
    if (doi != ('10.1038/s41467-026-73783-w',) or len(methods) != 1
            or 'compensation points' not in methods[0]
            or 'gas exchange rates' not in methods[0]):
        raise ValueError('primary-source specificity methods fail the independent evidence-role check')
    candidates = {row.candidate_id: row for row in supplier.candidates}
    if (len(kinetic_uses) != 2 or kinetic_uses[0].model != kinetic_uses[1].model
            or kinetic_uses[0].supplier != ObjectIdentity.from_record(kinetic_uses[0].model.product_id, kinetic_uses[0].model)
            or kinetic_uses[1].supplier != ObjectIdentity.from_record(kinetic_uses[0].product_id, kinetic_uses[0])
            or kinetic_uses[0].instance.candidate_ids != ('gp.wt', 'wilson2017-row17')
            or kinetic_uses[1].instance.candidate_ids != ('nt.a369.t391i', 'potato.ps3', 'potato.pst')):
        raise ValueError('finalist challenge requires actual compatible first use and subsequent reuse')
    source_identity = ObjectIdentity.from_record(supplier.source.input_id, supplier.source)
    for product in kinetic_uses:
        product.__post_init__()
        if product.instance.macro_source != source_identity:
            raise ValueError('kinetic use changes the actual authenticated macro source')
        if any(anchor.reference not in REFERENCES for anchor in product.anchors):
            raise ValueError('kinetic use changes exact target magnitudes under a reference name')
    cycle_anchors = tuple(row for product in kinetic_uses for row in product.anchors)
    cycle_candidates = {row.candidate.candidate_id: row.candidate for row in cycle_anchors}
    if set(cycle_candidates) != set(FINALIST_IDS):
        raise ValueError('kinetic query does not retain the exact frozen five-finalist denominator')
    cases = []
    for cid in FINALIST_IDS:
        candidate = candidates[cid]
        if cycle_candidates[cid] != candidate:
            raise ValueError('kinetic query has a substituted finalist recipe or endpoint')
        views = tuple(row for row in assessment.candidate_views if row.candidate_id == cid)
        if len(views) != 2 or any(row.point_joint_pass for row in views):
            raise ValueError('frozen negative challenge requires both actual separate reference views')
        anchors = tuple(row for row in cycle_anchors if row.candidate.candidate_id == cid)
        if (len(anchors) != 2
                or {row.reference[0] for row in anchors} != {row.reference_view for row in views}):
            raise ValueError('finalist challenge loses a reference scenario')
        missing = [
            'MATCHED_PAIRED_BIOCHEMICAL_TARGET_ENDPOINTS_AND_REFERENCE_PREPARATIONS',
            'CANDIDATE_LINK_TO_REQUIRED_MICROSCOPIC_CHANGE_UNMEASURED',
        ]
        if cid == 'gp.wt':
            missing.append('HISTORICAL_CATALOGUE_PREPARATION_AND_INITIATION_PROCESSING_JOIN')
        elif cid == 'wilson2017-row17':
            missing.append('SPECIFICITY_GAIN_NOT_INFERABLE_FROM_COMPOUND_SSU_SPEED_EFFECT')
        elif cid.startswith('potato.'):
            missing.append('COMPOUND_SUBUNIT_ASSEMBLY_EFFECT_NOT_IDENTIFIED_AS_INDEPENDENT_SITE_EFFECTS')
        else:
            missing.append('LOCAL_FAVOURABLE_TURNOVER_DIRECTION_DOES_NOT_SUPPLY_REQUIRED_SPECIFICITY')
        cases.append(FinalistCase(
            cid, ObjectIdentity.from_record(cid, candidate),
            sha256(candidate.lsu_sequence.encode('ascii')).hexdigest(),
            tuple((name, sha256(sequence.encode('ascii')).hexdigest())
                  for name, sequence in candidate.ssu_sequence_views),
            tuple((view.reference_view, view.turnover_ratio, view.specificity_ratio) for view in views),
            tuple((row.reference[0], sum(s.necessities.finite_release_can_meet_joint_targets for s in row.scenarios),
                   len(row.scenarios)) for row in anchors),
            candidate.assay_context, candidate.pairing_and_processing, tuple(sorted(missing)),
        ))
    assay = PairedAssayProposition(
        'proposal.rubisco-finalists.matched-biochemical-assays', FINALIST_IDS,
        ('Each exact shortlisted LSU/SSU assembly from saved sequences, with explicitly selected mature processing and tags',
         'A prospectively selected and sequence-verified maize reference assembly and preparation',
         'A prospectively selected and sequence-verified G. partita reference assembly and preparation'),
        ('25 C working comparison, paired candidate/reference batches',
         'Common explicitly frozen pH, activation, gas convention and active-site normalization before acquisition',
         'Quantify functional active-site concentration and retain inactive or failed preparations',
         'Retain homogeneous assembly verification; Gp M1/V1 views require a processing choice before material construction'),
        ('Independent enzyme preparations are the biological units; technical repeats and source/model views are nested',
         'Choose replication and precision prospectively from assay performance; this numerical inquiry fabricates no sample-size guarantee'),
        ('Direct carboxylation turnover per active site with paired maize control',
         'Direct CO2/O2 specificity with paired G. partita control, distinct from leaf gas-exchange inference',
         'Report both ratios, uncertainty, all preparation failures and negative/unevaluable outcomes'),
        'The same exact candidate must satisfy both target ratios; no endpoint compensation or choice of favourable historical assay.',
    )
    return FinalistChallenge(
        'challenge.rubisco-five-finalists.source-and-mechanism',
        ObjectIdentity.from_record(assessment.assessment_id, assessment),
        tuple(ObjectIdentity.from_record(product.product_id, product) for product in kinetic_uses), tuple(cases),
        (doi[0], YAMORI_BYTES, YAMORI_SHA256),
        ('RECENT_ENGINEERING_SPECIFICITY_IS_IN_VIVO_COMPENSATION_POINT_INFERENCE_NOT_PAIRED_ENZYME_LABEL',
         'ALL_FIVE_SAVED_SOURCE_CASES_LACK_AT_LEAST_ONE_CONDITIONAL_JOINT_TARGET_MARGIN',
         'REVERSIBLE_MODEL_POSSIBILITY_DOES_NOT_ASSIGN_A_MICROSCOPIC_GAIN_TO_A_RESIDUE',
         'REPORTED_EXPRESSION_OR_ASSEMBLY_DOES_NOT_ESTABLISH_THE_MATCHED_TARGET_ASSAYS'),
        assay, AssessmentDisposition.SATISFIED,
    )
