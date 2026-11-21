# SPDX-License-Identifier: MPL-2.0
"""Calibrate the prospective cost rule from authenticated complete native work."""

from dataclasses import dataclass
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.pilot_allocation import PilotAllocationRule, PilotCostMeasurement, allocate_pilot
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeConfig, PeriodicRestartConfig, AcceleratedPeriodicProbeConfig, AcceleratedPeriodicRestartConfig, capability_for, is_restart, validate_force_selection
from empirical_lawhood.domains.rubisco.rubisco_response.physical_path_protocol import complete_horizon, physical_settings, read_physical_path, read_physical_phase
from empirical_lawhood.domains.rubisco.rubisco_response.retained_native_outputs import recheck_original_native_outputs, scoped_original_reference


PROBES = (PeriodicProbeConfig, PeriodicRestartConfig, AcceleratedPeriodicProbeConfig, AcceleratedPeriodicRestartConfig)


@dataclass(frozen=True, slots=True)
class PilotForceScope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/pilot-force-scope'
    representation: ObjectIdentity
    path: ObjectIdentity
    cell: ObjectIdentity
    electronic: ObjectIdentity
    molecular: ObjectIdentity
    engine: ObjectIdentity

    def __post_init__(self):
        for name in ('representation', 'path', 'cell', 'electronic', 'molecular', 'engine'):
            exact(getattr(self, name), ObjectIdentity)

    @property
    def identity(self):
        return ObjectIdentity.from_record('scope.pilot-force.'+self.fingerprint(), self)


def pilot_force_scope(config):
    """Same complete operator/environment; a density guess is not a new scope."""
    if type(config) in PROBES:
        capability_for(config)
        selected = config.selection
    else:
        physical_settings(config)
        selected = config.original.selection
    return PilotForceScope(selected.representation, selected.path.identity, selected.cell.identity,
        selected.electronic.identity, selected.molecular.identity, selected.engine.identity)


@dataclass(frozen=True, slots=True)
class RetainedPilotCalibration:
    calibration_id: str
    config: object
    representation: object
    phase_bytes: bytes | None
    original_result: object | None
    native_subwork: object


def validate_pilot_sources(selection, sources):
    exact(selection, PilotAllocationRule)
    if (type(sources) is not tuple or any(type(s) is not RetainedPilotCalibration for s in sources)
            or tuple(s.calibration_id for s in sources) != tuple(c.calibration_id for c in selection.calibrations)):
        raise ValueError('pilot reader needs every selected original calibration carrier')
    profiles = {p.class_id: p for p in selection.cost_classes}
    for case, source in zip(selection.calibrations, sources, strict=True):
        if profiles[case.cost_class].unit != 'COMPLETE_COUPLED_FORCE_RETURN':
            raise ValueError('native force calibration cannot supply a non-force cost class')
        if source.config.identity != case.configuration or pilot_force_scope(source.config).identity != profiles[case.cost_class].scope:
            raise ValueError('pilot calibration substitutes the selected configuration, operator or environment')
        if type(source.config) in PROBES:
            if source.phase_bytes is not None:
                raise ValueError('a force probe does not use a trajectory phase carrier')
            validate_force_selection(source.config.selection, source.representation,
                source.config.seed if is_restart(source.config) else None)
        else:
            read_physical_phase(source.config, source.representation, source.phase_bytes)


def read_pilot_allocation(*, selection, sources, assessor_source):
    """No native call; preserve every failed/missing source and exact cost."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import read_periodic_probe
    validate_pilot_sources(selection, sources)
    exact(assessor_source, ObjectIdentity)
    measurements, originals = [], []
    for case, source in zip(selection.calibrations, sources, strict=True):
        result = source.original_result
        if result is None:
            measurements.append(PilotCostMeasurement(case.calibration_id, case.configuration, None,
                'MISSING_ORIGINAL', InquiryCost(None, None, None), 0, None, ('ORIGINAL_NOT_SUPPLIED_NOT_PROVEN_NONENTRY',)))
            originals.append(None)
            continue
        if type(source.config) in PROBES:
            report = read_periodic_probe(config=source.config, representation=source.representation,
                original_result=result, native_subwork=source.native_subwork,
                assessor_source=assessor_source, readout_id='readout.pilot.'+source.config.fingerprint())
            integrity = report.numerical_integrity
            numerical = (integrity is not None and integrity.disposition.value == 'SATISFIED'
                and report.geometry_quality.disposition == 'SCREEN_PASSED')
            units = 1
            originals.append(report.to_document())
        else:
            report = read_physical_path(config=source.config, representation=source.representation,
                phase_bytes=source.phase_bytes, original_result=result, native_subwork=source.native_subwork,
                assessor_source=assessor_source)
            assessment = report['assessment']
            numerical = (assessment is not None and source.config.selection.criteria is not None
                and not assessment['findings'] and complete_horizon(source.config, assessment)
                and report['assessment_error'] is None and report['gpu_assessment_error'] is None)
            units = physical_settings(source.config).steps+1
            originals.append(report)
        failed = result.completion.operational_status is not OperationalStatus.SUCCEEDED
        state = 'FAILED' if failed else 'COMPLETE' if numerical else 'UNASSESSED'
        reasons = ('ORIGINAL_NATIVE_FAILURE',) if failed else () if numerical else ('COMPLETE_NUMERICAL_RETURN_UNASSESSED',)
        measurements.append(PilotCostMeasurement(case.calibration_id, case.configuration,
            scoped_original_reference(source).identity, state, result.completion.cost,
            units if state == 'COMPLETE' else 0, result.completion.peak_rss_bytes, reasons))
    report = allocate_pilot(selection, tuple(measurements))
    report['original_readouts'] = tuple(originals)
    report['calibration_unit_cost_scope'] = 'WHOLE_NATIVE_TASK_COST_PER_COMPLETE_FORCE_INCLUDING_SETUP_NOT_A_WARM_CALL_BOUND'
    # Compact exact counts are sufficient for the shared closed analysis export.
    arrays = {'pilot.completed-units': np.asarray([r.completed_units for r in measurements], dtype='<i8'),
        'pilot.numerically-complete': np.asarray([r.disposition == 'COMPLETE' for r in measurements], dtype='bool')}
    recheck_original_native_outputs(sources, description='pilot cost calibration')
    return report, arrays
