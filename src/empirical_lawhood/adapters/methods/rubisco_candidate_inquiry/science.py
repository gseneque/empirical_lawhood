# SPDX-License-Identifier: MPL-2.0
"""Source-bound conditional transport necessities; no biological effect inference."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from math import exp, log
import csv
import io
import json
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
    WilsonArticleInputV1, TeParentGenbankInputV1, decode_source,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import WilsonMutantPanelV1
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .source_manifest import RECIPES, SOURCE_MANIFEST

D = Decimal
QUESTION = 'Which source-bound conditional Gp I95M transfer sensitivities meet both separate reference scenarios, and what candidate disposition follows?'
UNIT = 'rubisco-candidate-inquiry.exposed-source-analysis'
CUTOFF = 'exposed-through-2026-10-10-read-2026-10-11'
ALPHA_K = tuple(map(D, ('0', '0.5', '1', '2', '3', '4')))
ALPHA_S = tuple(map(D, ('-1', '0', '1')))
REFERENCES = (('historical-radiometric-conditional', D('5.46')), ('historical-coupled-conditional', D('3.70')))
UNRESOLVED = ('ACTUAL_GP_I95M_ENDPOINTS_UNKNOWN', 'GP_PREPARATION_UNRESOLVED', 'MATCHED_ASSAY_PREPARATION_UNRESOLVED', 'GTG_INITIATION_M1_V1_UNRESOLVED')


@dataclass(frozen=True, slots=True)
class SourceBytes(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/source-bytes'
    source_id: str
    size_bytes: int
    source_sha256: str
    raw_utf8: str

    def __post_init__(self):
        raw = self.raw_utf8.encode('utf-8')
        if (self.source_id, self.size_bytes, self.source_sha256) not in tuple(v[:3] for v in SOURCE_MANIFEST):
            raise ValueError('unselected source identity')
        if len(raw) != self.size_bytes or sha256(raw).hexdigest() != self.source_sha256:
            raise ValueError('source bytes or digest substitution')


@dataclass(frozen=True, slots=True)
class SourceAudit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/source-audit'
    input_id: str
    sources: tuple[SourceBytes, ...]
    cutoff: str = CUTOFF

    def __post_init__(self):
        validate_stable_id(self.input_id, field_name='input_id')
        if self.cutoff != CUTOFF or tuple((v.source_id, v.size_bytes, v.source_sha256) for v in self.sources) != tuple(v[:3] for v in SOURCE_MANIFEST):
            raise ValueError('source census, historical bytes or exposure cutoff substitution')
        for value in self.sources:
            SourceBytes(value.source_id, value.size_bytes, value.source_sha256, value.raw_utf8)

    def text(self, source_id):
        return next(v.raw_utf8 for v in self.sources if v.source_id == source_id)


def source_audit_from_bytes(raw_sources, *, input_id='input.rubisco-candidate.source-audit'):
    """Decode caller-selected original bytes without filesystem/source discovery."""
    if set(raw_sources) != {v[0] for v in SOURCE_MANIFEST}:
        raise ValueError('exact original/dependency source-key census differs')
    values = tuple(SourceBytes(source_id, size, digest, raw_sources[source_id].decode('utf-8'))
                   for source_id, size, digest, _ in SOURCE_MANIFEST)
    return SourceAudit(input_id, values)


def authentic_panel(audit):
    article = next(v for v in audit.sources if v.source_id == 'wilson2017-jbc.html')
    genbank = next(v for v in audit.sources if v.source_id == 'te-MG000148.gb')
    panel, _ = decode_source(WilsonArticleInputV1('input.rubisco-candidate.article', article.source_sha256, article.raw_utf8),
                             TeParentGenbankInputV1('input.rubisco-candidate.genbank', genbank.source_sha256, genbank.raw_utf8))
    if len(panel.rows) != 19:
        raise ValueError('complete authentic Wilson nineteen-row denominator differs')
    return panel


@dataclass(frozen=True, slots=True)
class ProteinRecipe(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/protein-recipe'
    sequence_id: str
    sequence_ascii: str
    length: int
    sha256_ascii: str
    source_accession: str
    role: str

    def __post_init__(self):
        if (self.sequence_id, self.sequence_ascii, self.length, self.sha256_ascii, self.source_accession, self.role) not in RECIPES:
            raise ValueError('wrong exact sequence recipe or source accession')
        if len(self.sequence_ascii) != self.length or sha256(self.sequence_ascii.encode('ascii')).hexdigest() != self.sha256_ascii:
            raise ValueError('protein recipe byte identity differs')


def recipes(audit, panel):
    result = tuple(ProteinRecipe(*v) for v in RECIPES)
    by_id = {v.sequence_id: v.sequence_ascii for v in result}
    native_lsu = json.loads(audit.text('followup-reference2.galdieria-O98949.json'))['sequence']['value']
    native_ssu = json.loads(audit.text('galdieria-O98950.json'))['sequence']['value']
    views = json.loads(audit.text('followup-reference2.galdieria-reference-sequence-inspection.json'))['paired_views']
    structural_ssu = views[1]['pdb_canonical_sequence']
    if (by_id['gp.lsu'] != native_lsu or by_id['gp.ssu.m1'] != native_ssu or by_id['gp.ssu.v1'] != structural_ssu
            or native_ssu[94] != 'I' or by_id['gp.ssu.i95m.m1'] != native_ssu[:94] + 'M' + native_ssu[95:]
            or by_id['gp.ssu.i95m.v1'] != structural_ssu[:94] + 'M' + structural_ssu[95:]):
        raise ValueError('Gp native parent or mutation identity differs')
    mapped = json.loads(audit.text('followup-plant4.te-galdieria-ssu-correspondence-inspection.json'))['correspondence_conclusion']['mapped_native_site']
    if (mapped['Galdieria_sequence_position_1based'], mapped['native_residue'], mapped['1BWV_author_position'], mapped['Te_sequence_position_1based'], mapped['Te_native_residue']) != (95, 'I', 112, 98, 'V'):
        raise ValueError('source correspondence differs')
    for row_id, prefix in ((12, 'te.p415a'), (17, 'te.p415a-v98m')):
        row = next(v for v in panel.rows if v.native_table_row.ordinal_0based == row_id)
        assembly = row.te_protein_specification
        if by_id[prefix + '.lsu'] != assembly.large_subunit_sequence or by_id[prefix + '.ssu'] != assembly.small_subunit_sequence:
            raise ValueError('Te recipe differs from authentic native row assembly')
    return result


def baseline(audit, panel):
    # Re-read raw catalogue, not the coordinator's quoted operands.
    catalogue = audit.text('flamholz-rubisco-data-DatasetS1_SourceRubiscoKinetics.csv')
    gp = next(row for row in csv.DictReader(io.StringIO(catalogue)) if row['identifier'] == 'partita_tokara_uemura')
    if (gp['species'], gp['vC'], gp['S'], gp['temp_C'], gp['pH']) != ('Galdieria partita Tokara', '1.6', '238', '25', '8'):
        raise ValueError('source-conditioned Gp catalogue operands differ')
    native = json.loads(audit.text('followup-reference2.sharwood2016-native-inspection.json'))
    table = next(v for v in native['native_tables'] if v['preceding_source_id'] == 'T1')
    maize = next(v for v in table['rows'] if v[0]['native_text'] == 'Z. mays')
    if tuple(v['native_text'] for v in maize[2:6]) != ('3.70±0.10 d', 'n=9', '5.46±0.10 d', 'n=6'):
        raise ValueError('distinct maize native assay operands differ')
    donors = tuple(next(v for v in panel.rows if v.native_table_row.ordinal_0based == row_id) for row_id in (12, 17))
    observed = tuple((v.endpoint('KCAT_C').mean, v.endpoint('SPECIFICITY_CO').mean) for v in donors)
    if observed != ((D('6.9'), D('52.6')), (D('9.5'), D('56.3'))):
        raise ValueError('source-bound exact two-endpoint donor contrast differs')
    return D(gp['vC']), D(gp['S']), observed


def original_source_scope(audit):
    return ScientificConditionScope('system.rubisco-candidate.original-sources', 'world.rubisco-candidate.initial-knowledge',
        audit.input_id, ('original-source-bytes',), ('byte',), 'receiver.authenticated-source-audit',
        'clock.exposed-through-2026-10-10',
        'Eleven selected original/retained sources with exact dependency bytes and sequence/assay contexts; retained interpretation adds no independent biological measurement, transport result or conditional threshold assessment.',
        source_config_sha256=audit.fingerprint())


def scope(audit):
    return ScientificConditionScope('system.rubisco-candidate-inquiry', 'world.rubisco-candidate-inquiry.exposed',
        audit.input_id, ('specificity', 'turnover'), ('dimensionless', 's^-1'),
        'receiver.conditional-reference-scenarios', 'clock.exposed-initial-knowledge',
        'Exact source-bound Te-P415A/SSU-V98M donor contrast and Gp I95M M1/V1 recipes; conditional sensitivities only; complete nineteen Wilson rows, four hypotheses, zero new biological units; actual Gp effects and matched assays unresolved.',
        source_config_sha256=audit.fingerprint(), instance_id=UNIT)


@dataclass(frozen=True, slots=True)
class ConditionalPoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/conditional-point'
    alpha_k: Decimal
    alpha_s: Decimal
    turnover_s_inv: Decimal
    specificity_dimensionless: Decimal


@dataclass(frozen=True, slots=True)
class Threshold(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/threshold'
    reference_view: str
    maize_turnover_s_inv: Decimal
    minimum_turnover_multiplier: Decimal
    alpha_k_required: Decimal
    alpha_s_required: Decimal


def supplier_arithmetic(audit, panel):
    k, s, ((k0, s0), (k1, s1)) = baseline(audit, panel)
    points = tuple(ConditionalPoint(ak, ass, D(repr(float(k) * exp(float(ak) * log(float(k1 / k0))))),
                    D(repr(float(s) * exp(float(ass) * log(float(s1 / s0)))))) for ak in ALPHA_K for ass in ALPHA_S)
    thresholds = tuple(Threshold(view, target, target / k, D(repr(log(float(target / k)) / log(float(k1 / k0)))), D(0)) for view, target in REFERENCES)
    return points, thresholds


@dataclass(frozen=True, slots=True)
class SupplierScopeCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/supplier-scope-check'
    check_id: str
    source: ObjectIdentity
    complete_native_row_count: int
    exact_recipe_count: int
    selected_source_count: int
    new_biological_units: int
    condition: str

    def __post_init__(self):
        validate_stable_id(self.check_id, field_name='check_id')
        if ((self.complete_native_row_count, self.exact_recipe_count, self.selected_source_count, self.new_biological_units) != (19, 9, 11, 0)
                or self.condition != 'SOURCE_SCOPE_COMPLETE_CONDITIONAL_NECESSITIES_ONLY_INDEPENDENT_CONSUMER_REQUIRED'):
            raise ValueError('supplier scope check cannot create biological evidence or discard denominator')


def supplier_scope_check(audit):
    return SupplierScopeCheck('assessment.rubisco-candidate-inquiry.supplier-scope', ObjectIdentity.from_record(audit.input_id, audit),
                              19, 9, 11, 0, 'SOURCE_SCOPE_COMPLETE_CONDITIONAL_NECESSITIES_ONLY_INDEPENDENT_CONSUMER_REQUIRED')


@dataclass(frozen=True, slots=True)
class CandidateSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/supply'
    product_id: str
    source: SourceAudit
    panel: WilsonMutantPanelV1
    protein_recipes: tuple[ProteinRecipe, ...]
    points: tuple[ConditionalPoint, ...]
    thresholds: tuple[Threshold, ...]
    check: SupplierScopeCheck
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        validate_stable_id(self.product_id, field_name='product_id')
        SourceAudit(self.source.input_id, self.source.sources, self.source.cutoff)
        if self.panel != authentic_panel(self.source) or self.protein_recipes != recipes(self.source, self.panel):
            raise ValueError('supplier source panel or recipes differ')
        if (self.points, self.thresholds) != supplier_arithmetic(self.source, self.panel) or self.check != supplier_scope_check(self.source) or self.scope != scope(self.source) or self.disposition is not AssessmentDisposition.SATISFIED:
            raise ValueError('supplier conditional mathematics or scope differs')


def supply(source):
    panel = authentic_panel(source)
    points, thresholds = supplier_arithmetic(source, panel)
    return CandidateSupply('product.rubisco-candidate-inquiry.supply', source, panel, recipes(source, panel), points, thresholds, supplier_scope_check(source), scope(source), AssessmentDisposition.SATISFIED)


@dataclass(frozen=True, slots=True)
class CandidateEntry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/candidate-entry'
    candidate_id: str
    ssu_view: str
    lsu_sequence_id: str
    ssu_sequence_id: str
    assembly: str
    turnover_s_inv: Decimal | None
    specificity_dimensionless: Decimal | None


@dataclass(frozen=True, slots=True)
class CandidateFrontierInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/frontier-input'
    instance_id: str
    candidates: tuple[CandidateEntry, ...]
    references: tuple[str, ...] = tuple(v[0] for v in REFERENCES)
    conditional_only: bool = True

    def __post_init__(self):
        validate_stable_id(self.instance_id, field_name='instance_id')


def authentic_candidate(supplier):
    entries = tuple(CandidateEntry(candidate, view, 'gp.lsu', f'gp.ssu.{suffix}{view}', 'homogeneous L8S8',
                      D('1.6') if candidate == 'gp.wt' else None, D(238) if candidate == 'gp.wt' else None)
                    for candidate, suffix in (('gp.wt', ''), ('gp.i95m', 'i95m.')) for view in ('m1', 'v1'))
    donors = tuple(CandidateEntry(candidate, 'native', candidate + '.lsu', candidate + '.ssu', 'homogeneous L8S8', row.endpoint('KCAT_C').mean, row.endpoint('SPECIFICITY_CO').mean)
                   for candidate, row_id in (('te.p415a', 12), ('te.p415a-v98m', 17))
                   for row in supplier.panel.rows if row.native_table_row.ordinal_0based == row_id)
    return CandidateFrontierInput('instance.rubisco-candidate-inquiry.portfolio', entries + donors)


@dataclass(frozen=True, slots=True)
class FrontierRow(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/frontier-row'
    reference_view: str
    alpha_k: Decimal
    alpha_s: Decimal
    turnover_s_inv: Decimal
    specificity_dimensionless: Decimal
    turnover_ratio: Decimal
    specificity_ratio: Decimal
    joint_conditional_pass: bool
    conditional_nondominated_candidate_views: tuple[str, ...]

    def __post_init__(self):
        references = dict(REFERENCES)
        if self.reference_view not in references or self.alpha_k not in ALPHA_K or self.alpha_s not in ALPHA_S:
            raise ValueError('frontier changes exact reference/grid identity')
        with localcontext() as context:
            context.prec = 50
            k = D('1.6') * (D('9.5') / D('6.9')) ** self.alpha_k
            s = D(238) * (D('56.3') / D('52.6')) ** self.alpha_s
            rk, rs = k / references[self.reference_view], s / D(238)
        if ((self.turnover_s_inv, self.specificity_dimensionless, self.turnover_ratio, self.specificity_ratio) != (k, s, rk, rs)
                or self.joint_conditional_pass is not (rk >= 1 and rs >= 1)
                or tuple(sorted(set(self.conditional_nondominated_candidate_views))) != self.conditional_nondominated_candidate_views):
            raise ValueError('frontier changes independent conditional endpoints or joint ratios')


@dataclass(frozen=True, slots=True)
class CandidateVerdict(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/candidate-verdict'
    candidate_id: str
    ssu_view: str
    reference_view: str
    disposition: AssessmentDisposition
    turnover_ratio: Decimal | None
    specificity_ratio: Decimal | None
    biological_admission: str


def _near(left, right):
    return abs(left - right) <= D('1e-12') * max(D(1), abs(right))


def conditional_frontier(instance, oracle_k, oracle_s):
    # Only this explicit mathematical scenario substitutes the unknown mutant
    # phenotype. The separate actual-candidate verdict remains UNEVALUABLE.
    candidates = []
    for candidate in instance.candidates:
        k, s = ((oracle_k, oracle_s) if candidate.candidate_id == 'gp.i95m' else
                (candidate.turnover_s_inv, candidate.specificity_dimensionless))
        if k is not None and s is not None:
            candidates.append((candidate.candidate_id + '.' + candidate.ssu_view, k, s))
    return tuple(sorted(identifier for identifier, k, s in candidates
                       if not any(other_k >= k and other_s >= s and (other_k > k or other_s > s)
                                  for _, other_k, other_s in candidates)))


def consumer_arithmetic(supplier, instance):
    expected = authentic_candidate(supplier)
    if instance.references != expected.references or instance.conditional_only is not True:
        return (), (), (), AssessmentDisposition.REFUSED, ('WRONG_REFERENCE_OR_UNCONDITIONAL_ADMISSION',)
    def assembly(v):
        return (v.candidate_id, v.ssu_view, v.lsu_sequence_id, v.ssu_sequence_id, v.assembly)
    if tuple(map(assembly, instance.candidates)) != tuple(map(assembly, expected.candidates)):
        return (), (), (), AssessmentDisposition.REFUSED, ('WRONG_CANDIDATE_ASSEMBLY_OR_ROSTER',)
    for actual, target in zip(instance.candidates, expected.candidates, strict=True):
        for name in ('turnover_s_inv', 'specificity_dimensionless'):
            if getattr(actual, name) is not None and getattr(actual, name) != getattr(target, name):
                return (), (), (), AssessmentDisposition.REFUSED, ('UNSUPPORTED_BIOLOGICAL_ENDPOINT',)
    k, s, ((k0, s0), (k1, s1)) = baseline(supplier.source, supplier.panel)
    rows, thresholds, verdicts = [], [], []
    with localcontext() as context:
        context.prec = 50
        kr, sr = k1 / k0, s1 / s0
        for supplied in supplier.thresholds:
            threshold = (supplied.maize_turnover_s_inv / k).ln() / kr.ln()
            if not _near(supplied.alpha_k_required, threshold) or supplied.alpha_s_required != 0:
                return (), (), (), AssessmentDisposition.FALSIFIED, ('INDEPENDENT_THRESHOLD_ORACLE_MISMATCH',)
            thresholds.append(Threshold(supplied.reference_view, supplied.maize_turnover_s_inv, supplied.maize_turnover_s_inv / k, threshold, D(0)))
        for point in supplier.points:
            oracle_k, oracle_s = k * kr ** point.alpha_k, s * sr ** point.alpha_s
            if not _near(point.turnover_s_inv, oracle_k) or not _near(point.specificity_dimensionless, oracle_s):
                return (), (), (), AssessmentDisposition.FALSIFIED, ('INDEPENDENT_POWER_ORACLE_MISMATCH',)
            for view, target in REFERENCES:
                r_k, r_s = oracle_k / target, oracle_s / s
                rows.append(FrontierRow(view, point.alpha_k, point.alpha_s, oracle_k, oracle_s, r_k, r_s, r_k >= 1 and r_s >= 1,
                            conditional_frontier(instance, oracle_k, oracle_s)))
        for candidate in instance.candidates:
            for view, target in REFERENCES:
                if candidate.turnover_s_inv is None or candidate.specificity_dimensionless is None:
                    disposition, rk, rs = AssessmentDisposition.UNEVALUABLE, None, None
                else:
                    rk, rs = candidate.turnover_s_inv / target, candidate.specificity_dimensionless / s
                    disposition = AssessmentDisposition.SATISFIED if rk >= 1 and rs >= 1 else AssessmentDisposition.FALSIFIED
                verdicts.append(CandidateVerdict(candidate.candidate_id, candidate.ssu_view, view, disposition, rk, rs,
                                'UNEVALUABLE_MATCHED_ASSAY_PREPARATION'))
    return tuple(rows), tuple(thresholds), tuple(verdicts), AssessmentDisposition.SATISFIED, ()


@dataclass(frozen=True, slots=True)
class CandidateAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-candidate-inquiry/assessment'
    assessment_id: str
    supplier: ObjectIdentity
    scope: ScientificConditionScope
    instance: CandidateFrontierInput
    frontier: tuple[FrontierRow, ...]
    independently_checked_thresholds: tuple[Threshold, ...]
    candidate_verdicts: tuple[CandidateVerdict, ...]
    disposition: AssessmentDisposition
    reason_codes: tuple[str, ...]
    candidate_decision: str
    unresolved: tuple[str, ...] = UNRESOLVED
    comparison: str = 'UNEVALUATED'
    nominee: str | None = None

    def __post_init__(self):
        validate_stable_id(self.assessment_id, field_name='assessment_id')
        if self.unresolved != UNRESOLVED or self.comparison != 'UNEVALUATED' or self.nominee is not None:
            raise ValueError('conditional consumer cannot create biological nomination or comparison evidence')
        if self.disposition is AssessmentDisposition.SATISFIED:
            if len(self.frontier) != 36 or len(self.independently_checked_thresholds) != 2 or len(self.candidate_verdicts) != 12:
                raise ValueError('consumer loses complete nested scenario or candidate denominator')
            if self.candidate_decision != 'RETAIN_EXPLORATORY_I95M_REQUIRE_MATCHED_CANDIDATE_BACKGROUND_KINETICS_REJECT_UNIT_TRANSFER_NOMINATION_AND_ASSAY_SUBSTITUTION':
                raise ValueError('consumer changes supported candidate disposition')
        elif not self.reason_codes or self.frontier or self.independently_checked_thresholds or self.candidate_verdicts:
            raise ValueError('adverse consumer result must preserve reason without fabricated ratios')


def assess(supplier, instance):
    CandidateSupply(supplier.product_id, supplier.source, supplier.panel, supplier.protein_recipes, supplier.points,
                    supplier.thresholds, supplier.check, supplier.scope, supplier.disposition)
    rows, thresholds, verdicts, disposition, reasons = consumer_arithmetic(supplier, instance)
    decision = ('RETAIN_EXPLORATORY_I95M_REQUIRE_MATCHED_CANDIDATE_BACKGROUND_KINETICS_REJECT_UNIT_TRANSFER_NOMINATION_AND_ASSAY_SUBSTITUTION'
                if disposition is AssessmentDisposition.SATISFIED else 'RETAIN_ADVERSE_SCOPED_RESULT_NO_NOMINATION')
    return CandidateAssessment('assessment.rubisco-candidate-inquiry.use', ObjectIdentity.from_record(supplier.product_id, supplier),
                               supplier.scope, instance, rows, thresholds, verdicts, disposition, reasons, decision)
