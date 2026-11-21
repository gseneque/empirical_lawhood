"""Native acquisition and external-format binding for the domain science."""

from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping, Sequence
from empirical_lawhood.domains.quantum.response_control.contracts import QuantumResponseControlConfig, Verdict

from empirical_lawhood.domains.quantum.response_control.compatibility_assessment import (
    CompatibilityCheck as _science_CompatibilityCheck,
    CompatibilityExpectedIdentities as _science_CompatibilityExpectedIdentities,
    CompatibilityResult as _science_CompatibilityResult,
    REFERENCE_REQUIRED as _science_REFERENCE_REQUIRED,
    _check,
    assess_action_compatibility as _science_assess_action_compatibility,
)

def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def _document(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, Mapping):
        raise TypeError(f"predecessor document is not an object: {path}")
    nested = value.get("value", value)
    if not isinstance(nested, Mapping):
        raise TypeError(f"predecessor value is not an object: {path}")
    return nested


def verify_payload_receipt(root: Path, relative_path: str) -> _science_CompatibilityCheck:
    payload_path = root / relative_path
    receipt_path = payload_path.with_suffix(payload_path.suffix + ".receipt.json")
    if not payload_path.is_file() or not receipt_path.is_file():
        return _science_CompatibilityCheck(
            f"receipt:{relative_path}",
            False,
            "MISSING",
            "PAYLOAD_AND_RECEIPT",
            "predecessor-payload-or-receipt-missing",
        )
    payload_sha = _sha_file(payload_path)
    receipt = _document(receipt_path)
    passed = (
        receipt.get("relative_path") == relative_path
        and receipt.get("size_bytes") == payload_path.stat().st_size
        and receipt.get("sha256") == payload_sha
    )
    return _science_CompatibilityCheck(
        f"receipt:{relative_path}",
        passed,
        payload_sha,
        str(receipt.get("sha256")),
        None if passed else "predecessor-receipt-mismatch",
    )


def evaluate_compatibility(
    *,
    config: QuantumResponseControlConfig,
    reference_validation_root: Path,
    preparation_qualification_root: Path,
    expected: _science_CompatibilityExpectedIdentities,
    forbidden_import_hits: Sequence[str] = (),
) -> _science_CompatibilityResult:
    checks: list[_science_CompatibilityCheck] = []
    required_exports = (
        *((reference_validation_root, path) for path in _science_REFERENCE_REQUIRED),
        *((preparation_qualification_root, path) for path in (
            "controls/freeze.json",
            "stages/base-compatibility/result.json",
            "stages/statistical-conformance/result.json",
            "stages/development/result.json",
            "stages/evaluation/result.json",
            "closeout/result.json",
        )),
    )
    missing = tuple(
        f"{root}/{path}"
        for root, path in required_exports
        if not (root / path).is_file()
        or not (root / (path + ".receipt.json")).is_file()
    )
    if missing:
        return _science_CompatibilityResult(
            verdict=Verdict.PREDECESSOR_RECEIPT_STOP,
            checks=(_science_CompatibilityCheck(
                "target-predecessor-export",
                False,
                ";".join(missing),
                "CURRENT_DESCRIPTORS_AND_VERIFIED_TARGET_CUSTODY",
                "target-predecessor-export-required",
            ),),
            basis_sha256=None,
            hamiltonian_sha256_by_action={},
            current_sha256_by_action={},
            reason_codes=("target-predecessor-export-required",),
        )
    for relative_path, verdict in _science_REFERENCE_REQUIRED.items():
        checks.append(verify_payload_receipt(reference_validation_root, relative_path))
        document = _document(reference_validation_root / relative_path)
        checks.extend(
            (
                _check(
                    f"declared contract-verdict:{relative_path}",
                    document.get("verdict"),
                    verdict,
                    "declared contract-component-verdict-mismatch",
                ),
                _check(
                    f"declared contract-implementation:{relative_path}",
                    document.get("implementation_sha256"),
                    expected.reference_validation_implementation_sha256,
                    "declared contract-implementation-identity-mismatch",
                ),
            )
        )
    for relative_path in (
        "controls/freeze.json",
        "stages/base-compatibility/result.json",
        "stages/statistical-conformance/result.json",
        "stages/development/result.json",
        "stages/evaluation/result.json",
        "closeout/result.json",
    ):
        checks.append(verify_payload_receipt(preparation_qualification_root, relative_path))
    freeze = _document(preparation_qualification_root / "controls/freeze.json")
    closeout = _document(preparation_qualification_root / "closeout/result.json")
    evaluation_result = _document(preparation_qualification_root / "stages/evaluation/result.json")
    checks.extend(
        (
            _check(
                "declared contract-plan",
                closeout.get("plan_sha256"),
                expected.preparation_qualification_plan_sha256,
                "declared contract-plan-identity-mismatch",
            ),
            _check(
                "declared contract-config",
                closeout.get("config_sha256"),
                expected.preparation_qualification_config_sha256,
                "declared contract-config-identity-mismatch",
            ),
            _check(
                "declared contract-implementation",
                closeout.get("implementation_sha256"),
                expected.preparation_qualification_implementation_sha256,
                "declared contract-implementation-identity-mismatch",
            ),
            _check(
                "declared contract-freeze",
                freeze.get("freeze_sha256"),
                expected.preparation_qualification_freeze_sha256,
                "declared contract-freeze-identity-mismatch",
            ),
            _check(
                "declared contract-closeout-payload",
                _sha_file(preparation_qualification_root / "closeout/result.json"),
                expected.preparation_qualification_closeout_sha256,
                "declared contract-closeout-identity-mismatch",
            ),
            _check(
                "declared contract-closeout-receipt",
                _sha_file(preparation_qualification_root / "closeout/result.json.receipt.json"),
                expected.preparation_qualification_closeout_receipt_sha256,
                "declared contract-closeout-receipt-identity-mismatch",
            ),
            _check(
                'declared compatibility-evaluation verdict',
                evaluation_result.get("verdict"),
                "QUANTUM_TRAJECTORY_PREPARATION_QUALIFICATION_STRONG_SOURCE_PREPARATION_QUALIFIED",
                "declared contract-preparation-verdict-mismatch",
            ),
            _check(
                "declared contract-handoff",
                closeout.get("handoff"),
                "RESPONSE_CONTROL_STRONG_ONLY_PLANNING_ELIGIBLE",
                "declared contract-handoff-mismatch",
            ),
            _check(
                "declared contract-selected-cutoff",
                evaluation_result.get("selected_burnin"),
                200.0,
                "declared contract-cutoff-mismatch",
            ),
            _check(
                "declared contract-config-cutoff",
                str(config.cutoff),
                "200",
                "declared contract-cutoff-mismatch",
            ),
            _check(
                "historical-runtime-imports",
                tuple(forbidden_import_hits),
                (),
                "forbidden-historical-runtime-import",
            ),
        )
    )
    return _science_assess_action_compatibility(config=config, checks=checks)
