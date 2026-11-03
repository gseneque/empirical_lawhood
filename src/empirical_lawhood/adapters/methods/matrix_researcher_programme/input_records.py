# SPDX-License-Identifier: MPL-2.0
"""Pure complete programme input joins, separate from custody and authority."""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING

from empirical_lawhood.adapters.methods.matrix_factor_confirmation.records import E1AllocationReservation
from empirical_lawhood.adapters.methods.matrix_factor_response.eligibility import MatrixFactorExposureCensus
from empirical_lawhood.adapters.methods.matrix_parameter_factor.records import MatrixParameterScalarDefinition
from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_records import MatrixE6EmpiricalTransportPolicy
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled
from empirical_lawhood.adapters.methods.matrix_scheduled_history.commitment import ScheduledExposureAudit, corpus_artifact
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_selection import ScheduledResponseSelection
from empirical_lawhood.adapters.methods.matrix_scheduled_history.source_index import ScheduledSourceIndex
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase
from .known_inputs import PHASE_INPUT_ROLES

if TYPE_CHECKING:
    from .scientific_design import MatrixProgrammeScientificDesign
    from .known_inputs import MatrixProgrammeInputCommitments

@dataclass(frozen=True, slots=True)
class ResolvedMatrixProgrammePhaseInputs:
    """Noncanonical operation-local bodies; no reusable admission decision."""
    role: str
    reservation: E1AllocationReservation | scheduled.ScheduledReservation
    native_specification: scheduled.ScheduledSpecification | None
    responses: ScheduledResponseSelection | None



@dataclass(frozen=True, slots=True)
class ResolvedMatrixProgrammeInputs:
    commitments: MatrixProgrammeInputCommitments
    scientific_design: MatrixProgrammeScientificDesign
    exposure_census: MatrixFactorExposureCensus
    exposure_audit: ScheduledExposureAudit
    producing_provenance: NumericalProducingProvenance
    scalar_definitions: tuple[MatrixParameterScalarDefinition, ...]
    phases: tuple[ResolvedMatrixProgrammePhaseInputs, ...]
    availability: AvailabilitySpec
    e6_policy: MatrixE6EmpiricalTransportPolicy

    def phase(self, role):
        for value in self.phases:
            if value.role == role:
                return value
        raise ValueError("unknown original programme input role: " + str(role))



def _require_assay(protocol, assay):
    for field in fields(assay):
        if field.name == "assay_id":
            continue
        if field.name == "array_artifact":
            actual = protocol.templates.array_artifact
        elif field.name == "members":
            actual = protocol.templates.members
        else:
            actual = getattr(protocol, field.name)
        if actual != getattr(assay, field.name):
            raise ValueError("programme response selection changes the frozen complete assay")



def _require_phase_science(phase, design, commitments, roots):
    """Join actual source settings to D without inferring choices from outcomes."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.selected_population import selected_e4_population_coordinates
    role = phase.role
    allocation = phase.reservation.allocation
    selected_pins = {root.coordinate for root in roots}
    coordinates = tuple(value for value in allocation.coordinates if scheduled.coordinate_identity(value) in selected_pins)
    if role == "e1":
        design.e1_criterion.validate_allocation(allocation, design.e1_factor_rule)
        return
    if role == "e2":
        source_design = design.e2
        expected_coordinates = source_design.coordinates
    else:
        source_design = design.training_protocol
        selected_roles = {"train": "TRAIN", "e3.calibration": "CALIBRATION", "e3.confirmation": "EVALUATION",
            "e5.development": "TRAIN", "e5.confirmation": "TRAIN",
            "e6.nearby": "TRANSFER_NEARBY", "e6.shifted": "TRANSFER_SHIFTED"}
        if role.startswith("e4."):
            expected_coordinates = selected_e4_population_coordinates(tuple(sorted(design.e4_preparation_coordinates,
                key=lambda value: value.family_id)),
                design.e4_development, namespace=commitments.namespace + ".e4")
        else:
            pin = dict(design.e3.role_coordinates)[selected_roles[role]]
            expected_coordinates = tuple(value for value in source_design.coordinates
                if scheduled.coordinate_identity(value) == pin)
    # E4 has one complete shared coordinate bank. An IID CAL/CONF draw may
    # legitimately omit a family while retaining all nine cases per group.
    if (allocation.coordinates if role.startswith('e4.') else coordinates) != expected_coordinates:
        raise ValueError("programme input substitutes the frozen complete physical/numerical coordinate census")
    native = phase.native_specification.selection
    if native.numerical_design != source_design.numerical_design:
        raise ValueError("programme input changes its frozen independent history numerical controls")
    if role.startswith("e4.") or role.startswith("e5."):
        nominal = dict(design.e3.role_coordinates)["TRAIN"]
        nominal_policy = dict(source_design.coordinate_policies)[nominal]
        expected_policies = tuple(value for value in source_design.prefix_policies
            if scheduled.identity(value) == nominal_policy)
        if (native.prefix_policies != expected_policies
                or any(pin != nominal_policy for _, pin in native.coordinate_policies)):
            raise ValueError("programme E4/E5 input substitutes its original frozen causal prefix policy")
    else:
        actual_pins = {scheduled.coordinate_identity(value) for value in allocation.coordinates}
        expected_bindings = tuple((coordinate, policy) for coordinate, policy in source_design.coordinate_policies
            if coordinate in actual_pins)
        policy_pins = {policy for _, policy in expected_bindings}
        expected_policies = tuple(value for value in source_design.prefix_policies if scheduled.identity(value) in policy_pins)
        if native.coordinate_policies != expected_bindings or native.prefix_policies != expected_policies:
            raise ValueError("programme input changes the exact frozen coordinate/prefix-policy join")
    group_coordinates = {}
    for root in roots:
        group_coordinates.setdefault(root.root.independent_group_id, set()).add(root.coordinate)
    if role.startswith("e4."):
        phase_design = getattr(design, role.replace('.', '_'))
        iid = phase_design.family_sampling_rule == 'IID_UNIFORM_FOUR_FAMILIES_NO_REDRAW'
        streams = commitments.e4_streams
        if iid and streams.family_seed_material_sha256 is None:
            raise ValueError('programme E4 IID family draw lacks its original committed material')
        expected_by_family = {}
        for coordinate in expected_coordinates:
            expected_by_family.setdefault(coordinate.family_id, set()).add(scheduled.coordinate_identity(coordinate))
        counts = dict.fromkeys(expected_by_family, 0)
        for group, pins in group_coordinates.items():
            families = tuple(family for family, expected in expected_by_family.items() if pins == expected)
            if len(families) != 1:
                raise ValueError("programme E4 group omits an original corner or centre coordinate")
            if iid and families[0] != streams.family(group):
                raise ValueError('programme E4 input changes its original IID family draw')
            counts[families[0]] += 1
        expected_groups = dict(design.phase_group_counts)[role] // len(expected_by_family)
        if not iid and any(count != expected_groups for count in counts.values()):
            raise ValueError("programme E4 input changes a complete per-family matched-group denominator")
        panels = dict(phase.responses.panels)
        for root in roots:
            group = root.root.independent_group_id
            if (root.streams != streams.streams(group, future=False)
                    or any(panel.streams != streams.streams(group, future=panel.role == 'INDEPENDENT_FUTURE')
                        for panel in panels[group])):
                raise ValueError('programme E4 input changes its original history/future stream recipe')
    elif any(len(pins) != 1 for pins in group_coordinates.values()):
        raise ValueError("programme input creates multiple histories inside an independent single-coordinate root")
    criterion = (design.e4_calibration_criterion if role == "e4.calibration"
        else design.e3_calibration_criterion if role == "e3.calibration" else None)
    if phase.responses.calibration_criterion != criterion:
        raise ValueError("programme input changes the original calibration construction rule")



def validate_programme_input_records(resolved):
    """Pure complete role/stream/design join after actual body authentication."""
    from empirical_lawhood.adapters.methods.matrix_researcher_programme.scientific_design import MatrixProgrammeScientificDesign
    from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
    from empirical_lawhood.adapters.methods.matrix_experimental_programme.e6_transport_science import validate_e6_transport_policy
    if type(resolved) is not ResolvedMatrixProgrammeInputs or type(resolved.scientific_design) is not MatrixProgrammeScientificDesign:
        raise TypeError("programme input joins require their exact current resolved bodies")
    original, design, census = resolved.commitments, resolved.scientific_design, resolved.exposure_census
    original.__post_init__()
    design.__post_init__()
    census.__post_init__()
    if tuple(value.role for value in resolved.phases) != PHASE_INPUT_ROLES:
        raise ValueError("programme input join omits the complete original phase census")
    original.scientific_design.require_record(design, design.identity)
    original.exposure_census.require_record(census, ObjectIdentity.from_record(census.census_id, census))
    audit = resolved.exposure_audit
    if type(audit) is not ScheduledExposureAudit or type(resolved.producing_provenance) is not NumericalProducingProvenance:
        raise TypeError("programme inputs omit original exposure audit or producing provenance bodies")
    audit.__post_init__()
    resolved.producing_provenance.__post_init__()
    original.exposure_audit.require_record(audit, scheduled.identity(audit))
    original.producing_provenance.require_record(resolved.producing_provenance, resolved.producing_provenance.identity)
    if audit.census != census or original.exposure_census.publication not in audit.prior_corpus:
        raise ValueError("programme exposure audit substitutes its actual original complete census publication")
    expected_scalars = {ObjectIdentity.from_record(value.definition_id, value): value for value in
        (design.e1_scalar_definition, design.e2.scalar_definition, design.training_protocol.scalar_definition)}
    if (type(resolved.scalar_definitions) is not tuple or tuple(ObjectIdentity.from_record(value.definition_id, value)
            for value in resolved.scalar_definitions) != tuple(value.record for value in original.scalar_definitions)
            or {ObjectIdentity.from_record(value.definition_id, value): value
                for value in resolved.scalar_definitions} != expected_scalars):
        raise ValueError("programme inputs substitute or omit exact original typed scalar definitions")
    for value, selected in zip(resolved.scalar_definitions, original.scalar_definitions, strict=True):
        value.__post_init__()
        selected.require_record(value, ObjectIdentity.from_record(value.definition_id, value))
    from .retained_training_continuation import retained_source_files
    from .completed_source import completed_source_files
    retained = retained_source_files(original)
    completed = completed_source_files(original)
    if len(retained) > 1 or len(completed) > 1 or {artifact for artifact, publication in original.support_files
            if (artifact, publication) not in (*retained, *completed)} != {
            design.training_protocol.full_factor_rule.scalar_closure.normalization_owner}:
        raise ValueError("programme inputs omit or substitute the exact original normalization source FILE")
    expected_counts = dict(design.phase_group_counts)
    group_owners, seed_owners, dev_families, allocation_members, source_indexes = {}, {}, {}, {}, {}
    exposed_groups, exposed_seeds = set(census.exposed_independent_groups), set(census.effective_seed_exclusions)

    def own_seed(seed, owner):
        if seed in exposed_seeds or seed_owners.setdefault(seed, owner) != owner:
            raise ValueError("programme inputs reuse an exposed stream or cross whole-group stream ownership")

    kinds = {"e1": MatrixProgrammeRole.CONFIRMATION, "e2": MatrixProgrammeRole.DEVELOPMENT,
        "train": MatrixProgrammeRole.DEVELOPMENT, "e3.calibration": MatrixProgrammeRole.CALIBRATION,
        "e3.confirmation": MatrixProgrammeRole.CONFIRMATION, "e4.development": MatrixProgrammeRole.DEVELOPMENT,
        "e4.calibration": MatrixProgrammeRole.CALIBRATION, "e4.confirmation": MatrixProgrammeRole.CONFIRMATION,
        "e5.development": MatrixProgrammeRole.DEVELOPMENT, "e5.confirmation": MatrixProgrammeRole.CONFIRMATION,
        "e6.nearby": MatrixProgrammeRole.WITHHELD_TRANSFER, "e6.shifted": MatrixProgrammeRole.WITHHELD_TRANSFER}
    e6_physics = set()
    other_physics = set()
    for phase, selected in zip(resolved.phases, original.phases, strict=True):
        if type(phase) is not ResolvedMatrixProgrammePhaseInputs:
            raise TypeError("programme phase join requires its exact operation-local resolved operands")
        reservation = phase.reservation
        reservation.__post_init__()
        selected.reservation.require_record(reservation, scheduled.identity(reservation))
        allocation = reservation.allocation
        if phase.role == "e1":
            if allocation.exposure != census:
                raise ValueError("E1 inputs substitute their actual original exposure census")
            roots = allocation.roots
            if allocation.coordinates != design.e1_coordinates:
                raise ValueError("E1 inputs substitute frozen full-history physical coordinates")
        else:
            native, responses = phase.native_specification, phase.responses
            if type(native) is not scheduled.ScheduledSpecification or type(responses) is not ScheduledResponseSelection:
                raise TypeError("programme role omits its actual original native or response selection")
            native.__post_init__()
            responses.validate_allocation(allocation)
            selected.native_specification.require_record(native, scheduled.identity(native))
            selected.responses.require_record(responses, responses.identity)
            if (allocation.exposure.census != census or native.selection.reservation != scheduled.identity(reservation)
                    or allocation.exposure.prior_scheduled_coordinates != audit.prior_scheduled_coordinates
                    or allocation.exposure.scheduled_audit != corpus_artifact(original.exposure_audit.publication)):
                raise ValueError("programme role substitutes original source parents or exposure census")
            if {pin for pin, _ in native.selection.coordinate_policies} != {
                    scheduled.coordinate_identity(value) for value in allocation.coordinates}:
                raise ValueError("programme source omits the complete original coordinate/prefix-policy census")
            ids = {protocol.public_source.root.root_id for protocol in responses.protocols}
            roots = tuple(root for root in allocation.roots if root.root.root_id in ids)
            if len(roots) != len(ids):
                raise ValueError("programme response drops a complete original coordinate case")
            by_root = {root.root.root_id: root for root in roots}
            coordinates = {scheduled.coordinate_identity(value): value for value in allocation.coordinates}
            policies = {scheduled.identity(value): value for value in native.selection.prefix_policies}
            coordinate_policies = dict(native.selection.coordinate_policies)
            index_key = scheduled.identity(reservation), scheduled.identity(native)
            if index_key not in source_indexes:
                source_indexes[index_key] = ScheduledSourceIndex.from_shared(reservation=reservation,
                    specification=native, provenances=(resolved.producing_provenance,))
            source_index = source_indexes[index_key]
            assay = design.e2.assay if phase.role == "e2" else design.training_assay
            for protocol in responses.protocols:
                public = protocol.public_source
                root = by_root[public.root.root_id]
                if (public.root != root.root or public.reservation != scheduled.identity(reservation)
                        or public.allocation != scheduled.identity(allocation)
                        or public.coordinate != coordinates[root.coordinate]
                        or public.policy != policies[coordinate_policies[root.coordinate]]):
                    raise ValueError("programme response substitutes its original source, coordinate or prefix policy")
                _require_assay(protocol, assay)
                # The bounded source identity joins specification, selection and
                # provenance without adding private operands to the public view.
                reference = source_index.reference(source_id=public.source.object_id, root_id=public.root.root_id,
                    provenance=resolved.producing_provenance.identity)
                public.validate_source(source_index.resolve(reference))
            for group, panels in responses.panels:
                for panel in panels:
                    category = "history" if panel.role == "COMMON_NOISE_PANEL" else "future"
                    for stream in panel.streams:
                        own_seed(stream.effective_seed, (phase.role, group, category, stream.purpose))
        _require_phase_science(phase, design, original, roots)
        allocation_pin = scheduled.identity(allocation)
        if allocation_pin not in allocation_members:
            allocation_members[allocation_pin] = (allocation, set())
        all_roots = allocation_members[allocation_pin][1]
        root_ids = {root.root.root_id for root in roots}
        if all_roots & root_ids:
            raise ValueError("programme roles alias one original reserved root")
        all_roots.update(root_ids)
        groups = {root.root.independent_group_id for root in roots}
        if len(groups) != expected_counts[phase.role]:
            raise ValueError("programme input changes its complete assigned whole-group denominator")
        for root in roots:
            group = root.root.independent_group_id
            if (root.root.role is not kinds[phase.role] or group in exposed_groups
                    or group_owners.setdefault(group, phase.role) != phase.role):
                raise ValueError("programme input reuses an exposed group or changes its original phase role")
            for stream in root.streams:
                own_seed(stream.effective_seed, (phase.role, group, "history", stream.purpose))
            if phase.role == "e4.development":
                family = next(value.family_id for value in allocation.coordinates
                    if scheduled.coordinate_identity(value) == root.coordinate)
                if dev_families.setdefault(group, family) != family:
                    raise ValueError("E4 matched group crosses declared preparation families")
        selected_coordinates = {root.coordinate for root in roots}
        physics = {scheduled.physical_key(value) for value in allocation.coordinates
            if scheduled.coordinate_identity(value) in selected_coordinates}
        (e6_physics if phase.role.startswith("e6.") else other_physics).update(physics)
    if len(e6_physics) != 2 or e6_physics & other_physics:
        raise ValueError("programme source consumes a full physical key reserved for E6")
    for allocation, selected_roots in allocation_members.values():
        if selected_roots != {root.root.root_id for root in allocation.roots}:
            raise ValueError("programme input omits an assigned original root from its complete role census")
    prior_scheduled = {value.key for value in census.scheduled_physical_exclusions}
    prior_constant = {value.key for value in census.constant_physical_exclusions}
    if (e6_physics & prior_scheduled or any((key[0], key[1], key[2], key[3], key[5], key[4], key[7], key[8])
            in prior_constant for key in e6_physics)):
        raise ValueError("programme E6 reserve reuses a previously exposed full physical regime")
    # Bind prospective fold ordinals to the actual declared DEV group census.
    family_groups = {family: sorted(group for group, selected in dev_families.items() if selected == family)
        for family in set(dev_families.values())}
    try:
        expected_folds = tuple(sorted((family_groups[family][ordinal], fold)
            for family, ordinal, fold in design.e4_revision.fold_slots))
    except (KeyError, IndexError) as error:
        raise ValueError("programme revision folds omit an actual declared DEV family/group") from error
    if original.revision_folds != expected_folds or set(dict(expected_folds)) != set(dev_families):
        raise ValueError("programme inputs change the original complete whole-group revision folds")
    availability = resolved.availability
    original.availability.require_record(availability,
        ObjectIdentity.from_record(original.availability.record.object_id, availability))
    if (availability.phase is not CausalPhase.PREPARATION or availability.outcome_access is not OutcomeAccess.OUTCOME_BLIND
            or availability.available_at is None or availability.available_at < 0):
        raise ValueError("programme input commitments lack actual blind pre-acquisition availability")
    policy = resolved.e6_policy
    original.e6_policy.require_record(policy, policy.identity)
    future_roles = (("CALIBRATION", "e3.calibration"), ("EVALUATION", "e3.confirmation"),
        ("TRANSFER_NEARBY", "e6.nearby"), ("TRANSFER_SHIFTED", "e6.shifted"))
    future = tuple((role, resolved.phase(slot).responses) for role, slot in future_roles)
    reservations = tuple(resolved.phase(slot).reservation for _, slot in future_roles)
    if any(value != reservations[0] for value in reservations[1:]):
        raise ValueError("programme changes the one original pre-TRAIN E3/E6 reserve")
    validate_e6_transport_policy(policy, candidate_specification=design.e3, future_reservation=reservations[0],
        future_response_selections=future, availability=(original.availability.record, availability),
        criterion=design.e6_policy.criterion)
