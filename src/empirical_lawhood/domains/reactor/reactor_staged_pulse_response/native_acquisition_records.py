"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from dataclasses import dataclass
from functools import lru_cache
from typing import ClassVar
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.config import Request
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.frozen_records import ClassicalFrozenRoot, ClassicalFrozenStage
from empirical_lawhood.domains.reactor.reactor_staged_pulse_response.records import ClassicalNativeWindow
from empirical_lawhood.domains.reactor.reactor_prefix_response.contracts import ReactorDelivery
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.storage.contracts.canonical_record_archive import CanonicalRecordArchive
from empirical_lawhood.execution.controller_runtime import DeliveryControllerTickReceipt

@dataclass(frozen=True, slots=True)
class ClassicalNativeStage(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-staged-pulse-response/classical-native-stage'
    frozen: CanonicalRecordArchive
    tick: DeliveryControllerTickReceipt | None
    deliveries: tuple[ReactorDelivery, ...]

    @lru_cache(maxsize=32)
    def unpack(self) -> ClassicalFrozenStage:
        # Measurement, sealing and reveal consume the same immutable child.
        # Key by the whole stage, including its tick and actual deliveries, so
        # another owner/receipt still traverses the validation below.
        value = decode_canonical_bytes(
            self.frozen.unpack(), ClassicalFrozenStage, maximum_bytes=self.frozen.decoded_bytes
        )
        if (
            self.frozen.subject != ObjectIdentity.from_record(value.record_id, value)
            or (self.tick is not None and self.tick.commitment != value.commitment)
            or (self.deliveries and (self.tick is None or not value.admitted))
        ):
            raise ValueError("actual native stage substitutes its frozen owner")
        return value

@dataclass(frozen=True, slots=True)
class ClassicalNativeUse(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-staged-pulse-response/classical-native-use'
    policy: str
    request: Request
    stages: tuple[ClassicalNativeStage, ...]
    windows: tuple[ClassicalNativeWindow, ...]
    native_calls: int
    failures: tuple[str, ...]
    known_unsafe: bool

    def __post_init__(self) -> None:
        if (
            self.native_calls not in (0, 1, 2)
            or not 1 <= len(self.stages) <= 2
            or any(
                (s.unpack().policy, s.unpack().request) != (self.policy, self.request)
                for s in self.stages
            )
            or (not self.native_calls and (self.windows or any(s.deliveries for s in self.stages)))
        ):
            raise ValueError("native use changes its actual decision/view census")
        if len(self.stages) == 2 and (
            self.stages[0].tick is None
            or self.stages[1].unpack().causal.predecessor
            != ObjectIdentity.from_record(self.stages[0].tick.tick_id, self.stages[0].tick)
        ):
            raise ValueError("second native stage substitutes its actual predecessor")

@dataclass(frozen=True, slots=True)
class ClassicalNativeRoot(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/reactor-staged-pulse-response/classical-native-root'
    root: str
    frozen: ObjectIdentity
    scenario: ObjectIdentity
    uses: tuple[ClassicalNativeUse, ...]
    references: tuple[ClassicalNativeWindow, ...]
    reference_calls: int

    def __post_init__(self) -> None:
        if (
            self.frozen.object_schema != ClassicalFrozenRoot.SCHEMA
            or self.scenario.object_id != self.root
            or self.reference_calls not in range(5)
            or len({(u.policy, u.request.request_id) for u in self.uses}) != len(self.uses)
            or any(s.unpack().causal.root != self.root for u in self.uses for s in u.stages)
        ):
            raise ValueError(
                "prospective native result changes its assigned root or reference budget"
            )

    @property
    def native_calls(self) -> int:
        return self.reference_calls + sum(u.native_calls for u in self.uses)

    @property
    def record_id(self) -> str:
        return f"{self.root}.native-observation"
