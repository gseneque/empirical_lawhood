# SPDX-License-Identifier: MPL-2.0
"""WT03 closed raw ancestry and independently assessed current-use instances.

No original preparation product, return or completion is manufactured. The
original interrupted act remains UNKNOWN; new postprocessing and mathematical
proofs are distinct operands. The caller authenticates all retained originals.
"""

from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics import contracts as p
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.durable_contracts import DurableUnitReturn, geometry_keys
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.geometry_reuse import GeometryReusePlan
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.physical_preparation_geometry import GeometryDiagnostic
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_coordinate_assessment import GEOMETRY_METHOD, ORIGIN_METHOD
from empirical_lawhood.adapters.methods.rubisco_insilico_dynamics.serialized_preparation_assessment import (
    SerializedPreparationGeometry, SerializedPreparationIntegrity,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.kernel.serialization import CanonicalRecord, canonical_json_bytes, validate_sha256, validate_stable_id
from empirical_lawhood.runtime.native_subwork import (
    NativeSubworkBegin, NativeSubworkCompletion, NativeSubworkContact, NativeSubworkDefinition, NativeSubworkState,
)

from . import contracts as sampling, control_contracts as c
from .derived_model_admission import (
    ASSET_NAMES, INDEPENDENT_OWNERS, RAW_NAMES, DerivedChemicalForcePlan,
    _binding_matches, _canonical, _document, validate_derived_operands,
)

GLOBAL_MODEL = 'model.gp.wt.m1.joint-01.published-global-kcx-override'
MODEL_IDS = tuple(c.model_id(key) for key in p.model_roster())
UNIT_IDS = tuple(sorted((*MODEL_IDS, *('geometry.' + '.'.join(key) for key in geometry_keys()))))
HISTORY_SCOPE = 'CLOSED_RAW_UNKNOWN_NATIVE_COMPLETION'


def _decode_json(value, kind):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode()
    return decode_canonical_bytes(raw, kind, maximum_bytes=len(raw))


def _record_evidence(record, name):
    return p.FileEvidence(name, len(record.canonical_bytes()), record.fingerprint())


@dataclass(frozen=True, slots=True)
class ClosedRawModelHistory(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/closed-raw-model-history'
    history_id: str
    source: ObjectIdentity
    original_plan: GeometryReusePlan
    raw_custody_audit: p.NativeTextFile
    process_closure: p.NativeTextFile
    geometry_parent: p.NativeTextFile
    original_contacts: tuple[tuple[str, p.NativeTextFile], ...]
    files: tuple[p.FileEvidence, ...]
    original_unit_states: tuple[tuple[str, NativeSubworkState], ...]
    original_assignment_states: tuple[tuple[str, str], ...]
    model_id: str = GLOBAL_MODEL
    original_history_scope: str = HISTORY_SCOPE
    original_unit_return: str = 'ABSENT'
    original_typed_native_return: str = 'ABSENT'
    original_scientific_return: str = 'UNKNOWN'
    original_native_os_return: str = 'UNKNOWN'
    original_native_attempt_count: int | None = None
    original_native_completed_count: int | None = None
    original_native_cost: str = 'UNKNOWN'
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.history_id)
        self.source.__post_init__()
        if (type(self.original_plan) is not GeometryReusePlan or self.original_plan.source != self.source
                or self.model_id != GLOBAL_MODEL or self.original_history_scope != HISTORY_SCOPE
                or self.original_unit_return != 'ABSENT' or self.original_typed_native_return != 'ABSENT'
                or self.original_scientific_return != 'UNKNOWN' or self.original_native_os_return != 'UNKNOWN'
                or self.original_native_attempt_count is not None or self.original_native_completed_count is not None
                or self.original_native_cost != 'UNKNOWN' or self.physical_independent_units != 0):
            raise ValueError('closed raw history cannot recover the original interrupted return or cost')
        self.original_plan.__post_init__()
        audit, closure, parent = map(_document, (self.raw_custody_audit, self.process_closure, self.geometry_parent))
        if (audit.get('schema') != 'el.rubisco.wt03.closed-raw-fragment-custody-audit.v1'
                or audit.get('scientific_return') != 'UNKNOWN' or audit.get('native_os_return') != 'UNKNOWN'
                or audit.get('typed_original_native_process_return') != 'ABSENT'
                or audit.get('complete_model_unit_returns') != 'ABSENT' or audit.get('controller_readout') != 'ABSENT'
                or audit.get('original_definition_count') != 40 or audit.get('original_begin_count') != 5
                or audit.get('original_completion_count') != 0 or audit.get('original_completion_bindings') != []
                or audit.get('regular_file_count') != 23 or audit.get('symlink_or_special_members') != []
                or audit.get('unknown_replay') is not False
                or not _binding_matches(audit.get('genuine_root_process_closure'), self.process_closure.evidence)
                or closure.get('schema') != 'el.rubisco.wt03-live-root-metadata-observation.v1'
                or closure.get('definition_count') != 40 or closure.get('begin_count') != 5
                or closure.get('completion_count') != 0 or closure.get('full_completions') != []
                or closure.get('native_os_return') != 'UNKNOWN' or closure.get('scientific_return') != 'UNKNOWN'
                or closure.get('typed_process_return_exists') is not False
                or closure.get('os_process_closure_observed') is not True
                or closure.get('stable_raw_fragment_diagnosis_eligible') is not True
                or closure.get('selected_process_observations') != []
                or closure.get('unreadable_potentially_selected_processes') != []):
            raise ValueError('closed raw history lacks exact complete missing-return custody and process closure')
        observations = closure.get('original_identity_observations')
        if (type(observations) is not list or len(observations) != 5
                or any(type(row.get('pid')) is not int or type(row.get('original_start_time_ticks')) is not int
                    or row.get('same_original_identity_present') is not False for row in observations)
                or len({(row['pid'], row['original_start_time_ticks']) for row in observations}) != 5):
            raise ValueError('closed raw history omits exact original closed PID/startticks identities')
        definitions = tuple(_decode_json(row['record'], NativeSubworkDefinition) for row in closure.get('full_definitions', ()))
        begins = tuple(_decode_json(row['record'], NativeSubworkBegin) for row in closure.get('full_begins', ()))
        extra = ('preparation.metadata', 'preparation.launch', self.model_id + '.call.000001', self.model_id + '.call.000001.operand')
        if (len(definitions) != 40 or {row.subwork_id for row in definitions} != {*UNIT_IDS, *extra}
                or len(begins) != 5 or {row.definition.object_id for row in begins} != {self.model_id, *extra}
                or closure['full_definitions'] and [row['binding'] for row in closure['full_definitions']]
                    != audit.get('complete_original_definition_bindings')
                or [row['binding'] for row in closure['full_begins']] != audit.get('complete_original_begin_bindings')):
            raise ValueError('closed raw history changes the original40/5 definition and begin denominators')
        by_id = {row.subwork_id: row for row in definitions}
        code = sha256(canonical_json_bytes(self.original_plan.code_sources)).hexdigest()
        for row, retained in zip(definitions, closure['full_definitions'], strict=True):
            if (not _binding_matches(retained['binding'], _record_evidence(row, 'definition.json'))
                    or row.subwork_id in UNIT_IDS and (row.configuration != self.original_plan.identity
                        or row.code_sources_sha256 != code or row.dependency_lock_sha256 != self.original_plan.dependency_lock_sha256
                        or self.source not in row.sources)):
                raise ValueError('closed raw history substitutes original canonical definitions/source/plan')
        begin_map = {row.definition.object_id: row for row in begins}
        for row, retained in zip(begins, closure['full_begins'], strict=True):
            if (row.definition != by_id[row.definition.object_id].identity
                    or not _binding_matches(retained['binding'], _record_evidence(row, 'begin.json'))):
                raise ValueError('closed raw history substitutes original canonical begins')
        if tuple(name for name, _ in self.original_contacts) != tuple(sorted(begin_map)):
            raise ValueError('closed raw history omits original five contact records')
        for name, retained in self.original_contacts:
            retained.__post_init__()
            contact = decode_canonical_bytes(retained.raw_utf8.encode(), NativeSubworkContact, maximum_bytes=None)
            prefix = 'native-subwork.' + sha256((by_id[name].parent_contact.task_id + ':' + name).encode()).hexdigest()
            if contact.begin != ObjectIdentity.from_record(prefix + '.begin', begin_map[name]):
                raise ValueError('closed raw history substitutes original contact/begin lineage')
        inventory = audit.get('regular_file_inventory', ())
        if (type(self.files) is not tuple or len(self.files) != 23
                or tuple(row.relative_path for row in self.files) != tuple(row['relative_path'] for row in inventory)
                or any(not _binding_matches(row['binding'], evidence) for row, evidence in zip(inventory, self.files, strict=True))
                or sum(row.byte_count for row in self.files) != audit.get('regular_file_bytes')):
            raise ValueError('closed raw history omits or replaces its complete original23-file census')
        for row in self.files:
            row.__post_init__()
        returned = audit.get('complete_declared_typed_return_carrier_presence', ())
        expected = {(row.subwork_id, out.output_id) for row in definitions for out in row.outputs
            if out.output_id.endswith('.return') or out.output_id == 'call.witness'}
        if ({(row['subwork_id'], row['output_id']) for row in returned} != expected
                or len(returned) != len(expected)
                or any(row.get('present') is not False or row.get('manifest_present') is not False
                    or row.get('binding') is not None for row in returned)):
            raise ValueError('closed raw history loses the complete absence census of original typed returns')
        expected_states = tuple((name, NativeSubworkState.UNKNOWN_COMPLETION if name in begin_map else NativeSubworkState.NOT_ENTERED)
            for name in UNIT_IDS)
        if (self.original_unit_states != expected_states
                or self.original_assignment_states != tuple((name, 'ABSENT_NOT_ASSESSED') for name in MODEL_IDS)):
            raise ValueError('closed raw history invents original scientific completion or assessment')
        if (set(parent) != {'independent_integrity', 'original_archive', 'original_geometry', 'original_geometry_receipt', 'supply'}
                or _decode_json(parent['supply'], ObjectIdentity) not in self.original_plan.geometry_supplies
                or _decode_json(parent['original_geometry'], ObjectIdentity).object_id not in self.original_plan.reused_geometry_ids
                or not any(PurePosixPath(row.relative_path).name == 'geometry-reuse-parent.json'
                    and (row.byte_count, row.sha256) == (self.geometry_parent.evidence.byte_count, self.geometry_parent.evidence.sha256)
                    for row in self.files)):
            raise ValueError('closed raw history substitutes authentic original geometry ancestry')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.history_id, self)


@dataclass(frozen=True, slots=True)
class ClosedRawModelSupply(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/closed-raw-model-supply'
    supply_id: str
    history: ClosedRawModelHistory
    assets: ObjectIdentity
    postprocessing_readout: p.NativeTextFile
    assignment_readout: p.NativeTextFile
    geometry_readout: p.NativeTextFile
    producer_source_manifest: p.NativeTextFile
    producer_owner_source_manifest: p.NativeTextFile
    independent_source_manifest: p.NativeTextFile
    geometry_diagnostic: p.NativeTextFile

    def __post_init__(self):
        validate_stable_id(self.supply_id)
        if type(self.history) is not ClosedRawModelHistory or self.assets.object_schema != p.ModelAssets.SCHEMA:
            raise ValueError('closed raw supply substitutes its explicit history/assets owner')
        self.history.__post_init__()
        self.assets.__post_init__()
        produced, assignment, geometry, producer, owner, independent = map(_document, (
            self.postprocessing_readout, self.assignment_readout, self.geometry_readout,
            self.producer_source_manifest, self.producer_owner_source_manifest, self.independent_source_manifest))
        self.geometry_diagnostic.__post_init__()
        diagnostic = decode_canonical_bytes(self.geometry_diagnostic.raw_utf8.encode(), GeometryDiagnostic, maximum_bytes=None)
        if (produced.get('schema') != 'el.rubisco.wt03.closed-raw-derived-postprocessing.v1'
                or produced.get('derived_postprocessing') != 'PRODUCTS_PRODUCED' or produced.get('error') is not None
                or produced.get('new_postprocess_load_count') != 1
                or any(produced.get(name) != 0 for name in ('molecular_acquisition_count', 'native_solver_count', 'tleap_count'))
                or not _binding_matches(produced.get('source_manifest'), self.producer_source_manifest.evidence)
                or producer.get('schema') != 'el.rubisco.wt03.closed-raw-derived-postprocessing-source.v1'
                or not _binding_matches(producer.get('reused_producer_source_manifest'), self.producer_owner_source_manifest.evidence)
                or not _binding_matches(producer.get('independent_method_source_manifest'), self.independent_source_manifest.evidence)
                or owner.get('schema') != 'el.rubisco.scoped-wt.additive-postprocessing-source.v1'
                or independent.get('schema') != 'el.rubisco.scoped-wt.independent-composition-source.v1'):
            raise ValueError('closed raw supply lacks its separately completed postprocess and source custody')
        procedures = produced.get('postprocess_load_procedures')
        if type(procedures) is not list or len(procedures) != 1:
            raise ValueError('closed raw supply requires its one counted new postprocess procedure')
        procedure = procedures[0]
        try:
            costs = tuple(Decimal(procedure[name]) for name in ('cpu_seconds', 'wall_seconds'))
        except (KeyError, TypeError, ArithmeticError) as error:
            raise ValueError('closed raw postprocess omits its measured procedure costs') from error
        if (procedure.get('model_id') != GLOBAL_MODEL or procedure.get('termination') != 'COMPLETED'
                or procedure.get('error') is not None or any(not value.is_finite() or value < 0 for value in costs)
                or produced.get('original_origin_prefix_preserved') is not True
                or procedure.get('original_prmtop') != produced.get('original_raw_operands', {}).get('model.prmtop')
                or procedure.get('original_inpcrd') != produced.get('original_raw_operands', {}).get('model.inpcrd')):
            raise ValueError('closed raw supply replaces the genuine new load or original lexical origin prefix')
        for phase, row in (('assignment-origin', assignment), ('geometry', geometry)):
            if (row.get('schema') != 'el.rubisco.wt03.closed-raw-derived-independent-phase.v1'
                    or row.get('phase') != phase or row.get('phase_state') != 'COMPLETED'
                    or row.get('assessment_error') is not None or row.get('native_calls') != 0
                    or row.get('producer_reexecution') is not False or row.get('qualification') is not False
                    or row.get('physical_independent_units') != 0 or row.get('matched_I95M_admission') is not False
                    or not _binding_matches(row.get('source_manifest'), self.independent_source_manifest.evidence)
                    or not _binding_matches(row.get('historical_producer_source_manifest'), self.producer_source_manifest.evidence)
                    or not _binding_matches(row.get('derived_products'), self.postprocessing_readout.evidence)
                    or any(row.get(name) != produced.get(name) for name in ('original_raw_operands', 'derived_origin', 'derived_parameter_audit'))):
                raise ValueError('closed raw supply lacks complete same-product independent phase custody')
        expected = dict(original_history_scope=HISTORY_SCOPE, original_definition_count=40, original_begin_count=5,
            original_contact_count=5, original_completion_count=0, original_unit_return='ABSENT',
            original_typed_native_return='ABSENT', original_native_os_return='UNKNOWN', original_scientific_return='UNKNOWN',
            original_native_attempt_count='UNKNOWN', original_native_completed_count='UNKNOWN', original_native_cost='UNKNOWN',
            original_unit_states={name: state.value for name, state in self.history.original_unit_states},
            original_assignment_states=[list(row) for row in self.history.original_assignment_states], model_id=self.history.model_id)
        for row in (produced, assignment, geometry):
            if (any(row.get(name) != value for name, value in expected.items())
                    or not _binding_matches(row.get('original_raw_custody_audit'), self.history.raw_custody_audit.evidence)
                    or not _binding_matches(row.get('authoritative_original_process_closure'), self.history.process_closure.evidence)
                    or not _binding_matches(row.get('geometry_parent'), self.history.geometry_parent.evidence)):
                raise ValueError('closed raw condition relabels original UNKNOWN or missing-return history')
        result, geometry_result = assignment.get('result'), geometry.get('result')
        if type(result) is not dict or type(geometry_result) is not dict:
            raise ValueError('closed raw condition omits independent full result objects')
        counts, proof, support = (result.get(name) for name in ('complete_parameter_term_census', 'coordinate_origin_validation', 'inactive14_support'))
        if (type(counts) is not dict or set(counts) != {'atoms', 'bonds', 'angles', 'dihedrals'}
                or any(type(value) is not int or value < 0 for value in counts.values()) or counts['atoms'] != diagnostic.atom_count
                or type(proof) is not dict or proof.get('method') != asdict(ORIGIN_METHOD)
                or proof.get('complete_heavy_atom_count') != diagnostic.heavy_atom_count
                or type(proof.get('complete_source_group_count')) is not int
                or not 0 < proof['complete_source_group_count'] <= diagnostic.heavy_atom_count
                or type(support) is not dict or support.get('dihedral_count') != counts['dihedrals']
                or any(type(support.get(name)) is not int or support[name] < 0 for name in ('active14_term_count', 'inactive14_term_count'))
                or support['active14_term_count'] + support['inactive14_term_count'] != counts['dihedrals']
                or geometry_result.get('method') != _canonical(GEOMETRY_METHOD)
                or not _binding_matches(geometry_result.get('diagnostic'), self.geometry_diagnostic.evidence)
                or not _binding_matches(geometry_result.get('independent_assignment_origin_parent'), self.assignment_readout.evidence)
                or geometry_result.get('hard_geometry_disposition') != diagnostic.hard_geometry_disposition.value
                or geometry_result.get('pair_counts') != [list(row) for row in diagnostic.pair_counts]
                or geometry_result.get('bonded_counts') != [list(row) for row in diagnostic.bonded_counts]
                or any(dict(diagnostic.bonded_counts)[name] != counts[name] for name in ('bonds', 'angles', 'dihedrals'))):
            raise ValueError('closed raw condition replaces independent complete methods/atom/term/pair proofs')

    @property
    def model_id(self):
        return self.history.model_id

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.supply_id, self)


@dataclass(frozen=True, slots=True)
class KnownDerivedModelInstance(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/known-derived-model-instance'
    instance_id: str
    source: p.PreparationSelection
    plan: DerivedChemicalForcePlan
    preparation: p.PreparationProduct
    integrity: SerializedPreparationIntegrity
    geometry: SerializedPreparationGeometry
    custody: tuple[tuple[str, NativeSubworkDefinition, ObjectIdentity, NativeSubworkCompletion, ObjectIdentity, DurableUnitReturn], ...]

    def __post_init__(self):
        validate_stable_id(self.instance_id)
        if (type(self.plan) is not DerivedChemicalForcePlan or len(self.plan.selected_assets) != 1
                or self.plan.source != p.identity(self.source)):
            raise ValueError('known derived instance changes its original per-parent source/plan')
        self.plan.__post_init__()

    @property
    def model_id(self):
        return self.plan.selected_assets[0][0]

    @property
    def assets(self):
        return self.plan.selected_assets[0][1]

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.instance_id, self)


@dataclass(frozen=True, slots=True)
class ClosedRawModelInstance(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/closed-raw-model-instance'
    instance_id: str
    source: p.PreparationSelection
    supply: ClosedRawModelSupply

    def __post_init__(self):
        validate_stable_id(self.instance_id)
        self.source.__post_init__()
        if type(self.supply) is not ClosedRawModelSupply or self.supply.history.source != p.identity(self.source):
            raise ValueError('closed raw instance changes its exact original source')
        self.supply.__post_init__()

    @property
    def model_id(self):
        return self.supply.model_id

    @property
    def assets(self):
        return self.supply.assets

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.instance_id, self)


@dataclass(frozen=True, slots=True)
class ModelInstanceInputs(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-insilico-sampling/model-instance-inputs'
    inputs_id: str
    instances: tuple[ClosedRawModelInstance | KnownDerivedModelInstance, ...]

    def __post_init__(self):
        validate_stable_id(self.inputs_id)
        if (type(self.instances) is not tuple or not self.instances
                or any(type(row) not in (ClosedRawModelInstance, KnownDerivedModelInstance) for row in self.instances)
                or tuple(row.model_id for row in self.instances) != tuple(sorted(set(row.model_id for row in self.instances)))):
            raise ValueError('instance inputs duplicate or omit explicit per-model histories')
        for row in self.instances:
            row.__post_init__()

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.inputs_id, self)


@dataclass(frozen=True, slots=True)
class InstanceChemicalForcePlan(CanonicalRecord):
    """Same chemical schema, named1.4 wire form without false original returns."""
    SCHEMA: ClassVar[str] = c.ChemicalForcePlan.SCHEMA
    VERSION: ClassVar[str] = '1.4.0'
    plan_id: str
    source: ObjectIdentity
    instance_inputs: ObjectIdentity
    selected_assets: tuple[tuple[str, ObjectIdentity], ...]
    # Exact ordinary identities of all original parents, current instances and
    # independently assessed suppliers. The consumer recomputes this census.
    instance_operands: tuple[ObjectIdentity, ...]
    hardware: sampling.HardwareSelection
    workdir: str
    interpreter_path: str
    interpreter_sha256: str
    engine_inventory_sha256: str
    hardware_inspector_path: str
    hardware_inspector_sha256: str
    code_sources: tuple[tuple[str, str], ...]
    dependency_lock_sha256: str
    cutoff_nanometer: Decimal = Decimal('1')
    temperature_kelvin: Decimal = Decimal('298')
    platform_precision: str = 'mixed'
    device_index: str = '0'
    deterministic_forces: str = 'true'
    use_cpu_pme: str = 'false'
    minimizer_tolerance_kj_mol_nm: Decimal = Decimal('10')
    minimizer_max_iterations: int = 0
    minimizer_reporter_early_stop: bool = False
    objective_rms_normalization: str = 'SQRT_SUM_ALL_3N_OBJECTIVE_COMPONENTS_SQUARED_OVER_N_PARTICLES'
    external_runtime_files: tuple[tuple[str, int, str], ...] = ()
    terminal_position_join: str = 'FINITE_BINARY64_EXACT_BITS'
    model_census: tuple[tuple[str, str, str], ...] = p.model_roster()
    nve_census: tuple[tuple[str, str, str, str, str], ...] = sampling.trajectory_roster()
    physical_independent_units: int = 0

    def __post_init__(self):
        validate_stable_id(self.plan_id)
        for row, schema in ((self.source, p.PreparationSelection.SCHEMA), (self.instance_inputs, ModelInstanceInputs.SCHEMA)):
            if type(row) is not ObjectIdentity or row.object_schema != schema:
                raise ValueError('instance plan changes exact source/input owners')
            row.__post_init__()
        names = tuple(name for name, _ in self.selected_assets)
        if not names or names != tuple(sorted(set(names))) or set(names) - set(MODEL_IDS):
            raise ValueError('instance plan omits its explicit selected model subset')
        for _, row in self.selected_assets:
            if type(row) is not ObjectIdentity or row.object_schema != p.ModelAssets.SCHEMA:
                raise ValueError('instance plan replaces exact model asset owners')
            row.__post_init__()
        if (tuple(row.object_id for row in self.instance_operands) != tuple(sorted(set(row.object_id for row in self.instance_operands)))
                or self.instance_inputs not in self.instance_operands or self.source not in self.instance_operands):
            raise ValueError('instance plan omits exact ordinary parent/instance operand census')
        for row in self.instance_operands:
            row.__post_init__()
        self.hardware.__post_init__()
        for name in ('interpreter_sha256', 'engine_inventory_sha256', 'hardware_inspector_sha256', 'dependency_lock_sha256'):
            validate_sha256(getattr(self, name))
        for name in ('workdir', 'interpreter_path', 'hardware_inspector_path'):
            path = PurePosixPath(getattr(self, name))
            if not path.is_absolute() or '..' in path.parts:
                raise ValueError('instance plan needs exact selected absolute paths')
        if not PurePosixPath(self.workdir).is_relative_to(p.NATIVE_WORK_ROOT) or self.workdir == p.NATIVE_WORK_ROOT:
            raise ValueError('instance plan needs a fresh selected molecular workdir')
        if not self.code_sources or tuple(row[0] for row in self.code_sources) != tuple(sorted(set(row[0] for row in self.code_sources))):
            raise ValueError('instance plan omits complete selected producing source')
        for path, digest in self.code_sources:
            if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
                raise ValueError('instance plan source escapes selected checkout')
            validate_sha256(digest)
        if tuple(row[0] for row in self.external_runtime_files) != tuple(sorted(set(row[0] for row in self.external_runtime_files))):
            raise ValueError('instance plan duplicates external runtime files')
        for path, size, digest in self.external_runtime_files:
            if not PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or type(size) is not int or size <= 0:
                raise ValueError('instance plan omits full external runtime file bytes')
            validate_sha256(digest)
        numerical = ('cutoff_nanometer', 'temperature_kelvin', 'platform_precision', 'device_index', 'deterministic_forces',
            'use_cpu_pme', 'minimizer_tolerance_kj_mol_nm', 'minimizer_max_iterations', 'minimizer_reporter_early_stop',
            'objective_rms_normalization', 'terminal_position_join', 'model_census', 'nve_census', 'physical_independent_units')
        defaults = {row.name: row.default for row in fields(c.ChemicalForcePlan)}
        if (any(getattr(self, name) != defaults[name] for name in numerical)
                or type(self.minimizer_max_iterations) is not int or self.minimizer_reporter_early_stop is not False):
            raise ValueError('instance plan changes frozen numerical science or24/96 denominator')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.plan_id, self)


def ordinary_instance_records(inputs):
    """Exact canonical originals supplied as ordinary authenticated operands."""
    records = {inputs.identity: inputs}
    def retain(record, identity=None, parent=None):
        original = identity or (record.identity if hasattr(record, 'identity') else p.identity(record))
        # Original source/plan object IDs are reused across retained parents.
        # Transport each exact original under a per-instance ordinary alias;
        # original identities inside the scientific records remain unchanged.
        selected = original if parent is None else ObjectIdentity.from_record(
            parent + '.operand.' + sha256(original.canonical_bytes()).hexdigest()[:24], record)
        if selected in records and records[selected] != record:
            raise ValueError('instance operands repeat conflicting canonical originals')
        records[selected] = record
    for instance in inputs.instances:
        retain(instance)
        retain(instance.source, parent=instance.instance_id)
        if type(instance) is KnownDerivedModelInstance:
            retain(instance.plan, parent=instance.instance_id)
            for record in (instance.preparation, instance.integrity, instance.geometry, instance.plan.preparation_plan, *instance.plan.derived_supplies):
                retain(record, parent=instance.instance_id)
            for _, definition, ci, completion, ri, returned in instance.custody:
                retain(definition, parent=instance.instance_id)
                retain(completion, ci, instance.instance_id)
                retain(returned, ri, instance.instance_id)
        else:
            retain(instance.supply, parent=instance.instance_id)
            retain(instance.supply.history, parent=instance.instance_id)
            retain(instance.supply.history.original_plan, parent=instance.instance_id)
            history = instance.supply.history
            for label, record in (('audit', history.raw_custody_audit), ('closure', history.process_closure), ('geometry-parent', history.geometry_parent)):
                retain(record, ObjectIdentity.from_record(history.history_id + '.' + label, record), instance.instance_id)
            closure = _document(history.process_closure)
            definitions = {row['record']['value']['subwork_id']: _decode_json(row['record'], NativeSubworkDefinition)
                for row in closure['full_definitions']}
            for definition in definitions.values():
                retain(definition, parent=instance.instance_id)
            for row in closure['full_begins']:
                begin = _decode_json(row['record'], NativeSubworkBegin)
                definition = definitions[begin.definition.object_id]
                prefix = 'native-subwork.' + sha256((definition.parent_contact.task_id + ':' + definition.subwork_id).encode()).hexdigest()
                retain(begin, ObjectIdentity.from_record(prefix + '.begin', begin), instance.instance_id)
            for name, raw in history.original_contacts:
                contact = decode_canonical_bytes(raw.raw_utf8.encode(), NativeSubworkContact, maximum_bytes=None)
                definition = definitions[name]
                prefix = 'native-subwork.' + sha256((definition.parent_contact.task_id + ':' + name).encode()).hexdigest()
                retain(contact, ObjectIdentity.from_record(prefix + '.contact', contact), instance.instance_id)
    return tuple(sorted(records.items(), key=lambda row: row[0].object_id))


def validate_instance_operands(plan, source, inputs, integrity, geometry, assets, custody):
    if (type(plan) is not InstanceChemicalForcePlan or type(inputs) is not ModelInstanceInputs
            or integrity is not None or geometry is not None or custody != ()):
        raise ValueError('instance plan requires explicit per-parent inputs and absent legacy aggregate slots')
    plan.__post_init__(); source.__post_init__(); inputs.__post_init__()
    if plan.source != p.identity(source) or plan.instance_inputs != inputs.identity:
        raise ValueError('instance consumer substitutes exact selected source/input bytes')
    actual = tuple((c.model_id((row.construct_id, row.joint_view_id, row.parameter_view)), p.identity(row)) for row in assets)
    if actual != plan.selected_assets or actual != tuple((row.model_id, row.assets) for row in inputs.instances):
        raise ValueError('instance consumer replaces its exact per-model current-use assets')
    expected = {identity for identity, _ in ordinary_instance_records(inputs)} | {identity for _, identity in actual} | {plan.source}
    if tuple(sorted(expected, key=lambda row: row.object_id)) != plan.instance_operands:
        raise ValueError('instance consumer omits exact ordinary original custody/proof operands')
    scientific = tuple(row.name for row in fields(source) if row.name not in ('selection_id', 'native_workdir'))
    for instance, asset in zip(inputs.instances, assets, strict=True):
        asset.__post_init__()
        if (asset.source != p.identity(instance.source)
                or any(getattr(instance.source, name) != getattr(source, name) for name in scientific)
                or instance.source.engine_inventory_sha256 != plan.engine_inventory_sha256):
            raise ValueError('instance consumer changes original genotype/stock/chemical-state/engine lineage')
        if type(instance) is KnownDerivedModelInstance:
            validate_derived_operands(instance.plan, instance.source, instance.preparation, instance.integrity,
                instance.geometry, (asset,), instance.custody)
            supplier = instance.plan.derived_supplies[0]
        else:
            supplier = instance.supply
            produced = _document(supplier.postprocessing_readout)
            by_name = {PurePosixPath(row.evidence.relative_path).name: row for row in asset.files}
            if len(by_name) != len(asset.files) or set(by_name) != ASSET_NAMES:
                raise ValueError('closed raw consumer omits the five complete raw/derived assets')
            for name in (*RAW_NAMES, 'atom-origin-provenance.json'):
                original = produced.get('original_raw_operands', {}).get(name)
                evidence = next((row for row in supplier.history.files
                    if row.relative_path == supplier.model_id + '/' + name), None)
                if evidence is None or not _binding_matches(original, evidence):
                    raise ValueError('closed raw consumer replaces original authenticated model bytes')
                if name in RAW_NAMES and by_name[name].evidence != evidence:
                    raise ValueError('closed raw consumer substitutes original topology/restart/heavy evidence')
            for name, key in (('atom-origin-provenance.json', 'derived_origin'), ('complete-assigned-parameters.json', 'derived_parameter_audit')):
                if not _binding_matches(produced.get(key), by_name[name].evidence):
                    raise ValueError('closed raw consumer replaces independently assessed derived products')
            diagnostic = decode_canonical_bytes(supplier.geometry_diagnostic.raw_utf8.encode(), GeometryDiagnostic, maximum_bytes=None)
            if diagnostic.hard_geometry_disposition is not A.SATISFIED:
                raise ValueError('closed raw consumer refuses adverse independent hard geometry')
        manifest = _document(supplier.independent_source_manifest)
        members = manifest.get('members', ())
        if (tuple(row.get('relative_path') for row in members) != INDEPENDENT_OWNERS
                or any(dict(plan.code_sources).get(row['relative_path']) != row['frozen']['sha256'] for row in members)):
            raise ValueError('instance consumer replaces complete independent five-owner source pins')
    return plan
