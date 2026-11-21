# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound original operands for the six-question response assessment."""

from dataclasses import dataclass
from hashlib import sha256
import io
from typing import ClassVar

from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.inquiry.scientific_contributions import ContributionManifest
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_stable_id
from empirical_lawhood.science.inquiry.recursive_requirements import AssessmentDisposition
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import MODELS, POSITIONS, EnvironmentalPreparationResponseDesign, PreparationResponseDesign, PreparationResponseFrame, is_environmental, primary_response_frame, require_response_design, response_effects, response_stages
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_read import PreparationResponsePointReadout
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_selection import PreparationResponseCenter, PreparationResponsePoint, read_response_center

ACTION_SCHEMA = 'empirical-lawhood/rubisco-response/preparation-response-action-arrays'
ACTION_MAGIC = b'ELRSPA1\n'


@dataclass(frozen=True, slots=True)
class PreparationResponseAnalysis(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-analysis'
    analysis_id: str
    design: PreparationResponseDesign | EnvironmentalPreparationResponseDesign
    prefixes: tuple[ActivePreparationPrefixReadout, ...]
    centers: tuple[PreparationResponseCenter, ...]
    frames: tuple[PreparationResponseFrame, ...]
    points: tuple[PreparationResponsePoint, ...]
    readouts: tuple[PreparationResponsePointReadout, ...]
    parents: tuple[ContributionManifest, ...]

    def __post_init__(self):
        validate_stable_id(self.analysis_id)
        require_response_design(self.design)
        if (type(self.prefixes) is not tuple or len(self.prefixes) != 2
                or tuple(r.original_result.model_name for r in self.prefixes) != MODELS):
            raise ValueError('response analysis requires the two original preparation readouts')
        for prefix in self.prefixes:
            exact(prefix, ActivePreparationPrefixReadout)
            if prefix.original_result.prefix != self.design.prefix:
                raise ValueError('response analysis changes its paired preparation purchase')
        available = all(r.assessment is not None and all(p.disposition == 'AVAILABLE'
            for p in r.assessment.positions) for r in self.prefixes)
        if type(self.centers) is not tuple or type(self.frames) is not tuple:
            raise ValueError('response analysis requires an exact immutable checkpoint census')
        if not available:
            if self.centers or self.frames or self.points or self.readouts:
                raise ValueError('unavailable paired preparation cannot select a favorable response subset')
        elif (tuple((r.model_name, r.position) for r in self.centers) != POSITIONS
                or tuple(r.model_name for r in self.frames) != MODELS):
            raise ValueError('response analysis loses one of its four nested positions')
        for center in self.centers:
            exact(center, PreparationResponseCenter)
            if (center.design != self.design.identity
                    or center.original_readout != self.prefixes[MODELS.index(center.model_name)]):
                raise ValueError('response analysis substitutes an original accepted center')
        for frame in self.frames:
            exact(frame, PreparationResponseFrame)
            center = next(c for c in self.centers if (c.model_name, c.position) == (frame.model_name, 'initial'))
            if (frame.design != self.design.identity or frame.initial_checkpoint != center.checkpoint.identity
                    or frame.coordinate != dict(self.design.formation_coordinates)[frame.model_name]):
                raise ValueError('response analysis changes its fixed initial chemical frame')
        effects = {e.effect_id: e for stage in response_stages(self.design)
            for e in response_effects(self.design, stage)}
        if (type(self.points) is not tuple or tuple(p.effect.effect_id for p in self.points)
                != tuple(sorted({p.effect.effect_id for p in self.points}))):
            raise ValueError('response analysis repeats or reorders original effects')
        for point in self.points:
            exact(point, PreparationResponsePoint)
            if point.effect != effects.get(point.effect.effect_id):
                raise ValueError('response analysis changes the original finite effect census')
            center = next(c for c in self.centers if (c.model_name, c.position)
                == (point.effect.model_name, point.effect.position))
            frame = next(f for f in self.frames if f.model_name == point.effect.model_name)
            if is_environmental(self.design) and point.effect.stage == 'initial-primary':
                frame = primary_response_frame(frame)
            if (point.center, point.frame) != (center.identity, frame.identity):
                raise ValueError('response analysis changes a selected center or direction')
        for stage in {p.effect.stage for p in self.points}:
            if {p.effect for p in self.points if p.effect.stage == stage} != set(response_effects(self.design, stage)):
                raise ValueError('response analysis drops assigned unentered or failed effects')
        points = {p.effect.effect_id: p for p in self.points}
        if (type(self.readouts) is not tuple or tuple(r.point.effect.effect_id for r in self.readouts)
                != tuple(sorted({r.point.effect.effect_id for r in self.readouts}))):
            raise ValueError('response analysis repeats or reorders original point readouts')
        for readout in self.readouts:
            exact(readout, PreparationResponsePointReadout)
            if readout.point != points.get(readout.point.effect.effect_id):
                raise ValueError('response analysis substitutes an original selected point readout')
        if (type(self.parents) is not tuple or not self.parents or len(self.parents) > (5 if is_environmental(self.design) else 4)
                or tuple(p.contribution_id for p in self.parents) != tuple(sorted({p.contribution_id for p in self.parents}))):
            raise ValueError('response analysis requires its complete ordered contribution parents')
        for parent in self.parents:
            exact(parent, ContributionManifest)
        for record in (*self.prefixes, *self.readouts):
            self.product(record)

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.analysis_id, self)

    def product(self, record):
        rows = [(parent, product) for parent in self.parents for product in parent.products if product.record == record.identity]
        if len(rows) != 1 or rows[0][1].artifact.sha256 != record.fingerprint():
            raise ValueError('response analysis lacks the unique original receipt-backed operand')
        if rows[0][1].artifact.size_bytes != record.canonical_size_bytes():
            raise ValueError('response analysis changes complete original operand bytes')
        return rows[0]


def available_capture(readout):
    """Keep failed, incomplete and numerically rejected operands unavailable."""
    exact(readout, PreparationResponsePointReadout)
    result = readout.original.original_result
    if (readout.numerical_findings or result.completion.operational_status is not OperationalStatus.SUCCEEDED
            or readout.original.geometry_quality.disposition != 'SCREEN_PASSED'
            or result.returned.error is not None or readout.original.numerical_integrity is None
            or readout.original.numerical_integrity.disposition is not AssessmentDisposition.SATISFIED):
        return None
    returned = result.returned.returned
    if returned is None or returned.energy is None or returned.gradient is None:
        raise ValueError('successful response readout lacks complete original native operands')
    return returned


def binary_operands(analysis):
    """Return exact port, source identity, media type and retained byte count."""
    from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.raw_coupled_return import RAW_SCHEMA
    rows = []
    for center in analysis.centers:
        rows.append(('center.' + center.model_name + '.' + center.position, center.center_bytes,
            'application/octet-stream', center.arrays.size_bytes))
    for readout in analysis.readouts:
        returned = available_capture(readout)
        if returned is None:
            continue
        for name in ('energy', 'gradient'):
            capture = getattr(returned, name)
            manifest = capture.artifact_manifest
            pin = ObjectIdentity(manifest.logical.logical_artifact_id, RAW_SCHEMA, '1.0.0', manifest.logical.content_sha256)
            rows.append(('native-array.' + readout.point.effect.effect_id + '.' + name, pin,
                'application/gzip', manifest.materialization.size_bytes))
    return tuple(sorted(rows))


def assess_analysis(analysis, binary, *, assessor_source, assessment_id):
    """Use the original complete raw-array reader and the pure scientific assessor."""
    import numpy as np
    from empirical_lawhood.domains.rubisco.rubisco_insilico_free_energy.derivative_controls import _raw_operand
    from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_assessment import assess_response_operands, assess_unavailable_preparation
    exact(analysis, PreparationResponseAnalysis)
    expected = binary_operands(analysis)
    if set(binary) != {row[0] for row in expected}:
        raise ValueError('response assessment changes its complete original binary operand census')
    for name, pin, _, size in expected:
        raw = binary[name]
        if type(raw) is not bytes or len(raw) != size or sha256(raw).hexdigest() != pin.object_fingerprint:
            raise ValueError('response assessment substitutes original binary operand bytes')
    if not analysis.centers:
        return assess_unavailable_preparation(design=analysis.design, readouts=analysis.prefixes,
            assessor_source=assessor_source, assessment_id=assessment_id), ()
    centers = {(c.model_name, c.position): c for c in analysis.centers}
    frames = {f.model_name: f for f in analysis.frames}
    raw_centers = {(c.model_name, c.position): binary['center.' + c.model_name + '.' + c.position]
        for c in analysis.centers}
    for frame in analysis.frames:
        xyz, _ = read_response_center(centers[frame.model_name, 'initial'], raw_centers[frame.model_name, 'initial'])
        member, = frame.primary.coordinates.members
        if (member.shape != xyz.shape or member.sha256 != sha256(xyz.tobytes()).hexdigest()
                or frame.primary.coordinates.scientific_references != (frame.initial_checkpoint,)):
            raise ValueError('response assessment substitutes its fixed initial coordinate frame')
    values = {}
    for readout in analysis.readouts:
        returned = available_capture(readout)
        key = readout.point.effect.effect_id
        if returned is None:
            continue
        operands = []
        for name in ('energy', 'gradient'):
            capture = getattr(returned, name)
            raw = binary['native-array.' + key + '.' + name]
            def reader(manifest, *, capture=capture, raw=raw):
                if manifest != capture.artifact_manifest:
                    raise ValueError('response assessment substitutes original native array custody')
                return io.BytesIO(raw)
            operands.append(_raw_operand(capture, reader))
        energy, gradient = operands
        if energy.shape != () or not np.isfinite(energy) or gradient.dtype.str != '<f8' or not np.isfinite(gradient).all():
            raise ValueError('response assessment changes finite complete native energy or gradient')
        values[key] = (float(energy), gradient)
    return assess_response_operands(design=analysis.design, centers=centers, frames=frames, center_bytes=raw_centers,
        selected_points={p.effect.effect_id: p for p in analysis.points},
        readouts={r.point.effect.effect_id: r for r in analysis.readouts}, values=values,
        assessor_source=assessor_source, assessment_id=assessment_id)


def action_bytes(arrays):
    """Keep complete action arrays in the assessment's declared manifest order."""
    return ACTION_MAGIC + b''.join(array.tobytes(order='C') for _, array in arrays)


def read_action_bytes(assessment, raw):
    import numpy as np
    if type(raw) is not bytes or not raw.startswith(ACTION_MAGIC):
        raise ValueError('response action file changes its exact encoding')
    offset, arrays = len(ACTION_MAGIC), []
    for action in assessment.actions:
        if action.action is None:
            continue
        member, = action.action.members
        block = raw[offset:offset + member.size_bytes]
        if len(block) != member.size_bytes or sha256(block).hexdigest() != member.sha256:
            raise ValueError('response action file changes an original complete action')
        array = np.frombuffer(block, dtype=member.dtype).reshape(member.shape)
        if not np.isfinite(array).all():
            raise ValueError('response action file contains a nonfinite value')
        arrays.append((action.action, array))
        offset += member.size_bytes
    if offset != len(raw):
        raise ValueError('response action file appends unselected arrays or bytes')
    return tuple(arrays)
