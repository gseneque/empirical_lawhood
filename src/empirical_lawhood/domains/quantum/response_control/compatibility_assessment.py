"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from empirical_lawhood.science.records.serialization import validate_sha256
from empirical_lawhood.domains.quantum.response_control.basis import build_basis, build_boundary_current_operator, build_hamiltonian, hermiticity_residual, sparse_matrix_fingerprint
from empirical_lawhood.domains.quantum.response_control.contracts import Action, Verdict


REFERENCE_REQUIRED = {
    "stages/conformance/result.json": "SEMANTIC_CONTRACT_VALID",
    "stages/deterministic-reference/result.json": "DETERMINISTIC_REFERENCE_QUALIFIED",
    "stages/path-source/result.json": "PATH_SOURCE_QUALIFIED",
    "stages/ensemble-source/result.json": "ENSEMBLE_SOURCE_QUALIFIED",
}


@dataclass(frozen=True, slots=True)
class CompatibilityExpectedIdentities:
    """Caller supplied identities of the two predecessor evaluations."""

    reference_validation_implementation_sha256: str
    preparation_qualification_plan_sha256: str
    preparation_qualification_config_sha256: str
    preparation_qualification_implementation_sha256: str
    preparation_qualification_freeze_sha256: str
    preparation_qualification_closeout_sha256: str
    preparation_qualification_closeout_receipt_sha256: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            validate_sha256(getattr(self, name), field_name=name)


@dataclass(frozen=True, slots=True)
class CompatibilityCheck:
    check_id: str
    passed: bool
    observed: str
    expected: str
    reason_code: str | None


@dataclass(frozen=True, slots=True)
class CompatibilityResult:
    verdict: Verdict
    checks: tuple[CompatibilityCheck, ...]
    basis_sha256: str | None
    hamiltonian_sha256_by_action: Mapping[Action, str]
    current_sha256_by_action: Mapping[Action, str]
    reason_codes: tuple[str, ...]


def _check(
    check_id: str,
    observed: object,
    expected: object,
    reason: str,
) -> CompatibilityCheck:
    return CompatibilityCheck(
        check_id,
        observed == expected,
        str(observed),
        str(expected),
        None if observed == expected else reason,
    )


def assess_action_compatibility(*, config, checks):
    """Assess the Hamiltonian/current family from authenticated predecessor checks."""
    checks = list(checks)
    basis = build_basis(config.l_sites, config.particles)
    hamiltonians = {
        action: build_hamiltonian(
            basis,
            action=action,
            epsilon=float(config.epsilon),
            j_xy=float(config.j_xy),
            j_z=float(config.j_z),
        )
        for action in Action
    }
    currents = {
        action: build_boundary_current_operator(
            basis,
            action=action,
            epsilon=float(config.epsilon),
            j_xy=float(config.j_xy),
        )
        for action in Action
    }
    for action, matrix in hamiltonians.items():
        checks.append(
            _check(
                f"hamiltonian-hermitian:{action.value}",
                hermiticity_residual(matrix) <= 1e-12,
                True,
                "action-hamiltonian-not-hermitian",
            )
        )
    for action, matrix in currents.items():
        checks.append(
            _check(
                f"current-hermitian:{action.value}",
                hermiticity_residual(matrix) <= 1e-12,
                True,
                "boundary-current-not-hermitian",
            )
        )
    reasons = tuple(
        sorted(
            {
                check.reason_code
                for check in checks
                if not check.passed and check.reason_code is not None
            }
        )
    )
    if not reasons:
        verdict = Verdict.COMPATIBLE_STRONG_SOURCE_READY
    elif any("receipt" in reason for reason in reasons):
        verdict = Verdict.PREDECESSOR_RECEIPT_STOP
    elif any("action" in reason or "current" in reason for reason in reasons):
        verdict = Verdict.ACTION_COMPATIBILITY_STOP
    elif "forbidden-historical-runtime-import" in reasons:
        verdict = Verdict.IMPLEMENTATION_IDENTITY_STOP
    else:
        verdict = Verdict.SOURCE_COMPATIBILITY_STOP
    return CompatibilityResult(
        verdict=verdict,
        checks=tuple(checks),
        basis_sha256=basis.fingerprint,
        hamiltonian_sha256_by_action={
            action: sparse_matrix_fingerprint(matrix) for action, matrix in hamiltonians.items()
        },
        current_sha256_by_action={
            action: sparse_matrix_fingerprint(matrix) for action, matrix in currents.items()
        },
        reason_codes=reasons,
    )
