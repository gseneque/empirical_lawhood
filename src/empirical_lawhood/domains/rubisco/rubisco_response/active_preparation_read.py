# SPDX-License-Identifier: MPL-2.0
"""Read receipted preparation prefixes without native construction or execution."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import periodic_geometry_policy
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_model_preparation import verified_coordinates
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint, read_checkpoint_files
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_evaluation import CompletePreparationEvaluation, read_evaluation_files
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_operation import ActivePreparationPrefixResult, capability_for, definition_for
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_assessment import endpoint_geometry
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_operation import ActiveRelaxationReturn, MAX_RETURN, selected_seeds
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_read import authenticate_relaxation_files
from empirical_lawhood.domains.rubisco.rubisco_response.active_relaxation_selection import validate_relaxation_member
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model

METADATA = frozenset(('seed.json', 'site.json', 'protocol.json', 'settings.json',
    'original.prmtop', 'initial-whole-molecule-quality.json',
    'source-bindings.json', 'prefix-selection.json', 'relaxation-evaluations.jsonl',
    'native-observations.jsonl', 'preparation-prefix-summary.json'))


@dataclass(frozen=True, slots=True)
class PreparationCheckpointAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-checkpoint-assessment'
    checkpoint: ActivePreparationCheckpoint
    findings: tuple[str, ...]
    disposition: str
    stereocentres_checked: int
    nearest_water_magnesium_angstrom: Decimal

    def __post_init__(self):
        from empirical_lawhood.science.records.serialization import validate_decimal
        exact(self.checkpoint, ActivePreparationCheckpoint)
        if (type(self.findings) is not tuple or self.findings != tuple(sorted(set(self.findings)))
                or self.disposition != ('REJECTED' if self.findings else 'AVAILABLE')
                or type(self.stereocentres_checked) is not int or self.stereocentres_checked < 0):
            raise ValueError('checkpoint assessment changes its physical findings')
        for finding in self.findings:
            validate_stable_id(finding)
        validate_decimal(self.nearest_water_magnesium_angstrom, field_name='nearest_water', minimum=Decimal(0))


@dataclass(frozen=True, slots=True)
class PreparationPosition(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-position'
    position: str
    checkpoint: ObjectIdentity | None
    disposition: str

    def __post_init__(self):
        if (self.position not in ('initial', 'later')
                or self.disposition not in ('AVAILABLE', 'REJECTED', 'UNAVAILABLE')
                or (self.checkpoint is None) != (self.disposition == 'UNAVAILABLE')):
            raise ValueError('preparation position loses its selected state or unavailable outcome')
        if self.checkpoint is not None:
            exact(self.checkpoint, ObjectIdentity)
            if self.checkpoint.object_schema != ActivePreparationCheckpoint.SCHEMA:
                raise ValueError('preparation position requires an original accepted checkpoint')


@dataclass(frozen=True, slots=True)
class PreparationPrefixAssessment(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-prefix-assessment'
    configuration: ObjectIdentity
    assessor_source: ObjectIdentity
    evaluations: tuple[CompletePreparationEvaluation, ...]
    checkpoints: tuple[PreparationCheckpointAssessment, ...]
    positions: tuple[PreparationPosition, ...]
    complete_native_return_ledger: bool
    continuation: str
    scope: str = 'FINITE_PREPARATION_STATES_WITHOUT_STATIONARITY_POPULATION_FORCE_ACCURACY_OR_RATE_ADMISSION'

    def __post_init__(self):
        for pin in (self.configuration, self.assessor_source):
            exact(pin, ObjectIdentity)
        if (type(self.evaluations) is not tuple or type(self.checkpoints) is not tuple
                or type(self.positions) is not tuple or len(self.positions) != 2
                or type(self.complete_native_return_ledger) is not bool
                or self.continuation != ('OPTIMIZER_STATE_AVAILABLE_ELECTRONIC_INITIALIZATION_RESTART_REQUIRED'
                    if self.complete_native_return_ledger and self.checkpoints else 'UNAVAILABLE')
                or self.scope != 'FINITE_PREPARATION_STATES_WITHOUT_STATIONARITY_POPULATION_FORCE_ACCURACY_OR_RATE_ADMISSION'):
            raise ValueError('prefix assessment changes continuation or physical admission')
        for ordinal, row in enumerate(self.evaluations, 1):
            exact(row, CompletePreparationEvaluation)
            if row.ordinal != ordinal or row.configuration != self.configuration:
                raise ValueError('prefix assessment loses an original complete return')
        for iteration, row in enumerate(self.checkpoints):
            exact(row, PreparationCheckpointAssessment)
            if row.checkpoint.iterations != iteration or row.checkpoint.configuration != self.configuration:
                raise ValueError('prefix assessment loses an original accepted state')
        selected = (self.checkpoints[0] if self.checkpoints else None,
                    self.checkpoints[-1] if len(self.checkpoints) > 1 else None)
        for position, row, state in zip(('initial', 'later'), self.positions, selected, strict=True):
            exact(row, PreparationPosition)
            if (row.position != position or row.checkpoint != (None if state is None else state.checkpoint.identity)
                    or row.disposition != ('UNAVAILABLE' if state is None else state.disposition)):
                raise ValueError('prefix assessment substitutes a state position or duplicates its initial state')


@dataclass(frozen=True, slots=True)
class ActivePreparationPrefixReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/active-preparation-prefix-readout'
    readout_id: str
    original_result: ActivePreparationPrefixResult
    authenticated_file_count: int
    authenticated_uncompressed_bytes: int
    assessment: PreparationPrefixAssessment | None
    assessment_error: str | None
    independent_biological_replicates: int = 0
    original_material_count: int = 4
    original_site_count: int = 32
    original_starting_hypotheses: int = 384

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        exact(self.original_result, ActivePreparationPrefixResult)
        census = self.original_result.unit.returned.files.files
        if (self.authenticated_file_count != len(census)
                or self.authenticated_uncompressed_bytes != sum(r.byte_count for r in census)
                or (self.assessment is None) == (self.assessment_error is None)
                or (self.independent_biological_replicates, self.original_material_count,
                    self.original_site_count, self.original_starting_hypotheses) != (0, 4, 32, 384)):
            raise ValueError('prefix readout loses original failures, file census or the wider denominator')
        if self.assessment is not None:
            exact(self.assessment, PreparationPrefixAssessment)
            if self.assessment.configuration != self.original_result.configuration:
                raise ValueError('prefix readout substitutes its assessed source')
        elif type(self.assessment_error) is not str or not self.assessment_error:
            raise ValueError('prefix readout loses its actual assessment error')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.readout_id, self)


def _check_transition(previous, current):
    """Check descent, Armijo decrease and retained curvature against full operands."""
    import numpy as np
    from empirical_lawhood.methods.binary64_reduction import dot, norm
    step = current.coordinates - previous.coordinates
    change = current.gradient - previous.gradient
    directional = dot(previous.gradient, step)
    if (current.iterations != previous.iterations + 1 or current.evaluations <= previous.evaluations
            or current.initial_energy != previous.initial_energy or directional >= 0
            or current.energy >= previous.energy
            or current.energy > previous.energy + 1e-4 * directional
                + 8 * np.spacing(max(abs(previous.energy), abs(current.energy)))
            or current.invalid_trials < previous.invalid_trials):
        raise ValueError('checkpoint is not an accepted decreasing step of its original preparation')
    if current.phase == 'initial-scaled-descent':
        if (previous.phase != current.phase or current.history
                or current.descent_iterations != previous.descent_iterations + 1
                or current.curvature_skips != previous.curvature_skips):
            raise ValueError('checkpoint changes original initial-descent history')
    else:
        sy = dot(step, change)
        appended = sy > 1e-10 * norm(step) * norm(change)
        if (current.descent_iterations != previous.descent_iterations
                or current.curvature_skips != previous.curvature_skips + (not appended)):
            raise ValueError('checkpoint changes original curvature accounting')
        expected_tail = (step, change, 1 / sy) if appended else None
        if expected_tail is not None and (not current.history
                or any(not np.array_equal(a, b) for a, b in zip(current.history[-1], expected_tail, strict=True))):
            raise ValueError('checkpoint curvature does not arise from its complete original forces')
        # The minimizer may clear history after a non-descent direction. Any
        # retained prefix must nevertheless be an unchanged suffix of old memory.
        retained = current.history[:-1] if appended else current.history
        old = previous.history[-len(retained):] if retained else ()
        if len(retained) > len(previous.history) or any(
                not np.array_equal(a, b) for left, right in zip(retained, old, strict=True)
                for a, b in zip(left, right, strict=True)):
            raise ValueError('checkpoint substitutes original optimizer memory')


def _trace_evaluations(files, evaluations, arrays, *, prototype, physical_atoms, allowance):
    """Join sealed operands to original nested calls, retaining an incomplete tail."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import GRADIENT_UNIT
    rows = [json.loads(line) for line in files['relaxation-evaluations.jsonl'].splitlines()]
    native = [json.loads(line) for line in files['native-observations.jsonl'].splitlines()]
    entries = [r for r in rows if r['event'] == 'relaxation-entry']
    returns = [r for r in rows if r['event'] == 'relaxation-return']
    if (len(entries) > allowance or len(returns) > len(entries)
            or [r['evaluation'] for r in entries] != list(range(1, len(entries) + 1))
            or [r['evaluation'] for r in returns] != list(range(1, len(returns) + 1))
            or len(evaluations) > len(returns)
            or any(r['phase'] != 'preparation-prefix' or r['physical_atoms'] != physical_atoms for r in entries)):
        raise ValueError('preparation trace changes original complete-return purchase or ordered contact')
    electronic = {r['evaluation']: r for r in native if r['event'] == 'electronic-return'}
    coupled = {r['evaluation']: r for r in native if r['event'] == 'return'}
    for event in ('entry', 'electronic-return', 'return'):
        numbers = [r['evaluation'] for r in native if r['event'] == event]
        if numbers != list(range(1, len(numbers) + 1)) or len(numbers) > len(entries):
            raise ValueError('preparation trace loses an original nested electronic effect')
    findings = {}
    for record, (_, xyz, result), entry, returned in zip(evaluations, arrays,
            entries[:len(evaluations)], returns[:len(evaluations)], strict=True):
        ordinal = record.ordinal
        if (entry['coordinate_sha256'] != sha256(xyz.tobytes()).hexdigest()
                or returned['coordinate_sha256'] != entry['coordinate_sha256']
                or returned['phase'] != 'preparation-prefix' or returned['gradient_unit'] != GRADIENT_UNIT
                or returned['gradient_sha256'] != sha256(result['gradient_hartree_per_bohr'].tobytes()).hexdigest()
                or returned['energy_hartree'] != float(record.energy_hartree)
                or coupled[ordinal]['energy_hartree'] != returned['energy_hartree']):
            raise ValueError('preparation trace substitutes a sealed complete reference return')
        e = electronic[ordinal]
        findings[ordinal] = set() if (e['converged'] is True and np.isfinite(e['orbital_gradient_norm'])
            and e['orbital_gradient_norm'] < float(prototype.electronic.orbital_gradient_tolerance)) else {'electronic-solution-not-converged'}
    complete = (len(evaluations) == len(entries) == len(returns)
        and not any(r['event'] in ('error', 'relaxation-error') for r in (*rows, *native)))
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import accelerated_engine
    if accelerated_engine(prototype.engine) and complete and evaluations:
        from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import assess_gpu_log
        assess_gpu_log(files['native-observations.jsonl'], engine=prototype.engine,
            expected_evaluations=len(evaluations), successful=True, state=getattr(prototype.electronic, 'state', None))
    return complete, findings


def assess_preparation_files(*, config, representation, prepared, coordinate_bytes, files, assessor_source):
    """Assess authenticated files and return original complete evaluation operands."""
    import numpy  # noqa: F401 -- Load BLAS before selecting its original thread count.
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=config.original.prototype.engine.numerical_threads):
        return _assess_preparation_files(config=config, representation=representation, prepared=prepared,
            coordinate_bytes=coordinate_bytes, files=files, assessor_source=assessor_source)


def _assess_preparation_files(*, config, representation, prepared, coordinate_bytes, files, assessor_source):
    import numpy as np
    original = config.original
    seed, = selected_seeds(original, prepared)
    site = next(s for s in prepared.sites if s.identity == seed.site)
    source_coordinates = verified_coordinates(representation, coordinate_bytes)
    expected = (('seed.json', seed), ('site.json', site), ('protocol.json', prepared.protocol),
        ('settings.json', original.plan.settings), ('prefix-selection.json', config.prefix))
    if any(files[name] != record.canonical_bytes() for name, record in expected):
        raise ValueError('preparation prefix substitutes the original chemical or preparation selection')
    bindings = json.loads(files['source-bindings.json'])
    if (bindings['representation'] != representation.identity.to_document()
            or bindings['prototype'] != original.prototype.identity.to_document()
            or bindings['topology_sha256'] != representation.raw_topology.object_fingerprint
            or bindings['original_coordinate_sha256'] != seed.original_coordinate_sha256
            or bindings['initial_coordinate_sha256'] != seed.expanded_coordinate_sha256
            or bindings['physical_atoms'] != len(source_coordinates)
            or bindings['cell'] != original.prototype.cell.to_document()
            or bindings['state_graph'] != seed.graph.to_document()):
        raise ValueError('preparation prefix changes complete original physical source bindings')
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration
    configuration = original_configuration(config)
    pins = dict(configuration=configuration, seed=seed.identity, prototype=original.prototype.identity)
    records, operands = [], []
    for name in sorted(files):
        if re.fullmatch(r'evaluation-\d{8}\.json', name):
            record = decode_canonical_bytes(files[name], CompletePreparationEvaluation, maximum_bytes=2**20)
            if name != f'evaluation-{record.ordinal:08d}.json' or record.ordinal != len(records) + 1:
                raise ValueError('preparation prefix loses its complete ordered return ledger')
            records.append(record)
            operands.append(read_evaluation_files(record, files, **pins))
    if records and sha256(operands[0][1].tobytes()).hexdigest() != seed.expanded_coordinate_sha256:
        raise ValueError('preparation prefix substitutes its initial complete state')
    complete, native_findings = _trace_evaluations(files, records, operands, prototype=original.prototype,
        physical_atoms=len(source_coordinates), allowance=config.prefix.allowance_for(original.model_name))
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality import bound_geometry_terms, assess_molecular_geometry
    geometry_terms = bound_geometry_terms(representation, files['original.prmtop'])
    for ordinal, xyz, _ in operands:
        quality = assess_molecular_geometry(xyz, geometry_terms,
            policy=periodic_geometry_policy(original.prototype.molecular),
            cell_angstrom=tuple(map(float, original.prototype.cell.lengths_angstrom)),
            exempt_bonded_atoms=site.path.qm_atom_indices)
        native_findings[ordinal].update(quality['findings'])
    assessments, checkpoint_arrays, previous = [], {}, None
    for name in sorted(files):
        if not re.fullmatch(r'accepted-\d{8}\.json', name):
            continue
        checkpoint = decode_canonical_bytes(files[name], ActivePreparationCheckpoint, maximum_bytes=2**20)
        if name != f'accepted-{checkpoint.iterations:08d}.json' or checkpoint.iterations != len(assessments):
            raise ValueError('preparation prefix omits or reorders an accepted state')
        state, arrays = read_checkpoint_files(checkpoint, files, **pins)
        if checkpoint.native_evaluation > len(operands):
            raise ValueError('accepted preparation state lacks its complete original native return')
        evaluation, xyz, returned = operands[checkpoint.native_evaluation - 1]
        if (evaluation != checkpoint.evaluations or not np.array_equal(xyz, arrays['coordinates-angstrom'])
                or not np.array_equal(returned['gradient_hartree_per_bohr'], arrays['gradient-hartree-per-bohr'])
                or checkpoint.energy_hartree != records[evaluation - 1].energy_hartree
                or checkpoint.maximum_gradient_kj_mol_nm != original.plan.settings.maximum_gradient_kj_mol_nm):
            raise ValueError('accepted preparation state substitutes its original force or convergence selection')
        if previous is None:
            if (checkpoint.native_evaluation != 1 or state.history or state.phase != 'initial-scaled-descent'
                    or state.energy != state.initial_energy or state.invalid_trials or state.curvature_skips
                    or state.descent_iterations):
                raise ValueError('preparation initial state changes its original optimizer origin')
        else:
            _check_transition(previous, state)
        geometry, nearest, stereo = endpoint_geometry(representation=representation, site=site,
            protocol=prepared.protocol, seed=seed, original=source_coordinates, final=xyz,
            cell=original.prototype.cell, settings=original.plan.settings)
        findings = tuple(sorted(geometry | native_findings[evaluation]))
        assessments.append(PreparationCheckpointAssessment(checkpoint, findings,
            'REJECTED' if findings else 'AVAILABLE', stereo, Decimal.from_float(nearest)))
        checkpoint_arrays[checkpoint.identity] = arrays
        previous = state
    selected = (assessments[0] if assessments else None, assessments[-1] if len(assessments) > 1 else None)
    positions = tuple(PreparationPosition(position, None if state is None else state.checkpoint.identity,
        'UNAVAILABLE' if state is None else state.disposition) for position, state in zip(('initial', 'later'), selected, strict=True))
    continuation = getattr(config, 'continuation', None)
    if continuation is not None:
        previous = continuation.readout.assessment
        if (tuple(records[:len(previous.evaluations)]) != previous.evaluations
                or tuple(assessments[:len(previous.checkpoints)]) != previous.checkpoints
                or len(records) > len(previous.evaluations) + continuation.remaining_allowance):
            raise ValueError('continued preparation changes original accepted states, completed returns or remaining allowance')
    assessment = PreparationPrefixAssessment(configuration, assessor_source, tuple(records), tuple(assessments),
        positions, complete, 'OPTIMIZER_STATE_AVAILABLE_ELECTRONIC_INITIALIZATION_RESTART_REQUIRED'
        if complete and assessments else 'UNAVAILABLE')
    return assessment, checkpoint_arrays, tuple(operands)


def read_preparation_prefix(*, config, representation, prepared, coordinate_bytes, original_result,
        native_subwork, assessor_source, readout_id, include_operands=False):
    """Authenticate original custody even when native work failed after a safe state."""
    capability_for(config)
    exact(original_result, ActivePreparationPrefixResult)
    exact(assessor_source, ObjectIdentity)
    original = config.original
    validate_periodic_probe_model(original.prototype, representation)
    validate_relaxation_member(plan=original.plan, model_name=original.model_name, prepared=prepared,
        prototype=original.prototype, representation=representation)
    verified_coordinates(representation, coordinate_bytes)
    from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_continuation import original_configuration
    if (original_result.configuration != original_configuration(config) or original_result.prefix != config.prefix
            or original_result.model_name != original.model_name or type(include_operands) is not bool):
        raise ValueError('preparation read substitutes its original selected configuration')
    unit = original_result.unit
    definition = unit.definition
    expected = definition_for(config, prepared, parent=definition.parent_contact,
        materialization_ids=definition.input_materialization_ids)
    if definition != expected:
        raise ValueError('preparation read changes its exact original native definition')
    completed = native_subwork.recover(definition)
    if completed is None or completed.completion != unit.completion or completed.receipt != unit.receipt:
        raise ValueError('preparation read lacks original completion custody; unknown contact cannot be replayed')
    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'relaxation.return')),
        ActiveRelaxationReturn, maximum_bytes=MAX_RETURN)
    if returned != unit.returned:
        raise ValueError('preparation read substitutes its original receipted return')
    names = METADATA | frozenset(PurePosixPath(r.relative_path).name for r in returned.files.files
        if re.fullmatch(r'(?:accepted|evaluation)-\d{8}(?:\.[a-z-]+\.npy|\.json)', PurePosixPath(r.relative_path).name))
    files, census, exceeds = authenticate_relaxation_files(native_subwork, definition, returned,
        endpoint_members=names, maximum_endpoint_bytes=None, retain_failed_members=True)
    assessment, error, arrays, operands = None, None, {}, ()
    try:
        if exceeds:
            raise ValueError('original prefix exceeds its explicit 1 GiB assessment envelope; complete archive authenticated')
        assessment, arrays, operands = assess_preparation_files(config=config, representation=representation,
            prepared=prepared, coordinate_bytes=coordinate_bytes, files=files, assessor_source=assessor_source)
    except (ValueError, KeyError, TypeError, ArithmeticError, EOFError, IndexError):
        error = traceback.format_exc()
    readout = ActivePreparationPrefixReadout(readout_id, original_result, len(census.files),
        sum(r.byte_count for r in census.files), assessment, error)
    return (readout, arrays, operands) if include_operands else readout
