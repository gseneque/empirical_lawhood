# SPDX-License-Identifier: MPL-2.0
"""Exact original E3 source/reservation joins before a TRAIN payload loader.

This owner checks typed source facts, declared causal availability and original
publication bytes. The API must authenticate the listed publications and their
availability through original custody. Neither constructors nor byte equality
establish genuine source eligibility, chronology, qualification or authority.
"""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.adapters.methods.matrix_prospective.records import MatrixProgrammeRole
from empirical_lawhood.adapters.methods.matrix_parameter_history.records import coordinate_identity
from empirical_lawhood.adapters.methods.matrix_scheduled_history.records import (
    ScheduledAllocation, ScheduledReservation, ScheduledSpecification, identity, physical_key, _publication,
)
from empirical_lawhood.adapters.simulators.six_matrix_response.parameter_history import MatrixParameterCoordinate
from empirical_lawhood.kernel.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.kernel.experimental_matching import PopulationReservationBinding
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.kernel.time import AvailabilitySpec, InformationCutoff
from empirical_lawhood.runtime.artifacts import ArtifactWriteResult
from empirical_lawhood.runtime.execution import TaskContext, WorkerInputKind, WorkerInputPort
from empirical_lawhood.runtime.experimental_matching import require_reserved_population
from empirical_lawhood.runtime.plans import ExecutionTask, ScientificInputSpec
from empirical_lawhood.runtime.prepared_native_invocation import PreparedInvocationContract, PreparedNativeInputContract

from .experiment_specification import MatrixResponseErrorSpecification


@dataclass(frozen=True, slots=True)
class ProtectedE3SourceInputs:
    specification: MatrixResponseErrorSpecification
    training_allocation: UnitAllocation
    reservation: ScheduledReservation
    native_specification: ScheduledSpecification
    nominal: MatrixParameterCoordinate
    nearby: MatrixParameterCoordinate
    shifted: MatrixParameterCoordinate

    def __post_init__(self):
        for name, kind in (("specification", MatrixResponseErrorSpecification), ("training_allocation", UnitAllocation),
                ("reservation", ScheduledReservation), ("native_specification", ScheduledSpecification),
                ("nominal", MatrixParameterCoordinate), ("nearby", MatrixParameterCoordinate), ("shifted", MatrixParameterCoordinate)):
            value = getattr(self, name)
            if type(value) is not kind:
                raise TypeError("protected E3 source inputs require exact original " + name)
            value.__post_init__()
        if (self.specification.evidence_scope != "PROSPECTIVE_REQUIRED"
                or self.specification.calibration_target_view != "MAX_PAIRED_VIEWS"
                or self.native_specification.selection.reservation != identity(self.reservation)):
            raise ValueError("protected E3 changes selected paired-view science or original native reservation")
        self.reservation.allocation.__post_init__()
        nominal_key = physical_key(self.nominal)
        for coordinate, temperature in ((self.nominal, Decimal(1)), (self.nearby, Decimal("1.25")), (self.shifted, Decimal(3))):
            key = physical_key(coordinate)
            if (coordinate.q != 2 or coordinate.family_id != "matrix-history.joint-decreasing-coupling"
                    or coordinate.primary_view.bath_temperature != temperature
                    or coordinate.primary_view.friction_gamma != Decimal(1) or coordinate.member.cross_coupling_gamma != Decimal(1)
                    or coordinate.primary_view.timestep != self.specification.measurement.primary_timestep
                    or coordinate.fine_view.timestep != self.specification.measurement.fine_timestep
                    or key[:5] + key[6:] != nominal_key[:5] + nominal_key[6:]):
                raise ValueError("protected E3 requires the complete nominal and two selected E6 physical regimes")
        declared = {coordinate_identity(row): row for row in self.reservation.allocation.coordinates}
        if set(declared) != {coordinate_identity(self.nominal), coordinate_identity(self.nearby), coordinate_identity(self.shifted)}:
            raise ValueError("protected E3 source omits or adds an original nominal/E6 coordinate")
        policies = {identity(row): row for row in self.native_specification.selection.prefix_policies}
        assignments = dict(self.native_specification.selection.coordinate_policies)
        if set(assignments) != set(declared) or any(policies[key].cutoff_tick != self.specification.measurement.origin_tick
                or policies[key].origin_sector != "Y" for key in assignments.values()):
            raise ValueError("protected E3 native selection changes its actual PRIMARY origin/cutoff policies")


def project_protected_e3_allocation(inputs):
    """Project actual originals; no labels/seeds or future populations are made."""
    if type(inputs) is not ProtectedE3SourceInputs:
        raise TypeError("protected E3 allocation requires its exact original source handle")
    inputs.__post_init__()
    spec, original, fresh = inputs.specification, inputs.training_allocation, inputs.reservation.allocation
    train = spec.population("TRAIN")
    units = tuple(row for row in original.units if (train.family_id is None or row.family_id == train.family_id)
        and (train.unit_ids is None or row.unit_id in train.unit_ids))
    original_roles = {row.unit_id: row.role for row in original.roles}
    if (len(units) != train.expected_units or train.unit_ids is not None and tuple(row.unit_id for row in units) != train.unit_ids
            or any(not row.exposed or original_roles[row.unit_id] not in ("train", "development") for row in units)):
        raise ValueError("protected E3 TRAIN changes the selected complete original exposed training population")
    projected = list(units)
    roles = [UnitRoleAssignment(row.unit_id, "train") for row in units]
    by_group = {}
    for row in fresh.roots:
        by_group.setdefault(row.root.independent_group_id, []).append(row)
    keys = {coordinate_identity(inputs.nominal): {MatrixProgrammeRole.CALIBRATION: "calibration", MatrixProgrammeRole.CONFIRMATION: "evaluation"},
        coordinate_identity(inputs.nearby): {MatrixProgrammeRole.WITHHELD_TRANSFER: "transfer_nearby"},
        coordinate_identity(inputs.shifted): {MatrixProgrammeRole.WITHHELD_TRANSFER: "transfer_shifted"}}
    for group, rows in sorted(by_group.items()):
        if len(rows) != 1:
            raise ValueError("protected E3 one whole root cannot be thinned or multiplied across coordinate cases")
        row = rows[0]
        role = keys[row.coordinate].get(row.root.role)
        if role is None:
            raise ValueError("protected E3 relabels original scheduled roles or withheld physical regimes")
        coordinate = next(c for c in fresh.coordinates if coordinate_identity(c) == row.coordinate)
        projected.append(IndependentUnit(group, fresh.allocation_id, coordinate.family_id, ("fine", "primary"), False))
        roles.append(UnitRoleAssignment(group, role))
    if len({row.unit_id for row in projected}) != len(projected):
        raise ValueError("protected E3 TRAIN and future/reserved original groups overlap")
    for selection in spec.populations:
        actual = tuple(sorted(row.unit_id for row in roles if row.role == selection.role.lower()))
        if (len(actual) != selection.expected_units or selection.unit_ids is not None and actual != selection.unit_ids):
            raise ValueError("protected E3 drops or substitutes an assigned whole-unit role denominator")
    sources = {}
    for reference in (*original.sources, original.identity, identity(fresh), identity(inputs.reservation), identity(inputs.native_specification)):
        if sources.setdefault(reference.object_id, reference) != reference:
            raise ValueError("protected E3 original source identities alias")
    digest = sha256((spec.fingerprint() + original.fingerprint() + fresh.fingerprint()).encode()).hexdigest()
    return UnitAllocation("allocation.matrix-e3.protected." + digest, tuple(sorted(sources.values(), key=lambda row: row.object_id)),
        tuple(sorted(projected, key=lambda row: row.unit_id)), tuple(sorted(roles, key=lambda row: row.unit_id)))


@dataclass(frozen=True, slots=True)
class E3RequiredPublication:
    key: str
    record: CanonicalRecord
    publication: ArtifactWriteResult
    availability: AvailabilitySpec

    def __post_init__(self):
        validate_stable_id(self.key)
        if (not isinstance(self.record, CanonicalRecord) or type(self.publication) is not ArtifactWriteResult
                or type(self.availability) is not AvailabilitySpec):
            raise TypeError("E3 pre-fit publications need their exact original record, custody and declared availability")
        _publication(self.publication, self.record)
        self.availability.__post_init__()
        if self.availability.outcome_access != self.publication.logical.outcome_access:
            raise ValueError("E3 pre-fit availability changes original publication outcome access")

    @property
    def artifact(self):
        logical, physical = self.publication.logical, self.publication.materialization
        return ArtifactIdentity(logical.logical_artifact_id, "original-e3-prefit-publication", logical.payload_schema,
            logical.content_sha256, logical.media_type, physical.size_bytes)


@dataclass(frozen=True, slots=True)
class ProtectedE3PublicationTransport:
    """Original publication joined to its exact current prepared byte copy.

    This transport witness carries no chronology, qualification or authority.
    Owning parent custody must authenticate the actual original publication.
    The prefit scientific record continues to name that original publication.
    """
    key: str
    original_publication: ArtifactWriteResult
    prepared_input: PreparedNativeInputContract
    scientific_edge: ScientificInputSpec

    def __post_init__(self):
        if (self.key not in ("allocation", "native-selection", "reservation", "roles")
                or type(self.original_publication) is not ArtifactWriteResult
                or type(self.prepared_input) is not PreparedNativeInputContract
                or type(self.scientific_edge) is not ScientificInputSpec):
            raise TypeError("protected E3 transport requires exact original, prepared input and scientific edge records")
        publication, contract, edge = self.original_publication, self.prepared_input, self.scientific_edge
        publication.__post_init__()
        contract.__post_init__()
        edge.__post_init__()
        expected_name = {"allocation": "original-allocation", "roles": "allocation"}.get(self.key, self.key)
        if (contract.logical != publication.logical
                or contract.physical_sha256 != publication.materialization.physical_sha256
                or contract.binding.size_bytes != publication.materialization.size_bytes
                or contract.binding.kind is not WorkerInputKind.EXTERNAL
                or edge.consumer_input_id != expected_name
                or edge.producer_task_id is not None or edge.producer_output_id is not None
                or edge.external_input_id is None
                or (edge.operational_logical_artifact_id, edge.payload_schema, edge.media_type,
                    edge.maximum_size_bytes, edge.outcome_access, edge.visibility_ceiling) != (
                    contract.artifact_id, contract.logical.payload_schema, contract.logical.media_type,
                    contract.binding.size_bytes, contract.logical.outcome_access, contract.logical.visibility_ceiling)):
            raise ValueError("protected E3 transport changes exact original bytes or current prepared external edge")


def e3_prepared_publication_transports(publications, context):
    """Project witnesses only from the actual complete prepared current fit.

    A copied input has its own materialization identity. Its exact prepared
    logical/physical bytes and compiled external edge must join the preserved
    original, without relabeling that copy as a historical publication.
    """
    if (type(context) is not TaskContext or type(context.prepared_invocation) is not PreparedInvocationContract
            or type(context.prepared_invocation.execution_task_record) is not ExecutionTask
            or type(publications) is not tuple or any(type(row) is not E3RequiredPublication for row in publications)
            or tuple(row.key for row in publications) != ("allocation", "native-selection", "reservation", "roles")):
        raise TypeError("protected E3 publication transport requires its actual complete prepared fit context")
    prepared = context.prepared_invocation
    prepared.validate_context(context)
    if (prepared.manifest.capability_key != "matrix-e3-protected.fit" or prepared.native_effect
            or prepared.task_id != context.task_id or prepared.execution_task_record.task_id != context.task_id):
        raise ValueError("protected E3 publication transport substitutes its actual current task")
    contracts = {row.artifact_id: row for row in prepared.inputs}
    ports = {row.artifact_id: row for row in context.input_ports}
    witnesses = []
    for row in publications:
        row.__post_init__()
        artifact_id = row.publication.logical.logical_artifact_id
        contract, port = contracts.get(artifact_id), ports.get(artifact_id)
        edges = tuple(edge for edge in prepared.execution_task_record.scientific_inputs
            if edge.operational_logical_artifact_id == artifact_id)
        external = tuple(value for value in prepared.execution_task_record.external_inputs
            if value.logical_artifact_id == artifact_id)
        if (contract is None or type(port) is not WorkerInputPort or port.binding != contract.binding
                or len(edges) != 1 or len(external) != 1
                or (external[0].expected_payload_schema, external[0].expected_content_sha256,
                    external[0].expected_media_type,
                    external[0].expected_outcome_access, external[0].expected_visibility_ceiling) != (
                    row.publication.logical.payload_schema, row.publication.logical.content_sha256,
                    row.publication.logical.media_type, row.publication.logical.outcome_access,
                    row.publication.logical.visibility_ceiling)
                or external[0].expected_size_bytes not in (None, row.publication.materialization.size_bytes)):
            raise ValueError("protected E3 publication transport loses exact actual prepared source custody")
        # Prospective compilation retains the scientific edge's bounded size
        # while its ordinary external spec deliberately leaves exact size
        # unspecified. The witness below still requires the authenticated
        # current binding size, physical digest and edge bound to equal the
        # original publication; an absent optional expectation adds no bytes.
        witnesses.append(ProtectedE3PublicationTransport(row.key, row.publication, contract, edges[0]))
    return tuple(witnesses)


@dataclass(frozen=True, slots=True)
class ProtectedE3PreFitJoin(CanonicalRecord):
    """Descriptive joins only; an API authenticates original custody separately."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-response-experiment/protected-prefit-join"
    record_id: str
    specification: ObjectIdentity
    allocation: ObjectIdentity
    training_allocation: ObjectIdentity
    original_allocation: ObjectIdentity
    reservation: ObjectIdentity
    native_specification: ObjectIdentity
    publications: tuple[tuple[str, ArtifactIdentity, str, AvailabilitySpec], ...]
    fit_cutoff: InformationCutoff

    def __post_init__(self):
        validate_stable_id(self.record_id)
        for value, kind in ((self.specification, MatrixResponseErrorSpecification), (self.allocation, UnitAllocation),
                (self.training_allocation, UnitAllocation), (self.original_allocation, ScheduledAllocation),
                (self.reservation, ScheduledReservation), (self.native_specification, ScheduledSpecification)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError("E3 pre-fit join substitutes an exact original scientific source")
        if (type(self.fit_cutoff) is not InformationCutoff or type(self.publications) is not tuple
                or tuple(row[0] for row in self.publications) != ("allocation", "native-selection", "reservation", "roles")):
            raise ValueError("E3 pre-fit join drops original reservation, role or selection publications")
        for _, artifact, materialization, availability in self.publications:
            if type(artifact) is not ArtifactIdentity or type(availability) is not AvailabilitySpec:
                raise TypeError("E3 pre-fit join requires exact original publication and availability records")
            validate_stable_id(materialization)
            self.fit_cutoff.require_allows(availability)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.record_id, self)


def _require_reserved_fit_publications(inputs, allocation, *, publications, ports, fit_cutoff, record_id,
        publication_transports=()):
    """Read only the four original metadata publications before TRAIN loading.

    The API must authenticate these exact publications, the current exposure
    census and their declared availability. This byte join does
    not replace that authentication or scientific source assessment.
    Without transport witnesses, ports must name the original materializations.
    Exact prepared copies use their actual current IDs only for byte delivery;
    the returned scientific join always preserves original publication IDs.
    """
    if (type(publications) is not tuple or any(type(row) is not E3RequiredPublication for row in publications)
            or tuple(row.key for row in publications) != ("allocation", "native-selection", "reservation", "roles")
            or type(ports) is not dict or set(ports) != {row.key for row in publications}
            or type(fit_cutoff) is not InformationCutoff):
        raise ValueError("protected E3 requires its complete four original publication ports before TRAIN loading")
    expected = {"allocation": inputs.reservation.allocation, "native-selection": inputs.native_specification.selection,
        "reservation": inputs.reservation, "roles": allocation}
    for row in publications:
        row.__post_init__()
        if row.record != expected[row.key]:
            raise ValueError("E3 pre-fit publication substitutes original source/reservation/role bytes")
        fit_cutoff.require_allows(row.availability)
    if (type(publication_transports) is not tuple
            or any(type(row) is not ProtectedE3PublicationTransport for row in publication_transports)
            or publication_transports and tuple(row.key for row in publication_transports) != tuple(row.key for row in publications)):
        raise ValueError("protected E3 transport requires the complete exact original publication census")
    transport_ids = {}
    for original, witness in zip(publications, publication_transports, strict=bool(publication_transports)):
        witness.__post_init__()
        port = ports[original.key]
        if (witness.original_publication != original.publication or type(port) is not WorkerInputPort
                or port.binding != witness.prepared_input.binding):
            raise ValueError("protected E3 transport substitutes its actual original or current prepared port")
        transport_ids[original.key] = port.materialization_id
    original = publications[0]
    binding = PopulationReservationBinding(record_id + ".original-allocation", allocation.identity,
        identity(inputs.reservation.allocation), "allocation_id", original.artifact,
        transport_ids.get(original.key, original.publication.materialization.materialization_id),
        ("calibration", "evaluation", "transfer_nearby", "transfer_shifted"))
    require_reserved_population(binding, allocation, inputs.reservation.allocation, ports["allocation"],
        fitting_unit_ids=allocation.unit_ids("train"))
    for row in publications[1:]:
        port, publication = ports[row.key], row.publication
        if (type(port) is not WorkerInputPort or (port.artifact_id, port.materialization_id, port.payload_schema,
                port.media_type, port.size_bytes, port.outcome_access, port.visibility_ceiling) != (
                publication.logical.logical_artifact_id, transport_ids.get(row.key, publication.materialization.materialization_id),
                publication.logical.payload_schema, publication.logical.media_type, publication.materialization.size_bytes,
                publication.logical.outcome_access, publication.logical.visibility_ceiling)):
            raise ValueError("E3 pre-fit port substitutes exact original reservation/selection/role custody")
        cursor = port.cursor()
        try:
            raw = cursor.read()
        finally:
            cursor.close()
        if raw != row.record.canonical_bytes():
            raise ValueError("E3 pre-fit port changes complete original publication bytes")
    return tuple((row.key, row.artifact, row.publication.materialization.materialization_id, row.availability)
        for row in publications)


def require_e3_reserved_fit_inputs(inputs, *, publications, ports, fit_cutoff, record_id,
        publication_transports=()):
    """Join the fixed scientific family after its exact source/allocation checks."""
    allocation = project_protected_e3_allocation(inputs)
    joined = _require_reserved_fit_publications(inputs, allocation, publications=publications, ports=ports,
        fit_cutoff=fit_cutoff, record_id=record_id, publication_transports=publication_transports)
    return ProtectedE3PreFitJoin(record_id, inputs.specification.identity, allocation.identity,
        inputs.training_allocation.identity, identity(inputs.reservation.allocation), identity(inputs.reservation),
        identity(inputs.native_specification), joined, fit_cutoff)
