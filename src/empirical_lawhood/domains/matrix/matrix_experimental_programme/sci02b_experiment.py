# SPDX-License-Identifier: MPL-2.0
"""Supported SCI02-B retained-development inputs and code-derived experiment."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02b_bindings as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Selection
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02b_records import PROTOCOL_ID as PROTOCOL_ID, Sci02BDesign, Sci02BRetainedCase


@dataclass(frozen=True, slots=True)
class Sci02BSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02b/specification'
    specification_id: str
    study: ObjectIdentity
    selection: ObjectIdentity
    cases: tuple[ObjectIdentity, ...]
    provenance: ObjectIdentity
    campaign: ObjectIdentity
    tranche: str = 'DEVELOPMENT'

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value, kind in ((self.study, Sci02BDesign), (self.selection, Sci02Selection),
                (self.provenance, NumericalProducingProvenance), (self.campaign, CampaignSpec),
                *((p, Sci02BRetainedCase) for p in self.cases)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('SCI02-B specification changes its exact selected inputs')
            value.__post_init__()
        if self.tranche != 'DEVELOPMENT' or len(self.cases) != 8 or len(set(self.cases)) != 8:
            raise ValueError('SCI02-B development requires all eight original retained roots')

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id, self)


def input_record_types(): return Sci02BDesign, Sci02Selection, Sci02BRetainedCase, NumericalProducingProvenance, CampaignSpec


def allocation_for(selection):
    roots = tuple(selection.root('DEV', i) for i in range(8))
    views = tuple(sorted((selection.design.coordinate.primary_view.view_id, selection.design.coordinate.fine_view.view_id)))
    return UnitAllocation('allocation.sci02b.development.' + selection.fingerprint(), (selection.identity,),
        tuple(IndependentUnit(r.group_id, selection.record_id, selection.design.coordinate.family_id, views, False) for r in roots),
        tuple(UnitRoleAssignment(r.group_id, 'development') for r in roots))


def expected_records(specification):
    return {'study': (Sci02BDesign, specification.study), 'selection': (Sci02Selection, specification.selection),
        'provenance': (NumericalProducingProvenance, specification.provenance), 'campaign': (CampaignSpec, specification.campaign),
        **{f'root{i:02d}': (Sci02BRetainedCase, p) for i, p in enumerate(specification.cases)}}


def bind_inputs(specification, records, *, files=None):
    expected = expected_records(specification)
    if set(records) - set(expected) or set(files or {}) - {f'root{i:02d}-arrays' for i in range(8)}:
        raise ValueError('SCI02-B binding includes undeclared scientific operands')
    for key, value in records.items():
        kind, pin = expected[key]
        if type(value) is not kind or ObjectIdentity.from_record(pin.object_id, value) != pin:
            raise ValueError('SCI02-B binding substitutes ' + key)
        value.__post_init__()
    selection, study = records.get('selection'), records.get('study')
    if study is not None and selection is not None and (study.original_selection != selection.identity or study.physical != selection.design):
        raise ValueError('SCI02-B study changes the original reservation or physical design')
    for i in range(8):
        case, file = records.get(f'root{i:02d}'), (files or {}).get(f'root{i:02d}-arrays')
        if case is not None and selection is not None and (case.root != selection.root('DEV', i) or case.design != selection.design):
            raise ValueError('SCI02-B retained case changes its original root ordinal')
        if file is not None and (case is None or file.identity != case.arrays.array_artifact):
            raise ValueError('SCI02-B binding substitutes original retained array bytes')
    return PreparedExperimentInputs({} if selection is None else {'selection': allocation_for(selection)}, (records, files or {}))


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    specification.__post_init__(); execution.__post_init__()
    records, files = ({}, {}) if method_inputs is None else method_inputs
    dependencies = []
    for key in expected_records(specification):
        if key not in records:
            dependencies.append(ExperimentDependency('sci02b.input.' + key, DependencyKind.EXTERNAL_INPUT, 'Supply original SCI02-B ' + key + '.', key))
    for i in range(8):
        key = f'root{i:02d}-arrays'
        if key not in files:
            dependencies.append(ExperimentDependency('sci02b.input.' + key, DependencyKind.EXTERNAL_INPUT, 'Supply authenticated retained root arrays.', key))
    for key in ('environment_id', 'source_snapshot', 'output_root', 'workers'):
        if getattr(execution, key) is None:
            dependencies.append(ExperimentDependency('sci02b.execution.' + key, DependencyKind.ENVIRONMENT, 'Select explicit ' + key + '.'))
    if protocol_bytes is not None: raise ValueError('SCI02-B protocol bytes belong to the exact scientific study design')
    allocation, draft, inputs, input_files = None, None, (), ()
    if not dependencies:
        bind_inputs(specification, records, files=files)
        allocation = allocation_for(records['selection'])
        if scientific_inputs != {'selection': allocation}: raise ValueError('SCI02-B substitutes its original independent-root allocation')
        cases = tuple(records[f'root{i:02d}'] for i in range(8))
        draft, inputs = binding.lower(records['study'], records['selection'], cases, records['provenance'], records['campaign'],
            draft_id='draft.' + specification.specification_id)
        input_files = tuple(sorted(('external.' + f.identity.artifact_id,
            PreparedExperimentFile(f.identity, '1.0.0', f.path, f.identity.size_bytes)) for f in files.values()))
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((('whole-roots', 8),), (('whole-roots', 0 if allocation is None else 8),),
            (('operations', 17),), (('representation-candidates', 2), ('retained-response-packages', 24)), 0),
        tuple(sorted(dependencies, key=lambda d: d.code)), allocation=allocation, draft=draft, input_records=inputs,
        execution=execution, specification_record=specification, input_files=input_files,
        design_records=tuple(sorted((v.campaign_id if k == 'campaign' else v.identity.object_id, v) for k, v in records.items())))


def validate_instance(*, specification, allocation, draft, source_records):
    pins = {pin: key for key, (_, pin) in expected_records(specification).items()}
    records = {}
    for object_id, value in source_records:
        key = pins.get(ObjectIdentity.from_record(object_id, value))
        if key is None or key in records: raise ValueError('SCI02-B instance changes the exact original source census')
        records[key] = value
    if set(records) != set(expected_records(specification)): raise ValueError('SCI02-B instance omits an original source')
    bind_inputs(specification, records)
    expected, _ = binding.lower(records['study'], records['selection'], tuple(records[f'root{i:02d}'] for i in range(8)),
        records['provenance'], records['campaign'], draft_id='draft.' + specification.specification_id)
    if allocation != allocation_for(records['selection']) or draft != expected:
        raise ValueError('SCI02-B instance changes its code-derived original development graph')
