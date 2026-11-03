# SPDX-License-Identifier: MPL-2.0
"""Freeze fixed current aggregate custody before its calibration and reveal.

This operational addition freezes only the current complete metadata corpus.
It does not claim to precede the original acquisition futures, fit a model,
qualify a parent or grant access to any retained sealed case output.
"""

from empirical_lawhood.runtime.recursive_provider import (
    RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveExecutionProperties,
)
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import RunnerResult, TaskContext, TaskOutputPayload, WorkerInputKind
from empirical_lawhood.runtime.plans import BarrierKind, OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import RecursivePortContract

from .compact_records import ScheduledCompactBank, compact_identity
from .operation_bindings import BUDGET
from .programme_acquisition_custody import ScheduledProgrammeAcquisitionWaveCustody
from .programme_calibration import ScheduledProgrammeWaveCustody
from .programme_global import validate_programme_root
from .programme_records import NAMESPACE, ScheduledProgramme, validate_programme_bank

from empirical_lawhood.adapters.methods.matrix_response_study.numerical_runtime import MATRIX_PROVENANCE_REQUIREMENT

TASK_ID = NAMESPACE+'.tail-custody-freeze'
CONFIG_ID = 'config.'+TASK_ID
MAXIMUM_CONFIG_BYTES, MAXIMUM_BYTES = 4*1024**2, 16*1024**2
BLIND, PROSPECTIVE = OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeTailFreezeConfig(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/tail-custody-freeze-config'
    config_id: str
    programme: ScheduledProgramme
    bank: ObjectIdentity
    wave_custody: tuple[ObjectIdentity, ...]

    def __post_init__(self):
        if (self.config_id != CONFIG_ID or type(self.programme) is not ScheduledProgramme
                or self.programme.mode != 'E4_REVISION_CALIBRATION' or self.bank != self.programme.bank
                or len(self.wave_custody) != 16 or len(set(self.wave_custody)) != 16
                or len({p.object_schema for p in self.wave_custody}) != 1
                or any(p.object_schema not in (ScheduledProgrammeWaveCustody.SCHEMA,
                    ScheduledProgrammeAcquisitionWaveCustody.SCHEMA) or p.object_version != '1.0.0' for p in self.wave_custody)
                or len(self.canonical_bytes()) > MAXIMUM_CONFIG_BYTES):
            raise ValueError('tail metadata freeze requires exact fixed global64 programme/bank and sixteen homogeneous custody pins')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.config_id, self)


@dataclass(frozen=True, slots=True)
class ScheduledProgrammeFrozenTailCustody(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-scheduled-programme/frozen-tail-custody'
    freeze_id: str
    configuration: ScheduledProgrammeTailFreezeConfig

    def __post_init__(self):
        if (type(self.configuration) is not ScheduledProgrammeTailFreezeConfig
                or self.freeze_id != self.configuration.programme.programme_id+'.tail-custody-freeze'):
            raise ValueError('tail freeze changes the actual fixed aggregate custody declaration')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.freeze_id, self)


def scientific_root_validator(config, context):
    if (type(config) is not ScheduledProgrammeTailFreezeConfig or context.node_id != TASK_ID
            or context.stage is not ScientificStage.FREEZE or context.outcome_access is not BLIND
            or context.visibility_ceiling is not PROSPECTIVE or context.unit_ids != config.programme.group_ids):
        raise ValueError('tail metadata freeze changes its actual blind stage or complete global scope')
    validate_programme_root(config.programme, context)


class ScheduledProgrammeTailCustodyFreezer:
    def __init__(self, manifest):
        self.manifest = manifest

    def execute(self, context):
        try:
            if (type(context) is not TaskContext or context.task_id != TASK_ID
                    or context.permissions != self.manifest.permissions or context.outcome_access is not BLIND
                    or not BUDGET.contains(context.resource_budget)
                    or any(p.kind is not WorkerInputKind.EXTERNAL or p.outcome_access is not BLIND
                        or p.visibility_ceiling is not PROSPECTIVE for p in context.input_ports)):
                raise PermissionError('tail freeze refuses protected or changed input authority before reads')
            types = {c.SCHEMA: c for c in (ScheduledProgrammeTailFreezeConfig, ScheduledCompactBank,
                ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody)}
            values = {}
            for port in context.input_ports:
                cls = types.get(port.payload_schema)
                if cls is None:
                    raise ValueError('tail freeze receives an undeclared input schema')
                raw = port.read()
                record = decode_canonical_bytes(raw, cls, maximum_bytes=MAXIMUM_CONFIG_BYTES
                    if cls is ScheduledProgrammeTailFreezeConfig else MAXIMUM_BYTES)
                if raw != record.canonical_bytes() or len(raw) != port.size_bytes:
                    raise ValueError('tail freeze changes exact canonical current metadata bytes')
                values.setdefault(cls, []).append((record, port))
            if any(len(values.get(c, ())) != 1 for c in (ScheduledProgrammeTailFreezeConfig, ScheduledCompactBank)):
                raise ValueError('tail freeze omits exact actual config/shared bank')
            config, config_port = values[ScheduledProgrammeTailFreezeConfig][0]
            bank, bank_port = values[ScheduledCompactBank][0]
            custody = tuple(row[0] for cls in (ScheduledProgrammeWaveCustody, ScheduledProgrammeAcquisitionWaveCustody)
                for row in values.get(cls, ()))
            by_pin = {c.identity: c for c in custody}
            if (context.config.config_id != config.config_id or context.config.config_schema != config.SCHEMA
                    or context.config.content_sha256 != config.fingerprint() or context.config.artifact_id != config_port.artifact_id
                    or bank_port.artifact_id != bank.bank_id or compact_identity(bank) != config.bank
                    or len(custody) != 16 or set(by_pin) != set(config.wave_custody)
                    or tuple(by_pin[p].wave_id for p in config.wave_custody) != tuple(w.wave_id for w in config.programme.waves)
                    or any(c.configuration.programme != config.programme.identity or c.configuration.bank != config.bank
                        or c.configuration.wave != wave for c, wave in zip(
                            (by_pin[p] for p in config.wave_custody), config.programme.waves, strict=True))):
                raise ValueError('tail freeze substitutes actual config/bank or complete original fixed wave metadata')
            validate_programme_bank(config.programme, bank)
            product = ScheduledProgrammeFrozenTailCustody(config.programme.programme_id+'.tail-custody-freeze', config)
            if (len(context.output_ports) != 1 or context.output_ports[0].output_id != TASK_ID+'.product'
                    or context.output_ports[0].payload_schema != product.SCHEMA
                    or context.output_ports[0].profile is not ArtifactProfile.CANONICAL_JSON):
                raise ValueError('tail freeze changes its distinct actual output contract')
            return RunnerResult((TaskOutputPayload(TASK_ID+'.product', product.canonical_bytes()),),
                (ReceiptCheck('scheduled-programme-fixed-current-tail-custody-freeze', True, ()),))
        finally:
            for port in context.input_ports:
                port.close()


def operation_factories():
    return tuple(row.provider_factory() for row in operation_declarations())


def operation_declarations():
    inputs = (('bank', ScheduledCompactBank, 1, 1), ('wave-custody', ScheduledProgrammeWaveCustody, 0, 16), ('acquisition-wave-custody', ScheduledProgrammeAcquisitionWaveCustody, 0, 16))
    selected = RecursiveOperationDeclaration(
        capability_key=NAMESPACE + "." + 'tail-custody-freeze',
        capability_version="1.0.0",
        implementation_id='fixed-current-tail-metadata-before-reduction-reveal.v1',
        kind=CapabilityKind.EXPERIMENT_DESIGNER,
        config_record_type=ScheduledProgrammeTailFreezeConfig,
        stage=ScientificStage.FREEZE,
        input_ports=tuple(sorted((RecursivePortContract(name, cls.SCHEMA, 'application/json', MAXIMUM_BYTES, minimum_count=low, maximum_count=high) for name, cls, low, high in inputs), key=lambda port: port.port_id)),
        outputs=(OutputTemplate('product', ScheduledProgrammeFrozenTailCustody.SCHEMA, ArtifactProfile.CANONICAL_JSON, 'application/json', '.json'),),
        permissions=tuple(sorted((CapabilityPermission.READ_EXTERNAL_ARTIFACTS, CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS, CapabilityPermission.READ_FROZEN_MODELS))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE,
        outcome_access=BLIND,
        visibility_ceiling=PROSPECTIVE,
        resources=BUDGET,
        conformance_check_ids=tuple(sorted(('metadata-only-fixed-corpus', 'no-pre-original-future-chronology-claim'))),
        runner_factory=lambda: ScheduledProgrammeTailCustodyFreezer(selected.manifest()),
        record_codecs={ScheduledProgrammeFrozenTailCustody.SCHEMA: ScheduledProgrammeFrozenTailCustody, **{kind.SCHEMA: kind for _, kind, _, _ in inputs}},
        scientific_hooks=RecursiveScientificHooks(scientific_operand_sha256s=lambda c: tuple(sorted({c.programme.fingerprint(), c.bank.object_fingerprint})), scientific_unit_ids=lambda c: c.programme.group_ids, scientific_root_validator=scientific_root_validator),
        execution_properties=RecursiveExecutionProperties(barrier=BarrierKind.FREEZE),
        provenance_requirements=(MATRIX_PROVENANCE_REQUIREMENT,),
    )
    return (selected,)
