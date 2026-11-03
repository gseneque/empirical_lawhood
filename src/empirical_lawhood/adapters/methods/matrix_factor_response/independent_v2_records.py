# SPDX-License-Identifier: MPL-2.0
"""Exact scientific declaration of the independent numerical method."""

from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord, validate_stable_id


REFERENCE_METHOD = "FULL192_TRACE_WORD_DERIVATIVE_BAOAB_BOTH_FORCE_KICKS_V2"



HESSIAN_METHOD = "FULL96_POTENTIAL_SECOND_DIFFERENCES"



@dataclass(frozen=True, slots=True)
class MatrixResponseIndependentMethodV2(CanonicalRecord):
    SCHEMA: ClassVar[str] = "empirical-lawhood/matrix-factor-response/independent-method"
    VERSION: ClassVar[str] = "2.0.0"
    method_id: str
    implementation: ObjectIdentity
    formulation: str = REFERENCE_METHOD
    hessian_reference: str = HESSIAN_METHOD
    reuse: str = "IMMUTABLE_HS_BASIS_CONSTANT_TRACE_WORDS_ENDPOINT_GRADIENT_ONE_HOLD_PER_PANEL"
    standing: str = "EXPOSED_INDEPENDENT_METHOD_NO_QUALIFICATION"

    def __post_init__(self):
        validate_stable_id(self.method_id)
        if (self.implementation.object_schema != "empirical-lawhood/matrix-factor-response/independent-implementation"
                or self.implementation.object_version != "2.0.0" or self.formulation != REFERENCE_METHOD
                or self.hessian_reference != HESSIAN_METHOD
                or self.reuse != "IMMUTABLE_HS_BASIS_CONSTANT_TRACE_WORDS_ENDPOINT_GRADIENT_ONE_HOLD_PER_PANEL"
                or self.standing != "EXPOSED_INDEPENDENT_METHOD_NO_QUALIFICATION"):
            raise ValueError("independent v2 method changes its explicit formulation/identity/standing")

    @property
    def identity(self):
        return ObjectIdentity.from_record(self.method_id, self)
