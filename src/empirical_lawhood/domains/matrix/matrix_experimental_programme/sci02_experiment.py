# SPDX-License-Identifier: MPL-2.0
"""Public SCI02 DEV8 preparation through the existing experiment seam."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs

from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_bindings import lower
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Selection


@dataclass(frozen=True, slots=True)
class Sci02Specification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02/specification'
    specification_id: str
    selection: ObjectIdentity
    provenance: ObjectIdentity
    campaign: ObjectIdentity
    tranche: str = 'DEV8'

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        for value, kind in ((self.selection, Sci02Selection), (self.provenance, NumericalProducingProvenance), (self.campaign, CampaignSpec)):
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('SCI02 specification changes an exact original scientific input')
            value.__post_init__()
        if self.tranche != 'DEV8':
            raise ValueError('SCI02 first accepted route admits only the original eight development roots')

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id, self)


def input_record_types(): return Sci02Selection, NumericalProducingProvenance, CampaignSpec


def allocation_for(selection):
    roots = tuple(selection.root('DEV', i) for i in range(8))
    views = tuple(sorted((selection.design.coordinate.primary_view.view_id, selection.design.coordinate.fine_view.view_id)))
    return UnitAllocation('allocation.sci02.dev8.' + selection.fingerprint(), (selection.identity,),
        tuple(IndependentUnit(r.group_id, selection.record_id, selection.design.coordinate.family_id, views, False) for r in roots),
        tuple(UnitRoleAssignment(r.group_id, 'development') for r in roots))


def bind_inputs(specification, records, *, files=None):
    expected = {'selection': Sci02Selection, 'provenance': NumericalProducingProvenance, 'campaign': CampaignSpec}
    if set(records) - set(expected) or set(files or {}) - {'templates'}:
        raise ValueError('SCI02 binding contains undeclared source operands')
    for key, value in records.items():
        identity = ObjectIdentity.from_record(value.campaign_id, value) if type(value) is CampaignSpec else getattr(value, 'identity', None)
        if type(value) is not expected[key] or identity != getattr(specification, key):
            raise ValueError('SCI02 binding substitutes its original ' + key)
        value.__post_init__()
    selection = records.get('selection')
    templates = (files or {}).get('templates')
    if templates is not None and (selection is None or templates.identity != selection.design.assay.template_artifact):
        raise ValueError('SCI02 binding changes its original fixed instrument template bytes')
    return PreparedExperimentInputs({} if selection is None else {'selection': allocation_for(selection)}, (records, files or {}))


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    specification.__post_init__(); execution.__post_init__()
    records, files = ({}, {}) if method_inputs is None else method_inputs
    dependencies = []
    for key in ('selection', 'provenance', 'campaign'):
        if key not in records:
            dependencies.append(ExperimentDependency('sci02.input.' + key, DependencyKind.EXTERNAL_INPUT, 'Supply the exact SCI02 ' + key + '.', key))
    if 'templates' not in files:
        dependencies.append(ExperimentDependency('sci02.input.templates', DependencyKind.EXTERNAL_INPUT,
            'Supply the original inherited instrument template NPZ.', 'templates'))
    for key in ('environment_id', 'source_snapshot', 'output_root', 'workers'):
        if getattr(execution, key) is None:
            dependencies.append(ExperimentDependency('sci02.execution.' + key, DependencyKind.ENVIRONMENT, 'Select explicit ' + key + '.'))
    if protocol_bytes is not None:
        raise ValueError('SCI02 physics and successor protocol belong to its exact selected design')
    allocation, draft, inputs, input_files = None, None, (), ()
    if not dependencies:
        bind_inputs(specification, records, files=files)
        selection = records['selection']
        allocation = allocation_for(selection)
        if scientific_inputs != {'selection': allocation}:
            raise ValueError('SCI02 preparation changes its original independent-unit allocation')
        draft, inputs = lower(selection, tuple(selection.root('DEV', i) for i in range(8)), records['provenance'], records['campaign'],
            draft_id='draft.' + specification.specification_id)
        binding = files['templates']
        input_files = (('external.templates.' + binding.identity.sha256,
            PreparedExperimentFile(binding.identity, '1.0.0', binding.path, binding.identity.size_bytes)),)
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((('whole-roots', 8),), (('whole-roots', 0 if allocation is None else 8),),
            (('operations', 224),), (('assigned-response-packages', 24), ('methods-per-package', 5)), 80),
        tuple(sorted(dependencies, key=lambda row: row.code)), allocation=allocation, draft=draft, input_records=inputs,
        execution=execution, specification_record=specification, input_files=input_files,
        design_records=tuple(sorted((v.campaign_id if k == 'campaign' else v.identity.object_id, v)
            for k, v in records.items())))


def validate_instance(*, specification, allocation, draft, source_records):
    records = {}
    for _, value in source_records:
        key = {Sci02Selection: 'selection', NumericalProducingProvenance: 'provenance', CampaignSpec: 'campaign'}.get(type(value))
        if key is None or key in records: raise ValueError('SCI02 instance changes its exact source record census')
        records[key] = value
    if set(records) != {'selection', 'provenance', 'campaign'}:
        raise ValueError('SCI02 instance omits an original source')
    bind_inputs(specification, records)
    selection = records['selection']
    expected, _ = lower(selection, tuple(selection.root('DEV', i) for i in range(8)), records['provenance'], records['campaign'],
        draft_id='draft.' + specification.specification_id)
    if allocation != allocation_for(selection) or draft != expected:
        raise ValueError('SCI02 instance substitutes its code-derived complete DEV8 graph')
