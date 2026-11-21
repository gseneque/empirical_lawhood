# SPDX-License-Identifier: MPL-2.0
"""Structured, bounded explanations shared by every application client.

Only explicitly public contract values belong in ``expected`` and ``actual``.
Trace frames contain code locations, never exception messages, source lines,
local variables, input bodies or scientific observations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


_OWNERS = frozenset({"science", "design", "methods", "domains", "adapters",
                     "execution", "storage", "api", "cli", "workbench"})
_PACKAGE = Path(__file__).resolve().parents[1]
_REMEDIATION = {
    "science": "investigation", "design": "investigation",
    "methods": "method", "domains": "domain", "adapters": "adapter",
    "execution": "platform", "storage": "platform", "api": "investigation",
    "cli": "platform", "workbench": "platform",
}


@dataclass(frozen=True, slots=True)
class DiagnosticFrame:
    module: str
    function: str
    line: int


@dataclass(frozen=True, slots=True)
class OperationDiagnostic:
    """An explanation of one failed contract at its authored boundary."""

    authored_object: str | None
    operation: str
    owner: str
    contract: str
    expected: str
    actual: str
    implementation: str
    evidence: str | None
    remediation: str
    trace: tuple[DiagnosticFrame, ...] = ()

    def __post_init__(self) -> None:
        if self.owner not in _OWNERS:
            raise ValueError("diagnostic owner must name an EL package responsibility")
        if self.remediation not in {"investigation", "method", "domain", "adapter", "platform"}:
            raise ValueError("diagnostic remediation must identify its public job or platform")
        for name in ("authored_object", "operation", "contract", "expected", "actual", "implementation", "evidence"):
            value = getattr(self, name)
            if value is None and name in {"authored_object", "evidence"}:
                continue
            if type(value) is not str or not value or len(value.encode("utf-8")) > 4096:
                raise ValueError(f"diagnostic {name} must be bounded nonempty public text")
        if len(self.trace) > 16 or any(type(frame) is not DiagnosticFrame for frame in self.trace):
            raise ValueError("diagnostic trace must contain at most sixteen code frames")

    def to_mapping(self) -> dict[str, object]:
        return asdict(self)


def code_trace(error: BaseException) -> tuple[DiagnosticFrame, ...]:
    """Retain the deepest relevant code frames, with no source or value access."""
    frames: list[DiagnosticFrame] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen and len(seen) < 5:
        seen.add(id(current))
        traceback = current.__traceback__
        while traceback is not None:
            code = traceback.tb_frame.f_code
            try:
                path = Path(code.co_filename).resolve().relative_to(_PACKAGE)
            except (ValueError, OSError):
                pass
            else:
                module = "empirical_lawhood." + ".".join(path.with_suffix("").parts)
                frames.append(DiagnosticFrame(module, code.co_name, traceback.tb_lineno))
            traceback = traceback.tb_next
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return tuple(frames[-16:])


def explain_failure(*, operation: str, error: BaseException, contract: str,
                    authored_object: str | None = None, expected: str | None = None,
                    actual: str | None = None, evidence: str | None = None,
                    owner: str | None = None) -> OperationDiagnostic:
    """Build a safe explanation; missing observations remain explicitly unknown."""
    trace = code_trace(error)
    frame = trace[-1] if trace else None
    observed_owner = frame.module.split(".")[1] if frame is not None else "api"
    selected_owner = owner or (observed_owner if observed_owner in _OWNERS else "api")
    implementation = (f"{frame.module}:{frame.function}:{frame.line}" if frame else
                      f"{type(error).__module__}.{type(error).__qualname__}")
    return OperationDiagnostic(
        authored_object=authored_object, operation=operation, owner=selected_owner,
        contract=contract, expected=expected or "The declared contract must be satisfied.",
        actual=actual or f"{type(error).__name__}; operand values were not disclosed by the owner.",
        implementation=implementation, evidence=evidence,
        remediation=_REMEDIATION[selected_owner], trace=trace,
    )
