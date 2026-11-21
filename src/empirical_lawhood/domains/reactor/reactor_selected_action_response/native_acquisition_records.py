"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from empirical_lawhood.domains.reactor.native_ports import PreparedNativeRequest
from empirical_lawhood.methods.control.prepared_forecast import PreparedForecastLock
from empirical_lawhood.domains.reactor.reactor_causal_response.measurements import NativeEpisode
from empirical_lawhood.execution.controller_runtime import DeliveryControllerTickReceipt

@dataclass(frozen=True)
class ClassicalRootAcquisition:
    root: str
    prepared: tuple[PreparedNativeRequest | None, ...]
    nominal: tuple[NativeEpisode | None, ...]
    refined: tuple[NativeEpisode | None, ...]
    evaluator_chart: tuple[NativeEpisode, ...]
    ticks: tuple[DeliveryControllerTickReceipt | None, ...]
    native_calls: int
    reasons: tuple[str, ...]
    locks: tuple[PreparedForecastLock, ...] = ()

    def __post_init__(self) -> None:
        if (
            any(len(x) != 1 for x in (self.prepared, self.nominal, self.refined, self.ticks))
            or len(self.evaluator_chart) not in (0, 4)
            or len(self.locks) not in (0, 1)
            or self.native_calls
            != sum(x is not None for x in (*self.nominal, *self.refined))
            + len(self.evaluator_chart)
        ):
            raise ValueError(
                "classical acquisition changed its one request and reference/audit census"
            )
