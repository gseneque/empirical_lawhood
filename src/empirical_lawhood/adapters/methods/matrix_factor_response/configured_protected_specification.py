# SPDX-License-Identifier: MPL-2.0
"""Protected configured E3 selection with its explicit prospective boundary.

Measurement, methods and comparison validation share the configured owner.
This record supplies no source eligibility, issue or outcome-access authority.
"""
from dataclasses import dataclass, field
from typing import ClassVar

from .configured_specification import ConfiguredMatrixResponseErrorSpecification


@dataclass(frozen=True, slots=True)
class ConfiguredProtectedE3Specification(ConfiguredMatrixResponseErrorSpecification):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/matrix-response-experiment/configured-protected-specification'
    VERSION: ClassVar[str] = '3.0.0'
    evidence_scope: str = field(kw_only=True)

    def __post_init__(self):
        self._validate_selected_contract('PROSPECTIVE_REQUIRED')
