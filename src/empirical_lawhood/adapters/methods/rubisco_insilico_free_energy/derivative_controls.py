# SPDX-License-Identifier: MPL-2.0
"""Complete physical Cartesian derivative controls for one selected Hamiltonian.

This domain protocol and PURE reducer supply no launch, issue or qualification
authority. The original C4 source-LJ representation result is a reusable,
narrow dependency; this protocol addresses missing total QM/MM/boundary and
displacement-refinement evidence. Every original return is captured before
scientific interpretation through the existing raw-return custody owner.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
import gzip
from hashlib import sha256
import io
import math
from typing import ClassVar

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .raw_coupled_return import (
    BLOCK_BYTES, CoupledEvaluationRequest, RawCoupledReturn, assess_native_return,
    capture_native_return, return_outputs,
)

ASH_ANGSTROM_PER_BOHR = Decimal("0.5291772109303")
ROLES = frozenset(("QM", "MM", "BOUNDARY_QM", "BOUNDARY_MM"))
OUTCOMES = frozenset(("NOT_ENTERED", "UNKNOWN", "KNOWN_FAILURE", "RETURNED"))


def _identity(value):
    if type(value) is not ObjectIdentity:
        raise ValueError("derivative control requires exact source identities")
    value.__post_init__()


def _positive(value):
    if type(value) is not Decimal or not value.is_finite() or value <= 0:
        raise ValueError("derivative numerical settings need positive finite Decimal values")


def _nonnegative(value):
    if type(value) is not Decimal or not value.is_finite() or value < 0:
        raise ValueError("derivative relative settings need nonnegative finite Decimal values")


def _decimal(value):
    with localcontext() as context:
        context.prec = max(80, value.denominator.bit_length() * 30103 // 100000 + 40)
        return Decimal(value.numerator) / Decimal(value.denominator)


@dataclass(frozen=True, slots=True)
class PointFieldHamiltonian(CanonicalRecord):
    """Explicit realized point-field profile, separate from Gaussian embedding."""
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/point-field-hamiltonian"
    profile_id: str
    source_members: tuple[ObjectIdentity, ...]
    native_stock: ObjectIdentity
    term_census: ObjectIdentity
    model_scope: str
    embedding: str = "EXACT_ORDERED_POINT_CHARGES_HARDNESS99"
    quantum_method: str = "GFN2-xTB-6.7.1"
    classical_method: str = "SOURCE_AMBER_TERMS_AND_EXACT_LJ_SCEE_MASKS"
    boundary_method: str = "ASH_SIMPLE_LINK_1.09_ANGSTROM_ADV_PROJECTION_SHIFT_NO_DIPOLE"
    scc_maximum_iterations: int = 250
    scc_accuracy: Decimal = Decimal("0.05")
    electronic_temperature_kelvin: int = 300
    physical_or_chemical_adequacy: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.profile_id)
        if (not self.source_members or tuple(row.object_id for row in self.source_members)
                != tuple(sorted(set(row.object_id for row in self.source_members)))):
            raise ValueError("point-field Hamiltonian needs its complete exact source roster")
        for identity in (*self.source_members, self.native_stock, self.term_census):
            _identity(identity)
        if self.model_scope not in ("SYNTHETIC_ETHANE_CONTROL", "SOURCE_RR_REFERENCE_CONDITIONAL"):
            raise ValueError("current point-field construction does not support an inferred Gp/reactive state")
        if (self.embedding != "EXACT_ORDERED_POINT_CHARGES_HARDNESS99"
                or self.quantum_method != "GFN2-xTB-6.7.1"
                or self.classical_method != "SOURCE_AMBER_TERMS_AND_EXACT_LJ_SCEE_MASKS"
                or self.boundary_method != "ASH_SIMPLE_LINK_1.09_ANGSTROM_ADV_PROJECTION_SHIFT_NO_DIPOLE"
                or type(self.scc_maximum_iterations) is not int or self.scc_maximum_iterations != 250
                or self.scc_accuracy != Decimal("0.05") or self.electronic_temperature_kelvin != 300
                or self.physical_or_chemical_adequacy is not A.UNEVALUABLE):
            raise ValueError("point-field profile changes its source Hamiltonian or scientific SCC contract")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.profile_id, self)


@dataclass(frozen=True, slots=True)
class CartesianPoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/physical-cartesian-point"
    point_id: str
    atom_ids: tuple[str, ...]
    # Exact finite native binary64, including signed zero; no Decimal display cast.
    coordinates_angstrom_hex: tuple[tuple[str, str, str], ...]
    coordinate_frame: str = "prepared-physical-atom-order"

    def __post_init__(self):
        validate_stable_id(self.point_id)
        if (not self.atom_ids or len(set(self.atom_ids)) != len(self.atom_ids)
                or len(self.coordinates_angstrom_hex) != len(self.atom_ids)
                or self.coordinate_frame != "prepared-physical-atom-order"):
            raise ValueError("physical coordinate point omits its complete ordered atom denominator")
        for atom in self.atom_ids:
            if type(atom) is not str or not atom or "\x00" in atom:
                raise ValueError("physical atom identity must preserve its exact source spelling")
        for row in self.coordinates_angstrom_hex:
            if type(row) is not tuple or len(row) != 3:
                raise ValueError("physical point omits complete Cartesian coordinates")
            for token in row:
                if (type(token) is not str or not math.isfinite(float.fromhex(token))
                        or float.fromhex(token).hex() != token):
                    raise ValueError("physical point requires exact finite binary64 hexadecimal tokens")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.point_id, self)


@dataclass(frozen=True, slots=True)
class DerivativeProtocol(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/derivative-control-protocol"
    VERSION: ClassVar[str] = "1.1.0"
    protocol_id: str
    profile: PointFieldHamiltonian
    prepared_material: ObjectIdentity
    baseline: CartesianPoint
    # Every physical atom is checked along all three coordinates at h and h/2.
    physical_atom_roles: tuple[str, ...]
    displacement_angstrom: Decimal
    gradient_absolute_tolerance_eh_per_angstrom: Decimal
    gradient_relative_tolerance: Decimal
    refinement_absolute_tolerance_eh_per_angstrom: Decimal
    refinement_relative_tolerance: Decimal
    producing_provenance: ObjectIdentity
    retained_c4_dependency: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.protocol_id)
        self.profile.__post_init__()
        self.baseline.__post_init__()
        _identity(self.prepared_material)
        _identity(self.producing_provenance)
        if self.producing_provenance.object_schema != "empirical-lawhood/kernel/numerical-producing-provenance":
            raise ValueError("derivative protocol needs its complete one producing source/lock identity")
        if (len(self.physical_atom_roles) != len(self.baseline.atom_ids)
                or any(role not in ROLES for role in self.physical_atom_roles)
                or not {"BOUNDARY_QM", "BOUNDARY_MM"}.issubset(self.physical_atom_roles)):
            raise ValueError("complete physical QM/MM/boundary derivative coverage is required")
        for value in (self.displacement_angstrom, self.gradient_absolute_tolerance_eh_per_angstrom,
                      self.refinement_absolute_tolerance_eh_per_angstrom):
            _positive(value)
        for value in (self.gradient_relative_tolerance, self.refinement_relative_tolerance):
            _nonnegative(value)
        if self.retained_c4_dependency is not None:
            _identity(self.retained_c4_dependency)
        # Binary64 projection must actually move both sides at both resolutions.
        for atom in range(len(self.baseline.atom_ids)):
            for axis in range(3):
                center = Fraction.from_float(float.fromhex(self.baseline.coordinates_angstrom_hex[atom][axis]))
                for resolution in (1, 2):
                    step = Fraction(self.displacement_angstrom) / resolution
                    minus, plus = float(center - step), float(center + step)
                    if not all(math.isfinite(value) for value in (minus, plus)) or not minus < float(center) < plus:
                        raise ValueError("selected displacement is unrepresentable at an actual native coordinate")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.protocol_id, self)


def control_points(protocol):
    """Complete prospective point census; no source selection or native effect."""
    protocol.__post_init__()
    yield protocol.baseline
    for atom in range(len(protocol.baseline.atom_ids)):
        for axis in range(3):
            center = Fraction.from_float(float.fromhex(protocol.baseline.coordinates_angstrom_hex[atom][axis]))
            for resolution in (1, 2):
                step = Fraction(protocol.displacement_angstrom) / resolution
                for sign in (-1, 1):
                    rows = list(protocol.baseline.coordinates_angstrom_hex)
                    row = list(rows[atom])
                    row[axis] = float(center + sign * step).hex()
                    rows[atom] = tuple(row)
                    yield CartesianPoint(f"{protocol.protocol_id}.a{atom}.d{axis}.h{resolution}.{'minus' if sign < 0 else 'plus'}",
                                         protocol.baseline.atom_ids, tuple(rows))


def request_for_point(protocol, point, *, producing_provenance):
    protocol.__post_init__()
    point.__post_init__()
    if producing_provenance != protocol.producing_provenance:
        raise ValueError("derivative evaluation changes the whole control producing source/lock")
    if point == protocol.baseline:
        expected = point
    else:
        prefix = protocol.protocol_id + ".a"
        if not point.point_id.startswith(prefix):
            raise ValueError("derivative point changes its selected protocol")
        try:
            atom_text, axis_text, resolution_text, sign = point.point_id[len(prefix):].split(".")
            atom, axis, resolution = int(atom_text), int(axis_text[1:]), int(resolution_text[1:])
            if (axis_text != f"d{axis}" or resolution_text != f"h{resolution}"
                    or atom_text != str(atom) or not 0 <= atom < len(protocol.baseline.atom_ids)
                    or axis not in (0, 1, 2) or resolution not in (1, 2) or sign not in ("minus", "plus")):
                raise ValueError("invalid selected displacement")
            rows = list(protocol.baseline.coordinates_angstrom_hex)
            row = list(rows[atom])
            center = Fraction.from_float(float.fromhex(row[axis]))
            row[axis] = float(center + (-1 if sign == "minus" else 1)
                              * Fraction(protocol.displacement_angstrom) / resolution).hex()
            rows[atom] = tuple(row)
            expected = CartesianPoint(point.point_id, protocol.baseline.atom_ids, tuple(rows))
        except (ValueError, IndexError) as error:
            raise ValueError("derivative point substitutes its selected full Cartesian displacement") from error
    if expected != point:
        raise ValueError("derivative evaluation substitutes its complete selected physical point")
    return CoupledEvaluationRequest(point.point_id + ".evaluation", protocol.identity,
        protocol.prepared_material, point.identity, producing_provenance, len(point.atom_ids))


@dataclass(frozen=True, slots=True)
class DerivativeOutcome(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/derivative-control-outcome"
    request: CoupledEvaluationRequest
    contact_state: str
    returned: RawCoupledReturn | None
    reason: str

    def __post_init__(self):
        self.request.__post_init__()
        if self.contact_state not in OUTCOMES or not self.reason:
            raise ValueError("derivative outcome needs its actual known/unknown contact disposition")
        if (self.contact_state == "RETURNED") != (self.returned is not None):
            raise ValueError("derivative outcome invents or drops an actual raw native return")
        if self.returned is not None:
            self.returned.__post_init__()
            if self.returned.request != self.request.identity:
                raise ValueError("derivative outcome substitutes its original raw request")


@dataclass(frozen=True, slots=True)
class DerivativeComponent(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/derivative-component"
    VERSION: ClassVar[str] = "1.1.0"
    atom_id: str
    axis: int
    physical_role: str
    analytic_eh_per_angstrom: Decimal | None
    coarse_fd_eh_per_angstrom: Decimal | None
    refined_fd_eh_per_angstrom: Decimal | None
    gradient_scaled_error: Decimal | None
    refinement_scaled_error: Decimal | None
    disposition: A

    def __post_init__(self):
        if type(self.atom_id) is not str or not self.atom_id or "\x00" in self.atom_id:
            raise ValueError("derivative component changes its source atom spelling")
        if (type(self.axis) is not int or self.axis not in (0, 1, 2) or self.physical_role not in ROLES
                or type(self.disposition) is not A
                or self.disposition not in (A.SATISFIED, A.FALSIFIED, A.UNEVALUABLE)):
            raise ValueError("derivative component loses its selected physical scope")
        fields = (self.analytic_eh_per_angstrom, self.coarse_fd_eh_per_angstrom,
                  self.refined_fd_eh_per_angstrom, self.gradient_scaled_error, self.refinement_scaled_error)
        if any(value is not None and (type(value) is not Decimal or not value.is_finite()) for value in fields):
            raise ValueError("derivative component substitutes finite actual numerical operands")
        if self.disposition in (A.SATISFIED, A.FALSIFIED) and any(value is None for value in fields):
            raise ValueError("decisive derivative component lacks its complete h/h2 operands")
        errors = (self.gradient_scaled_error, self.refinement_scaled_error)
        if any(value is not None and value < 0 for value in errors):
            raise ValueError("derivative component scaled errors must be nonnegative")
        if self.disposition is A.UNEVALUABLE:
            if any(value is not None for value in fields):
                raise ValueError("unevaluable derivative component cannot invent missing h/h2 operands")
        elif self.disposition is not (A.FALSIFIED if any(value > 1 for value in errors) else A.SATISFIED):
            raise ValueError("derivative component disposition contradicts its unchanged error gates")


def _derivative_reasons(outcomes, numerical, components):
    reasons = set()
    for outcome, (_, state) in zip(outcomes, numerical, strict=True):
        if outcome.returned is None:
            reasons.add("SELECTED_NATIVE_EVALUATION_UNENTERED_UNKNOWN_OR_FAILED")
        elif state is not A.SATISFIED:
            reasons.add("COMPLETE_NATIVE_NUMERICAL_INTEGRITY_NOT_SATISFIED")
            captures = (outcome.returned.energy, outcome.returned.gradient)
            # This is the recorded dtype census, not a numerical array decode.
            float_dtypes = tuple(capture.dtype for capture in captures if capture is not None)
            if (state is A.UNSUPPORTED and len(float_dtypes) == 2
                    and all(len(dtype) > 2 and dtype[0] in "<>=|" and dtype[1] == "f"
                            and dtype[2:].isdigit() for dtype in float_dtypes)
                    and any(int(dtype[2:]) != 8 for dtype in float_dtypes)):
                reasons.add("SELECTED_BINARY64_NATIVE_INTERPRETATION_UNSUPPORTED")
    if any(row.disposition is A.FALSIFIED for row in components):
        reasons.add("TOTAL_ENERGY_GRADIENT_OR_DISPLACEMENT_REFINEMENT_FAILED")
    return tuple(sorted(reasons))


def _derivative_disposition(numerical, components):
    states = tuple(row.disposition for row in components)
    return (A.FALSIFIED if A.FALSIFIED in states or any(state is A.FALSIFIED for _, state in numerical)
            else A.UNEVALUABLE if A.UNEVALUABLE in states
            or any(state is not A.SATISFIED for _, state in numerical) else A.SATISFIED)


@dataclass(frozen=True, slots=True)
class DerivativeAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/rubisco-coupled/derivative-control-assessment"
    VERSION: ClassVar[str] = "1.1.0"
    assessment_id: str
    protocol: ObjectIdentity
    assessor_source: ObjectIdentity
    # Whole ordered actual request/contact/raw-return denominator.
    outcomes: tuple[DerivativeOutcome, ...]
    numerical_integrity: tuple[tuple[str, A], ...]
    components: tuple[DerivativeComponent, ...]
    disposition: A
    reason_codes: tuple[str, ...]
    physical_reference_adequacy: A = A.UNEVALUABLE
    chemical_state_adequacy: A = A.UNEVALUABLE
    kinetic_prediction: A = A.UNEVALUABLE

    def __post_init__(self):
        validate_stable_id(self.assessment_id)
        _identity(self.protocol)
        _identity(self.assessor_source)
        if (self.protocol.object_schema != DerivativeProtocol.SCHEMA
                or not self.outcomes or len({row.request.request_id for row in self.outcomes}) != len(self.outcomes)
                or tuple(row[0] for row in self.numerical_integrity) != tuple(row.request.request_id for row in self.outcomes)
                or type(self.disposition) is not A):
            raise ValueError("derivative assessment loses its exact original denominator")
        atoms = self.outcomes[0].request.physical_atom_count
        if (len(self.outcomes) != 1 + 12 * atoms or len(self.components) != 3 * atoms
                or len({(row.atom_id, row.axis) for row in self.components}) != 3 * atoms
                or any(type(state) is not A or state not in (A.SATISFIED, A.FALSIFIED, A.UNSUPPORTED, A.UNEVALUABLE)
                       for _, state in self.numerical_integrity)):
            raise ValueError("derivative assessment omits selected physical components or evaluation rows")
        for row in (*self.outcomes, *self.components):
            row.__post_init__()
        first = self.outcomes[0].request
        if any(row.request.protocol != self.protocol or row.request.physical_atom_count != atoms
               or row.request.prepared_material != first.prepared_material
               or row.request.producing_provenance != first.producing_provenance
               or row.request.physical_coordinates.object_schema != CartesianPoint.SCHEMA
               for row in self.outcomes):
            raise ValueError("derivative assessment changes its complete protocol/material/source census")
        point_ids = (first.physical_coordinates.object_id, *(f"{self.protocol.object_id}.a{atom}.d{axis}.h{resolution}.{sign}"
            for atom in range(atoms) for axis in range(3) for resolution in (1, 2) for sign in ("minus", "plus")))
        if (tuple(row.request.physical_coordinates.object_id for row in self.outcomes) != point_ids
                or tuple(row.request.request_id for row in self.outcomes) != tuple(name + ".evaluation" for name in point_ids)):
            raise ValueError("derivative assessment changes its complete ordered point denominator")
        for atom in range(atoms):
            rows = self.components[atom * 3:atom * 3 + 3]
            if (tuple(row.axis for row in rows) != (0, 1, 2)
                    or len({row.atom_id for row in rows}) != 1 or len({row.physical_role for row in rows}) != 1):
                raise ValueError("derivative assessment changes its full ordered physical component denominator")
        for index, component in enumerate(self.components):
            offset = 1 + 4 * index
            decisive = all(self.numerical_integrity[ordinal][1] is A.SATISFIED
                           for ordinal in (0, *range(offset, offset + 4)))
            if decisive == (component.disposition is A.UNEVALUABLE):
                raise ValueError("derivative component disposition contradicts its baseline/h/h2 native integrity")
        if any(outcome.returned is None and state is not A.UNEVALUABLE
               for outcome, (_, state) in zip(self.outcomes, self.numerical_integrity, strict=True)):
            raise ValueError("missing native derivative outcome cannot supply decisive numerical integrity")
        if self.disposition is not _derivative_disposition(self.numerical_integrity, self.components):
            raise ValueError("derivative assessment disposition contradicts its complete component/native outcomes")
        if self.reason_codes != _derivative_reasons(self.outcomes, self.numerical_integrity, self.components):
            raise ValueError("derivative assessment changes its complete sorted adverse reason census")
        if any(value is not A.UNEVALUABLE for value in (self.physical_reference_adequacy,
                self.chemical_state_adequacy, self.kinetic_prediction)):
            raise ValueError("finite-difference controls cannot establish reference chemistry or kinetics")


def evaluate_then_capture(request, native_function, progress, entry):
    """One actual already-authorized native return, retained before any guard.

    No begin/contact/complete/launcher, fallback, retry or guard is performed.
    A failure propagates to the existing custody owner without invented zeros.
    The caller owns actual source/coordinate/force/stock joins and cost closure.
    """
    request.__post_init__()
    declared = {row.output_id: row for row in entry.definition.outputs}
    if (entry.definition.configuration != request.identity
            or not {request.protocol, request.prepared_material, request.physical_coordinates,
                    request.producing_provenance}.issubset(entry.definition.sources)
            or any(declared.get(row.output_id) != row for row in return_outputs())):
        raise ValueError("native derivative return lacks its committed exact request/source/output slots")
    energy, gradient = native_function()
    return capture_native_return(request, energy, gradient, progress, entry)


def _raw_operand(capture, reader_for_manifest):
    """Authenticate this exact read again before using any numerical operand."""
    import numpy as np
    source = reader_for_manifest(capture.artifact_manifest)
    stored_hash, stored_size = sha256(), 0
    class HashingReader:
        def read(self, size=-1):
            nonlocal stored_size
            payload = source.read(BLOCK_BYTES if size < 0 else min(size, BLOCK_BYTES))
            stored_hash.update(payload)
            stored_size += len(payload)
            return payload
    digest, size = sha256(), 0
    try:
        with gzip.GzipFile(fileobj=HashingReader(), mode="rb") as stream:
            header = stream.read(capture.npy_header_bytes)
            digest.update(header)
            size += len(header)
            header_stream = io.BytesIO(header)
            if np.lib.format.read_magic(header_stream) != (2, 0):
                raise ValueError("derivative operand changes its original NPY revision")
            shape, fortran, dtype = np.lib.format.read_array_header_2_0(
                header_stream, max_header_size=capture.npy_header_bytes)
            if (tuple(shape) != capture.shape or dtype.str != capture.dtype or fortran
                    or header_stream.tell() != len(header) or dtype.hasobject
                    or dtype.kind != "f" or dtype.itemsize != 8):
                raise ValueError("derivative interpretation requires original binary64 shape and dtype")
            value = np.empty(shape, dtype=dtype)
            view = memoryview(value).cast("B")
            offset = 0
            while offset < len(view):
                payload = stream.read(min(BLOCK_BYTES, len(view)-offset))
                if not payload:
                    raise ValueError("derivative interpretation lost original native elements")
                view[offset:offset+len(payload)] = payload
                offset += len(payload)
                size += len(payload)
                digest.update(payload)
            if stream.read(1):
                raise ValueError("derivative operand adds unselected trailing bytes")
    finally:
        source.close()
    materialization = capture.artifact_manifest.materialization
    if (size != capture.uncompressed_bytes or digest.hexdigest() != capture.uncompressed_sha256
            or stored_size != materialization.size_bytes
            or stored_hash.hexdigest() != materialization.physical_sha256):
        raise ValueError("derivative numerical read differs from authentic complete raw custody")
    return value


def assess_derivative_control(protocol, outcomes, reader_for_manifest, *, assessor_source, assessment_id):
    """Independent total-energy/gradient h/h2 reduction from exact retained bytes."""
    protocol.__post_init__()
    _identity(assessor_source)
    point_count = 1 + 12 * len(protocol.baseline.atom_ids)
    if type(outcomes) is not tuple or len(outcomes) != point_count:
        raise ValueError("derivative assessment drops its full baseline/12N evaluation denominator")
    numerical, energies = [], {}
    baseline_gradient = None
    point_names = []
    coordinate_values = []
    for ordinal, (point, outcome) in enumerate(zip(control_points(protocol), outcomes, strict=True)):
        point_names.append(point.point_id)
        if ordinal:
            atom, axis = divmod((ordinal - 1) // 4, 3)
            coordinate_values.append(Fraction.from_float(float.fromhex(point.coordinates_angstrom_hex[atom][axis])))
        outcome.__post_init__()
        expected = request_for_point(protocol, point, producing_provenance=outcome.request.producing_provenance)
        if outcome.request != expected:
            raise ValueError("derivative assessment substitutes point, protocol, material, units or order")
        verdict = A.UNEVALUABLE
        if outcome.returned is not None:
            assessed = assess_native_return(outcome.request, outcome.returned, reader_for_manifest,
                                           assessor_source=assessor_source)
            verdict = assessed.disposition
            if verdict is A.SATISFIED:
                import numpy as np
                if any(np.dtype(capture.dtype).kind != "f" or np.dtype(capture.dtype).itemsize != 8
                       for capture in (outcome.returned.energy, outcome.returned.gradient)):
                    verdict = A.UNSUPPORTED
                else:
                    energy = _raw_operand(outcome.returned.energy, reader_for_manifest)
                    if ordinal == 0:
                        baseline_gradient = _raw_operand(outcome.returned.gradient, reader_for_manifest)
                    energies[point.point_id] = Fraction.from_float(float(energy.item()))
        numerical.append((outcome.request.request_id, verdict))
    components = []
    for atom, role in enumerate(protocol.physical_atom_roles):
        for axis in range(3):
            offset = (3 * atom + axis) * 4
            quartet = point_names[1 + offset:1 + offset + 4]
            if baseline_gradient is None or any(name not in energies for name in quartet):
                component = DerivativeComponent(protocol.baseline.atom_ids[atom], axis, role,
                                                None, None, None, None, None, A.UNEVALUABLE)
            else:
                analytic = Fraction.from_float(float(baseline_gradient[atom, axis])) / Fraction(ASH_ANGSTROM_PER_BOHR)
                values = []
                for index, (minus, plus) in enumerate((quartet[:2], quartet[2:])):
                    denominator = coordinate_values[offset + 2 * index + 1] - coordinate_values[offset + 2 * index]
                    values.append((energies[plus] - energies[minus]) / denominator)
                coarse, refined = values
                gradient_error = max(abs(coarse - analytic), abs(refined - analytic)) / (
                    Fraction(protocol.gradient_absolute_tolerance_eh_per_angstrom)
                    + Fraction(protocol.gradient_relative_tolerance) * abs(analytic))
                refinement_error = abs(refined - coarse) / (
                    Fraction(protocol.refinement_absolute_tolerance_eh_per_angstrom)
                    + Fraction(protocol.refinement_relative_tolerance) * abs(refined))
                verdict = A.SATISFIED if gradient_error <= 1 and refinement_error <= 1 else A.FALSIFIED
                component = DerivativeComponent(protocol.baseline.atom_ids[atom], axis, role,
                    *(_decimal(value) for value in (analytic, coarse, refined, gradient_error, refinement_error)), verdict)
            components.append(component)
    verdict = _derivative_disposition(numerical, components)
    return DerivativeAssessment(assessment_id, protocol.identity, assessor_source, outcomes,
                               tuple(numerical), tuple(components), verdict,
                               _derivative_reasons(outcomes, numerical, components))


def validate_derivative_assessment(assessment, protocol, reader_for_manifest):
    """Consumer recomputation; producer's assessment is never self-certification."""
    if type(assessment) is not DerivativeAssessment:
        raise ValueError("consumer requires typed independent derivative assessment")
    expected = assess_derivative_control(protocol, assessment.outcomes, reader_for_manifest,
        assessor_source=assessment.assessor_source, assessment_id=assessment.assessment_id)
    if assessment != expected:
        raise ValueError("supplied derivative assessment changes authentic complete raw reduction")
    return assessment
