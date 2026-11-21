# SPDX-License-Identifier: MPL-2.0
"""Three SCI02-C tranches through the supported generic experiment compiler."""
from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.experiments.experimental_design import IndependentUnit, UnitAllocation, UnitRoleAssignment
from empirical_lawhood.science.identity.numerical_provenance import NumericalProducingProvenance
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.design.campaigns import CampaignSpec
from empirical_lawhood.execution.experiment_preparation import DependencyKind, ExperimentCensus, ExperimentDependency, ExperimentPreparation, PreparedExperimentFile, PreparedExperimentInputs

from empirical_lawhood.domains.matrix.matrix_experimental_programme import sci02c_bindings as binding
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02_records import Sci02Selection
from empirical_lawhood.domains.matrix.matrix_experimental_programme.sci02c_records import PROTOCOL_ID as PROTOCOL_ID, Sci02CDesign, Sci02CRetainedCase, Sci02CProduct


@dataclass(frozen=True, slots=True)
class Sci02CSpecification(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-sci02c/specification'
    specification_id: str
    study: ObjectIdentity
    selection: ObjectIdentity
    provenance: ObjectIdentity
    campaign: ObjectIdentity
    tranche: str
    cases: tuple[ObjectIdentity, ...] = ()
    frozen: ObjectIdentity | None = None
    calibrated: ObjectIdentity | None = None

    def __post_init__(self):
        validate_stable_id(self.specification_id)
        if (self.tranche not in ('TRAINING', 'CALIBRATION', 'CONFIRMATION')
                or len(self.cases) != (8 if self.tranche == 'TRAINING' else 0)
                or (self.frozen is None) != (self.tranche == 'TRAINING')
                or (self.calibrated is not None) != (self.tranche == 'CONFIRMATION')):
            raise ValueError('SCI02-C specification changes its complete frozen tranche inputs')
        pairs = ((self.study, Sci02CDesign), (self.selection, Sci02Selection), (self.provenance, NumericalProducingProvenance),
            (self.campaign, CampaignSpec), *((p, Sci02CRetainedCase) for p in self.cases),
            *((p, Sci02CProduct) for p in (self.frozen, self.calibrated) if p is not None))
        for value, kind in pairs:
            if type(value) is not ObjectIdentity or (value.object_schema, value.object_version) != (kind.SCHEMA, kind.VERSION):
                raise ValueError('SCI02-C specification substitutes an exact original input')
            value.__post_init__()

    @property
    def identity(self): return ObjectIdentity.from_record(self.specification_id, self)


def input_record_types(): return Sci02CDesign, Sci02Selection, Sci02CRetainedCase, Sci02CProduct, NumericalProducingProvenance, CampaignSpec


def roots_for(selection, tranche):
    return tuple(selection.root('HOLDOUT' if tranche == 'CONFIRMATION' else 'DEV', i)
        for i in (range(8) if tranche == 'TRAINING' else range(8, 16) if tranche == 'CALIBRATION' else range(32)))


def allocation_for(selection, tranche):
    roots = roots_for(selection, tranche)
    views = tuple(sorted((selection.design.coordinate.primary_view.view_id, selection.design.coordinate.fine_view.view_id)))
    return UnitAllocation('allocation.sci02c.' + tranche.lower() + '.' + selection.fingerprint(), (selection.identity,),
        tuple(IndependentUnit(r.group_id, selection.record_id, selection.design.coordinate.family_id, views, tranche == 'TRAINING') for r in roots),
        tuple(UnitRoleAssignment(r.group_id, tranche.lower()) for r in roots))


def expected_records(specification):
    return {'study': (Sci02CDesign, specification.study), 'selection': (Sci02Selection, specification.selection),
        'provenance': (NumericalProducingProvenance, specification.provenance), 'campaign': (CampaignSpec, specification.campaign),
        **{f'root{i:02d}': (Sci02CRetainedCase, p) for i, p in enumerate(specification.cases)},
        **({} if specification.frozen is None else {'frozen': (Sci02CProduct, specification.frozen)}),
        **({} if specification.calibrated is None else {'calibrated': (Sci02CProduct, specification.calibrated)})}


def expected_files(specification):
    return tuple(f'root{i:02d}-arrays' for i in range(8)) if specification.tranche == 'TRAINING' else ('templates',)


def bind_inputs(specification, records, *, files=None):
    expected = expected_records(specification)
    if set(records) - set(expected) or set(files or {}) - set(expected_files(specification)):
        raise ValueError('SCI02-C binding adds an unselected scientific operand')
    for key, value in records.items():
        kind, pin = expected[key]
        if type(value) is not kind or ObjectIdentity.from_record(pin.object_id, value) != pin:
            raise ValueError('SCI02-C binding substitutes ' + key)
        value.__post_init__()
    selection, study = records.get('selection'), records.get('study')
    if study is not None and selection is not None and (study.original_selection != selection.identity or study.physical != selection.design):
        raise ValueError('SCI02-C binding changes original physics or reservation')
    for i in range(8):
        case, file = records.get(f'root{i:02d}'), (files or {}).get(f'root{i:02d}-arrays')
        if case is not None and selection is not None and (case.root != selection.root('DEV', i) or case.design != selection.design):
            raise ValueError('SCI02-C training changes its original exposed root')
        if file is not None and (case is None or file.identity != case.arrays.array_artifact):
            raise ValueError('SCI02-C training changes its original retained arrays')
    template = (files or {}).get('templates')
    if template is not None and (selection is None or template.identity != selection.design.assay.template_artifact):
        raise ValueError('SCI02-C binding changes the original source64 instrument')
    fitted, calibrated = records.get('frozen'), records.get('calibrated')
    if fitted is not None and (fitted.config.phase != 'fit' or fitted.frozen_description is None
            or fitted.disposition != 'AVAILABLE' or study is not None and fitted.config.study != study):
        raise ValueError('SCI02-C continuation lacks its complete original frozen description')
    if calibrated is not None and (calibrated.config.phase != 'calibrate' or calibrated.calibration_result is None
            or study is not None and calibrated.config.study != study
            or fitted is not None and calibrated.calibration_result.model != fitted.frozen_description.identity):
        raise ValueError('SCI02-C confirmation lacks its exact rank-eight calibration')
    return PreparedExperimentInputs({} if selection is None else {'selection': allocation_for(selection, specification.tranche)}, (records, files or {}))


def lower(specification, records):
    return binding.lower(records['study'], records['selection'], roots_for(records['selection'], specification.tranche),
        records['provenance'], records['campaign'], draft_id='draft.' + specification.specification_id,
        cases=tuple(records[f'root{i:02d}'] for i in range(8)) if specification.tranche == 'TRAINING' else (),
        model=None if specification.frozen is None else records['frozen'].frozen_description,
        calibration=None if specification.calibrated is None else records['calibrated'].calibration_result)


def prepare(specification, *, scientific_inputs, execution, method_inputs=None, protocol_bytes=None):
    specification.__post_init__(); execution.__post_init__()
    records, files = ({}, {}) if method_inputs is None else method_inputs
    dependencies = []
    for key in expected_records(specification):
        if key not in records:
            dependencies.append(ExperimentDependency('sci02c.input.' + key, DependencyKind.EXTERNAL_INPUT, 'Supply exact SCI02-C ' + key + '.', key))
    for key in expected_files(specification):
        if key not in files:
            dependencies.append(ExperimentDependency('sci02c.input.' + key, DependencyKind.EXTERNAL_INPUT, 'Supply original authenticated array input.', key))
    for key in ('environment_id', 'source_snapshot', 'output_root', 'workers'):
        if getattr(execution, key) is None:
            dependencies.append(ExperimentDependency('sci02c.execution.' + key, DependencyKind.ENVIRONMENT, 'Select explicit ' + key + '.'))
    if protocol_bytes is not None: raise ValueError('SCI02-C protocol belongs to the exact frozen scientific design')
    allocation, draft, inputs, input_files = None, None, (), ()
    if not dependencies:
        bind_inputs(specification, records, files=files)
        allocation = allocation_for(records['selection'], specification.tranche)
        if scientific_inputs != {'selection': allocation}: raise ValueError('SCI02-C changes original whole-root allocation')
        draft, inputs = lower(specification, records)
        input_files = tuple(sorted((('external.templates.' + f.identity.sha256 if key == 'templates' else 'external.' + f.identity.artifact_id),
            PreparedExperimentFile(f.identity, '1.0.0', f.path, f.identity.size_bytes)) for key, f in files.items()))
    count = 32 if specification.tranche == 'CONFIRMATION' else 8
    training = specification.tranche == 'TRAINING'
    return ExperimentPreparation(specification.identity,
        ExperimentCensus((('whole-roots', count),), (('whole-roots', 0 if allocation is None else count),),
            (('operations', 9 if training else 29 * count + 1),), (('assigned-response-packages', 3 * count), ('fixed-description-routes', 2)),
            0 if training else 10 * count), tuple(sorted(dependencies, key=lambda d: d.code)), allocation=allocation, draft=draft,
        input_records=inputs, execution=execution, specification_record=specification, input_files=input_files,
        design_records=tuple(sorted((p.object_id, records[k]) for k, (_, p) in expected_records(specification).items() if k in records)))


def validate_instance(*, specification, allocation, draft, source_records):
    pins = {pin: key for key, (_, pin) in expected_records(specification).items()}
    records = {}
    for object_id, value in source_records:
        key = pins.get(ObjectIdentity.from_record(object_id, value))
        if key is None or key in records: raise ValueError('SCI02-C instance changes exact original source records')
        records[key] = value
    if set(records) != set(expected_records(specification)): raise ValueError('SCI02-C instance omits an exact source record')
    bind_inputs(specification, records)
    expected, _ = lower(specification, records)
    if allocation != allocation_for(records['selection'], specification.tranche) or draft != expected:
        raise ValueError('SCI02-C instance substitutes its code-derived complete original tranche')
