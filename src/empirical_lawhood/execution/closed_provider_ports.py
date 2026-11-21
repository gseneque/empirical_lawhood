"""Exact code-owned configuration and port census for static provider factories."""

from typing import TypeVar
from empirical_lawhood.science.records.serialization import CanonicalRecord
from empirical_lawhood.execution.executable_bindings import ExecutableCapabilityBinding, ExecutablePlatformPort
from empirical_lawhood.execution.providers import ExternalInputPayload

R = TypeVar("R", bound=CanonicalRecord)


def closed_ports(
    binding: ExecutableCapabilityBinding,
    records: tuple[CanonicalRecord, ...],
    kind: type[R],
    platform_ports: tuple[ExecutablePlatformPort, ...],
) -> tuple[R, dict[str, object]]:
    if len(records) != 1 or not isinstance(records[0], kind):
        raise ValueError("provider requires its exact installed configuration record")
    ports = {p.port_key: p.port for p in platform_ports}
    if tuple(sorted(ports)) != binding.required_platform_port_keys or len(ports) != len(
        platform_ports
    ):
        raise ValueError("provider changed its code-owned port census")
    return records[0], ports


def input_payloads(value: object) -> tuple[ExternalInputPayload, ...]:
    if not isinstance(value, tuple) or any(not isinstance(p, ExternalInputPayload) for p in value):
        raise TypeError("provider requires exact preauthenticated external payloads")
    return value
