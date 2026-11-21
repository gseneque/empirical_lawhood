# SPDX-License-Identifier: MPL-2.0
"""Two immutable SCI02-D tranches through the generic experiment compiler."""
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentInputs
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge import bindings as binding
from empirical_lawhood.domains.matrix.matrix_equilibrium_bridge.records import BANK_COUNTS, PROTOCOL_ID as PROTOCOL_ID, BridgeDesign, BridgeSelection, BridgeProduct


@dataclass(frozen=True, slots=True)
class BridgeSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02d/specification'
    specification_id: str
    design: ObjectIdentity
    selection: ObjectIdentity
    provenance: ObjectIdentity
    campaign: ObjectIdentity
    tranche: str
    frozen: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if self.tranche not in ('TRAINING', 'CONFIRMATION') or (self.frozen is None) != (self.tranche == 'TRAINING'):
            raise ValueError('SCI02-D changes its finite original tranche or frozen input')
        pairs = ((self.design, BridgeDesign), (self.selection, BridgeSelection), (self.provenance, NumericalProducingProvenance),
            (self.campaign, CampaignSpec), *((p, BridgeProduct) for p in (self.frozen,) if p is not None))
        for value, kind in pairs:
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('SCI02-D substitutes an exact canonical input')
            value.__post_init__()

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id, self)


def input_record_types(): return BridgeDesign, BridgeSelection, BridgeProduct, NumericalProducingProvenance, CampaignSpec


def roots_for(selection, tranche):
    if tranche not in ('TRAINING', 'CONFIRMATION'): raise ValueError('unknown SCI02-D tranche')
    return tuple(selection.root(bank, i) for bank in (('TRAINING',) if tranche == 'TRAINING' else ('CONFIRMATION', 'REFERENCE')) for i in range(BANK_COUNTS[bank]))


def allocation_for(selection, tranche):
    roots = roots_for(selection, tranche)
    return UnitAllocation('allocation.sci02d.'+tranche.lower()+'.'+selection.fingerprint(), (selection.identity,),
        tuple(IndependentUnit(r.group_id, selection.record_id, 'family.matrix-sci02d.canonical-target', binding.VIEWS, tranche == 'TRAINING') for r in roots),
        tuple(UnitRoleAssignment(r.group_id, r.bank.lower()) for r in roots))


def expected_records(specification):
    return {'design': (BridgeDesign, specification.design), 'selection': (BridgeSelection, specification.selection),
        'provenance': (NumericalProducingProvenance, specification.provenance), 'campaign': (CampaignSpec, specification.campaign),
        **({} if specification.frozen is None else {'frozen': (BridgeProduct, specification.frozen)})}


def bind_inputs(specification, records, *, files=None):
    expected = expected_records(specification)
    if set(records)-set(expected) or files: raise ValueError('SCI02-D binding adds unselected scientific operands')
    for key, value in records.items():
        kind, pin = expected[key]
        if type(value) is not kind or ObjectIdentity.from_record(pin.object_id, value) != pin:
            raise ValueError('SCI02-D binding substitutes '+key)
        value.__post_init__()
    selection, design, frozen = records.get('selection'), records.get('design'), records.get('frozen')
    if selection is not None and design is not None and selection.design != design:
        raise ValueError('SCI02-D changes its exact native design')
    if frozen is not None and (frozen.config.phase != 'fit' or frozen.fit is None
            or design is not None and frozen.config.design != design
            or selection is not None and frozen.config.selection != selection.identity):
        raise ValueError('SCI02-D continuation lacks its original complete frozen fit')
    return PreparedExperimentInputs({} if selection is None else {'selection': allocation_for(selection, specification.tranche)}, records)


def lower(specification, records):
    return binding.lower(records['design'], records['selection'], roots_for(records['selection'], specification.tranche),
        records['provenance'], records['campaign'], draft_id='draft.'+specification.specification_id,
        fitted=None if specification.frozen is None else records['frozen'].fit)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    specification.__post_init__(); execution.__post_init__()
    records = {} if method_inputs is None else method_inputs
    dependencies = [ExperimentDependency('sci02d.input.'+key, DependencyKind.EXTERNAL_INPUT, 'Supply exact SCI02-D '+key+'.', key)
        for key in expected_records(specification) if key not in records]
    dependencies.extend(ExperimentDependency('sci02d.execution.'+key, DependencyKind.ENVIRONMENT, 'Select explicit '+key+'.')
        for key in ('environment_id', 'source_snapshot', 'output_root', 'workers') if getattr(execution, key) is None)
    if protocol_bytes is not None: raise ValueError('SCI02-D protocol bytes belong to its exact frozen design')
    allocation, draft, inputs = None, None, ()
    if not dependencies:
        bind_inputs(specification, records)
        allocation = allocation_for(records['selection'], specification.tranche)
        if scientific_inputs != {'selection': allocation}: raise ValueError('SCI02-D changes the complete independent allocation')
        draft, inputs = lower(specification, records)
    count = 16 if specification.tranche == 'TRAINING' else 72
    operations = 34 if specification.tranche == 'TRAINING' else 145
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((('independent-bundles', count),), (('independent-bundles', 0 if allocation is None else count),),
            (('operations', operations),), (('native-hamiltonians', 2), ('numerical-views', 2), ('starting-histories', 2)), count),
        tuple(sorted(dependencies, key=lambda d: d.code)), allocation=allocation, draft=draft, input_records=inputs,
        execution=execution, specification_record=specification,
        design_records=tuple(sorted((p.object_id, records[k]) for k, (_, p) in expected_records(specification).items() if k in records)))


def validate_instance(*, specification, allocation, draft, source_records):
    pins = {pin: key for key, (_, pin) in expected_records(specification).items()}
    records = {}
    for object_id, value in source_records:
        key = pins.get(ObjectIdentity.from_record(object_id, value))
        if key is None or key in records: raise ValueError('SCI02-D instance changes its original exact records')
        records[key] = value
    if set(records) != set(expected_records(specification)): raise ValueError('SCI02-D instance omits an original source record')
    bind_inputs(specification, records)
    expected, _ = lower(specification, records)
    if draft != expected and records['design'].protocol_document_sha256 == 'cb2bb1a3be6fcf05be70d74cce7e7ef25edf34249b8333530ef7bfeb7d89587b':
        # Protocol v1's original November tranche used 192 MiB for both
        # publications. Accept that one exact historical draft, without changing
        # its bytes or extending current authoring/worker resource admission.
        from dataclasses import replace
        historical = replace(expected, operations=tuple(replace(operation,
            resource_budget=replace(operation.resource_budget, output_bytes=192 * 1024**2))
            for operation in expected.operations))
        if draft == historical:
            expected = historical
    if allocation != allocation_for(records['selection'], specification.tranche) or draft != expected:
        raise ValueError('SCI02-D instance substitutes its code-derived original complete tranche')
