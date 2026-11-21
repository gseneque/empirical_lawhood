# SPDX-License-Identifier: MPL-2.0
"""Matched four-material relaxation design, separate from physical admission."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_bytes, validate_decimal, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_packet import ActiveModelPreparation
from empirical_lawhood.domains.rubisco.rubisco_response.materials import RubiscoMaterial, exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import PeriodicProbeSelection


MODEL_NAMES = ('m1-i95m', 'm1-wt', 'v1-i95m', 'v1-wt')


@dataclass(frozen=True, slots=True)
class ActiveRelaxationSettings(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-settings'
    settings_id: str
    maximum_gradient_kj_mol_nm: Decimal = Decimal('1')
    maximum_hydrogen_bond_angstrom: Decimal = Decimal('1.3')
    occupied_water_maximum_angstrom: Decimal = Decimal('2.8')
    unoccupied_water_minimum_angstrom: Decimal = Decimal('3.3')
    minimum_heavy_contact_angstrom: Decimal = Decimal('1.0')
    minimum_stereocentre_volume_angstrom3: Decimal = Decimal('0.01')
    scope: str = 'UNRESTRAINED_REFERENCE_MINIMIZATION_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.settings_id)
        for name in ('maximum_gradient_kj_mol_nm', 'maximum_hydrogen_bond_angstrom',
                'occupied_water_maximum_angstrom', 'unoccupied_water_minimum_angstrom',
                'minimum_heavy_contact_angstrom', 'minimum_stereocentre_volume_angstrom3'):
            value = getattr(self, name)
            validate_decimal(value, field_name=name, minimum=Decimal(0))
            if value == 0:
                raise ValueError('active relaxation requires explicit positive geometric and force tolerances')
        if self.occupied_water_maximum_angstrom >= self.unoccupied_water_minimum_angstrom:
            raise ValueError('relaxation occupancy basins overlap')
        if self.scope != 'UNRESTRAINED_REFERENCE_MINIMIZATION_WITHOUT_ENSEMBLE_OR_RATE_ADMISSION':
            raise ValueError('relaxation selection cannot establish an active ensemble or physical rate')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.settings_id, self)


@dataclass(frozen=True, slots=True)
class ActiveRelaxationMember(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-relaxation-member'
    model_name: str
    material: RubiscoMaterial
    representation: ObjectIdentity
    preparation: ObjectIdentity
    prototype: ObjectIdentity
    site_ids: tuple[str, ...]
    state_census: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        if self.model_name not in MODEL_NAMES:
            raise ValueError('matched relaxation requires an actual M1/V1 WT/I95M model')
        exact(self.material, RubiscoMaterial)
        for value in (self.representation, self.preparation, self.prototype):
            exact(value, ObjectIdentity)
        if (type(self.site_ids) is not tuple or len(self.site_ids) != 8
                or self.site_ids != tuple(sorted(set(self.site_ids)))
                or type(self.state_census) is not tuple or len(self.state_census) != 96
                or self.state_census != tuple(sorted(set(self.state_census)))
                or {r[0] for r in self.state_census} != set(self.site_ids)):
            raise ValueError('matched relaxation loses its complete site/state denominator')
        for value in self.site_ids:
            validate_stable_id(value)
        ssu = [c.sequence for c in self.material.chains if c.subunit == 'SSU']
        if (self.material.processing_view != self.model_name.split('-')[0]
                or any(len(sequence) < 95 or sequence[94] != ('M' if self.model_name.endswith('i95m') else 'I') for sequence in ssu)):
            raise ValueError('relaxation model name differs from actual processing and all-eight-SSU sequences')


@dataclass(frozen=True, slots=True)
class MatchedActiveRelaxationPlan(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/matched-active-relaxation-plan'
    plan_id: str
    members: tuple[ActiveRelaxationMember, ...]
    preparation_protocol: ObjectIdentity
    electronic_settings: ObjectIdentity
    molecular_settings: ObjectIdentity
    numerical_engine: ObjectIdentity
    settings: ActiveRelaxationSettings
    interpretation: str = 'FOUR_MATCHED_MATERIALS_EIGHT_NESTED_SITES_NO_INDEPENDENT_BIOLOGICAL_REPLICATION'

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        exact(self.settings, ActiveRelaxationSettings)
        for value in (self.preparation_protocol, self.electronic_settings, self.molecular_settings, self.numerical_engine):
            exact(value, ObjectIdentity)
        if type(self.members) is not tuple or tuple(m.model_name for m in self.members) != MODEL_NAMES:
            raise ValueError('matched relaxation requires the complete four-material census')
        for member in self.members:
            exact(member, ActiveRelaxationMember)
        for processing in ('m1', 'v1'):
            mutant, parent = [m for m in self.members if m.model_name.startswith(processing)]
            if (parent.site_ids != mutant.site_ids or parent.state_census != mutant.state_census
                    or parent.material.organism != mutant.material.organism):
                raise ValueError('paired relaxation changes a matched chemical/site context')
            for left, right in zip(parent.material.chains, mutant.material.chains, strict=True):
                if (left.chain_id, left.subunit, len(left.sequence)) != (right.chain_id, right.subunit, len(right.sequence)):
                    raise ValueError('paired relaxation changes the full sequence correspondence')
                differences = [(i, a, b) for i, (a, b) in enumerate(zip(left.sequence, right.sequence, strict=True), 1) if a != b]
                if differences != ([(95, 'I', 'M')] if left.subunit == 'SSU' else []):
                    raise ValueError('paired relaxation differs from the selected all-eight-SSU I95M substitution')
        if self.interpretation != 'FOUR_MATCHED_MATERIALS_EIGHT_NESTED_SITES_NO_INDEPENDENT_BIOLOGICAL_REPLICATION':
            raise ValueError('relaxation plan cannot invent biological replication or physical admission')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id, self)


def prepare_matched_relaxation_plan(*, models, settings):
    """Derive the complete matched roster from four retained preparations.

    Each input is (material, preparation, original periodic prototype). The
    author separately joins the full representation and all original arrays.
    """
    exact(settings, ActiveRelaxationSettings)
    if type(models) is not tuple or len(models) != 4:
        raise ValueError('relaxation design requires all four original prepared materials')
    members, contexts = [], []
    for material, prepared, prototype in models:
        exact(material, RubiscoMaterial)
        exact(prepared, ActiveModelPreparation)
        exact(prototype, PeriodicProbeSelection)
        if prepared.prototype != prototype.identity or prepared.representation != prototype.representation:
            raise ValueError('relaxation design substitutes an original complete preparation')
        amino = {c.sequence[94] for c in material.chains if c.subunit == 'SSU' and len(c.sequence) >= 95}
        if amino not in ({'I'}, {'M'}):
            raise ValueError('relaxation design has no uniform selected residue 95')
        name = material.processing_view+('-i95m' if amino == {'M'} else '-wt')
        sites = {site.identity: site.path.reactive_site_id for site in prepared.sites}
        members.append(ActiveRelaxationMember(name, material, prepared.representation, prepared.identity,
            prototype.identity, tuple(sites.values()),
            tuple(sorted((sites[s.site], s.state_label, s.water_occupancy) for s in prepared.seeds))))
        contexts.append((prepared.protocol.identity, prototype.electronic.identity,
            prototype.molecular.identity, prototype.engine.identity))
    if any(context != contexts[0] for context in contexts):
        raise ValueError('matched relaxation changes chemical, numerical or engine selections between arms')
    members = tuple(sorted(members, key=lambda m: m.model_name))
    digest = sha256((''.join(m.preparation.object_fingerprint for m in members)+settings.fingerprint()).encode()).hexdigest()
    return MatchedActiveRelaxationPlan('plan.gp-active-relaxation.'+digest, members, *contexts[0], settings)


def validate_relaxation_member(*, plan, model_name, prepared, prototype, representation):
    """Join one runtime model to its complete four-model matched design."""
    exact(plan, MatchedActiveRelaxationPlan)
    exact(prepared, ActiveModelPreparation)
    exact(prototype, PeriodicProbeSelection)
    selected = next((m for m in plan.members if m.model_name == model_name), None)
    if (selected is None or selected.material != representation.material
            or selected.representation != representation.identity or prepared.representation != representation.identity
            or selected.preparation != prepared.identity or selected.prototype != prototype.identity
            or prepared.prototype != prototype.identity or prototype.representation != representation.identity
            or (prepared.protocol.identity, prototype.electronic.identity, prototype.molecular.identity, prototype.engine.identity)
                != (plan.preparation_protocol, plan.electronic_settings, plan.molecular_settings, plan.numerical_engine)):
        raise ValueError('relaxation runtime changes a selected matched material or reference model')
    sites = {site.identity: site.path.reactive_site_id for site in prepared.sites}
    if selected.state_census != tuple(sorted((sites[s.site], s.state_label, s.water_occupancy) for s in prepared.seeds)):
        raise ValueError('relaxation runtime changes the complete selected state census')
    return selected


@dataclass(frozen=True, slots=True)
class ConditionalActiveRelaxationSelection(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/conditional-active-relaxation-selection'
    selection_id: str
    plan: ObjectIdentity
    state_census: tuple[tuple[str, str, str], ...]
    assumptions: tuple[str, ...]
    interpretation: str = 'PROSPECTIVE_MATCHED_SUBSET_UNSELECTED_STATES_UNMEASURED_NO_POPULATION_OR_RATE_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.selection_id)
        exact(self.plan, ObjectIdentity)
        if self.plan.object_schema != MatchedActiveRelaxationPlan.SCHEMA:
            raise ValueError('conditional relaxation requires its original complete matched plan')
        if (type(self.state_census) is not tuple or not 0 < len(self.state_census) <= 96
                or any(type(row) is not tuple or len(row) != 3
                    or any(type(value) is not str or not value for value in row) for row in self.state_census)
                or self.state_census != tuple(sorted(set(self.state_census)))):
            raise ValueError('conditional relaxation requires a nonempty exact ordered state selection')
        if (type(self.assumptions) is not tuple or not self.assumptions
                or any(type(value) is not str or not value.strip() or len(value) > 4096 for value in self.assumptions)
                or len(set(self.assumptions)) != len(self.assumptions)):
            raise ValueError('conditional relaxation requires explicit distinct chemical scenario assumptions')
        if self.interpretation != 'PROSPECTIVE_MATCHED_SUBSET_UNSELECTED_STATES_UNMEASURED_NO_POPULATION_OR_RATE_ADMISSION':
            raise ValueError('conditional relaxation cannot infer unmeasured states, populations or rates')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.selection_id, self)


def validate_conditional_relaxation_selection(plan, selection):
    exact(plan, MatchedActiveRelaxationPlan)
    exact(selection, ConditionalActiveRelaxationSelection)
    if (selection.plan != plan.identity
            or any(not set(selection.state_census).issubset(member.state_census) for member in plan.members)):
        raise ValueError('conditional relaxation changes its original plan or matched state membership')


def prepare_conditional_relaxation_selection(*, plan, state_census, assumptions):
    """Select the same prospective chemical/site scope in every complete material."""
    exact(plan, MatchedActiveRelaxationPlan)
    digest = sha256(canonical_json_bytes((plan.identity.to_document(), state_census, assumptions))).hexdigest()
    selection = ConditionalActiveRelaxationSelection('selection.conditional-active-relaxation.'+digest,
        plan.identity, state_census, assumptions)
    validate_conditional_relaxation_selection(plan, selection)
    return selection
