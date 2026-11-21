# SPDX-License-Identifier: MPL-2.0
"""Two gas parameter transformations through the existing native lifecycle."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import resource
import time
import traceback
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_contracts import DurableRawFileCensus
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_preparation import RAW_MAGIC, _ChunkReader, publish_directory, publish_record, uncompressed_archive_chunks, directory_census
from empirical_lawhood.domains.rubisco.rubisco_insilico_dynamics.durable_roster import json_output, raw_output
from empirical_lawhood.science.identity.authority import ResourceBudget
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord, canonical_json_document_bytes, validate_stable_id
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ArtifactProfile, CanonicalTaskReceipt, ReceiptCheck
from empirical_lawhood.execution.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.execution.execution import RunnerResult, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.execution.native_effects import NativeEntryRefused
from empirical_lawhood.execution.native_subwork import NativeSubworkCompletion, NativeSubworkDefinition, NativeSubworkObservationPublicationError, NativeSubworkRoster, NativeSubworkState, invoke_native_subwork, require_native_completion_receipt
from empirical_lawhood.execution.plans import OutputTemplate, ScientificStage
from empirical_lawhood.execution.prepared_native_invocation import PreparedNativeWork
from empirical_lawhood.execution.recursive_compiler import RecursivePortContract
from empirical_lawhood.execution.recursive_handoff import RecursiveImplementationBinding
from empirical_lawhood.execution.recursive_provider import RecursiveExecutionProperties, RecursiveOperationDeclaration, RecursiveScientificHooks
from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_records import GASES, MAX_METADATA, MAX_SOURCE, GasParameterSource, authenticate_gas_parameter_engine
from empirical_lawhood.adapters.rubisco.rubisco_response.gas_topology import append_gas_parameter_tables
from empirical_lawhood.domains.rubisco.rubisco_response.gas_topology_assessment import assess_gas_parameter_tables
from empirical_lawhood.domains.rubisco.rubisco_response.construction_engine import _absolute
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact


CAPABILITY = 'rubisco-response.prepare-gas-parameter-pair'
UNIT = 'unit.gp-original-1bwv-assembly'
BUDGET = ResourceBudget(1, 8*2**30, 0, None, 512*2**20, 2*2**30)


@dataclass(frozen=True, slots=True)
class GasParameterConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-config'
    config_id: str
    source: ObjectIdentity
    source_size_bytes: int
    implementation: RecursiveImplementationBinding
    provenance: NumericalProducingProvenance
    work_directory: str

    def __post_init__(self):
        validate_stable_id(self.config_id)
        for value, kind in ((self.source, ObjectIdentity), (self.implementation, RecursiveImplementationBinding),
                (self.provenance, NumericalProducingProvenance)):
            exact(value, kind)
        _absolute(self.work_directory)
        if (self.source.object_schema != GasParameterSource.SCHEMA
                or self.source.object_version != GasParameterSource.VERSION
                or type(self.source_size_bytes) is not int or not 0 < self.source_size_bytes <= MAX_SOURCE
                or any(getattr(self.provenance, key) != getattr(self.implementation, key) for key in (
                    'package_sources', 'code_sources_sha256', 'dependency_lock_sha256',
                    'observed_git_head', 'observed_checkout_clean'))):
            raise ValueError('gas parameter configuration changes its exact source/provenance binding')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class GasParameterReturn(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-return'
    source: ObjectIdentity
    gas: str
    files: DurableRawFileCensus
    error: str | None

    def __post_init__(self):
        exact(self.source, ObjectIdentity)
        exact(self.files, DurableRawFileCensus)
        if self.source.object_schema != GasParameterSource.SCHEMA or self.gas not in GASES:
            raise ValueError('gas parameter return substitutes its selected source or gas')
        if self.error is not None and (type(self.error) is not str or not self.error):
            raise ValueError('gas parameter return loses its actual native diagnostic')


@dataclass(frozen=True, slots=True)
class GasParameterUnitProduct(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-unit-product'
    returned: GasParameterReturn
    definition: NativeSubworkDefinition
    completion: NativeSubworkCompletion
    receipt: CanonicalTaskReceipt
    assessment_json: str | None
    assessment_error: str | None

    def __post_init__(self):
        for value, kind in ((self.returned, GasParameterReturn), (self.definition, NativeSubworkDefinition),
                (self.completion, NativeSubworkCompletion), (self.receipt, CanonicalTaskReceipt)):
            exact(value, kind)
        require_native_completion_receipt(self.completion, self.receipt,
            outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY)
        if (self.definition.operation_id != CAPABILITY
                or self.definition.subwork_id != 'gas-parameters.'+self.returned.gas.lower()
                or self.definition.configuration != self.returned.source
                or self.completion.definition != self.definition.identity
                or self.completion.operational_status is not (
                    OperationalStatus.SUCCEEDED if self.returned.error is None else OperationalStatus.FAILED)):
            raise ValueError('gas parameter product changes its original native scope/completion')
        logical_id = self.receipt.task_id+'.output.build.return'
        logical = tuple(row for row in self.receipt.output_logical_artifacts if row.logical_artifact_id == logical_id)
        physical = tuple(row for row in self.receipt.output_materializations if row.logical_artifact_id == logical_id)
        raw = self.returned.canonical_bytes()
        if (len(logical) != 1 or len(physical) != 1 or logical[0].payload_schema != GasParameterReturn.SCHEMA
                or logical[0].content_sha256 != sha256(raw).hexdigest()
                or (physical[0].physical_sha256, physical[0].size_bytes) != (sha256(raw).hexdigest(), len(raw))):
            raise ValueError('gas parameter product substitutes its receipted original raw return')
        if self.assessment_json is not None:
            report = json.loads(self.assessment_json)
            file = next((row for row in self.returned.files.files
                if row.relative_path == self.definition.subwork_id+'/gas.prmtop'), None)
            if (self.returned.error is not None or self.assessment_error is not None or file is None
                    or report.get('augmented_topology_sha256') != file.sha256
                    or report.get('physical_or_chemical_admission') is not False
                    or canonical_json_document_bytes(report).decode('utf-8') != self.assessment_json):
                raise ValueError('gas parameter assessment substitutes its raw return or promotes its scope')
        if self.assessment_error is not None and (type(self.assessment_error) is not str or not self.assessment_error):
            raise ValueError('gas parameter product loses its actual assessment diagnostic')

    @property
    def identity(self):
        return ObjectIdentity.from_record('gas-parameter-unit.'+self.fingerprint(), self)


@dataclass(frozen=True, slots=True)
class GasParameterPairResult(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/gas-parameter-pair-result'
    source: ObjectIdentity
    units: tuple[GasParameterUnitProduct, ...]
    interpretation: str = 'PARAMETER_ASSIGNMENT_ONLY_NO_COORDINATE_CHEMISTRY_ENSEMBLE_OR_RATE_ADMISSION'

    def __post_init__(self):
        exact(self.source, ObjectIdentity)
        if (type(self.units) is not tuple or tuple(row.returned.gas for row in self.units) != GASES
                or any(row.returned.source != self.source for row in self.units)
                or self.interpretation != 'PARAMETER_ASSIGNMENT_ONLY_NO_COORDINATE_CHEMISTRY_ENSEMBLE_OR_RATE_ADMISSION'):
            raise ValueError('gas parameter result drops a selected gas or changes its original scope')
        for unit in self.units:
            exact(unit, GasParameterUnitProduct)

    @property
    def identity(self):
        return ObjectIdentity.from_record('result.gas-parameters.'+self.fingerprint(), self)


def operands(config):
    return tuple(sorted((config.identity, config.source, config.provenance.identity), key=lambda row: row.object_id))


def slots(config):
    return ('native.gas-parameters.'+config.fingerprint(),)


def native_work(context, config, parent):
    outputs = (json_output('build.return', GasParameterReturn), json_output('files.census', DurableRawFileCensus),
        raw_output('files.raw'))
    definitions = tuple(NativeSubworkDefinition('gas-parameters.'+gas.lower(), CAPABILITY, parent, config.source,
        operands(config), config.implementation.code_sources_sha256, config.implementation.dependency_lock_sha256,
        tuple(sorted(port.materialization_id for port in context.input_ports)), (), outputs) for gas in GASES)
    roster = NativeSubworkRoster('selected.native-subwork', parent, tuple(row.identity for row in definitions))
    return PreparedNativeWork(parent, (UNIT,), slots(config), definitions, (roster,))


def _decode(context):
    declaration = operation_declaration().manifest()
    if (context.task_id != CAPABILITY or context.permissions != declaration.permissions
            or context.resource_budget != BUDGET or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or len(context.input_ports) != 3):
        raise ValueError('gas parameter worker changes its complete task contract')
    received = {}
    for port in context.input_ports:
        maximum = MAX_SOURCE if port.payload_schema == GasParameterSource.SCHEMA else MAX_METADATA
        if (port.kind is not WorkerInputKind.EXTERNAL or port.media_type != 'application/json'
                or port.size_bytes > maximum or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
            raise ValueError('gas parameter worker changes a bounded direct exposed input')
        raw = port.read(maximum)
        if port.payload_schema in received:
            raise ValueError('gas parameter worker duplicates a direct input')
        received[port.payload_schema] = (port, raw)
    if set(received) != {GasParameterConfig.SCHEMA, GasParameterSource.SCHEMA, NumericalProducingProvenance.SCHEMA}:
        raise ValueError('gas parameter worker omits a complete direct native operand')
    port, raw = received[GasParameterConfig.SCHEMA]
    config = decode_canonical_bytes(raw, GasParameterConfig, maximum_bytes=MAX_METADATA)
    if (config.config_id, config.fingerprint(), port.artifact_id) != (
            context.config.config_id, context.config.content_sha256, context.config.artifact_id):
        raise ValueError('gas parameter worker substitutes its selected configuration')
    source_raw = received[GasParameterSource.SCHEMA][1]
    source = decode_canonical_bytes(source_raw, GasParameterSource, maximum_bytes=MAX_SOURCE)
    if (len(source_raw) != config.source_size_bytes or source.identity != config.source
            or received[NumericalProducingProvenance.SCHEMA][1] != config.provenance.canonical_bytes()):
        raise ValueError('gas parameter worker changes its exact source/provenance census')
    return config, source


def prepare_native_work(*, runner, context, expected_parent):
    if type(runner) is not GasParameterRunner:
        raise ValueError('gas parameter preparation requires its installed native owner')
    config, _ = _decode(context)
    return native_work(context, config, expected_parent)


def read_gas_parameter_files(native_subwork, definition, returned):
    """Authenticate every original raw member before returning topology bytes."""
    if sum(row.byte_count for row in returned.files.files) > BUDGET.output_bytes:
        raise ValueError('gas parameter return exceeds its selected output allocation')
    chunks = native_subwork.iter_completed_output(definition, 'files.raw')
    reader = _ChunkReader(uncompressed_archive_chunks(chunks))
    try:
        if reader.take(len(RAW_MAGIC)) != RAW_MAGIC:
            raise ValueError('gas parameter archive changes its original format')
        size = int.from_bytes(reader.take(8), 'big')
        if not 0 < size <= 2**20:
            raise ValueError('gas parameter archive exceeds its bounded census')
        header = reader.take(size)
        census = decode_canonical_bytes(header, DurableRawFileCensus, maximum_bytes=2**20)
        if census != returned.files or header != b''.join(native_subwork.iter_completed_output(definition, 'files.census')):
            raise ValueError('gas parameter archive changes its original raw census')
        files = {}
        for row in census.files:
            path = Path(row.relative_path)
            if path.parts != (definition.subwork_id, path.name):
                raise ValueError('gas parameter archive changes its original unit directory')
            parts, digest, remaining = [], sha256(), row.byte_count
            while remaining:
                block = reader.take(min(remaining, 2**20))
                remaining -= len(block)
                digest.update(block)
                if path.name == 'gas.prmtop':
                    parts.append(block)
            if digest.hexdigest() != row.sha256:
                raise ValueError('gas parameter archive contains changed original bytes')
            if path.name == 'gas.prmtop':
                files[path.name] = b''.join(parts)
        reader.finish()
        return files
    finally:
        close = getattr(chunks, 'close', None)
        if close is not None:
            close()


def assess_parameter_return(source, definition, returned, completed, native_subwork):
    assessment, error = None, None
    if returned.error is None:
        try:
            files = read_gas_parameter_files(native_subwork, definition, returned)
            if set(files) != {'gas.prmtop'}:
                raise ValueError('gas parameter return lacks its original complete topology')
            stock = next(row for row in source.stocks if row.gas == returned.gas)
            report = assess_gas_parameter_tables(original_topology_bytes=source.topology_ascii.encode('ascii'),
                augmented_topology_bytes=files['gas.prmtop'], stock=stock)
            assessment = canonical_json_document_bytes(report).decode('utf-8')
        except (ValueError, OSError, ArithmeticError):
            error = traceback.format_exc()
    return GasParameterUnitProduct(returned, definition, completed.completion, completed.receipt, assessment, error)


def _construct(source, stock, directory):
    """One actual library transformation; retain its raw bytes immediately."""
    raw = append_gas_parameter_tables(original_topology_bytes=source.topology_ascii.encode('ascii'), stock=stock)
    with (directory/'gas.prmtop').open('xb') as stream:
        stream.write(raw)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    # The original return remains on disk even if loaded-stock validation fails.
    authenticate_gas_parameter_engine(source.engine, loaded=True)


class GasParameterRunner:
    def __init__(self):
        self.manifest = operation_declaration().manifest()

    def preflight(self, context):
        _, source = _decode(context)
        authenticate_gas_parameter_engine(source.engine)

    def execute(self, context):
        raise ValueError('gas parameter construction requires ordinary native lifecycle authority')

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        try:
            config, source = _decode(context)
            prepared = context.prepared_invocation
            if prepared is None or prepared.implementation != config.implementation:
                raise ValueError('gas parameter construction changes its frozen producing source')
            authenticate_gas_parameter_engine(source.engine)
            work = native_work(context, config, native_subwork.parent_contact)
            if prepared.native_work != work:
                raise ValueError('gas parameter construction changes its complete prepared native census')
            root = Path(config.work_directory)
            if root.is_symlink():
                raise ValueError('gas parameter work directory cannot be a symlink')
            root.mkdir(parents=False, exist_ok=True)
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            units = []
            for definition, stock in zip(work.definitions, source.stocks, strict=True):
                completed = native_subwork.recover(definition)
                if completed is not None:
                    returned = decode_canonical_bytes(b''.join(native_subwork.iter_completed_output(definition, 'build.return')),
                        GasParameterReturn, maximum_bytes=MAX_METADATA)
                else:
                    if native_subwork.inspect(definition).state is not NativeSubworkState.NOT_ENTERED:
                        raise ValueError('uncertain gas parameter contact cannot be repeated')
                    authenticate_gas_parameter_engine(source.engine)
                    directory = root/definition.subwork_id
                    directory.mkdir()
                    entry = native_subwork.begin(definition)
                    native_subwork.contact(entry)
                    cpu, wall, error = time.process_time(), time.monotonic(), None
                    try:
                        invoke_native_subwork(native_subwork, entry, _construct, source, stock, directory)
                    except (NativeEntryRefused, NativeSubworkObservationPublicationError):
                        raise
                    except Exception:
                        error = traceback.format_exc()
                        with (directory/'process-error.txt').open('x') as stream:
                            stream.write(error)
                    census, _ = publish_directory(native_subwork, entry, directory, root, selected_census=directory_census(directory, root))
                    returned = GasParameterReturn(source.identity, stock.gas, census, error)
                    publish_record(native_subwork, entry, 'build.return', returned)
                    completed = native_subwork.complete(entry,
                        operational_status=OperationalStatus.SUCCEEDED if error is None else OperationalStatus.FAILED,
                        cost=InquiryCost(Decimal(str(time.process_time()-cpu)), Decimal(str(time.monotonic()-wall)),
                            Decimal(sum(row.byte_count for row in census.files))),
                        cost_scope='One original host load, one gas construction and one combination plus raw publication; zero force evaluations.',
                        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                        reason_codes=() if error is None else ('gas-parameter-build-failure',))
                # Every original return and failure is sealed before assessment.
                units.append(assess_parameter_return(source, definition, returned, completed, native_subwork))
            result = GasParameterPairResult(source.identity, tuple(units))
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != CAPABILITY+'.product'
                    or context.output_ports[0].payload_schema != result.SCHEMA):
                raise ValueError('gas parameter construction changes its aggregate output contract')
            return RunnerResult((TaskOutputPayload(context.output_ports[0].output_id, result.canonical_bytes()),),
                (ReceiptCheck('complete-original-two-gas-parameter-census', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_declaration():
    from empirical_lawhood.domains.rubisco.rubisco_response.gas_parameter_translation import validate_root
    return RecursiveOperationDeclaration(capability_key=CAPABILITY, capability_version='1.0.0',
        implementation_id='complete-source-bound-gas-parameter-pair-v1', kind=CapabilityKind.SIMULATOR,
        config_record_type=GasParameterConfig, stage=ScientificStage.ACQUIRE,
        input_ports=(RecursivePortContract('native-provenance', NumericalProducingProvenance.SCHEMA, 'application/json', MAX_METADATA),
            RecursivePortContract('native-source', GasParameterSource.SCHEMA, 'application/json', MAX_SOURCE)),
        outputs=(OutputTemplate('product', GasParameterPairResult.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS,
            CapabilityPermission.READ_DEVELOPMENT))), evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE, visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY,
        resources=BUDGET, conformance_check_ids=('complete-host-and-two-gas-census', 'original-custody-no-replay',
            'raw-return-before-assessment', 'unchanged-host-parameters'), runner_factory=GasParameterRunner,
        record_codecs={kind.SCHEMA: kind for kind in (GasParameterConfig, GasParameterSource, GasParameterPairResult,
            NumericalProducingProvenance)}, scientific_hooks=RecursiveScientificHooks(
                scientific_operand_sha256s=lambda config: tuple(sorted({row.object_fingerprint for row in operands(config)})),
                scientific_unit_ids=lambda config: (UNIT,), native_effect_slot_ids=slots, scientific_root_validator=validate_root),
        execution_properties=RecursiveExecutionProperties(native_effect=True, complete_unit_census=True,
            native_work_preparer=prepare_native_work))
