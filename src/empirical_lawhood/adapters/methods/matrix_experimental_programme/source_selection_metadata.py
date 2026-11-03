# SPDX-License-Identifier: MPL-2.0
"""Private original source metadata projection, shared by guarded domain owners.

Each public owner validates its exact specification type and immutable records
before calling. Explicit frozen fields carry no outcome, qualification or
issue authority. Numerical/statistical outcome reducers are not imported here.
"""

from hashlib import sha256

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as original_identity, physical_key
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_matching import MatchedArmDesign, MatchedCoordinate
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import canonical_json_bytes
from empirical_lawhood.runtime.experimental_matching import validate_matched_arms

from .records import MatrixFrozenConsumerPackage, MatrixProgrammeRoster


def _source_allocation(*, phase: str, selection_sha256: str, roster: MatrixProgrammeRoster):
    """Derive units from original allocation members; views/arms remain nested."""
    from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import identity as allocation_identity

    sources = tuple(sorted((allocation_identity(row) for row in roster.allocations), key=lambda row: row.object_id))
    groups = {}
    for case in roster.cases:
        public = case.public_source
        prior = groups.setdefault(case.unit_id, case)
        if prior.public_source.root.role is not public.root.role:
            raise ValueError("matched preparation/transfer unit crosses its original scientific role")
    units = tuple(IndependentUnit(unit, case.public_source.allocation.object_id, case.public_source.root.regime_id,
        tuple(sorted((case.public_source.coordinate.primary_view.view_id, case.public_source.coordinate.fine_view.view_id))),
        case.public_source.root.role is MatrixProgrammeRole.DEVELOPMENT) for unit, case in sorted(groups.items()))
    role = "opportunity" if phase == "E5_OPPORTUNITY" else "confirmation" if phase == "E5_CONFIRMATION" else "transfer"
    return UnitAllocation("allocation.matrix-later." + selection_sha256, sources, units,
        tuple(UnitRoleAssignment(row.unit_id, role) for row in units))



def _validate_source_metadata(*, phase: str, roster_reference: ObjectIdentity, package_reference: ObjectIdentity,
        expected_groups: int, arm_ids: tuple[str, ...], transfer_regime_ids: tuple[str, ...], selection_sha256: str,
        roster: MatrixProgrammeRoster, package: MatrixFrozenConsumerPackage) -> tuple[UnitAllocation, MatchedArmDesign | None]:
    if type(roster) is not MatrixProgrammeRoster or type(package) is not MatrixFrozenConsumerPackage:
        raise TypeError("private source metadata requires its exact original roster and frozen package")
    if (roster.identity != roster_reference or roster.phase != phase
            or package.identity != package_reference or original_identity(roster.reservation) != package.reservation):
        raise ValueError("later Matrix changes its selected original roster/package/prior reservation")
    if any(case.arm_id not in arm_ids for case in roster.cases):
        raise ValueError("later Matrix adds an unselected preparation arm")
    if any(case.preparation_duration != case.public_source.coordinate.physical_time(case.public_source.policy.cutoff_tick)
            for case in roster.cases):
        raise ValueError("later Matrix changes its actual matched preparation duration/physical clock")
    allocation = _source_allocation(phase=phase, selection_sha256=selection_sha256, roster=roster)
    units = allocation.unit_ids()
    if set(units) & set(package.training_unit_ids):
        raise ValueError("later evaluation consumes original model training units")
    if phase in ("E5_CONFIRMATION", "E6_TRANSFER") and set(units) & set(package.selection_unit_ids):
        raise ValueError("later fresh confirmation/transfer population was used for upstream calibration/model/recipe selection")
    required_role = MatrixProgrammeRole.DEVELOPMENT if phase == "E5_OPPORTUNITY" else (
        MatrixProgrammeRole.CONFIRMATION if phase == "E5_CONFIRMATION" else MatrixProgrammeRole.WITHHELD_TRANSFER)
    if any(case.public_source.root.role is not required_role for case in roster.cases):
        raise ValueError("later Matrix cannot relabel exposed development roots as fresh confirmation/transfer")
    if phase == "E6_TRANSFER":
        if len(units) != 2 * expected_groups:
            raise ValueError("E6 regimes reuse independent groups instead of two separately allocated populations")
        regimes = {case.public_source.root.regime_id for case in roster.cases}
        if regimes != set(transfer_regime_ids):
            raise ValueError("E6 changes its complete original two-regime census")
        if len(roster.allocations) != 1 or original_identity(roster.allocations[0]) != original_identity(roster.reservation.allocation):
            raise ValueError("E6 must use its actual complete originally reserved source allocation")
        all_reserved = {row.root.root_id for row in roster.reservation.allocation.roots
            if row.root.role is MatrixProgrammeRole.WITHHELD_TRANSFER}
        if all_reserved != {case.public_source.root.root_id for case in roster.cases}:
            raise ValueError("E6 drops or substitutes an actual originally reserved transfer root")
        physics = {}
        for regime in transfer_regime_ids:
            cases = tuple(case for case in roster.cases if case.public_source.root.regime_id == regime)
            ids = tuple(sorted(case.unit_id for case in cases))
            if len(ids) != expected_groups or len(set(ids)) != len(ids):
                raise ValueError("E6 omits independent units or counts nested cases as fresh roots")
            keys = {physical_key(case.public_source.coordinate) for case in cases}
            if len(keys) != 1:
                raise ValueError("E6 regime mixes whole source-defined physical conditions")
            physics[regime] = next(iter(keys))
        if len(set(physics.values())) != 2:
            raise ValueError("E6 labels do not create two different untouched physical regimes")
        return allocation, None
    if len(units) != expected_groups:
        raise ValueError("E5 changes its complete independent matched-group denominator")
    cases = roster.cases
    by_allocation = {original_identity(row): row for row in roster.allocations}
    coordinates = []
    for case in cases:
        public = case.public_source
        roots = tuple(row for row in by_allocation[public.allocation].roots if row.root.root_id == public.root.root_id)
        original_root, = roots
        c = public.coordinate
        restored = (c.q, c.member.mass_x, c.member.mass_y, c.member.cross_coupling_gamma, c.member.beta_rule,
            c.primary_view.bath_temperature, c.primary_view.friction_gamma, c.primary_view.timestep,
            c.fine_view.timestep, c.primary_view.precision, c.primary_view.integrator,
            c.primary_view.time_unit, c.primary_view.rng_algorithm, c.primary_view.rng_version,
            c.primary_view.stream_derivation_rule_id,
            tuple(float(value).hex() for value in c.couplings(public.policy.cutoff_tick)))
        values = tuple(sorted((("assay", case.assay.object_fingerprint),
            ("duration", case.preparation_duration), ("initial-state", sha256(canonical_json_bytes((case.initial_state.sha256,
                case.initial_state.payload_schema, case.initial_state.media_type, case.initial_state.size_bytes))).hexdigest()),
            ("recipe", case.recipe.object_fingerprint), ("restored-context", case.restored_context.object_fingerprint),
            ("restored-physical-values", sha256(canonical_json_bytes(restored)).hexdigest()),
            ("dt", public.coordinate.primary_view.timestep),
            *(('stream.' + stream.purpose, stream.effective_seed) for stream in original_root.streams))))
        coordinates.append(MatchedCoordinate(case.unit_id, case.arm_id,
            ObjectIdentity.from_record(case.case_id, case), values))
    coordinates = tuple(sorted(coordinates, key=lambda row: (row.unit_id, row.arm_id)))
    design = MatchedArmDesign("design.matrix-later." + selection_sha256, allocation.identity,
        arm_ids, tuple(name for name, _ in coordinates[0].values), ("recipe",), coordinates)
    validate_matched_arms(design, allocation)
    for arm in arm_ids:
        if len({case.recipe for case in cases if case.arm_id == arm}) != 1:
            raise ValueError("E5 fixed recipe changes across assigned development/confirmation groups")
    return allocation, design
