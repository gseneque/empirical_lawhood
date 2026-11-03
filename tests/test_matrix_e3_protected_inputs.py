# SPDX-License-Identifier: MPL-2.0
"""Exposed source/publication consistency controls; no eligible E3 evidence.

All scheduled groups, streams and chronology assertions are explicit synthetic
metadata. No native producer, issue, source qualifier or authority is invoked.
"""

from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response.protected_experiment_inputs import (
    E3RequiredPublication, ProtectedE3SourceInputs,
    project_protected_e3_allocation, require_e3_reserved_fit_inputs,
)
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole as Role, MatrixProgrammeRoot
from empirical_lawhood.adapters.methods.matrix_scheduled_history import records as scheduled_records
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess
from empirical_lawhood.kernel.time import AvailabilitySpec, CausalPhase, InformationCutoff
from empirical_lawhood.runtime.execution import VerifiedArtifactInput
from tests.test_matrix_experiment_methods import fixture, selected_input_records
from tests.test_matrix_factor_confirmation_eligibility import publish, stock as stock, provenance as provenance  # noqa: F401
from tests.test_matrix_scheduled_history import CONSTRUCTION, scheduled as scheduled  # noqa: F401


ROOT = Path(__file__).parents[1]


@pytest.fixture
def source_inputs(scheduled):  # noqa: F811
    return build_source_inputs(scheduled)


def build_source_inputs(scheduled, *, selected64=False):
    plane, old = scheduled
    exposed_spec, training_sources, _, methods = fixture(**dict(selected64=True, train_count=64,
        cal_count=64, eval_count=64, minimum_usable=58)) if selected64 else fixture()
    spec = replace(exposed_spec, evidence_scope="PROSPECTIVE_REQUIRED")
    original_banks = selected_input_records(training_sources, methods)
    training = training_sources[spec.population("TRAIN").source_key]
    folder = ROOT / "programmes/foundations/emergent-structure/records/matrix-e2-e3-candidate"
    nominal, nearby, shifted = (decode_canonical_bytes((folder / ("matrix.e3.deanneal." + name + ".canonical.json")).read_bytes(),
        MatrixParameterCoordinate, maximum_bytes=None) for name in ("nominal", "e6-nearby", "e6-shifted"))
    coordinates = tuple(sorted((nominal, nearby, shifted), key=lambda row: row.coordinate_id))
    roots, scopes = [], []
    for role_name, role, coordinate in (("calibration", Role.CALIBRATION, nominal), ("evaluation", Role.CONFIRMATION, nominal),
            ("transfer_nearby", Role.WITHHELD_TRANSFER, nearby), ("transfer_shifted", Role.WITHHELD_TRANSFER, shifted)):
        groups = []
        for index in range(spec.population(role_name.upper()).expected_units):
            group = "group.literal.e3." + role_name.replace("_", "-") + "." + str(index).zfill(3)
            groups.append(group)
            streams = tuple(MatrixHistorySeed(purpose, sha256(("EXPOSED.LITERAL.E3." + group + purpose).encode()).hexdigest())
                for purpose in HISTORY_PURPOSES)
            root = MatrixProgrammeRoot("root." + group, group, "regime.literal." + role_name.replace("_", "-"),
                coordinate.coordinate_id, role, coordinate.clock_id)
            roots.append(scheduled_records.ScheduledRoot(root, coordinate_identity(coordinate), streams))
        scopes.append(scheduled_records.ScheduledMatchedScope("scope.literal.e3." + role_name.replace("_", "-"), role,
            tuple(groups), (coordinate_identity(coordinate),), CONSTRUCTION))
    allocation = scheduled_records.ScheduledAllocation("allocation.literal.e3-original", coordinates,
        tuple(sorted(roots, key=lambda row: row.root.root_id)), tuple(sorted(scopes, key=lambda row: row.scope_id)), old[0].allocation.exposure)
    reservation = scheduled_records.ScheduledReservation("reservation.literal.e3-original", allocation, publish(plane, allocation, "literal.e3.allocation"))
    old_policy = old[0].policy
    policy = replace(old_policy, policy_id="policy.literal.e3", cutoff_tick=256, origin_sector="Y",
        factor_rule=replace(old_policy.factor_rule, lattice=tuple(range(0, 257, 16)), risk_start_tick=0,
            trailing_persistence_ticks=0))
    selection = scheduled_records.ScheduledSelection("selection.literal.e3-original", scheduled_records.identity(reservation),
        old[0].numerical_design, (policy,), tuple((coordinate_identity(row), scheduled_records.identity(policy)) for row in coordinates))
    native = scheduled_records.ScheduledSpecification("specification.literal.e3-original", selection,
        publish(plane, selection, "literal.e3.selection"))
    inputs = ProtectedE3SourceInputs(spec, training, reservation, native, nominal, nearby, shifted)
    projected = project_protected_e3_allocation(inputs)
    availability = AvailabilitySpec("clock.literal.e3-publications", CausalPhase.PREPARATION, OutcomeAccess.OUTCOME_BLIND, D(0))
    cutoff = InformationCutoff("cutoff.literal.e3-before-train", availability.clock_id, CausalPhase.PREPARATION, D(1))
    publications = tuple(E3RequiredPublication(key, record, publication, availability) for key, record, publication in (
        ("allocation", allocation, reservation.publication), ("native-selection", selection, native.publication),
        ("reservation", reservation, publish(plane, reservation, "literal.e3.reservation")),
        ("roles", projected, publish(plane, projected, "literal.e3.roles"))))
    return SimpleNamespace(inputs=inputs, plane=plane, publications=publications, fit_cutoff=cutoff, allocation=projected,
        train_features=original_banks["train-features"], train_outcomes=original_banks["train-outcomes"], provenance=old[0].provenance)


def opened(case):
    return {row.key: case.plane.open(VerifiedArtifactInput(row.publication.logical, row.publication.materialization),
        maximum_bytes=None) for row in case.publications}


def join(case, *, publications=None, ports=None):
    selected_ports = opened(case) if ports is None else ports
    try:
        return require_e3_reserved_fit_inputs(case.inputs,
            publications=case.publications if publications is None else publications, ports=selected_ports,
            fit_cutoff=case.fit_cutoff, record_id="join.literal.e3-prefit")
    finally:
        if ports is None:
            for port in selected_ports.values():
                port.close()


def test_exact_original_reserve_and_role_publications_preserve_canonical_join(source_inputs):
    case = source_inputs
    originals = tuple(record.canonical_bytes() for record in (case.inputs.training_allocation,
        case.inputs.reservation, case.inputs.native_specification))
    ports = opened(case)
    try:
        joined = join(case, ports=ports)
        assert joined.allocation == case.allocation.identity
        assert case.allocation.role_counts == (("calibration", 20), ("evaluation", 8), ("train", 12), ("transfer_nearby", 2), ("transfer_shifted", 2))
        assert all(port.tell() == 0 for port in ports.values())
        assert joined.canonical_bytes() == decode_canonical_bytes(joined.canonical_bytes(), type(joined), maximum_bytes=None).canonical_bytes()
    finally:
        for port in ports.values():
            port.close()
    assert originals == tuple(record.canonical_bytes() for record in (case.inputs.training_allocation,
        case.inputs.reservation, case.inputs.native_specification))


@pytest.mark.parametrize("damage", ("late", "missing", "changed-roles", "changed-reservation", "reused-port"))
def test_publication_inconsistencies_refuse_the_original_join(source_inputs, damage):
    case = source_inputs
    publications, ports = case.publications, opened(case)
    if damage == "late":
        publications = tuple(replace(row, availability=replace(row.availability, available_at=D(2))) if row.key == "reservation" else row for row in publications)
    elif damage == "missing":
        publications = publications[:-1]
    elif damage == "changed-roles":
        changed = replace(case.allocation, allocation_id="allocation.literal.changed")
        publications = tuple(replace(row, record=changed, publication=publish(case.plane, changed, "literal.changed-roles")) if row.key == "roles" else row for row in publications)
    elif damage == "changed-reservation":
        changed = replace(case.inputs.reservation, reservation_id="reservation.literal.changed")
        publications = tuple(replace(row, record=changed, publication=publish(case.plane, changed, "literal.changed-reservation")) if row.key == "reservation" else row for row in publications)
    else:
        ports["reservation"].close()
        ports["reservation"] = ports["roles"]
    try:
        with pytest.raises((ValueError, PermissionError)):
            join(case, publications=publications, ports=ports)
    finally:
        for port in {id(port): port for port in ports.values()}.values():
            port.close()


@pytest.mark.parametrize("damage", ("withheld-group", "exposed-group", "purpose", "exposed-stream", "changed-physics", "nominal-overlap", "late-selection"))
def test_original_e6_whole_groups_purposes_exposure_and_physical_regimes_refuse(source_inputs, damage):
    case = source_inputs
    original = case.inputs.reservation.allocation
    with pytest.raises(ValueError):
        if damage == "withheld-group":
            replace(original, roots=original.roots[:-1])
        elif damage in ("exposed-group", "exposed-stream"):
            row = original.roots[-1]
            census = original.exposure.census
            census = replace(census, exposed_independent_groups=tuple(sorted((*census.exposed_independent_groups, row.root.independent_group_id)))) if damage == "exposed-group" else replace(census,
                effective_seed_exclusions=tuple(sorted((*census.effective_seed_exclusions, row.streams[0].effective_seed))))
            replace(original, exposure=replace(original.exposure, census=census))
        elif damage == "purpose":
            replace(original.roots[-1], streams=original.roots[-1].streams[:-1])
        elif damage in ("changed-physics", "nominal-overlap"):
            coordinate = case.inputs.nearby
            coordinate = replace(coordinate, autonomous_ticks=coordinate.autonomous_ticks + 16,
                observation_ticks=(*coordinate.observation_ticks, coordinate.total_ticks + 16)) if damage == "changed-physics" else case.inputs.nominal
            replace(case.inputs, nearby=coordinate)
        else:
            selection = replace(case.inputs.native_specification.selection, reservation=scheduled_records.identity(replace(case.inputs.reservation,
                reservation_id="reservation.literal.foreign")))
            native = scheduled_records.ScheduledSpecification("specification.literal.foreign", selection,
                publish(case.plane, selection, "literal.e3.foreign-selection"))
            replace(case.inputs, native_specification=native)
