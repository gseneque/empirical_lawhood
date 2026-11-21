"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from empirical_lawhood.domains.reactor.native_ports import PreparedNativeRequest
from empirical_lawhood.domains.reactor.reactor_regime_response.prepared_lock import RegimeDPreparedRequestLock
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.execution.controller_runtime import DeliveryControllerTickReceipt

@dataclass(frozen=True)
class ProspectiveRootAcquisition:
    root: str
    prepared: tuple[PreparedNativeRequest | None, ...]
    nominal: tuple[NativeEpisode | None, ...]
    refined: tuple[NativeEpisode | None, ...]
    evaluator_chart: tuple[NativeEpisode, ...]
    ticks: tuple[DeliveryControllerTickReceipt | None, ...]
    native_calls: int
    reasons: tuple[str, ...]
    locks: tuple[RegimeDPreparedRequestLock, ...] = ()

    def __post_init__(self) -> None:
        if (
            len(self.prepared) != 4
            or len(self.nominal) != 4
            or len(self.refined) != 4
            or len(self.ticks) != 4
            or len(self.evaluator_chart) not in (0, 6)
            or self.native_calls != sum(value is not None for value in (*self.nominal, *self.refined))
            + len(self.evaluator_chart)
            or self.native_calls > 14
            or len(self.locks) not in (0, 4)
        ):
            raise ValueError("D action changes its four branches or six-word-view chart")
