# SPDX-License-Identifier: MPL-2.0
"""Authentic portfolios and single-effect interpolation support, never biology forecasts."""
from base64 import b64decode, b64encode
from dataclasses import dataclass
from decimal import Decimal, localcontext
from functools import lru_cache
from hashlib import sha256
from math import log
import json
import re
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry import science as gp_source
from empirical_lawhood.adapters.methods.rubisco_candidate_inquiry.source_manifest import SOURCE_MANIFEST as GP_MANIFEST
from empirical_lawhood.adapters.methods.rubisco_combinations.source_binding import (
    TeParentGenbankInputV1, WilsonArticleInputV1, decode_source,
)
from empirical_lawhood.adapters.physical.rubisco_kinetics.mcdonald2026 import decode_mcdonald2026
from empirical_lawhood.adapters.physical.rubisco_kinetics.wilson2017 import _TableParser
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition, ScientificConditionScope
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from .source_manifest import SOURCE_MANIFEST

D = Decimal
QUESTION = 'Which exact source-supported Rubisco routes lack joint-target support from nonextrapolative observed single-effect interpolation, and what measurements or separately assessed models are needed?'
UNIT = 'rubisco-portfolio-inquiry.exposed-source-analysis'
CUTOFF = 'exposed-through-2026-10-11'
REFERENCES = (('radiometric', D('5.46'), D(238)), ('coupled', D('3.70'), D(238)))
BIOLOGICAL_ADMISSION = 'UNEVALUABLE_MATCHED_PREPARATION_AND_PAIRED_TARGET_ASSAYS'


@dataclass(frozen=True, slots=True)
class SourceBlob(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/source-blob'
    source_id: str
    filename: str
    size_bytes: int
    source_sha256: str
    raw_base64: str

    def __post_init__(self):
        if (self.source_id, self.filename, self.size_bytes, self.source_sha256) not in SOURCE_MANIFEST:
            raise ValueError('source identity is outside this selected original-byte contract')
        raw = self.bytes()
        if len(raw) != self.size_bytes or sha256(raw).hexdigest() != self.source_sha256:
            raise ValueError('source length or original-byte digest substitution')

    def bytes(self):
        return b64decode(self.raw_base64, validate=True)


@dataclass(frozen=True, slots=True)
class SourceAudit(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/source-audit'
    input_id: str
    sources: tuple[SourceBlob, ...]
    selected_candidate_ids: tuple[str, ...]
    cutoff: str = CUTOFF

    def __post_init__(self):
        validate_stable_id(self.input_id)
        if tuple((v.source_id, v.filename, v.size_bytes, v.source_sha256) for v in self.sources) != SOURCE_MANIFEST or self.cutoff != CUTOFF:
            raise ValueError('closed source/dependency census or declared exposure cutoff differs')
        if not self.selected_candidate_ids or self.selected_candidate_ids != tuple(sorted(set(self.selected_candidate_ids))):
            raise ValueError('candidate selection must be explicit, sorted and unique')
        for v in self.sources:
            v.__post_init__()

    def named(self, name):
        values = tuple(v for v in self.sources if v.filename == name)
        if len(values) != 1:
            raise ValueError('named original source is not uniquely selected')
        return values[0].bytes()


def source_audit_from_bytes(raw_sources, *, candidate_ids, input_id='input.rubisco-portfolio.source-audit', cutoff=CUTOFF):
    if set(raw_sources) != {v[0] for v in SOURCE_MANIFEST}:
        raise ValueError('missing or extra selected original source keys')
    blobs = tuple(SourceBlob(i, n, size, digest, b64encode(raw_sources[i]).decode('ascii')) for i, n, size, digest in SOURCE_MANIFEST)
    audit = SourceAudit(input_id, blobs, tuple(candidate_ids), cutoff)
    available = {v.candidate_id for v in _all_candidates(audit)}
    if not set(audit.selected_candidate_ids) <= available:
        raise ValueError('selected candidate has no authentic full recipe and source join')
    return audit


@dataclass(frozen=True, slots=True)
class Candidate(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/candidate'
    candidate_id: str
    background: str
    parent_id: str
    lsu_sequence: str
    ssu_sequence_views: tuple[tuple[str, str], ...]
    turnover_s_inv: Decimal | None
    specificity_dimensionless: Decimal | None
    turnover_native_token: str
    specificity_native_token: str
    turnover_error_token: str
    specificity_error_token: str
    source_identity: str
    source_row: str
    assay_context: str
    pairing_and_processing: str
    assembly: str = 'REPORTED_HOMOGENEOUS_L8S8_NOT_REVALIDATED'
    biological_admission: str = BIOLOGICAL_ADMISSION

    def __post_init__(self):
        validate_stable_id(self.candidate_id)
        validate_stable_id(self.parent_id)
        if (self.assembly != 'REPORTED_HOMOGENEOUS_L8S8_NOT_REVALIDATED' or self.biological_admission != BIOLOGICAL_ADMISSION
                or not self.lsu_sequence or not self.ssu_sequence_views
                or any(set(v) - set('ACDEFGHIKLMNPQRSTVWY') for v in (self.lsu_sequence, *(s for _, s in self.ssu_sequence_views)))):
            raise ValueError('candidate cannot manufacture an assembly, preparation or biological admission')
        for value in (self.turnover_s_inv, self.specificity_dimensionless):
            if value is not None and (not value.is_finite() or value <= 0):
                raise ValueError('candidate endpoint must be positive or explicitly unknown')


def _candidate(cid, bg, pid, lsu, ssu, k, s, kt, st, ke, se, source, row, assay, limits):
    return Candidate(cid, bg, pid, lsu, ssu, k, s, kt, st, ke, se, source, row, assay, limits)


@lru_cache(maxsize=None)
def _all_candidates(audit):
    # Selected canonical panels are comparison aids. Scientific operands are rederived from original bytes.
    wilson, _ = decode_source(
        WilsonArticleInputV1('input.rubisco-portfolio.wilson', sha256(audit.named('wilson2017-jbc.html')).hexdigest(), audit.named('wilson2017-jbc.html').decode()),
        TeParentGenbankInputV1('input.rubisco-portfolio.te-parent', sha256(audit.named('te-MG000148.gb')).hexdigest(), audit.named('te-MG000148.gb').decode()))
    plant = decode_mcdonald2026(*(audit.named(n) for n in ('primary.xml', 'sciadv.aeh3246_table_s4.xlsx', 'sciadv.aeh3246_table_s5.xlsx', 'sciadv.aeh3246_table_s8.xlsx')))
    gp_raw = {}
    for name, _, _, _ in GP_MANIFEST:
        filename = name.split('.', 1)[1] if name.startswith(('followup-plant4.', 'followup-reference2.')) else name
        gp_raw[name] = audit.named(filename)
    gp = gp_source.source_audit_from_bytes(gp_raw)
    gp_panel = gp_source.authentic_panel(gp)
    recipes = {v.sequence_id: v.sequence_ascii for v in gp_source.recipes(gp, gp_panel)}
    gp_k, gp_s, _ = gp_source.baseline(gp, gp_panel)
    result = []
    for row in wilson.rows:
        recipe = row.te_protein_specification
        if recipe is None:
            continue
        k, s = row.endpoint('KCAT_C'), row.endpoint('SPECIFICITY_CO')
        result.append(_candidate(row.sample_id, 'te', 'wilson2017-row8', recipe.large_subunit_sequence, (('native', recipe.small_subunit_sequence),),
            k.mean, s.mean, k.native_token, s.native_token, k.native_token, s.native_token, wilson.table.source_sha256, str(row.native_table_row.ordinal_0based),
            '25C;turnover_pH8.05_soluble_extract_active_site_normalized;specificity_pH8.1_purified_competing_gas_tritium_HPLC;means_SE_and_endpoint_column_counts',
            wilson.joint_endpoint_pairing + ';DERIVED_PROTEIN_RECIPE_NO_MUTANT_DNA'))
    for context in plant.contexts:
        recipe = context.protein_recipe
        if recipe is None:
            continue
        k, s = context.quantity('KCAT_C'), context.quantity('SPECIFICITY_CO')
        result.append(_candidate('nt.a369.' + (recipe.edit or 'parent').lower(), 'nt.a369', 'nt.a369.parent', recipe.translated_lsu, (('translated', recipe.translated_ssu),),
            k.mean, s.mean, k.mean_cell.token or '', s.mean_cell.token or '', str(k.sd_cell.token if k.sd_cell else 'UNKNOWN'), str(s.sd_cell.token if s.sd_cell else 'UNKNOWN'),
            plant.fingerprint(), context.name_cell.token, 'BACTERIAL_RECOMBINANT_A369_BACKGROUND;native_raw_counts_and_cached_means_errors;25C',
            'TERMINAL_PROCESSING_CLEAVAGE_ENDPOINT_PAIRING_AND_COVARIANCE_UNRESOLVED;SOURCE_DERIVED_RECIPE_NOT_MUTANT_DNA'))
    potato = json.loads(audit.named('potato-paired-subunit-inspection-v1.json'))
    # Independent primary Table2 tokens join all seven contexts, including the three nonhomogeneous/native controls.
    parser = _TableParser(target_section_id='tbl2')
    parser.feed(audit.named('martin-avila2020-primary-original.html').decode())
    parser.close()
    source_rows = tuple(tuple(c.text for c in r.cells) for r in parser.rows)
    inspection_rows = tuple(tuple(' '.join(c['value']['raw_text'].split()) for c in r['cells']) for r in potato['complete_native_Table2']['rows'])
    if source_rows != inspection_rows or len(source_rows) != 8:
        raise ValueError('potato inspection does not match complete original Table2 cells')
    precursor = potato['pS3_independent_genomic_sequence_join']
    if precursor['precursor_sequence'] not in audit.named('sgn-locus-2653-original.html').decode():
        raise ValueError('pS3 independent precursor is absent from original genomic-source bytes')
    # Native deposited translations independently authenticate the pS1/pST pair.
    deposited = {}
    for accession in ('MT596797.1', 'MT596798.1', 'MT596799.1'):
        text = audit.named(accession + '.embl').decode()
        deposited[accession] = tuple(re.sub(r'\s+', '', match) for match in re.findall(r'/translation="([^"]+)"', text.replace('FT                   ', ''), re.DOTALL))
    if (potato['common_potato_LSU']['full_translated_protein'] not in deposited['MT596797.1']
            or potato['common_potato_LSU']['full_translated_protein'] not in deposited['MT596798.1']
            or potato['SSU_recipes']['pS1']['full_translated_protein'] not in deposited['MT596798.1']
            or potato['SSU_recipes']['pST']['full_translated_protein'] not in deposited['MT596799.1']):
        raise ValueError('potato source inspection disagrees with native deposited protein translations')
    for name in ('pS2', 'pS3'):
        sequence = list(potato['SSU_recipes']['pS1']['full_translated_protein'])
        for edit in potato['SSU_recipes'][name]['all_declared_edits_relative_to_pS1']:
            index = edit['encoded_position'] - 1
            if edit['encoded_position'] != edit['native_position'] + 2 or sequence[index] != edit['from_residue']:
                raise ValueError('potato native/encoded residue correspondence differs')
            sequence[index] = edit['to_residue']
        if ''.join(sequence) != potato['SSU_recipes'][name]['full_translated_protein']:
            raise ValueError('potato compound recipe differs from all four reported source edits')
    ps3_native = potato['SSU_recipes']['pS3']['full_translated_protein']
    if ps3_native[:1] + ps3_native[3:] != precursor['mature_suffix_sequence']:
        raise ValueError('pS3 four-site protein recipe differs from independently deposited genomic precursor suffix')
    lsu = potato['common_potato_LSU']['full_translated_protein']
    for name in ('pS1', 'pS2', 'pS3', 'pST'):
        rec = potato['SSU_recipes'][name]
        ssu = rec['full_translated_protein']
        if sha256(lsu.encode()).hexdigest() != potato['common_potato_LSU']['protein_sha256'] or sha256(ssu.encode()).hexdigest() != rec['protein_sha256']:
            raise ValueError('potato full protein recipe digest differs')
        context = next(v for v in potato['complete_kinetic_contexts'] if v['context'] == 'tobpL' + name)
        k, s = context['endpoints']['kcatc'], context['endpoints']['Sc_over_o']
        native = source_rows[context['native_row_ordinal_0based']]
        if k['native_text'] not in native or s['native_text'] not in native:
            raise ValueError('potato endpoint role differs from original native cells')
        result.append(_candidate('potato.' + name.lower(), 'potato', 'potato.ps1', lsu, (('SP-extension-translated', ssu),),
            D(k['mean_decimal']), D(s['mean_decimal']), k['native_text'], s['native_text'], k['SD_decimal'], s['SD_decimal'],
            potato['primary']['sha256'], str(context['native_row_ordinal_0based']), '25C;native_SD;endpoint_specific_biological_sample_declarations_not_joint_n',
            'SP_EXTENSION_PROCESSING_AND_ENDPOINT_PAIRING_UNKNOWN;PS3_FOUR_SITE_INTERVENTION_NOT_ISOLATED_LOOP_PAIR;NUCLEOTIDE_COUNT_CONFLICT'))
    for cid, suffix, k, s in (('gp.wt', '', gp_k, gp_s), ('gp.i95m', 'i95m.', None, None)):
        result.append(_candidate(cid, 'gp', 'gp.wt', recipes['gp.lsu'], tuple((view, recipes['gp.ssu.' + suffix + view]) for view in ('m1', 'v1')),
            k, s, '1.6 catalogue' if k else 'UNKNOWN', '238 catalogue' if s else 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', gp.fingerprint(), 'catalogue-and-exact-protein-views',
            '25C_pH8_CATALOGUE_QUOTATION_NOT_MATCHED_CANDIDATE_BACKGROUND_ASSAY', 'GTG_INITIATION_M1_V1_PREPARATION_AND_MATCHED_ASSAY_JOINS_UNRESOLVED'))
    if len(result) != 32 or len({v.candidate_id for v in result}) != 32:
        raise ValueError('selected source panel loses or duplicates a genuine hypothesis')
    return tuple(sorted(result, key=lambda v: v.candidate_id))


def complete_candidate_roster(audit):
    """Authenticated full denominator; source-only projection, no effect assessment."""
    return _all_candidates(audit)


def parent_anchors(audit):
    by_id = {v.candidate_id: v for v in _all_candidates(audit)}
    return tuple(by_id[k] for k in sorted({v.parent_id for v in selected_candidates(audit)}))


def selected_candidates(audit):
    all_rows = _all_candidates(audit)
    selected = tuple(v for v in all_rows if v.candidate_id in audit.selected_candidate_ids)
    if tuple(v.candidate_id for v in selected) != audit.selected_candidate_ids:
        raise ValueError('candidate selection has no authentic full-sequence source witness')
    return selected


def original_source_scope(audit):
    return ScientificConditionScope('system.rubisco-portfolio.original-sources', 'world.rubisco-portfolio.exposed-inputs', audit.input_id,
        ('original-source-bytes',), ('byte',), 'receiver.closed-source-audit', 'clock.' + audit.cutoff,
        'Authenticated original/dependency bytes and exact protein/source contexts; no new biological measurements or observed-effect support assessment.', source_config_sha256=audit.fingerprint())


def scope(audit):
    return ScientificConditionScope('system.rubisco-portfolio-inquiry', 'world.rubisco-portfolio-inquiry.exposed', audit.input_id,
        ('specificity', 'turnover'), ('dimensionless', 's^-1'), 'receiver.single-effect-support-assessment', 'clock.' + audit.cutoff,
        'Selected exact biological hypotheses with complete19Wilson/12plant/7potato source denominators and nestedGpviews. Single-effect nonextrapolative interpolation support only; no biological exclusion, new independent units, matched assay join or nomination.',
        source_config_sha256=audit.fingerprint(), instance_id=UNIT)


@dataclass(frozen=True, slots=True)
class Effect(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/effect'
    candidate_id: str
    parent_id: str
    background: str
    log_turnover_contrast: Decimal
    log_specificity_contrast: Decimal


def effect_rows(audit, *, independent=False):
    candidates = _all_candidates(audit)
    by_id = {v.candidate_id: v for v in candidates}
    result = []
    with localcontext() as ctx:
        ctx.prec = 60
        for row in candidates:
            parent = by_id[row.parent_id]
            if row.candidate_id == row.parent_id or row.turnover_s_inv is None or row.specificity_dimensionless is None:
                continue
            kr, sr = row.turnover_s_inv / parent.turnover_s_inv, row.specificity_dimensionless / parent.specificity_dimensionless
            lk = kr.ln() if independent else D(repr(log(float(row.turnover_s_inv) / float(parent.turnover_s_inv))))
            ls = sr.ln() if independent else D(repr(log(float(row.specificity_dimensionless) / float(parent.specificity_dimensionless))))
            result.append(Effect(row.candidate_id, parent.candidate_id, row.background, lk, ls))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class SourceCheck(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/source-check'
    check_id: str
    source: ObjectIdentity
    authenticated_source_count: int
    full_candidate_count: int
    selected_candidate_count: int
    wilson_rows: int = 19
    plant_contexts: int = 12
    potato_contexts: int = 7
    new_biological_units: int = 0

    def __post_init__(self):
        if (self.authenticated_source_count != len(SOURCE_MANIFEST) or self.full_candidate_count != 32
                or not 1 <= self.selected_candidate_count <= self.full_candidate_count
                or (self.wilson_rows, self.plant_contexts, self.potato_contexts, self.new_biological_units) != (19, 12, 7, 0)):
            raise ValueError('source scope check discards denominator or creates independent biology')


def supplier_scope_check(audit):
    return SourceCheck('assessment.rubisco-portfolio-inquiry.source-scope', ObjectIdentity.from_record(audit.input_id, audit),
        len(audit.sources), len(_all_candidates(audit)), len(selected_candidates(audit)))


@dataclass(frozen=True, slots=True)
class PortfolioSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/supply'
    product_id: str
    source: SourceAudit
    candidates: tuple[Candidate, ...]
    effects: tuple[Effect, ...]
    check: SourceCheck
    scope: ScientificConditionScope
    disposition: AssessmentDisposition

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if (self.candidates != selected_candidates(self.source) or self.effects != effect_rows(self.source)
                or self.check != supplier_scope_check(self.source) or self.scope != scope(self.source)
                or self.disposition is not AssessmentDisposition.SATISFIED):
            raise ValueError('supplier source, recipe, full effect roster or arithmetic differs')


def supply(source):
    return PortfolioSupply('product.rubisco-portfolio-inquiry.supply', source, selected_candidates(source), effect_rows(source), supplier_scope_check(source), scope(source), AssessmentDisposition.SATISFIED)


@dataclass(frozen=True, slots=True)
class PortfolioInput(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/instance'
    instance_id: str
    candidates: tuple[Candidate, ...]
    references: tuple[tuple[str, Decimal, Decimal], ...] = REFERENCES
    model_role: str = 'SINGLE_OBSERVED_EFFECT_LOG_CONVEX_INTERPOLATION_NOT_ARBITRARY_COMBINATIONS'
    conditional_only: bool = True

    def __post_init__(self):
        validate_stable_id(self.instance_id)


def authentic_candidate(supplier):
    return PortfolioInput('instance.rubisco-portfolio-inquiry.portfolio', supplier.candidates)


def joint_hull_covers(points, required_k, required_s):
    """Exact 2D feasibility: vertices or an edge crossing a required coordinate."""
    points = ((D(0), D(0)), *tuple(points))
    if any(k >= required_k and s >= required_s for k, s in points):
        return True
    with localcontext() as ctx:
        ctx.prec = 60
        for i, (ka, sa) in enumerate(points):
            for kb, sb in points[i + 1:]:
                for a, b, required in ((ka, kb, required_k), (sa, sb, required_s)):
                    if a == b or not min(a, b) <= required <= max(a, b):
                        continue
                    weight = (required - a) / (b - a)
                    k, s = ka + weight * (kb - ka), sa + weight * (sb - sa)
                    if k >= required_k and s >= required_s:
                        return True
    return False


@dataclass(frozen=True, slots=True)
class CandidateView(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/candidate-view'
    candidate_id: str
    reference_view: str
    turnover_ratio: Decimal | None
    specificity_ratio: Decimal | None
    point_joint_pass: bool | None
    within_background_point_nondominated: bool | None
    biological_admission: str = BIOLOGICAL_ADMISSION


@dataclass(frozen=True, slots=True)
class SupportQuery(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/support-query'
    background: str
    parent_id: str
    reference_view: str
    required_turnover_multiplier: Decimal
    required_specificity_multiplier: Decimal
    observed_effect_count: int
    observed_max_turnover_multiplier: Decimal | None
    observed_max_specificity_multiplier: Decimal | None
    within_background_single_effect_support: AssessmentDisposition
    transported_all_background_envelope_support: AssessmentDisposition
    query: str
    exclusion_scope: str = 'DECLARED_NONEXTRAPOLATIVE_SINGLE_EFFECT_INTERPOLATOR_ONLY_NOT_BIOLOGICAL_DESCENDANTS'


def _consumer_rows(supplier, instance):
    if instance != authentic_candidate(supplier):
        raise ValueError('consumer refuses wrong roster, sequence/assembly, source endpoint, reference or model role')
    effects = effect_rows(supplier.source, independent=True)
    if len(effects) != len(supplier.effects):
        raise ValueError('independent consumer loses effect denominator')
    for a, b in zip(effects, supplier.effects, strict=True):
        if (a.candidate_id, a.parent_id, a.background) != (b.candidate_id, b.parent_id, b.background) or any(abs(x - y) > D('1e-12') for x, y in ((a.log_turnover_contrast, b.log_turnover_contrast), (a.log_specificity_contrast, b.log_specificity_contrast))):
            raise ValueError('independent Decimal contrast oracle disagrees with supplier float logarithms')
    all_rows = _all_candidates(supplier.source)
    by_id = {r.candidate_id: r for r in all_rows}
    views, queries = [], []
    with localcontext() as ctx:
        ctx.prec = 60
        for row in instance.candidates:
            known = row.turnover_s_inv is not None and row.specificity_dimensionless is not None
            peers = tuple(v for v in all_rows if v.background == row.background and v.turnover_s_inv is not None and v.specificity_dimensionless is not None)
            nd = None if not known else not any(v.turnover_s_inv >= row.turnover_s_inv and v.specificity_dimensionless >= row.specificity_dimensionless and (v.turnover_s_inv > row.turnover_s_inv or v.specificity_dimensionless > row.specificity_dimensionless) for v in peers)
            for name, target_k, target_s in instance.references:
                kr = None if row.turnover_s_inv is None else row.turnover_s_inv / target_k
                sr = None if row.specificity_dimensionless is None else row.specificity_dimensionless / target_s
                views.append(CandidateView(row.candidate_id, name, kr, sr, None if not known else kr >= 1 and sr >= 1, nd))
        parents = tuple(sorted({r.parent_id for r in instance.candidates}))
        for pid in parents:
            parent = by_id[pid]
            local = tuple(v for v in effects if v.parent_id == pid)
            for name, target_k, target_s in instance.references:
                rk, rs = target_k / parent.turnover_s_inv, target_s / parent.specificity_dimensionless
                maxk = max((by_id[v.candidate_id].turnover_s_inv / parent.turnover_s_inv for v in local), default=None)
                maxs = max((by_id[v.candidate_id].specificity_dimensionless / parent.specificity_dimensionless for v in local), default=None)
                local_support = AssessmentDisposition.UNEVALUABLE if not local else AssessmentDisposition.SATISFIED if joint_hull_covers(tuple((v.log_turnover_contrast, v.log_specificity_contrast) for v in local), rk.ln(), rs.ln()) else AssessmentDisposition.FALSIFIED
                transported = AssessmentDisposition.SATISFIED if joint_hull_covers(tuple((v.log_turnover_contrast, v.log_specificity_contrast) for v in effects), rk.ln(), rs.ln()) else AssessmentDisposition.FALSIFIED
                query = 'MATCHED_CANDIDATE_BACKGROUND_PAIRED_KINETICS_AND_PREPARATION_JOIN' if parent.background == 'gp' else 'NEW_SOURCE_SUPPORTED_SPECIFICITY_RESPONSE_OR_SEPARATELY_ASSESSED_CONTEXT_MECHANISM_REQUIRED'
                queries.append(SupportQuery(parent.background, pid, name, rk, rs, len(local), maxk, maxs, local_support, transported, query))
    return tuple(views), tuple(queries)


@dataclass(frozen=True, slots=True)
class SourceSentinel(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/source-sentinel'
    candidate_id: str
    parent_id: str
    log_turnover_contrast: Decimal
    log_specificity_contrast: Decimal
    point_direction: str
    intervention: str
    interpretation: str = 'EXPOSED_WHOLE_INTERVENTION_POINT_DIRECTION_NOT_STATISTICAL_PRESERVATION_OR_ISOLATED_EDIT_CAUSALITY'


def source_sentinels(audit):
    by_id = {r.candidate_id: r for r in _all_candidates(audit)}
    selected = ('wilson2017-row17', 'nt.a369.t391i', 'potato.ps3', 'potato.pst')
    effects = {r.candidate_id: r for r in effect_rows(audit, independent=True)}
    result = []
    for cid in selected:
        row, effect = by_id[cid], effects[cid]
        parent = by_id[row.parent_id]
        if cid.startswith('potato.'):
            intervention = 'FOUR_SITE_SSU_COMPOUND' if cid == 'potato.ps3' else 'HOMOGENEOUS_FULL_SSU_REPLACEMENT_LENGTH_AND_SEQUENCE_CHANGE_NOT_INDEPENDENT_SINGLE_EDITS'
        else:
            l = sum(a != b for a, b in zip(row.lsu_sequence, parent.lsu_sequence, strict=True))
            s = sum(a != b for a, b in zip(row.ssu_sequence_views[0][1], parent.ssu_sequence_views[0][1], strict=True))
            intervention = f'WHOLE_REPORTED_RECIPE_LSU_EDITS_{l}_SSU_EDITS_{s}_INTERACTION_NOT_ASSIGNED_ZERO'
        sign = lambda v: 'POSITIVE' if v > 0 else 'NEGATIVE' if v < 0 else 'TIED'
        result.append(SourceSentinel(cid, effect.parent_id, effect.log_turnover_contrast, effect.log_specificity_contrast,
            sign(effect.log_turnover_contrast) + '/' + sign(effect.log_specificity_contrast), intervention))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class PortfolioAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-portfolio-inquiry/assessment'
    assessment_id: str
    supplier: ObjectIdentity
    instance: PortfolioInput
    candidate_views: tuple[CandidateView, ...]
    support_queries: tuple[SupportQuery, ...]
    scope: ScientificConditionScope
    disposition: AssessmentDisposition
    scientific_outcome: str = 'RETAIN_EXPLORATORY_DIVERSITY_REQUIRE_NEW_PAIRED_RESPONSE_OR_ASSESSED_MECHANISM_REJECT_UNSUPPORTED_NOMINATION'
    comparison: str = 'UNEVALUATED'
    nomination: str = 'UNSUPPORTED'
    nominee: str | None = None
    new_biological_units: int = 0
    sentinels: tuple[SourceSentinel, ...] = ()

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        if (self.comparison, self.nomination, self.nominee, self.new_biological_units) != ('UNEVALUATED', 'UNSUPPORTED', None, 0):
            raise ValueError('conditional support cannot create comparison, nominee or biology')


def assess(supplier, instance):
    views, queries = _consumer_rows(supplier, instance)
    return PortfolioAssessment('assessment.rubisco-portfolio-inquiry.use', ObjectIdentity.from_record(supplier.product_id, supplier), instance,
        views, queries, supplier.scope, AssessmentDisposition.SATISFIED, sentinels=source_sentinels(supplier.source))
