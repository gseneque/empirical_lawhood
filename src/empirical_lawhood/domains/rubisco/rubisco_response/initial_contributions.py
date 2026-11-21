# SPDX-License-Identifier: MPL-2.0
"""Minimal effective contributions to the selected conditional endpoints.

The entered objects are paired dimensionless quantities, not absolute rates.
Carbon commitment is shared across both endpoints. No oxygen time, separate
formation reversal, or collection of microscopic rates is required here.
Original scientific support and simultaneous coverage still need assessment.
"""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_mechanism.contracts import Exact
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_strings, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.initial_model_records import InitialContrastEvidence, InitialContrastReview, interval
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact, identities
from empirical_lawhood.domains.rubisco.rubisco_response.paired_endpoint_bounds import RATIO_ORDER
from empirical_lawhood.domains.rubisco.rubisco_response.physical_first_passage_science import rational


CONTRIBUTION_ORDER = ('formation', 'addition_discrimination', 'carbon_commitment',
    'carbon_exit_time', 'oxygen_commitment')
# One direct contrast, or numerator / denominator. All ratios are mutant / WT.
DEPENDENCIES = (('a', ('formation',)), ('r_c', ('carbon_commitment', 'carbon_exit_time')),
    ('c_over_o', ('addition_discrimination',)),
    ('chi_c_over_chi_o', ('carbon_commitment', 'oxygen_commitment')))


@dataclass(frozen=True, slots=True)
class InitialContribution(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-contribution'
    quantity: str
    bounds: tuple[Exact, Exact] | None
    evidence_kind: str
    sources: tuple[ObjectIdentity, ...]
    unresolved_requirement_ids: tuple[str, ...]

    def __post_init__(self):
        if self.quantity not in CONTRIBUTION_ORDER:
            raise ValueError('initial contribution changes the minimal paired quantity census')
        if self.evidence_kind not in {'SOURCE_CONDITIONED', 'COMPUTED', 'DERIVED_BOUND',
                'IMPOSED_ASSUMPTION', 'DISCLOSED_CONTROL', 'UNIDENTIFIED', 'FAILED'}:
            raise ValueError('initial contribution changes its original evidence meaning')
        missing = self.evidence_kind in {'UNIDENTIFIED', 'FAILED'}
        if missing != (self.bounds is None):
            raise ValueError('missing contribution cannot acquire a supplied ratio')
        if self.bounds is not None:
            interval(self.bounds)
        identities(self.sources, allow_empty=missing)
        require_sorted_unique_strings(self.unresolved_requirement_ids, field_name='unresolved_requirement_ids')
        if (missing or self.evidence_kind in {'IMPOSED_ASSUMPTION', 'DISCLOSED_CONTROL'}) and not self.unresolved_requirement_ids:
            raise ValueError('unsupported contribution must retain its missing physical support')


@dataclass(frozen=True, slots=True)
class InitialContributionRealization(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/initial-contribution-realization'
    contribution_id: str
    case: ObjectIdentity
    context: ObjectIdentity
    state_selection: ObjectIdentity
    alternative_id: str
    realization_id: str
    dependence_group_id: str
    support_kind: str
    contributions: tuple[InitialContribution, ...]
    interpretation: str = 'PAIRED_EFFECTIVE_RATIOS_WITH_SHARED_CARBON_COMMITMENT'

    def __post_init__(self):
        for name in ('contribution_id', 'alternative_id', 'realization_id', 'dependence_group_id'):
            validate_stable_id(getattr(self, name))
        for pin in (self.case, self.context, self.state_selection):
            exact(pin, ObjectIdentity)
        if self.support_kind not in {'FIXED_JOINT_REALIZATION', 'JOINT_SAMPLE', 'JOINT_ENCLOSURE'}:
            raise ValueError('initial contribution loses its joint support interpretation')
        if type(self.contributions) is not tuple or tuple(c.quantity for c in self.contributions) != CONTRIBUTION_ORDER:
            raise ValueError('initial contribution must retain all five quantities, including missing oxygen')
        for row in self.contributions:
            exact(row, InitialContribution)
        if self.support_kind != 'JOINT_ENCLOSURE' and any(
                c.bounds is not None and c.bounds[0] != c.bounds[1] for c in self.contributions):
            raise ValueError('a point realization cannot silently acquire interval support')
        if self.interpretation != 'PAIRED_EFFECTIVE_RATIOS_WITH_SHARED_CARBON_COMMITMENT':
            raise ValueError('initial contribution changes the effective competing-exit connection')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.contribution_id, self)


def _project(selected):
    exact(selected, InitialContributionRealization)
    quantities = {c.quantity:c for c in selected.contributions}
    result = {}
    for contrast, names in DEPENDENCIES:
        inputs = tuple(quantities[n] for n in names)
        if any(c.bounds is None for c in inputs):
            bounds = None
        elif len(inputs) == 1:
            bounds = inputs[0].bounds
        else:
            numerator, denominator = (c.bounds for c in inputs)
            bounds = tuple(Exact.of(n.fraction/d.fraction)
                for n,d in zip(numerator, reversed(denominator), strict=True))
        kinds = {c.evidence_kind for c in inputs}
        kind = next((k for k in ('FAILED', 'UNIDENTIFIED', 'DISCLOSED_CONTROL', 'IMPOSED_ASSUMPTION') if k in kinds), None)
        if kind is None:
            kind = 'DERIVED_BOUND' if bounds[0] != bounds[1] or 'DERIVED_BOUND' in kinds else (
                'COMPUTED' if 'COMPUTED' in kinds else 'SOURCE_CONDITIONED')
        result[contrast] = dict(bounds=bounds, evidence_kind=kind, inputs=inputs,
            unresolved=tuple(sorted({r for c in inputs for r in c.unresolved_requirement_ids})))
    return result


def read_initial_contributions(selected):
    """Exact arithmetic only; supplied bounds acquire no scientific authority."""
    projected = _project(selected)
    rows = {}
    for contrast, value in projected.items():
        bounds = value['bounds']
        names = tuple(c.quantity for c in value['inputs'])
        # Independently verify the two positive quotient endpoint balances.
        residuals = ()
        if bounds is not None:
            numerator = value['inputs'][0].bounds
            denominator = value['inputs'][1].bounds if len(names) == 2 else (Exact.of(1),)*2
            residuals = tuple(b.fraction*d.fraction-n.fraction
                for b,d,n in zip(bounds, reversed(denominator), numerator, strict=True))
            if any(residuals):
                raise ValueError('initial contribution quotient balance differs')
        rows[contrast] = dict(
            ratio_bounds=None if bounds is None else tuple(rational(v.fraction) for v in bounds),
            required_quantities=names, evidence_kind=value['evidence_kind'],
            unresolved_requirement_ids=value['unresolved'],
            exact_balance_residuals=tuple(rational(v) for v in residuals),
            physical_support='REQUIRES_ORIGINAL_CONTRAST_AND_JOINT_SUPPORT_REVIEW')
    return dict(selection=selected.identity.to_document(), case=selected.case.to_document(),
        context=selected.context.to_document(), state_selection=selected.state_selection.to_document(),
        alternative_id=selected.alternative_id, realization_id=selected.realization_id,
        dependence_group_id=selected.dependence_group_id, support_kind=selected.support_kind,
        original_contributions=tuple(c.to_document() for c in selected.contributions), contrasts=rows,
        shared_contributions={'carbon_commitment':('r_c', 'chi_c_over_chi_o')},
        interval_interpretation='OUTER_ENCLOSURE_OF_ENTERED_JOINT_SUPPORT_NO_NEW_COVERAGE',
        unrequested_operands=('ABSOLUTE_WT_RATES', 'OXYGEN_EXIT_TIME', 'SEPARATE_FORMATION_REVERSAL'),
        new_native_calls=0, physical_model_admission='UNEVALUABLE')


def initial_contrast_evidence(selected, *, reviews=()):
    """Prepare the existing reader's contrasts from one original joint row.

The caller publishes the original contribution record and supporting sources
through the existing artifact writer. No review or missing rate is generated.
"""
    if type(reviews) is not tuple:
        raise TypeError('contribution join needs the original contrast reviews')
    for review in reviews:
        exact(review, InitialContrastReview)
    if len({r.contrast for r in reviews}) != len(reviews):
        raise ValueError('contribution join duplicates a contrast review')
    by_name = {r.contrast:r for r in reviews}
    projected = _project(selected)
    result = []
    for contrast in RATIO_ORDER:
        row = projected[contrast]
        review = by_name.get(contrast)
        sources = {selected.identity, *(p for c in row['inputs'] for p in c.sources)}
        if review is not None:
            if ((review.case, review.context, review.state_selection, review.covered_bounds) !=
                    (selected.case, selected.context, selected.state_selection, row['bounds'])
                    or not sources.issubset(review.supporting_sources)):
                raise ValueError('contribution review substitutes the original case, values or source support')
            sources.update((review.identity, *review.supporting_sources))
        unresolved = set(row['unresolved'])
        if review is None:
            unresolved.add('requirement.'+selected.contribution_id+'.'+contrast+'.applicability-review')
        elif review.conditional_support.value != 'SATISFIED':
            unresolved.update(review.unresolved_requirement_ids)
        result.append(InitialContrastEvidence(contrast, row['bounds'], row['evidence_kind'],
            tuple(sorted(sources, key=lambda p:p.object_id)), review.identity if review else None,
            tuple(sorted(unresolved))))
    return tuple(result)


def validate_initial_contribution_projection(selected, case, alternative, realization, contrast):
    """Reconstruct an authenticated source's projection at original-read time."""
    if ((selected.case, selected.context, selected.state_selection, selected.alternative_id,
            selected.realization_id, selected.dependence_group_id, selected.support_kind) !=
            (case.case.identity, case.context.identity, case.state_selection, alternative.alternative_id,
            realization.realization_id, realization.dependence_group_id, realization.support_kind)):
        raise ValueError('initial contribution substitutes original case, chemical alternative or joint dependence')
    row = _project(selected)[contrast.contrast]
    sources = {selected.identity, *(p for c in row['inputs'] for p in c.sources)}
    if ((contrast.bounds, contrast.evidence_kind) != (row['bounds'], row['evidence_kind'])
            or not sources.issubset(contrast.sources)
            or not set(row['unresolved']).issubset(contrast.unresolved_requirement_ids)):
        raise ValueError('initial contribution differs from its original exact projection or missing operands')


__all__ = ('InitialContribution', 'InitialContributionRealization', 'CONTRIBUTION_ORDER',
    'read_initial_contributions', 'initial_contrast_evidence', 'validate_initial_contribution_projection')
