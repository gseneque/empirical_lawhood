"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from typing import Any, Protocol
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorDelivery, ReactorFinalDelivery

class NativeController(Protocol):
    def reset(self, spec: dict[str, Any]) -> None: ...
    def step(self, t_s: float, y: dict[str, float], dt_s: float) -> tuple[float, float]: ...

class CallbackOwner(Protocol):
    failed: bool

    def advance(
        self, controller: NativeController, previous: tuple[float, float], session: Any
    ) -> ReactorDelivery | ReactorFinalDelivery | None: ...


from empirical_lawhood.execution.controller_compiler import CompiledDeliveryControllerStudy
from empirical_lawhood.execution.controller_runtime import DeliveryControllerDecisionCommitment


class PreparedNativeRequest(Protocol):
    """Read-only scientific identity surface of an already prepared native owner."""

    @property
    def compiled(self) -> CompiledDeliveryControllerStudy: ...

    @property
    def commitment(self) -> DeliveryControllerDecisionCommitment: ...
