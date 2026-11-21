"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import asdict, dataclass
from typing import Any
import numpy as np
from empirical_lawhood.domains.reactor.reactor_causal_response.numerical import Observation, FrozenFit, exploration, digest
from empirical_lawhood.domains.reactor.reactor_causal_response.controller import NumericalController, EmpiricalNonattempt
from empirical_lawhood.domains.reactor.reactor_causal_response.calibration import RootOperands
from empirical_lawhood.domains.reactor.reactor_causal_response.experiment_records import EmpiricalEpisodeEnvelope, EmpiricalArrayPayload
from empirical_lawhood.domains.reactor.reactor_causal_response.actuator import Actuator, measured_labels, project_tape

@dataclass(frozen=True)
class NativeEpisode:
    root: str
    episode: str
    dt: float
    observations: np.ndarray
    requests: np.ndarray
    stages: np.ndarray
    exposure: np.ndarray
    grid: np.ndarray
    callback_cpu: np.ndarray
    failure: str | None

    @property
    def complete(self) -> bool:
        return (
            self.failure is None
            and self.observations.shape == (2880, 4)
            and self.stages.shape == (2880, 4)
            and self.callback_cpu.shape == (2880,)
            and all(
                a.dtype == np.dtype("float64")
                for a in (
                    self.observations,
                    self.requests,
                    self.stages,
                    self.exposure,
                    self.grid,
                    self.callback_cpu,
                )
            )
            and self.requests.shape == (2880, 2)
            and self.exposure.shape == (2880, int(10 / self.dt), 4)
            and self.grid.shape == (int(28800 / self.dt) + 1, 8)
        )

    def envelope(self) -> 'EmpiricalEpisodeEnvelope':
        return EmpiricalEpisodeEnvelope(
            self.root,
            self.episode,
            self.dt == 0.5,
            self.failure,
            EmpiricalArrayPayload.pack(
                {
                    name: getattr(self, name)
                    for name in (
                        "observations",
                        "requests",
                        "stages",
                        "exposure",
                        "grid",
                        "callback_cpu",
                    )
                }
            ),
        )

    @classmethod
    def from_envelope(cls, value: 'EmpiricalEpisodeEnvelope') -> "NativeEpisode":
        arrays = value.arrays.unpack()
        if set(arrays) != {
            "observations",
            "requests",
            "stages",
            "exposure",
            "grid",
            "callback_cpu",
        }:
            raise ValueError("native episode arrays differ")
        return cls(
            value.root,
            value.episode,
            0.5 if value.refined else 1.0,
            **arrays,
            failure=value.failure,
        )

class ExplorationController:
    def __init__(self, root: int, policy: int) -> None:
        self.root, self.policy = root, policy
        self.history: tuple[Observation, ...] = ()
        self.previous = (0.0, 316.0)
        self.actuator = Actuator()

    def reset(self, spec: dict[str, Any]) -> None:
        self.history, self.previous = (), (0.0, 316.0)

    def step(self, t_s: float, y: dict[str, float], dt_s: float) -> tuple[float, float]:
        o = Observation(
            float(t_s), float(y["t_reactor_k"]), float(y["t_jacket_k"]), float(y["dosed_kg"])
        )
        self.history += (o,)
        a = exploration(self.history, self.previous[1], self.root, self.policy)
        p = self.actuator.project(o, self.previous)[a]
        self.previous = p.applied
        return p.requested

class TapeController:
    def __init__(self, tape: np.ndarray) -> None:
        if tape.ndim != 2 or tape.shape[1] != 2 or len(tape) > 2880 or not np.isfinite(tape).all():
            raise ValueError("invalid donor request tape")
        self.tape = tape.copy()

    def reset(self, spec: dict[str, Any]) -> None:
        pass

    def step(self, t_s: float, y: dict[str, float], dt_s: float) -> tuple[float, float]:
        k = int(t_s / 10)
        if k >= len(self.tape):
            raise EmpiricalNonattempt("DONOR_TAPE_INCOMPLETE")
        return float(self.tape[k, 0]), float(self.tape[k, 1])

def paired_operands(
    nominal: NativeEpisode, refined: NativeEpisode, model: FrozenFit, q: float
) -> RootOperands:
    if nominal.root != refined.root or nominal.dt != 1 or refined.dt != 0.5:
        raise ValueError("paired views change assigned root or denominator")
    controller = NumericalController(model, q, Actuator())
    rows, actions = [], []
    for t, y, j, dose in nominal.observations:
        try:
            controller.step(
                float(t),
                dict(t_reactor_k=float(y), t_jacket_k=float(j), dosed_kg=float(dose)),
                10.0,
            )
        except EmpiricalNonattempt:
            break
        decision = controller.decisions[-1]
        assert decision.selected is not None
        rows.append(decision.candidates[decision.selected].features)
        actions.append(decision.selected)
        controller.decisions.clear()
    labels = np.empty((0, 2, 3))
    requests = np.empty((0, 2, 2))
    pn, pr = np.empty((0, 10, 4)), np.empty((0, 20, 4))
    if nominal.complete and refined.complete:
        labels = np.stack(
            [
                measured_labels(e.grid[:, 0], e.grid[:, 1], e.grid[:, 4], e.grid[:, 3], e.dt)
                for e in (nominal, refined)
            ],
            axis=1,
        )
        requests = np.stack([nominal.requests, refined.requests], axis=1)
        pn, pr = project_tape(nominal.requests, 1.0), project_tape(refined.requests, 0.5)
    return RootOperands(
        nominal.root,
        nominal.observations[:, 0],
        np.asarray(actions, dtype=int),
        np.asarray(rows).reshape(-1, 23),
        labels,
        pn,
        nominal.exposure,
        pr,
        refined.exposure,
        requests,
        nominal.observations,
        np.array([q]),
        np.array(list(bytes.fromhex(digest(asdict(model)))), dtype=np.int64),
        np.stack([nominal.stages, refined.stages], axis=1)
        if nominal.stages.shape == refined.stages.shape
        else np.empty((0, 2, 4)),
    )
