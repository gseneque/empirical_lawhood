"""Bounded exposed RC execution through existing provenance and receipt owners.

SPDX-License-Identifier: MPL-2.0
"""

from pathlib import Path
from time import monotonic

from empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts import (
    RCChainSummary,
    RCChainUnitResult,
    RCPrerequisiteChainConfig,
)
from empirical_lawhood.api.matrix_numerical_provenance import (
    authenticate_recorded_matrix_provenance,
    capture_matrix_provenance,
    numerical_package_code_sha256,
    selected_dependency_lock_sha256,
)
from empirical_lawhood.infrastructure.development_native_custody import (
    DevelopmentNativeCustody,
    preflight_development_native_store,
)
from empirical_lawhood.infrastructure.task_receipts import ExternalTaskReceiptStore
from empirical_lawhood.kernel.numerical_provenance import NumericalProducingProvenance


def rc_chain_run_id(config: RCPrerequisiteChainConfig) -> str:
    return "rc-chain." + config.fingerprint()[:24]


def prove_rc_chain(config: RCPrerequisiteChainConfig) -> dict[str, object]:
    """Inspect the complete design without importing numerical solvers or acquiring data."""
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import prove_chain

    proof = prove_chain(config)
    return {
        **proof.to_document()["value"],
        "run_id": rc_chain_run_id(config),
        "native_contact": "none",
        "scientific_execution_performed": False,
        "scientific_authority": "NONE",
        "qualification": "NOT_ESTABLISHED",
    }


def _custody(config, writer, implementation_commit, *, read_only=False):
    return DevelopmentNativeCustody(
        writer=writer,
        config=config,
        run_id=rc_chain_run_id(config),
        implementation_commit=implementation_commit,
        minimum_free_bytes=config.protocol.minimum_free_bytes,
        maximum_output_bytes=config.protocol.maximum_output_bytes,
        read_only=read_only,
    )


def _source_unchanged(provenance, project_root):
    if (
        numerical_package_code_sha256() != provenance.code_sources_sha256
        or selected_dependency_lock_sha256(project_root) != provenance.dependency_lock_sha256
    ):
        raise ValueError("RC producing source or dependency lock changed during the selected run")


def _receipt(config, writer, task_id):
    run_id = rc_chain_run_id(config)
    return ExternalTaskReceiptStore(writer).read_by_receipt_id(
        run_id, task_id, f"receipt.{run_id}.{task_id}.attempt-001"
    )


def _present(config, summary, provenance):
    run_id = rc_chain_run_id(config)
    return {
        "run_id": run_id,
        "config_sha256": config.fingerprint(),
        "summary_sha256": summary.fingerprint(),
        "summary": summary.to_document()["value"],
        "producing_provenance_sha256": provenance.fingerprint(),
        "producing_code_sha256": provenance.code_sources_sha256,
        "dependency_lock_sha256": provenance.dependency_lock_sha256,
        "observed_producing_git_head": provenance.observed_git_head,
        "observed_producing_checkout_clean": provenance.observed_checkout_clean,
        "retained_directory": f"runs/{run_id}",
        "scientific_authority": "NONE",
        "qualification": "NOT_ESTABLISHED",
    }


def read_rc_chain(*, config, artifact_writer, implementation_commit=None):
    """Authenticate every assigned unit and recompute only the retained reduction."""
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import (
        summarize_chain,
        verify_unit_result,
    )

    prove_rc_chain(config)
    producing_receipt = _receipt(config, artifact_writer, "producing-provenance")
    if producing_receipt is None:
        raise ValueError("RC chain lacks its actual producing-provenance receipt")
    producing_commit = producing_receipt.implementation_commit
    if implementation_commit is not None and implementation_commit != producing_commit:
        raise ValueError("RC selected implementation commit differs from its actual producing receipt")
    custody = _custody(config, artifact_writer, producing_commit, read_only=True)
    provenance = custody.load("producing-provenance", NumericalProducingProvenance)
    summary = custody.load("terminal", RCChainSummary)
    if provenance is None or summary is None:
        raise ValueError("RC chain lacks its complete terminal/provenance receipts; preserve and resume the same input")
    authenticate_recorded_matrix_provenance(provenance)
    if provenance.observed_git_head != producing_commit:
        raise ValueError("RC retained provenance differs from the receipt implementation commit")
    results = []
    for unit in config.units:
        result = custody.load(unit.unit_id, RCChainUnitResult)
        if result is None:
            raise ValueError("RC terminal omits a completed assigned-unit receipt")
        verify_unit_result(config, result)
        if result.unit_id != unit.unit_id:
            raise ValueError("RC receipt substitutes another assigned unit")
        results.append(result)
    expected = summarize_chain(config, tuple(results))
    if summary != expected:
        raise ValueError("RC terminal differs from its complete retained unit reduction")
    return _present(config, summary, provenance)


def run_rc_chain(*, config, artifact_writer, project_root: Path, implementation_commit, progress=None):
    """Run each assigned unit once; unknown contact refuses automatic repetition."""
    from empirical_lawhood.adapters.methods.rc_prerequisite_chain.science import (
        evaluate_unit,
        summarize_chain,
        verify_unit_result,
    )

    started = monotonic()
    prove_rc_chain(config)
    preflight_development_native_store(
        artifact_writer, minimum_free_bytes=config.protocol.minimum_free_bytes
    )
    if _receipt(config, artifact_writer, "terminal") is not None:
        return read_rc_chain(config=config, artifact_writer=artifact_writer)
    custody = _custody(config, artifact_writer, implementation_commit)
    if custody.load("terminal", RCChainSummary) is not None:
        return read_rc_chain(
            config=config, artifact_writer=artifact_writer,
            implementation_commit=implementation_commit,
        )
    from threadpoolctl import threadpool_limits

    with threadpool_limits(limits=1):
        observed = capture_matrix_provenance(project_root=project_root)
        if observed.observed_git_head != implementation_commit:
            raise ValueError("RC execution requires its actually observed checkout commit")
        provenance = custody.load("producing-provenance", NumericalProducingProvenance)
        if provenance is None:
            provenance = custody.retain("producing-provenance", observed)
        elif (
            provenance.code_sources_sha256 != observed.code_sources_sha256
            or provenance.dependency_lock_sha256 != observed.dependency_lock_sha256
            or provenance.runtime_observation_json != observed.runtime_observation_json
            or provenance.observed_git_head != observed.observed_git_head
        ):
            raise ValueError("RC recovery changes the actual producing source, lock or numerical runtime")
        results = []
        retained_bytes = len(config.canonical_bytes()) + len(provenance.canonical_bytes())
        for unit in config.units:
            result = custody.load(unit.unit_id, RCChainUnitResult)
            if result is None:
                if monotonic() - started >= float(config.protocol.maximum_elapsed_seconds):
                    raise ValueError("RC development invocation exhausted its wall-time budget before native contact")
                _source_unchanged(provenance, project_root)
                preflight_development_native_store(
                    artifact_writer, minimum_free_bytes=config.protocol.minimum_free_bytes
                )
                if retained_bytes + config.protocol.maximum_output_bytes > config.protocol.maximum_aggregate_output_bytes:
                    raise ValueError("RC development outputs exceed the complete aggregate byte budget")
                custody.begin_native_effect(unit.unit_id)
                result = evaluate_unit(config, unit.unit_id)
                verify_unit_result(config, result)
                custody.retain(unit.unit_id, result)
            else:
                verify_unit_result(config, result)
            if result.unit_id != unit.unit_id:
                raise ValueError("RC completed record substitutes another assigned unit")
            retained_bytes += len(result.canonical_bytes())
            if retained_bytes > config.protocol.maximum_aggregate_output_bytes:
                raise ValueError("RC retained payload census exceeds its aggregate byte budget")
            results.append(result)
            if progress is not None:
                progress(len(results), len(config.units))
        _source_unchanged(provenance, project_root)
        summary = summarize_chain(config, tuple(results))
        if retained_bytes + len(summary.canonical_bytes()) > config.protocol.maximum_aggregate_output_bytes:
            raise ValueError("RC terminal output exceeds the complete aggregate byte budget")
        _source_unchanged(provenance, project_root)
        custody.retain("terminal", summary)
    return _present(config, summary, provenance)
