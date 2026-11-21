"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from empirical_lawhood.domains.quantum.support_conditioned_identification.contracts import Verdict


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    verdict: Verdict
    checked_sha256: Mapping[str, str]
    reason_codes: tuple[str, ...]
    field_classification: Mapping[str, str]
