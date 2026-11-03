# SPDX-License-Identifier: MPL-2.0
"""Complete cross-wave numerical accounting, without scientific credentials.

Wave summaries retain all original case and native dispositions. The reducer
uses one global matched-group maximum and one global order statistic. It does
not sign qualification, issue, reveal, or authorize access to sealed products.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import (
    CanonicalRecord, require_sorted_unique_strings, validate_decimal,
    validate_stable_id,
)

from .programme_records import MODES, ScheduledProgramme, ScheduledProgrammeWave
from .records import ScheduledSource

NATIVE_PHASES = ('continue', 'prefix', 'responses')
DISPOSITIONS = ('COMPLETED', 'FAILED', 'UNKNOWN', 'UNENTERED')
NATIVE_DISPOSITIONS = (*DISPOSITIONS, 'NOT_USED')
NUMERICAL_DISPOSITIONS = ('SATISFIED', 'VIOLATED', 'UNKNOWN', 'UNENTERED')
NONUSE_DISPOSITIONS = ('NO_ORIGIN', 'UNEVALUABLE', 'INSTRUMENT_UNRESOLVED')


def _require_identity(value, schema, *, version='1.0.0'):
    if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (schema, version):
        raise ValueError('programme summary changes a closed scientific or custody identity')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeReceiptReference(CanonicalRecord):
    """Actual dependency header, without inventing an unavailable receipt hash."""
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/receipt-reference'
    receipt_id: str
    task_id: str
    output_materialization_ids: tuple[str, ...]

    def __post_init__(self):
        validate_stable_id(self.receipt_id, field_name='receipt_id')
        validate_stable_id(self.task_id, field_name='task_id')
        require_sorted_unique_strings(self.output_materialization_ids, field_name='actual dependency outputs', allow_empty=False)

    @classmethod
    def from_binding(cls, binding):
        from empirical_lawhood.runtime.execution import DependencyReceiptBinding
        if type(binding) is not DependencyReceiptBinding:
            raise ValueError('programme receipt reference requires its actual dependency header')
        return cls(binding.receipt_id, binding.task_id, binding.output_materialization_ids)


def _receipt_id(value):
    if type(value) is ScheduledProgrammeReceiptReference:
        return value.receipt_id
    _require_identity(value, 'empirical-lawhood/runtime/canonical-task-receipt')
    return value.object_id


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeNativeDisposition(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/native-disposition'
    phase: str
    disposition: str
    definition: ObjectIdentity | None
    completion: ObjectIdentity | None
    receipt: ObjectIdentity | None
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        if self.phase not in NATIVE_PHASES or self.disposition not in NATIVE_DISPOSITIONS:
            raise ValueError('programme changes its exact three native phase dispositions')
        if self.disposition == 'NOT_USED' and self.phase != 'responses':
            raise ValueError('programme cannot hide its required prefix or continuation as nonuse')
        require_sorted_unique_strings(self.reason_codes, field_name='native reasons')
        for value, schema in ((self.definition, 'empirical-lawhood/runtime/native-subwork-definition'),
                (self.completion, 'empirical-lawhood/runtime/native-subwork-completion'),
                (self.receipt, 'empirical-lawhood/runtime/canonical-task-receipt')):
            if value is not None:
                _require_identity(value, schema)
        if (self.disposition == 'COMPLETED' and any(v is None for v in (self.definition, self.completion, self.receipt))
                or self.disposition in ('UNENTERED', 'NOT_USED') and any(v is not None for v in (self.definition, self.completion, self.receipt))
                or self.disposition != 'COMPLETED' and not self.reason_codes):
            raise ValueError('programme native disposition invents successful or unentered custody')


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeCaseResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/case-result'
    root_id: str
    source: ObjectIdentity
    independent_group_id: str
    disposition: str
    numerical_disposition: str
    score_disposition: str
    cumulative_log_errors: tuple[Decimal | None, ...]
    log_error_points: tuple[Decimal | None, ...]
    upper_log_errors: tuple[Decimal | None, ...]
    forecast: ObjectIdentity | None
    score: ObjectIdentity | None
    full_assessment: ObjectIdentity | None
    ordinary_receipts: tuple[ObjectIdentity | ScheduledProgrammeReceiptReference, ...]
    native: tuple[ScheduledProgrammeNativeDisposition, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self):
        from .response_records import ScheduledResponseScore
        validate_stable_id(self.root_id)
        validate_stable_id(self.independent_group_id)
        _require_identity(self.source, ScheduledSource.SCHEMA, version=ScheduledSource.VERSION)
        for value, schema, version in ((self.forecast, 'empirical-lawhood/matrix-scheduled-history/forecast-seal', '1.0.0'),
                (self.score, ScheduledResponseScore.SCHEMA, ScheduledResponseScore.VERSION),
                (self.full_assessment, 'empirical-lawhood/matrix-scheduled-history/full-assessment', '1.0.0')):
            if value is not None:
                _require_identity(value, schema, version=version)
        if any(type(n) is not ScheduledProgrammeNativeDisposition for n in self.native):
            raise ValueError('programme case requires closed native disposition records')
        receipt_ids = tuple(_receipt_id(r) for r in self.ordinary_receipts)
        headers = tuple(r for r in self.ordinary_receipts if type(r) is ScheduledProgrammeReceiptReference)
        if len({r.task_id for r in headers}) != len(headers):
            raise ValueError('programme case aliases actual dependency task headers')
        require_sorted_unique_strings(self.reason_codes, field_name='case reasons')
        if (self.disposition not in DISPOSITIONS or self.numerical_disposition not in NUMERICAL_DISPOSITIONS
                or self.score_disposition not in ('FINITE', 'PARTIAL', 'NO_ORIGIN', 'UNEVALUABLE',
                    'NATIVE_CROSSCHECK_FAILED', 'INSTRUMENT_UNRESOLVED', 'FAILED', 'UNKNOWN', 'UNENTERED')
                or any(len(v) != 15 for v in (self.cumulative_log_errors, self.log_error_points, self.upper_log_errors))
                or tuple(n.phase for n in self.native) != NATIVE_PHASES
                or receipt_ids != tuple(sorted(set(receipt_ids)))):
            raise ValueError('programme case drops complete endpoints, ordinary receipts or native phases')
        for values in (self.cumulative_log_errors, self.log_error_points, self.upper_log_errors):
            for value in values:
                if value is not None:
                    validate_decimal(value, field_name='retained response log error', minimum=Decimal(0))
        if (self.score_disposition == 'FINITE' and any(value is None for value in self.cumulative_log_errors)
                or self.score_disposition == 'PARTIAL' and all(value is not None for value in self.cumulative_log_errors)
                or self.score_disposition not in ('FINITE', 'PARTIAL')
                    and any(value is not None for value in self.cumulative_log_errors)):
            raise ValueError('programme score disposition fabricates finite nonuse or hides partial endpoints')
        if self.disposition == 'COMPLETED':
            if (any(v is None for v in (self.forecast, self.score, self.full_assessment))
                    or len(self.ordinary_receipts) != 11 or self.numerical_disposition == 'UNENTERED'
                    or any(n.disposition != 'COMPLETED' for n in self.native if n.phase != 'responses')
                    or self.native[2].disposition not in ('COMPLETED', 'NOT_USED')):
                raise ValueError('completed programme case omits actual eleven-stage custody')
            if self.native[2].disposition == 'NOT_USED' and (self.score_disposition not in NONUSE_DISPOSITIONS
                    or self.numerical_disposition == 'SATISFIED' or any(v is not None for v in self.cumulative_log_errors)):
                raise ValueError('programme case turns legitimate response nonuse into numerical success')
        if self.score_disposition == 'FINITE' and any(v is None for v in self.cumulative_log_errors):
            raise ValueError('programme finite score omits a complete response endpoint')
        if self.score_disposition == 'NATIVE_CROSSCHECK_FAILED' and self.numerical_disposition != 'VIOLATED':
            raise ValueError('programme case hides an actual pulse numerical violation')
        if self.numerical_disposition == 'SATISFIED' and (self.disposition != 'COMPLETED'
                or any(n.disposition != 'COMPLETED' for n in self.native)
                or self.score_disposition not in ('FINITE', 'PARTIAL')):
            raise ValueError('programme case hides incomplete native work as numerically satisfied')
        if self.disposition != 'COMPLETED' and not self.reason_codes:
            raise ValueError('noncomplete programme case omits its retained operational reason')
        if self.disposition == 'UNENTERED' and (self.numerical_disposition != 'UNENTERED'
                or self.score_disposition != 'UNENTERED' or self.ordinary_receipts or any(v is not None for v in
                (self.forecast, self.score, self.full_assessment)) or any(n.disposition != 'UNENTERED' for n in self.native)
                or any(v is not None for values in (self.cumulative_log_errors, self.log_error_points, self.upper_log_errors) for v in values)):
            raise ValueError('unentered programme case fabricates contact or response endpoints')

    @classmethod
    def unentered(cls, case):
        return cls(case.root_id, case.source, case.independent_group_id, 'UNENTERED', 'UNENTERED', 'UNENTERED',
            (None,)*15, (None,)*15, (None,)*15, None, None, None, (),
            tuple(ScheduledProgrammeNativeDisposition(phase, 'UNENTERED', None, None, None,
                ('programme-native-phase-unentered',)) for phase in NATIVE_PHASES), ('programme-case-unentered',))


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeWaveResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/wave-result'
    result_id: str
    programme: ObjectIdentity
    wave_id: str
    group_ids: tuple[str, ...]
    root_ids: tuple[str, ...]
    cases: tuple[ScheduledProgrammeCaseResult, ...]

    def __post_init__(self):
        validate_stable_id(self.result_id)
        wave = ScheduledProgrammeWave(self.wave_id, self.group_ids, self.root_ids)
        if (any(type(c) is not ScheduledProgrammeCaseResult for c in self.cases)
                or tuple(c.root_id for c in self.cases) != wave.root_ids
                or tuple(sorted({c.independent_group_id for c in self.cases})) != wave.group_ids
                or any(sum(c.independent_group_id == group for c in self.cases) != 9 for group in wave.group_ids)):
            raise ValueError('programme wave result drops, duplicates or reorders a declared case')
        _require_identity(self.programme, ScheduledProgramme.SCHEMA, version=ScheduledProgramme.VERSION)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.result_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeReduction(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/reduction'
    reduction_id: str
    programme: ObjectIdentity
    mode: str
    wave_results: tuple[ObjectIdentity, ...]
    cases: tuple[ScheduledProgrammeCaseResult, ...]
    group_scores: tuple[tuple[str, Decimal | None], ...]
    group_reason_codes: tuple[tuple[str, tuple[str, ...]], ...]
    disposition_counts: tuple[tuple[str, int], ...]
    native_disposition_counts: tuple[tuple[str, int], ...]
    numerical_disposition: str
    order_statistic_rank: int
    radius: Decimal | None
    qualification_disposition: str

    def __post_init__(self):
        validate_stable_id(self.reduction_id)
        _require_identity(self.programme, ScheduledProgramme.SCHEMA, version=ScheduledProgramme.VERSION)
        if (self.mode not in MODES or self.qualification_disposition != 'UNENTERED'
                or self.numerical_disposition not in NUMERICAL_DISPOSITIONS
                or any(type(c) is not ScheduledProgrammeCaseResult for c in self.cases)
                or tuple(c.root_id for c in self.cases) != tuple(sorted({c.root_id for c in self.cases}))):
            raise ValueError('pure programme reduction cannot manufacture scientific qualification')
        for value in self.wave_results:
            _require_identity(value, ScheduledProgrammeWaveResult.SCHEMA)
        if not self.wave_results or len({v.object_id for v in self.wave_results}) != len(self.wave_results):
            raise ValueError('programme reduction omits or aliases actual wave results')
        groups = tuple(sorted({c.independent_group_id for c in self.cases}))
        if len(groups) != MODES[self.mode][1] or any(sum(c.independent_group_id == g for c in self.cases) != 9 for g in groups):
            raise ValueError('programme reduction changes complete global whole-group max135 census')
        expected = _reduce_case_rows(self.cases, self.mode)
        actual = (self.group_scores, self.group_reason_codes, self.disposition_counts, self.native_disposition_counts,
            self.numerical_disposition, self.order_statistic_rank, self.radius)
        if (type(self.order_statistic_rank) is not int
                or any(type(count) is not int for _, count in (*self.disposition_counts, *self.native_disposition_counts))
                or any(value is not None and type(value) is not Decimal for _, value in self.group_scores)
                or self.radius is not None and type(self.radius) is not Decimal or actual != expected):
            raise ValueError('programme reduction changes actual global scores, counts, disposition, rank or radius')


def programme_numerical_disposition(prefix_numerical, full_numerical, pulse_score, *, frame_numerical=None):
    """Preserve actual prefix, full and pulse negatives; nonuse is not a pass."""
    if (not prefix_numerical.numerical_pass or not full_numerical.numerical_pass
            or frame_numerical is not None and not frame_numerical.numerical_pass
            or pulse_score.disposition == 'NATIVE_CROSSCHECK_FAILED'
            or any(c.disposition == 'VIOLATED' for c in pulse_score.controls)):
        return 'VIOLATED'
    return 'SATISFIED' if pulse_score.numerical_pass else 'UNKNOWN'


def _reduce_case_rows(cases, mode):
    groups, group_reasons = [], []
    for group in sorted({c.independent_group_id for c in cases}):
        rows = tuple(c for c in cases if c.independent_group_id == group)
        values, reasons = [], []
        for row in rows:
            if row.disposition != 'COMPLETED':
                reasons.append(row.disposition)
            if row.score_disposition not in ('FINITE', 'PARTIAL'):
                reasons.append(row.score_disposition)
            if row.numerical_disposition != 'SATISFIED':
                reasons.append('NUMERICAL_'+row.numerical_disposition)
            reasons.extend('NATIVE_'+n.phase.upper()+'_'+n.disposition for n in row.native if n.disposition != 'COMPLETED')
            for error, point in zip(row.cumulative_log_errors, row.log_error_points, strict=True):
                if error is None or point is None:
                    reasons.append(row.score_disposition if error is None else 'NO_FINITE_PRE_FUTURE_POINT_FORECAST')
                else:
                    with localcontext() as context:
                        context.prec = 50
                        values.append(max(Decimal(0), error-point))
        groups.append((group, None if reasons else max(values)))
        group_reasons.append((group, tuple(sorted(set(reasons))) if reasons else ('complete-nine-case-whole-group-max135',)))
    numerical = ('VIOLATED' if any(c.numerical_disposition == 'VIOLATED' for c in cases) else
        'UNKNOWN' if any(c.numerical_disposition == 'UNKNOWN' or c.disposition in ('FAILED', 'UNKNOWN')
            or any(n.disposition in ('FAILED', 'UNKNOWN', 'NOT_USED') for n in c.native) for c in cases) else
        'UNENTERED' if any(c.numerical_disposition == 'UNENTERED' or c.disposition == 'UNENTERED'
            or any(n.disposition == 'UNENTERED' for n in c.native) for c in cases) else 'SATISFIED')
    value = (len(groups)+1)*Fraction(95, 100)
    rank = (value.numerator+value.denominator-1)//value.denominator
    ordered = sorted((score for _, score in groups), key=lambda score: (score is None, score or Decimal(0)))
    radius = ordered[rank-1] if mode == 'E4_REVISION_CALIBRATION' and rank <= len(ordered) else None
    return (tuple(groups), tuple(group_reasons),
        tuple((state, sum(c.disposition == state for c in cases)) for state in DISPOSITIONS),
        tuple((state, sum(n.disposition == state for c in cases for n in c.native)) for state in NATIVE_DISPOSITIONS),
        numerical, rank, radius)


def validate_programme_reduction(programme, reduction, *, wave_results):
    """Compare cold reduction with the complete frozen programme and waves.

    Actual receipt and publication custody remains the caller's access port;
    this check neither authenticates opaque dependency headers nor grants it.
    """
    if (type(programme) is not ScheduledProgramme or type(reduction) is not ScheduledProgrammeReduction
            or reduction.programme != programme.identity or reduction.mode != programme.mode):
        raise ValueError('programme reduction changes its frozen original global scope')
    expected_cases = tuple((c.root_id, c.source, c.independent_group_id) for c in programme.cases)
    if (tuple((c.root_id, c.source, c.independent_group_id) for c in reduction.cases) != expected_cases
            or tuple(g for g, _ in reduction.group_scores) != programme.group_ids):
        raise ValueError('programme reduction substitutes complete original source/group census')
    waves = tuple(wave_results)
    if (len(waves) != len(programme.waves) or any(type(w) is not ScheduledProgrammeWaveResult for w in waves)
            or tuple(w.wave_id for w in waves) != tuple(w.wave_id for w in programme.waves)
            or tuple(w.identity for w in waves) != reduction.wave_results):
        raise ValueError('programme reduction changes actual whole-group wave identities')
    for declared, result in zip(programme.waves, waves, strict=True):
        if (result.programme != programme.identity or result.group_ids != declared.group_ids or result.root_ids != declared.root_ids
                or result.cases != tuple(c for c in reduction.cases if c.root_id in declared.root_ids)):
            raise ValueError('programme reduction drops, overlaps or substitutes frozen wave cases')
    return reduction


def collect_completed_programme_case(programme, bank, case, *, products, receipts, authenticate_receipt):
    """Join actual eleven-stage products and known native custody before summary.

    The injected port authenticates retained receipts against the genuine
    issued run and its input/output manifests. This pure owner independently
    checks exact source, model, criterion, output bytes/access and native
    definition/completion joins. It never converts an operational failure into
    a completed case; those remain explicit failed/UNKNOWN/unentered rows.
    """
    from empirical_lawhood.kernel.status import OperationalStatus
    from empirical_lawhood.runtime.artifacts import CanonicalTaskReceipt
    from .compact_bindings import PHASES
    from .compact_records import NAMESPACE, ScheduledCompactConfig, compact_identity
    from .source_index import ScheduledSourceIndex, ScheduledNativeSourceContext
    from .programme_composition import phase_roles
    from .programme_records import validate_programme_bank
    from .operation_bindings import phase_access, phase_visibility
    from .records import identity

    validate_programme_bank(programme, bank)
    if case not in programme.cases or not callable(authenticate_receipt):
        raise ValueError('programme collector requires its actual declared case and custody port')
    descriptor = next(d for d in bank.sources if d.root_id == case.root_id)
    index = ScheduledSourceIndex.from_shared(reservation=bank.reservation,
        specification=bank.specification, provenances=bank.provenances)
    source = index.resolve(descriptor)
    prefix_config = ScheduledCompactConfig('config.'+NAMESPACE+'.'+case.root_id+'.prefix',
        'prefix', source.reference, compact_identity(bank))
    native_context = ScheduledNativeSourceContext(source, prefix_config, bank)
    roles = phase_roles(source, bank.forecast_design)
    if (set(products) != set(roles) or len(receipts) != 11
            or any(type(receipt) is not CanonicalTaskReceipt for receipt in receipts)):
        raise ValueError('programme collector drops the complete actual eleven-stage products/receipts')
    by_task = {r.task_id: r for r in receipts}
    if (len(by_task) != 11 or set(by_task) != {NAMESPACE+'.'+case.root_id+'.'+role for role in roles}
            or len({r.run_id for r in receipts}) != 1):
        raise ValueError('programme collector substitutes actual wave run/task custody')
    for role in roles:
        receipt, record = by_task[NAMESPACE+'.'+case.root_id+'.'+role], products[role]
        expected_type = next(p[2] for p in PHASES if p[0] == role)
        if (type(record) is not expected_type or record.source != case.source
                or receipt.operational_status is not OperationalStatus.SUCCEEDED):
            raise ValueError('programme collector substitutes original phase product or hides failed custody')
        authenticate_receipt(receipt)
        raw = record.canonical_bytes()
        logical = tuple(a for a in receipt.output_logical_artifacts if a.payload_schema == record.SCHEMA
            and a.content_sha256 == record.fingerprint())
        if len(logical) != 1:
            raise ValueError('programme collector lacks exact actual product logical publication')
        physical = tuple(m for m in receipt.output_materializations if m.logical_artifact_id == logical[0].logical_artifact_id)
        if (len(physical) != 1 or physical[0].physical_sha256 != record.fingerprint()
                or physical[0].size_bytes != len(raw) or logical[0].media_type != 'application/json'
                or logical[0].outcome_access is not phase_access(role)
                or logical[0].visibility_ceiling is not phase_visibility(role)):
            raise ValueError('programme collector substitutes actual physical bytes or issued outcome access')
    forecast_role = next(role for role in roles if role.startswith('forecast'))
    suffix = '-development' if 'continue-development' in roles else ''
    prefix, causal = products['prefix'], products['project']
    prefix_numerical, witness, frame = products['numerical'], products['measure'], products['check']
    forecast, physical = products[forecast_role], products['physical-forecast']
    full, assessment = products['continue'+suffix], products['full-numerical'+suffix]
    responses, score = products['responses'+suffix], products['response-score'+suffix]
    protocol, _ = bank.response_selection.validate_source(source)
    prefix.validate_source(source, native_context=native_context)
    full.validate_source(source, prefix, causal, forecast, physical, native_context=native_context)
    responses.validate_source(source, bank.response_selection, prefix, causal, physical, forecast,
        native_context=native_context)
    if (prefix_numerical.history != identity(prefix) or prefix_numerical.numerical_design != identity(source.numerical_design)
            or witness.history != identity(prefix) or witness.numerical != identity(prefix_numerical)
            or frame.witness != identity(witness) or frame.numerical_design != identity(source.policy.factor_numerical_design)
            or causal.history != identity(prefix) or causal.numerical != identity(prefix_numerical)
            or causal.witness != identity(witness) or causal.frame_assessment != identity(frame)
            or assessment.history != identity(full) or assessment.numerical_design != identity(source.numerical_design)
            or forecast.design != programme.forecast_design or forecast.model != bank.forecast_design.model
            or forecast.criterion != programme.criterion or score.criterion != programme.criterion
            or physical.protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)
            or physical.mechanical_model != ObjectIdentity.from_record(protocol.mechanical_model.model_id, protocol.mechanical_model)
            or score.root_id != case.root_id or score.causal_prefix != identity(causal)
            or score.physical_forecast != identity(physical)
            or score.error_forecast != identity(forecast) or score.responses != identity(responses)
            or score.independent_group_id != case.independent_group_id or score.role != case.role):
        raise ValueError('programme collector substitutes original global model, numerical design or response lineage')
    native = []
    for phase, record in (('continue', full), ('prefix', prefix), ('responses', responses)):
        events = record.native if phase == 'responses' else (record.native,)
        if not events:
            native.append(ScheduledProgrammeNativeDisposition(phase, 'NOT_USED', None, None, None,
                tuple(sorted(set(responses.reason_codes) | {responses.disposition}))))
        else:
            event, = events
            authenticate_receipt(event.receipt)
            native.append(ScheduledProgrammeNativeDisposition(phase, 'COMPLETED', event.definition.identity,
                ObjectIdentity.from_record('completion.'+event.definition.subwork_id, event.completion),
                ObjectIdentity.from_record(event.receipt.receipt_id, event.receipt), ()))
    return ScheduledProgrammeCaseResult(case.root_id, case.source, case.independent_group_id, 'COMPLETED',
        programme_numerical_disposition(prefix_numerical, assessment, score, frame_numerical=frame), score.disposition,
        score.cumulative_log_errors, forecast.log_error_points, forecast.log_error_uppers,
        identity(forecast), identity(score), identity(assessment),
        tuple(sorted((ObjectIdentity.from_record(r.receipt_id, r) for r in receipts), key=lambda r: r.object_id)),
        tuple(native), tuple(sorted(set(score.reason_codes))))


def reduce_programme(programme, wave_results, *, reduction_id, authenticate_wave):
    """Authenticate every complete wave and reduce the original global roster.

    ``authenticate_wave`` is the caller's custody/access port. It must verify
    the original wave manifest, completion receipt and all referenced retained
    case products before returning. A synthetic test port establishes software
    conformance only; the result itself always keeps qualification unentered.
    """
    if type(programme) is not ScheduledProgramme or not callable(authenticate_wave):
        raise ValueError('programme reduction requires its frozen scope and actual custody/access port')
    wave_results = tuple(wave_results)
    if any(type(result) is not ScheduledProgrammeWaveResult for result in wave_results):
        raise ValueError('programme reduction requires closed actual wave result records')
    expected = {wave.wave_id: wave for wave in programme.waves}
    received = {result.wave_id: result for result in wave_results}
    if len(received) != len(wave_results) or set(received) != set(expected):
        raise ValueError('programme reduction refuses missing or duplicated whole-group wave receipts')
    cases = []
    source_map = {case.root_id: (case.source, case.independent_group_id) for case in programme.cases}
    for wave in programme.waves:
        result = received[wave.wave_id]
        if (type(result) is not ScheduledProgrammeWaveResult or result.programme != programme.identity
                or result.group_ids != wave.group_ids or result.root_ids != wave.root_ids
                or any((case.source, case.independent_group_id) != source_map[case.root_id] for case in result.cases)):
            raise ValueError('programme reduction changes original source, phase or whole-group subdivision')
        authenticate_wave(result)
        cases.extend(result.cases)
    cases = tuple(sorted(cases, key=lambda case: case.root_id))
    if tuple(case.root_id for case in cases) != tuple(case.root_id for case in programme.cases):
        raise ValueError('programme reduction thins the global complete case denominator')
    result = ScheduledProgrammeReduction(reduction_id, programme.identity, programme.mode,
        tuple(received[w.wave_id].identity for w in programme.waves), cases,
        *_reduce_case_rows(cases, programme.mode), 'UNENTERED')
    return validate_programme_reduction(programme, result,
        wave_results=tuple(received[w.wave_id] for w in programme.waves))
