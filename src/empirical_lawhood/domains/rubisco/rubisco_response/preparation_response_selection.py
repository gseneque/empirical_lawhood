# SPDX-License-Identifier: MPL-2.0
"""Original checkpoint operands and prospectively frozen molecular response points."""

from dataclasses import dataclass, replace
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar

from empirical_lawhood.science.models.datasets import ArrayDatasetManifest
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord, validate_decimal, validate_sha256, validate_stable_id
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_checkpoint import ActivePreparationCheckpoint, read_checkpoint_arrays
from empirical_lawhood.domains.rubisco.rubisco_response.active_preparation_read import ActivePreparationPrefixReadout
from empirical_lawhood.domains.rubisco.rubisco_response.materials import exact
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_control_selection import BOHR_ANGSTROM
from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_action_read import direction_values
from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import PreparationResponseEffect, PreparationResponseFrame, is_environmental, require_response_design, response_effects

CENTER_SCHEMA = 'empirical-lawhood/rubisco-response/preparation-response-center-f64'
MAX_CENTER_BYTES = 64 * 2**20
CENTER_NAMES = ('coordinates-angstrom', 'gradient-hartree-per-bohr')


@dataclass(frozen=True, slots=True)
class PreparationResponseCenter(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-center'
    center_id: str
    design: ObjectIdentity
    model_name: str
    position: str
    original_readout: ActivePreparationPrefixReadout
    checkpoint: ActivePreparationCheckpoint
    arrays: ArrayDatasetManifest
    center_bytes: ObjectIdentity

    def __post_init__(self):
        validate_stable_id(self.center_id)
        for pin in (self.design, self.center_bytes):
            exact(pin, ObjectIdentity)
        exact(self.original_readout, ActivePreparationPrefixReadout)
        exact(self.checkpoint, ActivePreparationCheckpoint)
        exact(self.arrays, ArrayDatasetManifest)
        assessment = self.original_readout.assessment
        positions = {} if assessment is None else {r.position: r for r in assessment.positions}
        selected = positions.get(self.position)
        if (self.model_name != self.original_readout.original_result.model_name or selected is None
                or selected.disposition != 'AVAILABLE' or selected.checkpoint != self.checkpoint.identity
                or not any(r.checkpoint == self.checkpoint for r in assessment.checkpoints)
                or tuple(m.name for m in self.arrays.members) != CENTER_NAMES
                or self.arrays.scientific_references != (self.checkpoint.identity,)
                or self.center_bytes.object_schema != CENTER_SCHEMA or self.center_bytes.object_version != '1.0.0'
                or self.arrays.size_bytes > MAX_CENTER_BYTES):
            raise ValueError('response center loses its independently accepted original state')
        original = {m.name: m for m in self.checkpoint.arrays.members}
        if any(m != original.get(m.name) for m in self.arrays.members):
            raise ValueError('response center substitutes complete original checkpoint arrays')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.center_id, self)


def prepare_response_center(*, design, readout, position, checkpoint, checkpoint_arrays):
    require_response_design(design)
    exact(readout, ActivePreparationPrefixReadout)
    if readout.original_result.prefix != design.prefix:
        raise ValueError('response center changes the selected paired preparation')
    read_checkpoint_arrays(checkpoint, checkpoint_arrays, configuration=readout.original_result.configuration,
        seed=checkpoint.seed, prototype=checkpoint.prototype)
    arrays = ArrayDatasetManifest('arrays.response-center.' + checkpoint.fingerprint(),
        tuple(m for m in checkpoint.arrays.members if m.name in CENTER_NAMES), (checkpoint.identity,))
    raw = b''.join(checkpoint_arrays[m.name].tobytes(order='C') for m in arrays.members)
    digest = sha256(raw).hexdigest()
    provisional = PreparationResponseCenter('center.preparation-response.pending', design.identity,
        readout.original_result.model_name, position, readout, checkpoint, arrays,
        ObjectIdentity('bytes.response-center.' + digest, CENTER_SCHEMA, '1.0.0', digest))
    result = replace(provisional, center_id='center.preparation-response.' + provisional.fingerprint())
    read_response_center(result, raw)
    return result, raw


def read_response_center(center, raw):
    """Decode only complete finite original arrays; no source or native side effects."""
    import numpy as np
    exact(center, PreparationResponseCenter)
    if (type(raw) is not bytes or len(raw) != center.arrays.size_bytes
            or sha256(raw).hexdigest() != center.center_bytes.object_fingerprint):
        raise ValueError('response center changes original complete raw bytes')
    arrays, offset = [], 0
    for member in center.arrays.members:
        block = raw[offset:offset + member.size_bytes]
        if sha256(block).hexdigest() != member.sha256:
            raise ValueError('response center changes an original named array')
        value = np.frombuffer(block, dtype=member.dtype).reshape(member.shape)
        if not np.isfinite(value).all():
            raise ValueError('response center contains nonfinite coordinates or forces')
        arrays.append(value.copy())
        offset += member.size_bytes
    return tuple(arrays)


@dataclass(frozen=True, slots=True)
class PreparationResponsePrediction(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-prediction'
    prediction_id: str
    design: ObjectIdentity
    diagnostic_assessment: ObjectIdentity
    center: ObjectIdentity
    frame: ObjectIdentity
    primary_action: ArrayDatasetManifest
    base_receiver_hartree_per_bohr: Decimal
    predicted_change_hartree_per_bohr: Decimal
    scalar_change_hartree_per_bohr: Decimal
    omitted_change_hartree_per_bohr: Decimal
    scale_change_hartree_per_bohr: Decimal
    native_force_uncertainty: str = 'UNAVAILABLE'

    def __post_init__(self):
        validate_stable_id(self.prediction_id)
        for pin in (self.design, self.diagnostic_assessment, self.center, self.frame):
            exact(pin, ObjectIdentity)
        exact(self.primary_action, ArrayDatasetManifest)
        for value in (self.base_receiver_hartree_per_bohr, self.predicted_change_hartree_per_bohr,
                      self.scalar_change_hartree_per_bohr, self.omitted_change_hartree_per_bohr,
                      self.scale_change_hartree_per_bohr):
            validate_decimal(value, field_name='frozen_response_prediction')
        if self.scale_change_hartree_per_bohr < 0 or self.native_force_uncertainty != 'UNAVAILABLE':
            raise ValueError('response prediction invents a native uncertainty bound')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.prediction_id, self)


@dataclass(frozen=True, slots=True)
class PreparationResponsePoint(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/rubisco-response/preparation-response-point'
    point_id: str
    effect: PreparationResponseEffect
    center: ObjectIdentity
    frame: ObjectIdentity
    coordinate_sha256: str
    prediction: PreparationResponsePrediction | None

    def __post_init__(self):
        validate_stable_id(self.point_id)
        exact(self.effect, PreparationResponseEffect)
        for pin in (self.center, self.frame):
            exact(pin, ObjectIdentity)
        validate_sha256(self.coordinate_sha256)
        if (self.effect.stage == 'challenge') != (self.prediction is not None):
            raise ValueError('finite response requires its frozen pre-reveal prediction')
        if self.prediction is not None:
            exact(self.prediction, PreparationResponsePrediction)
            if (self.prediction.design, self.prediction.center, self.prediction.frame) != (
                    self.effect.design, self.center, self.frame):
                raise ValueError('finite response substitutes its original frozen prediction')

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.point_id, self)


def validate_response_operands(design, center, frame, effect, prototype):
    require_response_design(design)
    exact(center, PreparationResponseCenter)
    exact(frame, PreparationResponseFrame)
    exact(effect, PreparationResponseEffect)
    if (effect not in response_effects(design, effect.stage)
            or (center.design, frame.design, effect.design) != (design.identity,) * 3
            or center.original_readout.original_result.prefix != design.prefix
            or (center.model_name, center.position) != (effect.model_name, effect.position)
            or frame.model_name != center.model_name
            or frame.coordinate != dict(design.formation_coordinates)[center.model_name]
            or frame.initial_checkpoint != center.original_readout.assessment.positions[0].checkpoint
            or center.checkpoint.prototype != prototype.identity
            or frame.primary.representation != prototype.representation
            or frame.primary.physical_atom_count != prototype.physical_atom_count):
        raise ValueError('response operands change the actual fixed chemical frame or original operator')
    if is_environmental(design):
        if prototype.cell.lengths_angstrom != design.environment.cell_lengths_angstrom:
            raise ValueError('environmental response changes its original common Cartesian cell')
        if effect.stage == 'initial-primary':
            if frame.additional is not None or frame.challenge is not None:
                raise ValueError('initial-primary response requires its immutable pre-nomination frame')
        elif frame.additional is None or frame.challenge is None:
            raise ValueError('environmental response lacks its frozen original nomination')
        else:
            index_column = 4 + ('m1-i95m', 'm1-wt').index(frame.model_name)
            support = {row[index_column] for row in design.environment.atom_pairs}
            if any(atom not in support for atom, _, _ in frame.challenge.components):
                raise ValueError('environmental response escapes its prospective protein support')


def response_point_coordinates(*, design, center, frame, effect, prototype, center_bytes):
    import numpy as np
    validate_response_operands(design, center, frame, effect, prototype)
    xyz, _ = read_response_center(center, center_bytes)
    if is_environmental(design) and effect.stage == 'initial-primary':
        from empirical_lawhood.domains.rubisco.rubisco_response.preparation_response_design import validate_environmental_primary_frame
        validate_environmental_primary_frame(design=design, frame=frame, coordinates=xyz)
    direction = getattr(frame, effect.direction)
    if direction is None:
        raise ValueError('response point precedes its required frozen direction nomination')
    delta = float(effect.signed_step_bohr * BOHR_ANGSTROM) * direction_values(direction, len(xyz))
    with np.errstate(over='raise', invalid='raise'):
        displaced = np.asarray(xyz + delta, dtype='<f8', order='C')
    if not np.isfinite(displaced).all() or np.array_equal(displaced, xyz):
        raise ValueError('response displacement is nonfinite or lost in native coordinates')
    if is_environmental(design) and effect.direction != 'primary':
        receiver = list(frame.coordinate.native_atom_indices)
        if not np.array_equal(displaced[receiver], xyz[receiver]):
            raise ValueError('pure environmental challenge changes a local receiver atom')
    return displaced


def prepare_response_point(*, design, center, frame, effect, prototype, center_bytes, prediction=None):
    xyz = response_point_coordinates(design=design, center=center, frame=frame, effect=effect,
        prototype=prototype, center_bytes=center_bytes)
    provisional = PreparationResponsePoint('point.preparation-response.pending', effect, center.identity,
        frame.identity, sha256(xyz.tobytes()).hexdigest(), prediction)
    return replace(provisional, point_id='point.preparation-response.' + provisional.fingerprint())
