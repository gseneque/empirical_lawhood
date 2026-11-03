# SPDX-License-Identifier: MPL-2.0
"""Complete received-array response method for a separate prepared subject.

The registered tail must authenticate causal-frame/forecast publication and
native custody before using this method. This numerical owner supplies neither
those acts nor cross-preparation calibration. No RNG is created here. Every
future innovation is supplied explicitly, in the original physical-time metric.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import ClassVar

import numpy as np

from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixOriginResponseModel, model_predictors
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import (
    MatrixDenseResponseCell, MatrixDenseResponseDiagnostics, dense_response_measurements, response_error_norms,
)
from empirical_lawhood.adapters.methods.matrix_history_analysis.records import HISTORY_PURPOSES, MatrixHistorySeed
from empirical_lawhood.adapters.methods.matrix_parameter_response.paired_independent import verify_noise_pair
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_native import (
    ScheduledResponseTransitionControl, assess_scheduled_branch, native_scheduled_branch,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_records import (
    ScheduledResponseLossCell, ScheduledResponseProtocol, branch_census,
)
from empirical_lawhood.adapters.methods.matrix_scheduled_history.response_science import receiver_metric, validate_frozen_response_arrays
from empirical_lawhood.adapters.simulators.six_matrix_response.model import SixMatrixState
from empirical_lawhood.infrastructure.matrix_array_io import DecodedMatrixArrayInput, decode_matrix_arrays
from empirical_lawhood.kernel.matrix_inputs import MATRIX_ARRAY_SCHEMA, MAXIMUM_MATRIX_ARRAY_BYTES, MatrixArrayMember
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id

from .preparation_records import MatrixPreparationArrays, MatrixPreparationSource, preparation_identity
from .preparation_science import consume_preparation_arrays


STANDING = "RECEIVED_ARRAY_NUMERICAL_READOUT_NO_FORECAST_CUSTODY_OR_CROSS_PREPARATION_APPLICABILITY"


@dataclass(frozen=True, slots=True)
class MatrixPreparedResponsePanel(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-response-panel"
    panel_id: str
    independent_group_id: str
    role: str
    streams: tuple[MatrixHistorySeed, ...]
    innovation_scope: str = "SUPPLIED_FUTURE_INNOVATIONS_NO_CHECKPOINT_AUTHORITY"

    def __post_init__(self):
        validate_stable_id(self.panel_id)
        validate_stable_id(self.independent_group_id)
        if (self.role not in ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE") or type(self.streams) is not tuple
                or any(type(row) is not MatrixHistorySeed for row in self.streams)
                or tuple(row.purpose for row in self.streams) != HISTORY_PURPOSES
                or len({row.effective_seed for row in self.streams}) != 4
                or self.innovation_scope != "SUPPLIED_FUTURE_INNOVATIONS_NO_CHECKPOINT_AUTHORITY"):
            raise ValueError("prepared panel loses exact whole-group supplied future purposes or invents checkpoint authority")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.panel_id, self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedForecastArrays(CanonicalRecord):
    """Supplied immutable prediction arrays; publication ordering stays separate."""

    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-forecast-arrays"
    forecast_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    original_protocol: ObjectIdentity
    array_artifact: ArtifactIdentity
    members: tuple[MatrixArrayMember, ...]

    def __post_init__(self):
        validate_stable_id(self.forecast_id)
        if (type(self.source) is not ObjectIdentity or self.source.object_schema != MatrixPreparationSource.SCHEMA
                or type(self.preparation) is not ObjectIdentity or self.preparation.object_schema != MatrixPreparationArrays.SCHEMA
                or type(self.original_protocol) is not ObjectIdentity or self.original_protocol.object_schema != ScheduledResponseProtocol.SCHEMA
                or type(self.array_artifact) is not ArtifactIdentity or self.array_artifact.payload_schema != MATRIX_ARRAY_SCHEMA
                or self.array_artifact.media_type != "application/x-npz" or not 0 < self.array_artifact.size_bytes <= MAXIMUM_MATRIX_ARRAY_BYTES
                or type(self.members) is not tuple or any(type(row) is not MatrixArrayMember for row in self.members)
                or not 1 <= len(self.members) <= 256 or tuple(row.name for row in self.members) != tuple(sorted({row.name for row in self.members}))
                or sum(row.size_bytes for row in self.members) > MAXIMUM_MATRIX_ARRAY_BYTES):
            raise ValueError("prepared forecasts lose exact separate source/preparation/protocol or bounded supplied array census")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.forecast_id, self)


@dataclass(frozen=True, slots=True)
class MatrixPreparedResponseReadout(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-experimental-programme/prepared-response-readout"
    VERSION: ClassVar[str] = '2.0.0'
    record_id: str
    source: ObjectIdentity
    preparation: ObjectIdentity
    forecast: ObjectIdentity | None
    original_protocol: ObjectIdentity
    panels: tuple[ObjectIdentity, ...]
    controls: tuple[ScheduledResponseTransitionControl, ...]
    cells: tuple[ScheduledResponseLossCell | MatrixDenseResponseCell, ...]
    numerical_pass: bool
    disposition: str
    cumulative_log_errors: tuple[Decimal | None, ...]
    standing: str = STANDING
    unentered_branch_ids: tuple[str, ...] = ()
    dense: MatrixDenseResponseDiagnostics | None = None

    def __post_init__(self):
        validate_stable_id(self.record_id)
        received = self.disposition in ("FINITE", "PARTIAL", "NATIVE_CROSSCHECK_FAILED")
        amended = self.dense is not None
        if amended:
            if type(self.dense) is not MatrixDenseResponseDiagnostics:
                raise TypeError('prepared amended score requires its complete exact dense diagnostics')
            self.dense.__post_init__()
            self.dense.validate_cells(self.cells)
            if self.dense.numerical_usable != self.numerical_pass or self.cumulative_log_errors != self.dense.factor_log_targets:
                raise ValueError('prepared amended score changes its exact58 paired FACTOR targets')
        elif any(type(row) is not ScheduledResponseLossCell for row in self.cells):
            raise TypeError('prepared five-method score substitutes unbound amended cells')
        targets = 58 if amended else 15
        has_native = (any(value is not None for row in self.dense.amplitudes for value in row.position_norms)
            if amended else any(row.actual_odd_responses is not None for row in self.cells))
        if (self.standing != STANDING or type(self.numerical_pass) is not bool
                or len(self.controls) != (48 if received else 0)
                or len({row.control_id for row in self.controls}) != len(self.controls) or len(self.cells) != (3248 if amended else 240)
                or tuple(row.key for row in self.cells) != tuple(sorted({row.key for row in self.cells}))
                or len(self.cumulative_log_errors) != targets or len(self.panels) != 2
                or self.numerical_pass != (received and all(row.disposition == "SATISFIED" for row in self.controls))
                or self.disposition not in ("FINITE", "PARTIAL", "NATIVE_CROSSCHECK_FAILED", "NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED")
                or received and (self.forecast is None or self.unentered_branch_ids)
                or not received and (self.forecast is not None or len(self.unentered_branch_ids) != 48
                    or self.unentered_branch_ids != tuple(sorted(set(self.unentered_branch_ids)))
                    or self.cumulative_log_errors != (None,) * targets or has_native)
                or self.disposition in ("FINITE", "PARTIAL") and not self.numerical_pass
                or self.disposition == "FINITE" and (not self.numerical_pass or any(row is None for row in self.cumulative_log_errors))
                or self.disposition == "NATIVE_CROSSCHECK_FAILED" and self.numerical_pass):
            raise ValueError("prepared readout thins complete paired branch/endpoint denominators or invents numerical standing")
        for value, kind in ((self.source, MatrixPreparationSource), (self.preparation, MatrixPreparationArrays),
                (self.original_protocol, ScheduledResponseProtocol)):
            if type(value) is not ObjectIdentity or value.object_schema != kind.SCHEMA or value.object_version != kind.VERSION:
                raise ValueError("prepared readout substitutes its original prepared source/assay type/revision")
        if self.forecast is not None and (type(self.forecast) is not ObjectIdentity or self.forecast.object_schema != MatrixPreparedForecastArrays.SCHEMA):
            raise ValueError("prepared readout substitutes actual supplied prediction identity")


def _public_context(source, preparation, protocol, panels):
    if (type(source) is not MatrixPreparationSource or type(preparation) is not MatrixPreparationArrays
            or type(protocol) is not ScheduledResponseProtocol):
        raise TypeError("prepared response needs exact separate source/preparation and original unchanged assay")
    source.__post_init__()
    protocol.__post_init__()
    preparation.validate_source(source)
    if (protocol.public_source != source.original or protocol.receiver_count != 48
            or type(protocol.mechanical_model) is not MatrixOriginResponseModel and len(protocol.horizon_steps) != 3
            or source.total_ticks < source.coordinate.ramp_ticks):
        raise ValueError("prepared response changes original physical/menu/receiver contract, restored future or actual supplied forecast subject")
    validate_prepared_panels(source, panels)


def validate_prepared_panels(source, panels):
    """Exact original whole-group future purposes; no arrays, RNG or outcomes."""
    if (type(panels) is not tuple or any(type(row) is not MatrixPreparedResponsePanel for row in panels)
            or tuple(row.panel_id for row in panels) != tuple(sorted({row.panel_id for row in panels}))
            or len(panels) != 2 or any(row.independent_group_id != source.root.root.independent_group_id for row in panels)
            or tuple(sorted(row.role for row in panels)) != ("COMMON_NOISE_PANEL", "INDEPENDENT_FUTURE")):
        raise ValueError("prepared response loses its exact two whole-group future panels")
    seeds = set()
    for panel in panels:
        panel.__post_init__()
        if panel.role == "COMMON_NOISE_PANEL" and panel.streams != source.root.streams:
            raise ValueError("prepared common panel substitutes original matched purpose streams")
        for stream in panel.streams:
            if stream.effective_seed in seeds:
                raise ValueError("prepared future panels collide in actual consumed streams")
            seeds.add(stream.effective_seed)


def _context(source, preparation, protocol, panels, forecast, frozen_raw, *, frozen_input=None):
    _public_context(source, preparation, protocol, panels)
    if type(forecast) is not MatrixPreparedForecastArrays:
        raise TypeError("prepared response needs its actual supplied prediction array record")
    forecast.__post_init__()
    if (forecast.source != source.identity or forecast.preparation != preparation_identity(preparation)
            or forecast.original_protocol != ObjectIdentity.from_record(protocol.protocol_id, protocol)):
        raise ValueError("prepared response changes actual supplied forecast subject")
    if frozen_input is not None and type(frozen_input) is not DecodedMatrixArrayInput:
        raise TypeError("prepared response reuse requires its actual decoded Matrix input")
    frozen = (decode_matrix_arrays(frozen_raw, forecast) if frozen_input is None
        else frozen_input.for_operand(frozen_raw, forecast))
    expected = {"forces": ("<c16", (4, 2, 3, 4, 4)), "receivers": ("<c16", (48, 2, 2, 3, 4, 4)),
        **{view + "_" + predictor.lower(): ("<f8", (4, len(protocol.horizon_steps), 48))
            for view in ("primary", "fine") for predictor in model_predictors(protocol.mechanical_model)}}
    if not set(expected) <= set(frozen) or any(frozen[name].dtype.str != dtype or frozen[name].shape != shape for name, (dtype, shape) in expected.items()):
        raise ValueError("prepared forecast loses complete selected paired predictor/force/receiver geometry")
    validate_frozen_response_arrays(protocol, frozen, disposition='AVAILABLE')
    receiver_metric(protocol, frozen["receivers"])
    if (not np.isfinite(frozen["forces"]).all() or np.linalg.norm(frozen["forces"] - frozen["forces"].conj().swapaxes(-1, -2)) > 1e-12
            or any(abs(np.linalg.norm(force) - float(action.force_norm)) > float(protocol.receiver_gram_tolerance)
                for force, action in zip(frozen["forces"], protocol.actions, strict=True))):
        raise ValueError("prepared response changes the original fixed finite Hermitian force norm")
    return frozen


def unentered_prepared_responses(source, preparation, protocol, panels, *, record_id, disposition):
    """Retain a known unentered complete assay without invented received arrays."""
    _public_context(source, preparation, protocol, panels)
    if disposition not in ("NO_ORIGIN", "UNEVALUABLE", "INSTRUMENT_UNRESOLVED"):
        raise ValueError("unentered prepared response requires its actual nonuse disposition")
    if type(protocol.mechanical_model) is MatrixOriginResponseModel:
        # No native arrays or invented fixed instrument. Full unknown curves
        # retain every assigned action/panel/check, including ZERO_RESPONSE.
        frozen = {view.lower() + '_full_grid_' + predictor.lower(): np.full((4, 128, 48), np.nan, dtype='<f8')
            for view in ('PRIMARY', 'FINE') for predictor in model_predictors(protocol.mechanical_model)}
        cells, dense = dense_response_measurements(protocol, panels, {}, frozen, available=False, numerical_usable=False)
        return MatrixPreparedResponseReadout(record_id, source.identity, preparation_identity(preparation), None,
            ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in panels), (), cells,
            False, disposition, dense.factor_log_targets, unentered_branch_ids=tuple(row[0] for row in branch_census(protocol, panels)), dense=dense)
    cells = tuple(sorted((ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon,
        None, None, None, None, None) for view in ("PRIMARY", "FINE") for panel in panels for action in protocol.actions
        for predictor in PREDICTORS for horizon in protocol.horizon_steps), key=lambda row: row.key))
    return MatrixPreparedResponseReadout(record_id, source.identity, preparation_identity(preparation), None,
        ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in panels), (), cells,
        False, disposition, (None,) * 15, unentered_branch_ids=tuple(row[0] for row in branch_census(protocol, panels)))


def _future_noise(source, protocol, panels, innovations):
    from types import SimpleNamespace

    if not isinstance(innovations, Mapping) or set(innovations) != {row.panel_id for row in panels}:
        raise ValueError("prepared future omits or extends the complete selected panel census")
    horizon = protocol.horizon_steps[-1]
    paired = SimpleNamespace(primary=SimpleNamespace(horizon_steps=protocol.horizon_steps, view=source.primary_view), fine_view=source.fine_view)
    for panel in panels:
        noise = innovations[panel.panel_id]
        if not isinstance(noise, Mapping) or set(noise) != {"primary", "fine", "bridge"}:
            raise ValueError("prepared future loses paired and original bridge innovations")
        for name, count in (("primary", horizon), ("fine", 2 * horizon), ("bridge", horizon)):
            value = noise[name]
            if (not isinstance(value, np.ndarray) or value.shape != (count, 2, 3, 4, 4) or value.dtype.str != "<c16"
                    or not np.isfinite(value).all() or np.linalg.norm(value - value.conj().swapaxes(-1, -2)) > 1e-12):
                raise ValueError("prepared future loses exact complete finite Hermitian physical-time noise geometry")
        verify_noise_pair(paired, noise["primary"], noise["fine"], noise["bridge"])


def propagate_prepared_responses(source, initial_raw, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, innovations, *, on_step=None):
    """Actual unchanged48-branch native equations with supplied future arrays.

    The ordinary tail lifecycle owns entry and byte custody. This callable is
    also an explicit mathematical seam; it draws no random stream or origin.
    """
    frozen = _context(source, preparation, protocol, panels, forecast, frozen_raw)
    prefix = consume_preparation_arrays(source, initial_raw, preparation, preparation_raw)
    return _propagate_prepared_response_arrays(source, protocol, panels, innovations,
        prefix=prefix, frozen=frozen, on_step=on_step)


def _propagate_prepared_response_arrays(source, protocol, panels, innovations, *, prefix, frozen, on_step=None):
    """Native producer seam after exact actual-child array preparation."""
    _future_noise(source, protocol, panels, innovations)
    arrays = {}
    completed_steps = 0

    def completed_branch_step(_branch_counter):
        nonlocal completed_steps
        completed_steps += 1
        on_step(completed_steps)

    for panel in panels:
        noise = innovations[panel.panel_id]
        for name in ("primary", "fine", "bridge"):
            arrays["noise." + panel.panel_id + "." + name] = noise[name].copy()
    for branch, view, panel, action, sign in branch_census(protocol, panels):
        label, mult = view.lower(), 1 if view == "PRIMARY" else 2
        state = SixMatrixState(2, prefix[label + "_positions"][-1], prefix[label + "_momenta"][-1], mult * source.total_ticks,
            *map(float, source.recipe.half_tick_couplings[-1]))
        values = native_scheduled_branch(state, coordinate=source.coordinate, refinement=mult,
            direction=frozen["forces"][protocol.actions.index(action)], amplitude=0 if sign == "HOLD" else float(action.amplitude) * (1 if sign == "PLUS" else -1),
            pulse_steps=mult * action.pulse_steps, innovations=innovations[panel.panel_id][label],
            **({"on_step": completed_branch_step} if on_step is not None else {}))
        arrays.update({"branch." + branch + "." + name: value for name, value in values.items()})
    return dict(sorted(arrays.items()))


def assess_prepared_responses(source, initial_raw, preparation, preparation_raw, protocol, panels, forecast, frozen_raw, response_arrays, *, record_id, frozen_input=None):
    """Original literal transition/OU/HS24 metric and complete15-output target."""
    from types import SimpleNamespace

    frozen = _context(source, preparation, protocol, panels, forecast, frozen_raw, frozen_input=frozen_input)
    prefix = consume_preparation_arrays(source, initial_raw, preparation, preparation_raw)
    census = branch_census(protocol, panels)
    expected = {"noise." + panel.panel_id + "." + name for panel in panels for name in ("primary", "fine", "bridge")}
    expected.update("branch." + branch + "." + name for branch, *_ in census for name in ("positions", "momenta", "innovations", "ticks", "alpha_tilde"))
    if set(response_arrays) != expected:
        raise ValueError("prepared response loses complete48 branch/noise/state/schedule/clock members")
    paired = SimpleNamespace(primary=SimpleNamespace(horizon_steps=protocol.horizon_steps, view=source.primary_view), fine_view=source.fine_view)
    for panel in panels:
        verify_noise_pair(paired, *(response_arrays["noise." + panel.panel_id + "." + name] for name in ("primary", "fine", "bridge")))
    controls, cells = [], []
    for branch, view, panel, action, sign in census:
        label, mult = view.lower(), 1 if view == "PRIMARY" else 2
        values = {name: response_arrays["branch." + branch + "." + name] for name in ("positions", "momenta", "innovations", "ticks", "alpha_tilde")}
        if not np.array_equal(values["innovations"], response_arrays["noise." + panel.panel_id + "." + label]):
            raise ValueError("prepared response changes common innovations across counterfactual signs/actions")
        controls.append(assess_scheduled_branch(source.coordinate, values, refinement=mult,
            initial_positions=prefix[label + "_positions"][-1], initial_momenta=prefix[label + "_momenta"][-1], start_tick=mult * source.total_ticks,
            direction=frozen["forces"][protocol.actions.index(action)], amplitude=0 if sign == "HOLD" else float(action.amplitude) * (1 if sign == "PLUS" else -1),
            pulse_steps=mult * action.pulse_steps, tolerance=protocol.native_reference_tolerance,
            control_id="control.prepared." + source.source_id + "." + branch))
    if type(protocol.mechanical_model) is MatrixOriginResponseModel:
        passed = all(row.disposition == 'SATISFIED' for row in controls)
        cells, dense = dense_response_measurements(protocol, panels, response_arrays, frozen,
            available=True, numerical_usable=passed)
        cumulative = dense.factor_log_targets
        disposition = 'NATIVE_CROSSCHECK_FAILED' if not passed else 'PARTIAL' if any(value is None for value in cumulative) else 'FINITE'
        return MatrixPreparedResponseReadout(record_id, source.identity, preparation_identity(preparation), forecast.identity,
            ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in panels), tuple(controls),
            cells, passed, disposition, cumulative, dense=dense)
    for view, mult in (("PRIMARY", 1), ("FINE", 2)):
        for panel in panels:
            for action_index, action in enumerate(protocol.actions):
                truths = {}
                for predictor in PREDICTORS:
                    for horizon_index, horizon in enumerate(protocol.horizon_steps):
                        if horizon not in truths:
                            stem = view.lower() + "." + panel.panel_id + "." + action.action_id
                            odd = np.stack(tuple((response_arrays["branch." + stem + ".plus." + phase][mult * horizon]
                                - response_arrays["branch." + stem + ".minus." + phase][mult * horizon]) / 2 for phase in ("positions", "momenta")))
                            actual = np.einsum("rpsjab,psjab->r", frozen["receivers"].conj(), odd).real
                            truth = tuple(Decimal(str(float(value))) for value in actual)
                            truths[horizon] = actual, truth
                        else:
                            actual, truth = truths[horizon]
                        predicted = frozen[view.lower() + "_" + predictor.lower()][action_index, horizon_index]
                        signed = absolute = relative = normalized = None
                        if np.isfinite(predicted).all():
                            signed = tuple(Decimal(str(float(value))) for value in predicted - actual)
                            absolute = tuple(abs(value) for value in signed)
                            with localcontext() as context:
                                context.prec = 60
                                relative = tuple(None if abs(value) <= protocol.weak_response_minimum else error / abs(value)
                                    for value, error in zip(truth, absolute, strict=True))
                            _, _, normalized = response_error_norms(signed, action=action,
                                primary_timestep=source.primary_view.timestep, horizon_tick=horizon)
                        cells.append(ScheduledResponseLossCell(view, panel.panel_id, action.action_id, predictor, horizon, truth, signed, absolute, relative, normalized))
    passed = all(row.disposition == "SATISFIED" for row in controls)
    cumulative = []
    for predictor in PREDICTORS:
        for horizon in protocol.horizon_steps:
            values = tuple(row.normalized_error for row in cells if row.view == "PRIMARY" and row.predictor == predictor and row.horizon_tick <= horizon)
            with localcontext() as context:
                context.prec = 50
                cumulative.append(None if not passed or any(value is None for value in values) else (Decimal(1) + max(values)).ln())
    disposition = "NATIVE_CROSSCHECK_FAILED" if not passed else "PARTIAL" if any(value is None for value in cumulative) else "FINITE"
    return MatrixPreparedResponseReadout(record_id, source.identity, preparation_identity(preparation), forecast.identity,
        ObjectIdentity.from_record(protocol.protocol_id, protocol), tuple(row.identity for row in panels), tuple(controls),
        tuple(sorted(cells, key=lambda row: row.key)), passed, disposition, tuple(cumulative))
