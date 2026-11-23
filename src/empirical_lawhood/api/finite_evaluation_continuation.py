# SPDX-License-Identifier: MPL-2.0
"""Select the failed evaluation's actual pre-parent controls and acquired source publications."""

from decimal import Decimal
from hashlib import sha256

from empirical_lawhood.adapters.simulators.finite_response_law.locked_evaluation import (
    CONTROL_RESULTS,
    FiniteResponseLawLockedEvaluationRetention,
    FiniteResponseLawRetainedChoice,
)
from empirical_lawhood.design.source_qualification import (
    ProspectiveRetainedContinuation,
    ProspectiveRetainedPredecessor,
)
from empirical_lawhood.domains.matrix.finite_response_law.contracts import (
    native_invocations,
)
from empirical_lawhood.domains.matrix.finite_response_law.control_provider import (
    control_tasks,
)
from empirical_lawhood.execution.recovery import RunRecoveryIndex
from empirical_lawhood.science.evidence.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.science.identity.references import ArtifactIdentity
from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.storage.recovery import ExternalRunRecoveryStore
from empirical_lawhood.storage.task_receipts import ExternalTaskReceiptStore


def retained_evaluation_operands(
    packet, publication, artifact_writer, *, publisher=None
):
    """Reconstruct every import from the immutable terminal and its successful receipts.

    On initial authoring, publish bounded exact members to the ordinary content-addressed
    store. The issued import capability authenticates the original receipt and full typed
    members again at consumption. Recompiling a handoff reads the receipt census only.
    """
    from empirical_lawhood.api import finite_rerun_authoring as app

    if packet.stage != "prospective-evaluation" or packet.control is None:
        raise ValueError(
            "Locked continuation requires the assigned evaluation and its original controls"
        )
    source, run = packet.source, publication.run_id
    native = {
        t.task_id: t
        for t in native_invocations(source)
        if t.phase in ("prefix", "parent")
    }
    controls = control_tasks(packet.control)
    import_ids = set(native) | {
        key for key, (_, op) in controls.items() if op in CONTROL_RESULTS
    }
    (prior,) = (key for key, (_, op) in controls.items() if op == "freeze-prior")
    joins = {key for key, (_, op) in controls.items() if op == "join-parent"}
    with artifact_writer.read_context() as plane:
        issued, _, (package, _, plan) = app._authenticate_current_publication(
            publication, plane, expected_run=run, include_controls=True
        )
        app._require_issued_source(
            issued,
            source,
            plane,
            nomination=packet.nomination,
            expected_config=packet.control,
        )
        original_design = issued.base.authoring_package.draft
        if (
            original_design.development_unit_ids != packet.original_prior_unit_ids
            or original_design.development_seed_ids != packet.original_prior_seed_ids
        ):
            raise ValueError(
                "Retained evaluation changes the actual original design-exposure ledger"
            )
        recovery = ExternalRunRecoveryStore(plane)
        relative = f"runs/{run}/recovery/wave.{package.package_id}/resource-run-recovery-index.json"
        index = recovery.read_index(relative, expected_schema=RunRecoveryIndex.SCHEMA)
        terminal = recovery.read_terminal(index)
        tasks = {t.task_id: t for t in plan.tasks}
        if (
            index.execution_plan
            != ObjectIdentity.from_record(plan.execution_plan_id, plan)
            or index.implementation_commit
            != issued.source_closure.implementation_commit
            or terminal is None
            or terminal.run_id != run
            or terminal.operational_status != "FAILED"
            or set(terminal.completed_task_ids) != import_ids | {prior}
            or set(terminal.failed_task_ids) != joins
            or set(terminal.blocked_task_ids)
            != tasks.keys() - import_ids - joins - {prior}
        ):
            raise ValueError(
                "Expected every original pre-parent choice and parent, with no downstream acquisition"
            )
        attempts = {a.task_id: a for a in terminal.attempts}
        bindings = {b.task_id: b for b in index.tasks}
        if (
            tasks.keys() != attempts.keys()
            or len(attempts) != len(terminal.attempts)
            or tasks.keys() != bindings.keys()
            or any(len(b.attempts) != 1 for b in bindings.values())
        ):
            raise ValueError(
                "Original terminal does not cover its complete single-attempt roster"
            )
        receipts = ExternalTaskReceiptStore(plane)
        prefixes, parents, choices = [], [], []
        for key in sorted(import_ids):
            attempt = attempts[key]
            (candidate,) = bindings[key].attempts
            receipt = receipts.read(run, key, candidate.attempt_id)
            if (
                receipt is None
                or candidate.attempt_id != attempt.attempt_id
                or receipt.receipt_id != attempt.receipt_id
                or receipt.fingerprint() != attempt.receipt_sha256
            ):
                raise ValueError(
                    "Locked continuation lost a successful original receipt"
                )
            recovery._validate_receipt_static(index, tasks[key], candidate, receipt)
            logical = {
                a.logical_artifact_id: a for a in receipt.output_logical_artifacts
            }
            artifacts = []
            for material in receipt.output_materializations:
                member = logical[material.logical_artifact_id]
                if (
                    material.physical_sha256 != member.content_sha256
                    or material.partition_selector is not None
                    or material.compression != "none"
                    or member.outcome_access is not OutcomeAccess.OUTCOME_BLIND
                    or member.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE
                ):
                    raise ValueError(
                        "Retained member must be the original, complete, outcome-blind publication"
                    )
                artifact = ArtifactIdentity(
                    member.logical_artifact_id,
                    "retained-evaluation-member",
                    member.payload_schema,
                    member.content_sha256,
                    member.media_type,
                    material.size_bytes,
                )
                if publisher is not None:
                    raw = read_bounded_bytes(
                        plane.root.resolve(material.relative_path, for_write=False),
                        maximum_bytes=artifact.size_bytes,
                    )
                    if (
                        len(raw) != artifact.size_bytes
                        or sha256(raw).hexdigest() != artifact.sha256
                    ):
                        raise ValueError(
                            "Retained bytes differ from their receipted identity"
                        )
                    publisher.publish(raw, maximum_bytes=artifact.size_bytes)
                artifacts.append(artifact)
            ordered = tuple(sorted(artifacts, key=lambda a: a.artifact_id))
            receipt_bytes = receipt.canonical_bytes()
            witness = ArtifactIdentity(
                receipt.receipt_id,
                "retained-evaluation-receipt",
                receipt.SCHEMA,
                attempt.receipt_sha256,
                "application/json",
                len(receipt_bytes),
            )
            if publisher is not None:
                publisher.publish(receipt_bytes, maximum_bytes=witness.size_bytes)
            if key in native:
                inv = native[key]
                common = (
                    key,
                    inv.root.physical_unit_id,
                    "finite-response-law.reference-clock",
                    Decimal(inv.clocks[1]),
                    tuple(f"{inv.root.root_id}.flh-project.r{v}" for v in (1, 2)),
                    ordered,
                    witness,
                    OutcomeAccess.OUTCOME_BLIND,
                    VisibilityCeiling.PROSPECTIVE,
                )
                if inv.phase == "prefix":
                    prefixes.append(ProspectiveRetainedPredecessor(*common))
                else:
                    parents.append(
                        ProspectiveRetainedContinuation(
                            *common, inv.predecessor_segment_id, Decimal(inv.clocks[0])
                        )
                    )
            else:
                (product,) = ordered
                choices.append(FiniteResponseLawRetainedChoice(key, product, witness))
        app._require_current_grants(publication, plane)
        closeout = ArtifactIdentity(
            terminal.terminal_event_id,
            "original-failed-terminal",
            terminal.SCHEMA,
            terminal.fingerprint(),
            "application/json",
            len(terminal.canonical_bytes()),
        )
        return FiniteResponseLawLockedEvaluationRetention(
            source,
            run,
            closeout,
            tuple(prefixes),
            tuple(parents),
            tuple(choices),
            publication.issued_study,
            publication.execution_authority,
            publication.reveal_authority,
            ObjectIdentity.from_record(terminal.terminal_event_id, terminal),
        )


def require_evaluation_attestation(candidate, attestation, publisher, *, records=None):
    """Only the original blind assignment can authorize completing acquired evaluation roots."""
    from empirical_lawhood.design.study_issue import (
        HumanProposerAttestation,
        RetainedEvaluationProposerAttestation,
    )
    from empirical_lawhood.execution.candidate_compiler import ExecutableStudyCandidate
    from empirical_lawhood.adapters.simulators.finite_response_law.evaluation_continuation.discovery import (
        LOCKED_IMPORT_CAPABILITY,
        SOURCE_CAPABILITY,
    )
    from empirical_lawhood.adapters.simulators.finite_response_law.evaluation.discovery import (
        SOURCE_CAPABILITY as ORIGINAL_SOURCE,
    )

    extension = isinstance(candidate, ExecutableStudyCandidate)
    standard = candidate.base_candidate if extension else candidate
    steps = {s.step_id: s for s in standard.base_candidate.protocol.steps}
    imports = {
        key
        for key, s in steps.items()
        if s.config.config_schema == FiniteResponseLawLockedEvaluationRetention.SCHEMA
    }
    if not imports and not isinstance(
        attestation, RetainedEvaluationProposerAttestation
    ):
        return
    if (
        not isinstance(attestation, RetainedEvaluationProposerAttestation)
        or len(imports) != 320
    ):
        raise ValueError(
            "A locked evaluation continuation requires an explicit declaration of retained exposure"
        )
    original = publisher.load_executable_study(
        attestation.original_issue.object_id
    ).manifest
    past = (
        original.extension_proposer_attestation
        if extension
        else original.base.proposer_attestation
    )
    if (
        ObjectIdentity.from_record(original.issue_id, original)
        != attestation.original_issue
        or type(past) is not HumanProposerAttestation
        or not past.evaluation_units_and_seeds_unexposed
        or past.proposer_id != attestation.proposer_id
        or past.proposer != attestation.proposer
        or ObjectIdentity.from_record(past.attestation_id, past)
        != attestation.original_attestation
    ):
        raise ValueError(
            "Continued evaluation must bind the original owner's blinded assignment"
        )
    prior = {
        s.step_id: s for s in original.base.candidate.base_candidate.protocol.steps
    }
    expected = {
        key
        for key in prior
        if key.endswith((".prefix.native", ".parent.native"))
        or key.rsplit(".", 1)[-1] in CONTROL_RESULTS
    }
    if imports != expected or steps.keys() != prior.keys() or len(steps) != 1796:
        raise ValueError("Continuation changes the original task or choice inventory")
    for key, step in steps.items():
        old = prior[key]
        if key in imports:
            if (
                step.capability_key != LOCKED_IMPORT_CAPABILITY.capability_key
                or step.stage.value != "FREEZE"
                or step.dependency_step_ids
                != (
                    old.dependency_step_ids
                    if key.rsplit(".", 1)[-1] in CONTROL_RESULTS
                    else ()
                )
                or step.requested_outcome_access is not OutcomeAccess.OUTCOME_BLIND
                or (
                    step.config.config_id,
                    step.config.config_schema,
                    step.config.content_sha256,
                )
                != (
                    attestation.retained_inputs.object_id,
                    attestation.retained_inputs.object_schema,
                    attestation.retained_inputs.object_fingerprint,
                )
            ):
                raise ValueError(
                    "Continued evaluation must import its complete sealed commitments"
                )
        elif step.capability_key != (
            SOURCE_CAPABILITY.capability_key
            if old.capability_key == ORIGINAL_SOURCE.capability_key
            else old.capability_key
        ) or (
            step.config,
            step.dependency_step_ids,
            step.outputs,
            step.requested_outcome_access,
            step.maximum_attempts,
        ) != (
            old.config,
            old.dependency_step_ids,
            old.outputs,
            old.requested_outcome_access,
            old.maximum_attempts,
        ):
            raise ValueError(
                "Continued evaluation changes a remaining scientific operation"
            )
    if records is not None:
        (config,) = (
            r for r in records if type(r) is FiniteResponseLawLockedEvaluationRetention
        )
        if (
            ObjectIdentity.from_record(config.config_id, config)
            != attestation.retained_inputs
            or config.issued_study != attestation.original_issue
            or config.terminal != attestation.original_terminal
        ):
            raise ValueError(
                "Continuation attestation differs from its issued operand selection"
            )
