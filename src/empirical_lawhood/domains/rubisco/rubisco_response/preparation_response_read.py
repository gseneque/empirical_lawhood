# SPDX-License-Identifier: MPL-2.0
"""Independent complete-byte reading of original checkpoint-bound response points."""

from dataclasses import dataclass
from hashlib import sha256
import io
import json
from pathlib import PurePosixPath
from typing import ClassVar

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import periodic_geometry_policy
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_read import _values
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_operation import PeriodicProbeResult
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_read import PeriodicProbeReadout, read_original_periodic_return
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_selection import validate_periodic_probe_model
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_operation import capability_for, definition_for, node_id, selected_request
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import is_environmental, primary_response_frame
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import PreparationResponsePoint, response_point_coordinates


@dataclass(frozen=True, slots=True)
class PreparationResponsePointReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-point-readout'
    readout_id: str
    configuration: ObjectIdentity
    point: PreparationResponsePoint
    original: PeriodicProbeReadout
    numerical_findings: tuple[str, ...]
    native_force_uncertainty: str = 'UNAVAILABLE'
    scope: str = 'LOCAL_COMPLETE_FORCE_WITHOUT_ERROR_ENCLOSURE_POPULATION_OR_KINETIC_ADMISSION'

    def __post_init__(self):
        validate_stable_id(self.readout_id)
        exact(self.configuration, ObjectIdentity)
        exact(self.point, PreparationResponsePoint)
        exact(self.original, PeriodicProbeReadout)
        if (self.original.selection != self.point.identity
                or self.original.geometry_quality.coordinate_sha256 not in (None, self.point.coordinate_sha256)
                or type(self.numerical_findings) is not tuple
                or self.numerical_findings != tuple(sorted(set(self.numerical_findings)))
                or self.native_force_uncertainty != 'UNAVAILABLE'
                or self.scope != 'LOCAL_COMPLETE_FORCE_WITHOUT_ERROR_ENCLOSURE_POPULATION_OR_KINETIC_ADMISSION'):
            raise ValueError('response readout changes its actual original point or uncertainty')
        for finding in self.numerical_findings:
            validate_stable_id(finding)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.readout_id, self)


def read_response_point(*, config, representation, center_bytes, original_result, native_subwork,
                        assessor_source, readout_id):
    import numpy as np
    capability_for(config)
    exact(original_result, PeriodicProbeResult)
    prototype = config.original.selection
    validate_periodic_probe_model(prototype, representation)
    xyz = response_point_coordinates(design=config.protocol, center=config.center, frame=config.frame,
        effect=config.point.effect, prototype=prototype, center_bytes=center_bytes)
    definition = original_result.definition
    if (definition != definition_for(config, parent=definition.parent_contact,
            materialization_ids=definition.input_materialization_ids)
            or original_result.request != selected_request(config)
            or original_result.returned.selection != config.point.identity
            or sha256(xyz.tobytes()).hexdigest() != config.point.coordinate_sha256):
        raise ValueError('response read substitutes its original selected native effect')
    fingerprints = {'response-design.json': config.protocol.fingerprint(), 'response-point.json': config.point.fingerprint(),
        'response-center.json': config.center.fingerprint(), 'response-frame.json': config.frame.fingerprint(),
        'selection.json': prototype.path.fingerprint(), 'electronic-settings.json': prototype.electronic.fingerprint(),
        'cell.json': prototype.cell.fingerprint(), 'mm-settings.json': prototype.molecular.fingerprint(),
        'original.prmtop': prototype.cell.raw_topology.object_fingerprint,
        'original.inpcrd': prototype.cell.raw_coordinates.object_fingerprint}
    files = {PurePosixPath(row.relative_path).name: row.sha256 for row in original_result.returned.files.files}
    success = original_result.returned.error is None
    if success and any(files.get(name) != digest for name, digest in fingerprints.items()):
        raise ValueError('response read substitutes actual numerical input files')
    # Authenticate any retained selected inputs on failed attempts too.
    if any(name in files and files[name] != digest for name, digest in fingerprints.items()):
        raise ValueError('failed response substitutes a retained original input')
    validators, findings = {}, set()
    if success or 'coordinate-array.npy' in files:
        def coordinates(raw):
            stream = io.BytesIO(raw)
            values = np.load(stream, allow_pickle=False)
            if (stream.read(1) or values.dtype.str != '<f8' or values.shape != xyz.shape
                    or not np.array_equal(values, xyz)):
                raise ValueError('response return changes its selected full coordinate array')
        validators['coordinate-array.npy'] = (xyz.nbytes + 4096, coordinates)
    if success or 'native-observations.jsonl' in files:
        def native_log(raw):
            rows = [json.loads(line) for line in raw.splitlines()]
            if config.ACCELERATED:
                from empirical_lawhood.domains.rubisco.rubisco_response.periodic_backend_evidence import assess_gpu_log
                assess_gpu_log(raw, engine=prototype.engine, expected_evaluations=1, successful=success,
                    state=getattr(prototype.electronic, 'state', None))
            if not success:
                return
            for event in ('entry', 'electronic-return', 'return'):
                selected = [r for r in rows if r['event'] == event]
                if len(selected) != 1 or selected[0]['evaluation'] != 1:
                    raise ValueError('response return changes its single complete-force census')
            electronic, = [r for r in rows if r['event'] == 'electronic-return']
            if (electronic['converged'] is not True or not np.isfinite(electronic['orbital_gradient_norm'])
                    or electronic['orbital_gradient_norm'] >= float(prototype.electronic.orbital_gradient_tolerance)):
                findings.add('electronic-solution-not-converged')
        validators['native-observations.jsonl'] = (64 * 2**20, native_log)
    from empirical_lawhood.domains.rubisco.rubisco_response.molecular_quality_read import RetainedGeometryReader
    geometry_reader = RetainedGeometryReader(representation=representation, policy=periodic_geometry_policy(prototype.molecular),
        cell=prototype.cell, qm_atoms=prototype.path.qm_atom_indices,
        expected_coordinate_sha256=config.point.coordinate_sha256)
    report = read_original_periodic_return(original_result=original_result, native_subwork=native_subwork,
        assessor_source=assessor_source, readout_id=readout_id + '.raw', member_validators=validators, geometry_reader=geometry_reader)
    findings.update(report.geometry_quality.findings)
    return PreparationResponsePointReadout(readout_id, config.identity, config.point, report, tuple(sorted(findings)))


def response_values(readout, native_subwork):
    """Reauthenticate raw energy and gradient used in a comparison; retain absence."""
    if readout is None:
        return None
    exact(readout, PreparationResponsePointReadout)
    if readout.numerical_findings:
        return None
    return _values(readout.original, native_subwork, include_gradient=True)


def read_preparation_response(*, stages, representations, centers, frames, center_bytes, original_results,
                              native_subwork_for_result, assessor_source, assessment_id):
    """Reopen every original return and assess the complete selected stage census.

    Missing results remain missing. This method performs no provider or native
    operation and does not interpret progress exports as scientific evidence.
    """
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import assess_response_operands
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_translation import validate_configs
    if type(stages) is not tuple or not stages:
        raise ValueError('response read requires the originally selected stage configurations')
    points, readouts, values, configs = {}, {}, {}, {}
    design = None
    seen_stages = set()
    for stage in stages:
        base = validate_configs(stage)
        name = base.point.effect.stage
        if name in seen_stages or design is not None and base.protocol != design:
            raise ValueError('response read substitutes or repeats an original stage')
        seen_stages.add(name)
        design = base.protocol
        for config in stage:
            key = config.point.effect.effect_id
            configs[key], points[key] = config, config.point
    if set(original_results) - set(configs):
        raise ValueError('response read includes an unselected native effect')
    for key, result in original_results.items():
        config = configs[key]
        selected_center = centers[config.center.model_name, config.center.position]
        frame = frames[config.center.model_name]
        if is_environmental(design) and config.point.effect.stage == 'initial-primary':
            frame = primary_response_frame(frame)
        if selected_center != config.center or frame != config.frame:
            raise ValueError('response read changes an original checkpoint or fixed frame')
        custody = native_subwork_for_result(result)
        report = read_response_point(config=config, representation=representations[config.center.model_name],
            center_bytes=center_bytes[config.center.model_name, config.center.position], original_result=result,
            native_subwork=custody, assessor_source=(ObjectIdentity.from_record('source.response-assessor.' +
                config.original.implementation.code_sources_sha256, config.original.implementation)
                if is_environmental(design) else assessor_source),
            readout_id=node_id(config) + '.assessment' if is_environmental(design) else assessment_id + '.point.' + key)
        readouts[key] = report
        values[key] = response_values(report, custody)
    report, arrays = assess_response_operands(design=design, centers=centers, frames=frames, center_bytes=center_bytes,
        selected_points=points, readouts=readouts, values=values, assessor_source=assessor_source, assessment_id=assessment_id)
    return report, arrays, tuple(readouts[key] for key in sorted(readouts))
