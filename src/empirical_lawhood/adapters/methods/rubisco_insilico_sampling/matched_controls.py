# SPDX-License-Identifier: MPL-2.0
"""PURE joins of separate WT/I95M numerical episodes; no new entry gate.

Callers authenticate the original records and independently assessed contribution
parents before this reduction. This report joins their selected numerical scope;
it never constructs models, supplies authority, or assesses an ensemble effect.
"""

from dataclasses import dataclass, fields
from decimal import Decimal
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from . import contracts as sampling, control_contracts as force, nve_contracts as nve

MATERIALS = ('gp.wt.m1', 'gp.i95m.m1')
JOINT_VIEW = 'joint-01'
CHEMICAL_KEYS = p.PARAMETER_VIEWS
NVE_KEYS = tuple((parameter, ensemble[0], resolution[0]) for parameter in p.PARAMETER_VIEWS
                 for ensemble in sampling.ENSEMBLES for resolution in sampling.INTEGRATION)
REFINEMENT_KEYS = tuple((parameter, ensemble[0]) for parameter in p.PARAMETER_VIEWS for ensemble in sampling.ENSEMBLES)
APPARATUS_FIELDS = ('engine_inventory_sha256', 'interpreter_sha256', 'hardware_inspector_sha256',
                    'dependency_lock_sha256', 'hardware', 'external_runtime_files', 'cutoff_nanometer',
                    'temperature_kelvin', 'platform_precision', 'device_index', 'deterministic_forces',
                    'use_cpu_pme', 'minimizer_tolerance_kj_mol_nm', 'minimizer_max_iterations',
                    'minimizer_reporter_early_stop', 'objective_rms_normalization', 'terminal_position_join')
SCIENCE_PREFIXES = ('src/empirical_lawhood/adapters/methods/rubisco_insilico_dynamics/',
                    'src/empirical_lawhood/adapters/methods/rubisco_insilico_sampling/')
REQUIRED_NATIVE_OWNERS = tuple(prefix+'native.py' for prefix in SCIENCE_PREFIXES)


def _aggregate(outcomes):
    return A.REFUSED if A.REFUSED in outcomes else A.UNEVALUABLE if any(row is not A.SATISFIED for row in outcomes) else A.SATISFIED


@dataclass(frozen=True, slots=True)
class EpisodeNumericalEvidence(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/episode-numerical-evidence'
    VERSION: ClassVar[str] = '1.1.0'
    material: str
    source: ObjectIdentity
    chemical_plan: ObjectIdentity | None
    chemical_returns: tuple[ObjectIdentity, ...]
    chemical_assessments: tuple[ObjectIdentity, ...]
    # Exact original return -> independent assessment, including an assessed
    # return whose bytes are not supplied to this particular report.
    chemical_assessment_parents: tuple[tuple[ObjectIdentity, ObjectIdentity], ...]
    # Full24 chemical outcomes, including rows without independent assessment.
    chemical_outcomes: tuple[tuple[str, A, A, tuple[str, ...]], ...]
    nve_plan: ObjectIdentity | None
    nve_assessment: ObjectIdentity | None
    nve_returns: tuple[ObjectIdentity, ...]
    nve_assessed_returns: tuple[ObjectIdentity, ...]
    # The original full96/48 tables are preserved, never filtered to a positive.
    nve_cases: tuple[tuple[str, A, Decimal | None, tuple[str, ...]], ...]
    nve_refinements: tuple[tuple[str, A, Decimal | None, Decimal | None], ...]
    reported_component_excursions: tuple[tuple[str, int | None, int | None], ...]

    def __post_init__(self):
        if self.material not in MATERIALS or self.source.object_schema != p.PreparationSelection.SCHEMA:
            raise ValueError('matched episode substitutes source/material')
        self.source.__post_init__()
        for identity, kind in ((self.chemical_plan, force.ChemicalForcePlan), (self.nve_plan, nve.NVEControlPlan),
                               (self.nve_assessment, nve.NVEControlAssessment)):
            if identity is not None:
                identity.__post_init__()
                if identity.object_schema != kind.SCHEMA:
                    raise ValueError('matched episode substitutes original numerical owner')
        for rows, kind in ((self.chemical_returns, force.ChemicalForceReturn),
                           (self.chemical_assessments, force.ChemicalForceAssessment), (self.nve_returns, nve.NVEControlReturn),
                           (self.nve_assessed_returns, nve.NVEControlReturn)):
            if tuple(row.object_id for row in rows) != tuple(sorted(set(row.object_id for row in rows))):
                raise ValueError('matched episode duplicates/reorders authentic records')
            for identity in rows:
                identity.__post_init__()
                if identity.object_schema != kind.SCHEMA:
                    raise ValueError('matched episode changes original result identity')
        if (tuple(row[0] for row in self.chemical_outcomes) != tuple(sorted(force.model_id(key) for key in p.model_roster()))
                or tuple(row[0] for row in self.nve_cases) != nve.unit_ids()
                or tuple(row[0] for row in self.reported_component_excursions) != nve.unit_ids()
                or tuple(row[0] for row in self.nve_refinements) != tuple(nve.unit_id(key).rsplit('.', 1)[0]
                    for key in sampling.trajectory_roster() if key[-1] == 'primary')):
            raise ValueError('matched episode drops complete24/96/48 denominators')
        for _, objective, agreement, _ in self.chemical_outcomes:
            if type(objective) is not A or type(agreement) is not A:
                raise ValueError('matched episode replaces independently assessed dispositions')
        parent_ids = tuple(row[0].object_id for row in self.chemical_assessment_parents)
        if parent_ids != tuple(sorted(set(parent_ids))):
            raise ValueError('matched episode duplicates/reorders chemical assessment parents')
        assessed = set()
        parents = {}
        for returned, assessment in self.chemical_assessment_parents:
            for row, kind in ((returned, force.ChemicalForceReturn), (assessment, force.ChemicalForceAssessment)):
                row.__post_init__()
                if row.object_schema != kind.SCHEMA:
                    raise ValueError('matched episode substitutes chemical assessment parent owners')
            if returned.object_id not in {'control.chemical-force.'+name for name, *_ in self.chemical_outcomes}:
                raise ValueError('matched episode substitutes chemical assessment parent unit')
            assessed.add(assessment)
            parents[returned.object_id] = returned
        if (len(assessed) != len(self.chemical_assessment_parents)
                or assessed != set(self.chemical_assessments)):
            raise ValueError('matched episode loses exact independent chemical assessment parents')
        if self.chemical_plan is None and (self.chemical_returns or self.chemical_assessments or self.nve_plan is not None):
            raise ValueError('matched episode loses original chemical plan')
        for returned in self.chemical_returns:
            if returned.object_id in parents and parents[returned.object_id] != returned:
                raise ValueError('matched episode substitutes assessed original chemical return bytes')
        for name, objective, agreement, _ in self.chemical_outcomes:
            if any(row is not A.UNEVALUABLE for row in (objective, agreement)) and (
                    self.chemical_plan is None or 'control.chemical-force.'+name not in parents):
                raise ValueError('matched episode loses per-unit independent chemical outcome parents')
        if self.nve_plan is None and (self.nve_assessment is not None or self.nve_returns or self.nve_assessed_returns):
            raise ValueError('matched episode loses original NVE plan')
        if self.nve_assessment is None and (self.nve_assessed_returns
                or any(row[1] is not A.UNEVALUABLE for row in (*self.nve_cases, *self.nve_refinements))
                or any(row[1:] != (None, None) for row in self.reported_component_excursions)):
            raise ValueError('matched episode loses independent NVE assessment parent')
        actual = {row.object_id: row for row in self.nve_returns}
        assessed_returns = {row.object_id: row for row in self.nve_assessed_returns}
        if any(row.object_id not in nve.unit_ids() for row in self.nve_assessed_returns):
            raise ValueError('matched episode substitutes assessed NVE return unit')
        if any(assessed_returns.get(name) != row for name, row in actual.items()) and self.nve_assessment is not None:
            raise ValueError('matched episode substitutes independently assessed NVE return bytes')
        for name, status, *_ in self.nve_cases:
            if type(status) is not A or (status is A.SATISFIED and (
                    self.nve_plan is None or self.nve_assessment is None or name not in assessed_returns)):
                raise ValueError('matched episode loses independently assessed positive NVE return')
        case_status = {row[0]: row[1] for row in self.nve_cases}
        for name, status, *_ in self.nve_refinements:
            if type(status) is not A or (status is A.SATISFIED and (
                    self.nve_plan is None or self.nve_assessment is None or any(
                        name+'.'+resolution[0] not in assessed_returns
                        or case_status[name+'.'+resolution[0]] is not A.SATISFIED
                        for resolution in sampling.INTEGRATION))):
                raise ValueError('matched episode loses both independently assessed refinement returns')


@dataclass(frozen=True, slots=True)
class MatchedNumericalAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/matched-numerical-assessment'
    VERSION: ClassVar[str] = '1.1.0'
    product_id: str
    episodes: tuple[EpisodeNumericalEvidence, ...]
    source_compatibility: A
    apparatus_compatibility: A
    paired_chemical: tuple[tuple[str, A, A, A], ...]
    paired_nve: tuple[tuple[tuple[str, str, str], A, A, A], ...]
    paired_refinements: tuple[tuple[tuple[str, str], A, A, A], ...]
    selected_numerical_disposition: A
    reason_codes: tuple[str, ...]
    ensemble_adequacy: A = A.UNEVALUABLE
    structural_effect: A = A.UNEVALUABLE
    native_optimizer_convergence: A = A.UNEVALUABLE
    kinetic_transport: A = A.UNEVALUABLE
    biological_target: A = A.UNEVALUABLE
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.product_id)
        if tuple(row.material for row in self.episodes) != MATERIALS or self.episodes[0].source == self.episodes[1].source:
            raise ValueError('matched comparison needs both distinct original source episodes')
        for row in self.episodes:
            row.__post_init__()
        if (tuple(row[0] for row in self.paired_chemical) != CHEMICAL_KEYS
                or tuple(row[0] for row in self.paired_nve) != NVE_KEYS
                or tuple(row[0] for row in self.paired_refinements) != REFINEMENT_KEYS):
            raise ValueError('matched comparison drops a declared parameter/seed/resolution pair')
        for parameter, left, right, _ in self.paired_chemical:
            expected = tuple(_chemical_status(episode, parameter) for episode in self.episodes)
            if (left, right) != expected:
                raise ValueError('matched chemical pair substitutes original assessed outcomes')
        for key, left, right, _ in self.paired_nve:
            if (left, right) != tuple(_nve_status(episode, key) for episode in self.episodes):
                raise ValueError('matched NVE pair substitutes original assessed/returned cases')
        for key, left, right, _ in self.paired_refinements:
            if (left, right) != tuple(_refinement_status(episode, key) for episode in self.episodes):
                raise ValueError('matched refinement pair substitutes original assessed/returned cases')
        for rows in (self.paired_chemical, self.paired_nve, self.paired_refinements):
            for _, left, right, disposition in rows:
                if any(type(value) is not A for value in (left, right, disposition)) or disposition is not _aggregate((left, right)):
                    raise ValueError('matched comparison hides missing/adverse paired controls')
        outcomes = (self.source_compatibility, self.apparatus_compatibility,
                    *(row[3] for rows in (self.paired_chemical, self.paired_nve, self.paired_refinements) for row in rows))
        if any(type(row) is not A for row in outcomes) or self.selected_numerical_disposition is not _aggregate(outcomes):
            raise ValueError('matched numerical result hides unresolved selected operands')
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError('matched numerical reasons must retain a unique stable census')
        if (self.physical_independent_units != 0 or any(row is not A.UNEVALUABLE for row in (
                self.ensemble_adequacy, self.structural_effect, self.native_optimizer_convergence,
                self.kinetic_transport, self.biological_target))):
            raise ValueError('100ps numerical controls cannot qualify physical, structural or kinetic effects')


def _record_identity(record):
    return record.identity if hasattr(record, 'identity') else ObjectIdentity.from_record(record.product_id, record)


def _chemical_status(episode, parameter):
    name = force.model_id((episode.material, JOINT_VIEW, parameter))
    statuses = next(row[1:3] for row in episode.chemical_outcomes if row[0] == name)
    if ('control.chemical-force.'+name not in {row.object_id for row in episode.chemical_returns}
            and A.REFUSED not in statuses):
        return A.UNEVALUABLE
    return _aggregate(statuses)


def _nve_status(episode, key):
    name = nve.unit_id((episode.material, JOINT_VIEW, *key))
    status = next(row[1] for row in episode.nve_cases if row[0] == name)
    return status if status is A.REFUSED or name in {row.object_id for row in episode.nve_returns} else A.UNEVALUABLE


def _refinement_status(episode, key):
    name = nve.unit_id((episode.material, JOINT_VIEW, *key, 'primary')).rsplit('.', 1)[0]
    actual = {row.object_id for row in episode.nve_returns}
    status = next(row[1] for row in episode.nve_refinements if row[0] == name)
    both = all(name+'.'+resolution[0] in actual for resolution in sampling.INTEGRATION)
    return status if status is A.REFUSED or both else A.UNEVALUABLE


def _unique(records, key):
    rows = {getattr(row, key): row for row in records}
    if len(rows) != len(records):
        raise ValueError('matched input duplicates original numerical records')
    for row in records:
        row.__post_init__()
    return rows


def _episode(material, source, chemical_plan, chemical_returns, chemical_assessments, nve_plan, nve_returns, nve_assessment):
    source.__post_init__()
    chemical_by_unit = _unique(chemical_returns, 'unit_id')
    assessments = _unique(chemical_assessments, 'returned')
    if len({row.returned.object_id for row in chemical_assessments}) != len(chemical_assessments):
        raise ValueError('matched input ambiguously substitutes revisions of one chemical return')
    nve_by_unit = _unique(nve_returns, 'unit_id')
    if chemical_plan is None:
        if chemical_returns or chemical_assessments or nve_plan is not None:
            raise ValueError('matched input supplies numerical records without their actual plan')
    else:
        chemical_plan.__post_init__()
        if chemical_plan.source != p.identity(source) or chemical_plan.engine_inventory_sha256 != source.engine_inventory_sha256:
            raise ValueError('matched input substitutes original chemical source/engine')
        selected = dict(chemical_plan.selected_assets)
        for returned in chemical_returns:
            if (returned.plan != chemical_plan.identity or not returned.unit_id.startswith('control.chemical-force.')
                    or returned.assets != selected.get(returned.unit_id.removeprefix('control.chemical-force.'))):
                raise ValueError('matched input substitutes original chemical return/assets')
        for assessment in chemical_assessments:
            if assessment.plan != chemical_plan.identity:
                raise ValueError('matched input substitutes independent chemical assessment plan')
            if assessment.returned.object_id not in {'control.chemical-force.'+name for name in selected}:
                raise ValueError('matched independent chemical assessment concerns an unselected model')
            original = chemical_by_unit.get(assessment.returned.object_id)
            if original is not None and assessment.returned != original.identity:
                raise ValueError('matched independent chemical assessment substitutes original return bytes')
    chemical = []
    for name in sorted(force.model_id(key) for key in p.model_roster()):
        returned = chemical_by_unit.get('control.chemical-force.'+name)
        assessment = assessments.get(returned.identity) if returned is not None else next(
            (row for row in chemical_assessments if row.returned.object_id == 'control.chemical-force.'+name), None)
        if assessment is None:
            chemical.append((name, A.UNEVALUABLE, A.UNEVALUABLE, ('ORIGINAL_RETURN_OR_INDEPENDENT_ASSESSMENT_MISSING',)))
        else:
            if returned is not None and not returned.operators_completed and (assessment.objective_precision_disposition is A.SATISFIED
                    or assessment.force_agreement_disposition is A.SATISFIED):
                raise ValueError('matched input promotes known failed chemical operators')
            chemical.append((name, assessment.objective_precision_disposition, assessment.force_agreement_disposition, assessment.reason_codes))
    if nve_plan is None:
        if nve_returns or nve_assessment is not None:
            raise ValueError('matched input supplies NVE records without their actual plan')
    else:
        nve_plan.__post_init__()
        if chemical_plan is None or nve_plan.chemical_controls != chemical_plan:
            raise ValueError('matched input changes original NVE chemical parent')
        for name, _, _, _, returned_id, assessment_id in nve_plan.admitted_parents:
            returned = chemical_by_unit.get('control.chemical-force.'+name)
            assessment = assessments.get(returned.identity) if returned is not None else None
            if returned is not None and returned.identity != returned_id:
                raise ValueError('matched NVE changes original chemical return')
            if assessment is not None and _record_identity(assessment) != assessment_id:
                raise ValueError('matched NVE changes original independent chemical assessment')
        supplies = {name: supply for name, supply, *_ in nve_plan.admitted_parents}
        for returned in nve_returns:
            key = next(key for key in sampling.trajectory_roster() if nve.unit_id(key) == returned.unit_id)
            if (returned.plan != nve_plan.identity or key not in nve_plan.selected_cases
                    or returned.relaxed_supply != supplies[force.model_id(key[:3])]):
                raise ValueError('matched input substitutes original NVE return/supply/selection')
    if nve_assessment is None:
        cases = tuple((name, A.UNEVALUABLE, None, ('INDEPENDENT_NVE_ASSESSMENT_MISSING',)) for name in nve.unit_ids())
        refinements = tuple((nve.unit_id(key).rsplit('.', 1)[0], A.UNEVALUABLE, None, None)
                            for key in sampling.trajectory_roster() if key[-1] == 'primary')
        components = tuple((name, None, None) for name in nve.unit_ids())
    else:
        nve_assessment.__post_init__()
        if nve_assessment.plan != nve_plan.identity or any(row.identity not in nve_assessment.returned for row in nve_returns):
            raise ValueError('matched input substitutes independently assessed NVE plan/returns')
        cases, refinements, components = nve_assessment.cases, nve_assessment.refinements, nve_assessment.reported_component_excursions
        for returned in nve_returns:
            if not returned.operators_completed and dict((row[0], row[1]) for row in cases)[returned.unit_id] is A.SATISFIED:
                raise ValueError('matched input promotes failed NVE operators')
    evidence = EpisodeNumericalEvidence(material, p.identity(source), chemical_plan.identity if chemical_plan else None,
        tuple(row.identity for row in sorted(chemical_returns, key=lambda row: row.unit_id)),
        tuple(_record_identity(row) for row in sorted(chemical_assessments, key=lambda row: row.product_id)),
        tuple((row.returned, _record_identity(row)) for row in sorted(chemical_assessments, key=lambda row: row.returned.object_id)), tuple(chemical),
        nve_plan.identity if nve_plan else None, _record_identity(nve_assessment) if nve_assessment else None,
        tuple(row.identity for row in sorted(nve_returns, key=lambda row: row.unit_id)),
        nve_assessment.returned if nve_assessment else (), cases, refinements, components)
    return evidence, chemical_by_unit, nve_by_unit


def assess_matched_numerical(product_id, wt_source, i95m_source, *, wt_chemical_plan=None, i95m_chemical_plan=None,
                             wt_chemical_returns=(), i95m_chemical_returns=(), wt_chemical_assessments=(), i95m_chemical_assessments=(),
                             wt_nve_plan=None, i95m_nve_plan=None, wt_nve_returns=(), i95m_nve_returns=(),
                             wt_nve_assessment=None, i95m_nve_assessment=None):
    """Join assessed parents directly; unselected full-census outcomes stay explicit.

    This is not required before I95M preparation or any native entry. Matching
    means identical declared scientific source, parameter view and apparatus,
    with different source/workdir identities and the sole declared I95M edit.
    No difference of whole-system energies or numerical errors is interpreted as
    a mutation effect. 100ps NVE has no ensemble confidence interval here.
    """
    first = _episode(MATERIALS[0], wt_source, wt_chemical_plan, wt_chemical_returns, wt_chemical_assessments,
                     wt_nve_plan, wt_nve_returns, wt_nve_assessment)
    second = _episode(MATERIALS[1], i95m_source, i95m_chemical_plan, i95m_chemical_returns, i95m_chemical_assessments,
                      i95m_nve_plan, i95m_nve_returns, i95m_nve_assessment)
    reasons = []
    scientific_fields = tuple(row.name for row in fields(wt_source) if row.name not in ('selection_id', 'native_workdir'))
    source_match = all(getattr(wt_source, name) == getattr(i95m_source, name) for name in scientific_fields)
    wt = next(row for row in wt_source.constructs if row.construct_id == MATERIALS[0])
    mutant = next(row for row in i95m_source.constructs if row.construct_id == MATERIALS[1])
    differences = tuple(index+1 for index, (a, b) in enumerate(zip(wt.ssu_sequence, mutant.ssu_sequence, strict=True)) if a != b)
    source_match = source_match and wt.lsu_sequence == mutant.lsu_sequence and differences == (95,)
    source_disposition = A.SATISFIED if source_match else A.REFUSED
    if not source_match:
        reasons.append('MATCHED_SCIENTIFIC_SOURCE_OR_SOLE_I95M_EDIT_DIFFERS')
    apparatus = A.UNEVALUABLE
    if wt_chemical_plan is not None and i95m_chemical_plan is not None:
        same = all(getattr(wt_chemical_plan, name) == getattr(i95m_chemical_plan, name) for name in APPARATUS_FIELDS)
        owner_rows = tuple(tuple(row for row in plan.code_sources if row[0].startswith(SCIENCE_PREFIXES)
            and not row[0].endswith('/matched_controls.py')) for plan in (wt_chemical_plan, i95m_chemical_plan))
        source_complete = all(set(REQUIRED_NATIVE_OWNERS).issubset({name for name, _ in rows}) for rows in owner_rows)
        same = same and owner_rows[0] == owner_rows[1]
        if wt_nve_plan is not None and i95m_nve_plan is not None:
            same = same and all(getattr(wt_nve_plan, name) == getattr(i95m_nve_plan, name) for name in (
                'dependency_lock_sha256', 'ensembles', 'integration', 'numerical_window_picosecond',
                'receiver_cadence_picosecond', 'receiver_contract'))
            nve_owners = tuple(tuple(row for row in plan.code_sources if row[0].startswith(SCIENCE_PREFIXES)
                and not row[0].endswith('/matched_controls.py')) for plan in (wt_nve_plan, i95m_nve_plan))
            source_complete = source_complete and all(set(REQUIRED_NATIVE_OWNERS).issubset({name for name, _ in rows}) for rows in nve_owners)
            same = same and nve_owners[0] == nve_owners[1]
        apparatus = A.UNEVALUABLE if not source_complete else A.SATISFIED if same else A.REFUSED
        if not source_complete:
            reasons.append('MATCHED_NATIVE_OPERATOR_SOURCE_BINDINGS_MISSING')
        if not same:
            reasons.append('MATCHED_NUMERICAL_APPARATUS_DIFFERS')
    else:
        reasons.append('ACTUAL_CHEMICAL_PLAN_MISSING_FOR_APPARATUS_JOIN')
    paired_chemical, paired_nve, paired_refinements = [], [], []
    for parameter in CHEMICAL_KEYS:
        statuses = tuple(_chemical_status(episode, parameter) for episode, _, _ in (first, second))
        paired_chemical.append((parameter, *statuses, _aggregate(statuses)))
    for key in NVE_KEYS:
        statuses = tuple(_nve_status(episode, key) for episode, _, _ in (first, second))
        paired_nve.append((key, *statuses, _aggregate(statuses)))
    for key in REFINEMENT_KEYS:
        statuses = tuple(_refinement_status(episode, key) for episode, _, _ in (first, second))
        paired_refinements.append((key, *statuses, _aggregate(statuses)))
    outcomes = (source_disposition, apparatus, *(row[3] for rows in (paired_chemical, paired_nve, paired_refinements) for row in rows))
    if any(row is not A.SATISFIED for row in outcomes):
        reasons.append('SELECTED_MATCHED_NUMERICAL_CONTROLS_NOT_ALL_SATISFIED')
    return MatchedNumericalAssessment(product_id, (first[0], second[0]), source_disposition, apparatus,
        tuple(paired_chemical), tuple(paired_nve), tuple(paired_refinements), _aggregate(outcomes), tuple(sorted(reasons)))
