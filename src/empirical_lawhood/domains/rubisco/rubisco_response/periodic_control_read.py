# SPDX-License-Identifier: MPL-2.0
"""Independent retained numerical comparisons; no engine imports or native calls."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
import io
import math
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import periodic_geometry_policy
from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.derivative_controls import _raw_operand
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_operation import capability_for, definition_for, selected_request
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import BOHR_ANGSTROM, PeriodicControlPoint, PeriodicControlProtocol, PeriodicRefinementBudget, control_points, displaced_coordinates, point_coordinates, validate_control_point
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_translation import validate_configs
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeResult
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import PeriodicProbeReadout, _CompletedByteReader, read_original_periodic_return
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import OPEN_REQUIREMENTS, validate_periodic_probe_model


@dataclass(frozen=True, slots=True)
class ControlPointReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-control-point-readout'
    point: PeriodicControlPoint
    original: PeriodicProbeReadout | None

    def __post_init__(self):
        exact(self.point, PeriodicControlPoint)
        if self.original is not None:
            exact(self.original, PeriodicProbeReadout)
            if (self.original.selection != self.point.identity
                    or self.original.geometry_quality.coordinate_sha256 not in (None, self.point.coordinate_sha256)):
                raise ValueError('periodic control readout substitutes its original numerical point')


@dataclass(frozen=True, slots=True)
class DirectionalComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-directional-comparison'
    direction: ObjectIdentity
    step_bohr: Decimal
    previous_step_bohr: Decimal | None
    minus_point: ObjectIdentity
    plus_point: ObjectIdentity
    energy_difference_hartree_per_bohr: Decimal | None
    gradient_projection_hartree_per_bohr: Decimal | None
    absolute_error_hartree_per_bohr: Decimal | None
    step_change_hartree_per_bohr: Decimal | None
    maximum_midpoint_shift_bohr: Decimal | None
    energy_roundoff_bound_hartree_per_bohr: Decimal | None
    disposition: A

    def __post_init__(self):
        for pin in (self.direction, self.minus_point, self.plus_point):
            exact(pin, ObjectIdentity)
        validate_decimal(self.step_bohr, field_name='step_bohr', minimum=Decimal(0))
        if self.step_bohr == 0 or type(self.disposition) is not A:
            raise ValueError('periodic comparison changes its finite step or disposition')
        if self.previous_step_bohr is not None:
            validate_decimal(self.previous_step_bohr, field_name='previous_step_bohr', minimum=self.step_bohr)
            if self.previous_step_bohr == self.step_bohr:
                raise ValueError('periodic comparison repeats a displacement step')
        values = (self.energy_difference_hartree_per_bohr, self.gradient_projection_hartree_per_bohr,
            self.absolute_error_hartree_per_bohr, self.maximum_midpoint_shift_bohr, self.energy_roundoff_bound_hartree_per_bohr)
        if any(v is None for v in values):
            if any(v is not None for v in values) or self.step_change_hartree_per_bohr is not None or self.disposition is not A.UNEVALUABLE:
                raise ValueError('periodic comparison invents partially missing numerical operands')
        else:
            for i, value in enumerate(values):
                validate_decimal(value, field_name='directional_value', minimum=None if i < 2 else Decimal(0))
            with localcontext() as context:
                context.prec = 80
                if self.absolute_error_hartree_per_bohr != abs(values[0]-values[1]):
                    raise ValueError('periodic comparison changes its independent directional error')
        if self.step_change_hartree_per_bohr is not None:
            validate_decimal(self.step_change_hartree_per_bohr, field_name='step_change', minimum=Decimal(0))
            if self.previous_step_bohr is None:
                raise ValueError('periodic comparison invents a preceding step')


@dataclass(frozen=True, slots=True)
class RefinementComparison(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-refinement-comparison'
    VERSION: ClassVar[str] = '2.0.0'
    refinement: ObjectIdentity
    point: ObjectIdentity
    budget: PeriodicRefinementBudget
    energy_change_hartree: Decimal | None
    maximum_gradient_component_change_hartree_per_bohr: Decimal | None
    rms_gradient_component_change_hartree_per_bohr: Decimal | None
    disposition: A

    def __post_init__(self):
        exact(self.refinement, ObjectIdentity)
        exact(self.point, ObjectIdentity)
        exact(self.budget, PeriodicRefinementBudget)
        values = (self.energy_change_hartree, self.maximum_gradient_component_change_hartree_per_bohr, self.rms_gradient_component_change_hartree_per_bohr)
        if any(v is None for v in values) and any(v is not None for v in values):
            raise ValueError('periodic refinement invents partially missing operands')
        for i, value in enumerate(values):
            if value is not None:
                validate_decimal(value, field_name='refinement_difference', minimum=None if i == 0 else Decimal(0))
        if self.disposition is not _refinement_disposition(self.budget, *values):
            raise ValueError('periodic refinement changes its prospective sensitivity disposition')


def _refinement_disposition(budget, energy, maximum, rms):
    if any(value is None for value in (energy, maximum, rms)):
        return A.UNEVALUABLE
    if (maximum > budget.maximum_gradient_component_change_hartree_per_bohr
            or budget.maximum_rms_gradient_component_change_hartree_per_bohr is not None
                and rms > budget.maximum_rms_gradient_component_change_hartree_per_bohr
            or budget.maximum_absolute_energy_change_hartree is not None
                and energy.copy_abs() > budget.maximum_absolute_energy_change_hartree):
        return A.FALSIFIED
    return A.SATISFIED


def _disposition(protocol, error, step_change, previous_step):
    if error is None or protocol.maximum_directional_error_hartree_per_bohr is None:
        return A.UNEVALUABLE
    if (error > protocol.maximum_directional_error_hartree_per_bohr
            or step_change is not None and step_change > protocol.maximum_step_change_hartree_per_bohr):
        return A.FALSIFIED
    return A.UNEVALUABLE if previous_step is not None and step_change is None else A.SATISFIED


def _aggregate(rows):
    if any(row.disposition is A.FALSIFIED for row in rows):
        return A.FALSIFIED
    return A.SATISFIED if rows and all(row.disposition is A.SATISFIED for row in rows) else A.UNEVALUABLE


@dataclass(frozen=True, slots=True)
class PeriodicControlsReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/periodic-controls-readout'
    VERSION: ClassVar[str] = '2.0.0'
    readout_id: str
    protocol: PeriodicControlProtocol
    points: tuple[ControlPointReadout, ...]
    directions: tuple[DirectionalComparison, ...]
    refinements: tuple[RefinementComparison, ...]
    directional_disposition: A
    refinement_disposition: A
    numerical_disposition: A
    remaining_requirement_ids: tuple[str, ...] = OPEN_REQUIREMENTS

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        exact(self.protocol, PeriodicControlProtocol)
        for rows, kind in ((self.points, ControlPointReadout), (self.directions, DirectionalComparison),
                (self.refinements, RefinementComparison)):
            if type(rows) is not tuple:
                raise ValueError('periodic numerical readout requires its complete original tuple')
            for row in rows:
                exact(row, kind)
        if (tuple(row.point.ordinal for row in self.points) != tuple(range(self.protocol.point_count))
                or any(row.point.protocol != self.protocol.identity for row in self.points)
                or tuple((r.direction, r.step_bohr) for r in self.directions) != tuple(
                    (d.identity, step) for d in self.protocol.directions for step in self.protocol.steps_bohr)
                or tuple(r.refinement for r in self.refinements) != tuple(r.identity for r in self.protocol.refinements)
                or self.remaining_requirement_ids != OPEN_REQUIREMENTS
                or self.directional_disposition is not _aggregate(self.directions)
                or self.refinement_disposition is not _aggregate(self.refinements)
                or self.numerical_disposition is not _aggregate((*self.directions, *self.refinements))):
            raise ValueError('periodic readout drops selected points or widens numerical evidence')
        for row in self.points:
            validate_control_point(self.protocol, row.point)
        by_question = {(row.point.direction, row.point.signed_step_bohr):row.point.identity
            for row in self.points if row.point.role == 'DISPLACED'}
        by_refinement = {row.point.refinement:row.point.identity for row in self.points if row.point.role == 'REFINEMENT'}
        for row in self.directions:
            index = self.protocol.steps_bohr.index(row.step_bohr)
            previous = None if index == 0 else self.protocol.steps_bohr[index-1]
            if (row.minus_point != by_question[(row.direction, -row.step_bohr)]
                    or row.plus_point != by_question[(row.direction, row.step_bohr)] or row.previous_step_bohr != previous
                    or row.disposition is not _disposition(self.protocol, row.absolute_error_hartree_per_bohr,
                        row.step_change_hartree_per_bohr, row.previous_step_bohr)):
                raise ValueError('periodic readout changes its prospective numerical criterion')
        by_budget = {row.identity:row.budget for row in self.protocol.refinements}
        if any(row.point != by_refinement[row.refinement] or row.budget != by_budget[row.refinement]
                for row in self.refinements):
            raise ValueError('periodic readout substitutes a declared refinement point or budget')


def _read_point(config, original_result, native_subwork, assessor_source, readout_id, *, representation):
    exact(original_result, PeriodicProbeResult)
    definition = original_result.definition
    expected = definition_for(config, parent=definition.parent_contact,
        materialization_ids=definition.input_materialization_ids)
    if (definition != expected or original_result.request != selected_request(config)
            or original_result.returned.selection != config.point.identity):
        raise ValueError('periodic control read substitutes the exact original point or producing definition')
    validators = None
    if original_result.returned.error is None:
        # The captured force request alone cannot show that the intended
        # displaced coordinates reached the operator. Check its original
        # retained coordinate file and numerical input records independently.
        prototype = config.original.selection
        fingerprints = {'control-protocol.json':config.protocol.fingerprint(), 'control-point.json':config.point.fingerprint(),
            'selection.json':prototype.path.fingerprint(), 'electronic-settings.json':config.point.electronic.fingerprint(),
            'cell.json':prototype.cell.fingerprint(), 'mm-settings.json':config.point.molecular.fingerprint(),
            'original.prmtop':prototype.cell.raw_topology.object_fingerprint,
            'original.inpcrd':prototype.cell.raw_coordinates.object_fingerprint}
        files = {PurePosixPath(row.relative_path).name:row.sha256 for row in original_result.returned.files.files}
        if any(files.get(name) != digest for name, digest in fingerprints.items()):
            raise ValueError('periodic control return substitutes its actual original numerical input files')
        def coordinates(raw):
            import numpy as np
            stream = io.BytesIO(raw)
            xyz = np.load(stream, allow_pickle=False)
            if (stream.read(1) or xyz.dtype.str != '<f8' or xyz.shape != (config.protocol.physical_atom_count, 3)
                    or not np.isfinite(xyz).all() or sha256(xyz.tobytes(order='C')).hexdigest() != config.point.coordinate_sha256):
                raise ValueError('periodic control return substitutes its actual selected coordinates')
        validators = {'coordinate-array.npy':(config.protocol.physical_atom_count*24+4096, coordinates)}
    if config.ACCELERATED:
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import assess_gpu_log
        files = {PurePosixPath(row.relative_path).name for row in original_result.returned.files.files}
        if 'native-observations.jsonl' in files or original_result.returned.error is None:
            validators = {} if validators is None else validators
            validators['native-observations.jsonl'] = (64*2**20, lambda raw: assess_gpu_log(raw,
                engine=config.original.selection.engine, expected_evaluations=1,
                successful=original_result.returned.error is None,
                state=getattr(config.point.electronic, 'state', None)))
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality_read import RetainedGeometryReader
    prototype = config.original.selection
    geometry_reader = RetainedGeometryReader(representation=representation, policy=periodic_geometry_policy(config.point.molecular),
        cell=prototype.cell, qm_atoms=prototype.path.qm_atom_indices,
        expected_coordinate_sha256=config.point.coordinate_sha256)
    return read_original_periodic_return(original_result=original_result, native_subwork=native_subwork,
        assessor_source=assessor_source, readout_id=readout_id, member_validators=validators, geometry_reader=geometry_reader)


def read_periodic_control_point(*, config, representation, coordinate_bytes, original_result, native_subwork,
        assessor_source, readout_id):
    capability_for(config)
    validate_periodic_probe_model(config.original.selection, representation)
    point_coordinates(config.protocol, config.point, coordinate_bytes)
    return _read_point(config, original_result, native_subwork, assessor_source, readout_id, representation=representation)


def read_periodic_molecular_precision(*, config, representation, coordinate_bytes, original_result, native_subwork,
        assessor_source, readout_id):
    """Read the original accelerated baseline's additional complete MM control."""
    import json
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_mm_precision import ARRAY_NAMES, PREFIX, assess_molecular_precision
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import authenticate_probe_files
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import periodic_molecular_platform
    if (not config.ACCELERATED or config.point.role != 'BASELINE'
            or periodic_molecular_platform(config.original.selection.engine) != 'CUDA'):
        raise ValueError('molecular precision requires its original accelerated baseline point')
    read_periodic_control_point(config=config, representation=representation, coordinate_bytes=coordinate_bytes,
        original_result=original_result, native_subwork=native_subwork,
        assessor_source=assessor_source, readout_id=readout_id)
    members = {}
    validators = {name: (maximum, lambda raw, name=name: members.__setitem__(name, raw))
        for name, maximum in (
            ('coupling-audit.json', 16*2**20), (PREFIX+'request.json', 2**20), (PREFIX+'completion.json', 2**20),
            *((PREFIX+name+'.npy', config.protocol.physical_atom_count*24+4096) for name in ARRAY_NAMES))}
    authenticate_probe_files(native_subwork, original_result.definition, original_result.returned,
        member_validators=validators)
    audit = json.loads(members.pop('coupling-audit.json'))
    result = assess_molecular_precision(members, physical_atom_count=config.protocol.physical_atom_count,
        coordinate_sha256=config.point.coordinate_sha256,
        remainder_sha256=audit['remainder']['remainder_parameter_sha256'])
    return dict(result, original_completion_sha256=original_result.completion.fingerprint(),
        point=config.point.identity.to_document(), assessor_source=assessor_source.to_document())


def _values(report, native_subwork, *, include_gradient):
    """Reauthenticate the precise raw arrays used in the independent comparison."""
    if (report is None or report.original_result.completion.operational_status is not OperationalStatus.SUCCEEDED
            or report.original_result.returned.error is not None or report.numerical_integrity is None
            or report.geometry_quality.disposition != 'SCREEN_PASSED'
            or report.numerical_integrity.disposition is not A.SATISFIED):
        return None
    result = report.original_result
    raw = result.returned.returned
    def read(capture):
        def reader(manifest):
            if manifest != capture.artifact_manifest:
                raise ValueError('periodic comparison substitutes original operand custody')
            return _CompletedByteReader(native_subwork.iter_completed_output(result.definition, 'raw.'+capture.operand,
                maximum_chunk_bytes=2**20))
        return _raw_operand(capture, reader)
    return float(read(raw.energy)), read(raw.gradient) if include_gradient else None


def _directional(protocol, points, coordinate_bytes, values):
    import numpy as np
    original = np.frombuffer(coordinate_bytes, dtype='<f8').reshape(protocol.physical_atom_count, 3)
    baseline = values.get(points[0].point_id)
    by_question = {(p.direction, p.signed_step_bohr):p for p in points if p.role == 'DISPLACED'}
    rows = []
    for direction in protocol.directions:
        previous_step, previous_fd = None, None
        for step in protocol.steps_bohr:
            minus, plus = (by_question[(direction.identity, sign*step)] for sign in (-1, 1))
            minus_values, plus_values = values.get(minus.point_id), values.get(plus.point_id)
            fd = analytic = error = change = midpoint = rounding = None
            if baseline is not None and minus_values is not None and plus_values is not None:
                xm = displaced_coordinates(original, direction, -step)
                xp = displaced_coordinates(original, direction, step)
                # Use the actual binary64 coordinate secant, including its
                # rounding, with the independently retained original gradient.
                with localcontext() as context:
                    context.prec = 80
                    denominator = 2*step
                    fd = (Decimal.from_float(plus_values[0])-Decimal.from_float(minus_values[0]))/denominator
                    dot = math.fsum(float(g)*float(dx) for g, dx in zip(
                        baseline[1].flat, (xp-xm).flat, strict=True))
                    analytic = Decimal.from_float(dot)/(denominator*BOHR_ANGSTROM)
                    error = abs(fd-analytic)
                    change = None if previous_fd is None else abs(fd-previous_fd)
                    midpoint = Decimal.from_float(float(np.max(np.abs((xp-original)+(xm-original)))))/(2*BOHR_ANGSTROM)
                    rounding = (Decimal.from_float(math.ulp(plus_values[0]))+
                        Decimal.from_float(math.ulp(minus_values[0])))/(2*denominator)
            disposition = _disposition(protocol, error, change, previous_step)
            rows.append(DirectionalComparison(direction.identity, step, previous_step, minus.identity, plus.identity,
                fd, analytic, error, change, midpoint, rounding, disposition))
            previous_step, previous_fd = step, fd
    return tuple(rows)


def _refinements(protocol, points, values):
    import numpy as np
    baseline = values.get(points[0].point_id)
    by_refinement = {row.identity:row for row in protocol.refinements}
    rows = []
    for point in points:
        if point.role != 'REFINEMENT':
            continue
        refined = values.get(point.point_id)
        energy = maximum = rms = None
        if baseline is not None and refined is not None:
            refined_energy, original_energy = Decimal.from_float(refined[0]), Decimal.from_float(baseline[0])
            with localcontext() as context:
                context.prec = max(refined_energy.adjusted(), original_energy.adjusted()) - min(
                    refined_energy.as_tuple().exponent, original_energy.as_tuple().exponent) + 3
                energy = refined_energy-original_energy
            delta = refined[1]-baseline[1]
            maximum_float = float(np.max(np.abs(delta)))
            maximum = Decimal.from_float(maximum_float)
            rms = Decimal(0) if maximum_float == 0 else Decimal.from_float(
                maximum_float*float(np.sqrt(np.mean((delta/maximum_float)**2))))
        budget = by_refinement[point.refinement].budget
        rows.append(RefinementComparison(point.refinement, point.identity, budget, energy, maximum, rms,
            _refinement_disposition(budget, energy, maximum, rms)))
    return tuple(rows)


def read_periodic_controls(*, configs, representation, coordinate_bytes, original_results,
        native_subwork_for_result, assessor_source, readout_id):
    """Retain the full prospective denominator, including absent or failed returns.

    An absent completed result is reported as missing, without guessing whether
    its native contact was entered. Existing contact inspection owns that state.
    Every selected refinement must satisfy its prospective sensitivity budget;
    absent operands remain unevaluable. Directional conformance, refinement
    sensitivity, and the combined selected numerical tests retain separate
    dispositions. None proves exact-force accuracy or physical applicability.
    """
    base = validate_configs(configs)
    validate_periodic_probe_model(base.original.selection, representation)
    points = control_points(base.protocol, coordinate_bytes)
    if tuple(c.point for c in configs) != points or type(original_results) is not tuple:
        raise ValueError('periodic control reader changes its complete original point census')
    selected_points = {point.identity for point in points}
    results = {}
    for result in original_results:
        exact(result, PeriodicProbeResult)
        pin = result.returned.selection
        if pin not in selected_points or pin in results:
            raise ValueError('periodic control reader repeats or substitutes a selected original result')
        results[pin] = result
    reports, values = [], {}
    for config in configs:
        result = results.get(config.point.identity)
        report = None
        if result is not None:
            store = native_subwork_for_result(result)
            report = _read_point(config, result, store, assessor_source,
                readout_id+'.point.'+f'{config.point.ordinal:08d}', representation=representation)
            values[config.point.point_id] = _values(report, store, include_gradient=config.point.role != 'DISPLACED')
        reports.append(ControlPointReadout(config.point, report))
    directions = _directional(base.protocol, points, coordinate_bytes, values)
    refinements = _refinements(base.protocol, points, values)
    return PeriodicControlsReadout(readout_id, base.protocol, tuple(reports), directions, refinements,
        _aggregate(directions), _aggregate(refinements), _aggregate((*directions, *refinements)))
