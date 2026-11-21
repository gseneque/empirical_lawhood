"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.frozen_records import FrontierFrozenRoot
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.records import FrontierAssay
from empirical_lawhood.domains.reactor.reactor_finite_control_frontier.selection import FrontierUseRequest
from empirical_lawhood.domains.reactor.reactor_local_domain_qualification.records import LocalArrayPayload
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorDelivery
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.controller_runtime import DeliveryControllerTickReceipt

@dataclass(frozen=True, slots=True)
class FrontierNativeUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-finite-control-frontier/frontier-native-use'
    request: FrontierUseRequest
    arrays: LocalArrayPayload
    tick: DeliveryControllerTickReceipt | None
    native_deliveries: tuple[ReactorDelivery, ...]
    native_calls: int
    failures: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            self.native_calls not in (0, 1, 2)
            or len(self.native_deliveries) > 12
            or (
                self.native_calls == 0
                and (
                    self.tick is not None
                    or self.native_deliveries
                    or self.arrays.unpack()
                    or not self.failures
                )
            )
        ):
            raise ValueError("native use invented an acquisition or complete macro")

@dataclass(frozen=True, slots=True)
class FrontierNativeRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-finite-control-frontier/frontier-native-root'
    root: str
    frozen: ObjectIdentity
    uses: tuple[FrontierNativeUse, ...]
    assay: FrontierAssay

    def __post_init__(self) -> None:
        if (
            self.frozen.object_schema != FrontierFrozenRoot.SCHEMA
            or self.assay.root != self.root
            or self.native_calls > 128
        ):
            raise ValueError("prospective root changed its frozen parent or native budget")

    @property
    def native_calls(self) -> int:
        return self.assay.native_calls + sum(u.native_calls for u in self.uses)

    @property
    def record_id(self) -> str:
        return f"{self.root}.frontier-native-root"
