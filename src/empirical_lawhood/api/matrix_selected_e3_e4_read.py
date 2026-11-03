# SPDX-License-Identifier: MPL-2.0
"""Receipt-based exposed DEV accounting, including incomplete native outcomes.

This is a thin read projection over the existing recursive product and contact
readers. It starts no work, creates no issue/qualification and reads no sealed
upstream CAL scores. Missing case products never shrink the original32x9 census.
"""

from dataclasses import replace

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r, selected_e3_e4_science as science
from empirical_lawhood.adapters.methods.matrix_scheduled_history.programme_reduction import ScheduledProgrammeNativeDisposition
from empirical_lawhood.api.matrix_training_provenance import original_comparator_training
from empirical_lawhood.api.recursive_execution import _read_recursive_wave_with_roots
from empirical_lawhood.api.recursive_qualified_parents import _output_payload, MAX_PARENT_BYTES
from empirical_lawhood.infrastructure.native_effect_custody import ExternalNativeEffectContactStore
from empirical_lawhood.kernel.decoding import decode_canonical_bytes_with_identity
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.runtime.recursive_compiler import decode_recursive_config_input
from .matrix_read_indexes import product_record_index, unique_index


def _record_bytes(writer, products, task, kind, *, original_input_access=None, product_lookup=None):
    """Authenticate actual custody before transferring bytes to a decoder."""
    if product_lookup is None:
        product_lookup = product_record_index(products)
    rows = product_lookup.get((task, kind.SCHEMA), ())
    if not rows:
        return None
    if len(rows) != 1:
        raise ValueError("selected E4 read aliases one exact original scientific output")
    row, = rows
    receipt = products["receipts"].get(task)
    if receipt is None:
        raise ValueError("selected E4 read finds a product without its actual producer receipt")
    logicals = tuple(value for value in receipt.output_logical_artifacts if value.logical_artifact_id == row["logical_artifact_id"])
    if len(logicals) != 1:
        raise PermissionError("selected E4 read changes original complete development output scope")
    if (logicals[0].outcome_access, logicals[0].visibility_ceiling) != (r.DEV, r.EXPOSED):
        manifest = products.get('outputs', {}).get(row['logical_artifact_id'])
        if original_input_access is None or manifest is None or manifest.logical != logicals[0]:
            raise PermissionError('selected E4 protected product lacks its exact frozen output and current original access')
    if original_input_access is not None:
        original_input_access.require_current()
    raw = _output_payload(writer, receipt, logicals[0], MAX_PARENT_BYTES)
    if original_input_access is not None:
        original_input_access.require_current()
    return raw, row['sha256']


def _decode_record_bytes(payload, kind):
    if payload is None:
        return None
    raw, digest = payload
    decoded = decode_canonical_bytes_with_identity(raw, kind, maximum_bytes=MAX_PARENT_BYTES,
        expected_sha256=digest)
    if decoded.record.fingerprint() != decoded.content_sha256:
        raise ValueError("selected E4 read changes actual original canonical output bytes")
    return decoded.record


def _record(writer, products, task, kind, *, original_input_access=None, product_lookup=None):
    value = _decode_record_bytes(_record_bytes(writer, products, task, kind,
        original_input_access=original_input_access, product_lookup=product_lookup), kind)
    if original_input_access is not None:
        original_input_access.require_current()
    return value


def read_selected_e3_e4_development(*, directory, artifact_writer, allow_partial=False,
        _consume_original=None, _validate_authored=None, read_access=None):
    return _read_selected_e3_e4_development(directory=directory, artifact_writer=artifact_writer,
        allow_partial=allow_partial, _consume_original=_consume_original,
        _validate_authored=_validate_authored, read_access=read_access)


def _read_selected_e3_e4_development(*, directory, artifact_writer, allow_partial=False,
        _consume_original=None, _validate_authored=None, read_access=None):
    if type(allow_partial) is not bool:
        raise TypeError("selected E4 read requires an explicit partial-read choice")
    if _consume_original is not None and (not callable(_consume_original) or allow_partial):
        raise ValueError("original DEV scientific consumers require a complete ordinary read")
    if _validate_authored is not None and not callable(_validate_authored):
        raise TypeError("selected E4 owner preflight requires a callable")
    def validate_authored(*, packet, draft, source, payloads, run, plan, index):
        if _validate_authored is not None:
            _validate_authored(packet=packet, draft=draft, run=run, plan=plan)
        declarations = {value.capability_key: value for value in owner.operation_declarations()}
        entries = tuple(value for value in draft.operations if value.selection.capability_key == owner.NAMESPACE + ".entry")
        if len(entries) != 1 or draft.development_study is None or draft.prospective_draft is not None:
            raise PermissionError("selected E4 read requires original complete truthful DEV declaration")
        operation, = entries
        entry = decode_recursive_config_input(operation, declarations[operation.selection.capability_key].registration()).record
        if type(entry) is not owner.SelectedE3E4EntryConfig:
            raise PermissionError("selected E4 read changes original entry owner")
        return entry
    def original_consumer(**context):
        entry=selected_entry[0]
        access=getattr(context['payloads'], 'original_input_access', None)
        evidence=None
        if _consume_original is not None:
            from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
            from empirical_lawhood.runtime.prospective_experiment import source_filename
            if type(access) is not SelectedE3OriginalInputAccess:
                raise PermissionError('original DEV scientific consumer lacks its actual current original E3 access')
            access.require_current(artifact_writer=artifact_writer)
            raw=context['payloads'][source_filename(entry.evidence)]
            if len(raw)!=entry.evidence_size_bytes:
                raise PermissionError('original DEV scientific consumer changes exact entry evidence size')
            evidence=decode_canonical_bytes_with_identity(raw,r.SelectedE3E4Evidence,
                maximum_bytes=entry.evidence_size_bytes,expected_sha256=entry.evidence.object_fingerprint).record
            if (evidence.identity!=entry.evidence
                    or evidence.programme!=entry.programme.identity
                    or evidence.produced_input_parents!=entry.produced_input_parents
                    or evidence.produced_input_parents!=access.parents):
                raise PermissionError('original DEV scientific consumer substitutes its exact packet-bound evidence')
            access.require_current(artifact_writer=artifact_writer)
        return _development_result(artifact_writer=context['artifact_writer'],report=context['report'],
            products=context['products'],draft=context['draft'],plan=context['plan'],entry=entry,
            _consume_original=_consume_original,original_input_access=access,original_evidence=evidence)
    selected_entry=[]
    ordinary_validate=validate_authored
    def validate_authored(**values):
        entry=ordinary_validate(**values)
        selected_entry.append(entry)
        return entry
    base_only=_consume_original is not None or _validate_authored is not None
    selected, roots, entry = _read_recursive_wave_with_roots(directory=directory, artifact_writer=artifact_writer,
        include_products=True, terminal_product_format="compact", allow_partial=allow_partial,
        validate_authored=validate_authored,scientific_consumer=original_consumer if base_only else None,
        read_access=read_access)
    report, products, actual_draft, actual_plan = selected
    packet, draft, _, run, plan, _ = roots
    if (draft, plan, packet.fingerprint()) != (actual_draft, actual_plan, report["packet_sha256"]):
        raise PermissionError("selected E4 read changed actual retained packet or plan during authentication")
    result=report.get('scientific_result')
    if result is None:
        raise PermissionError('ordinary selected E4 read lacks its complete current scientific owner')
    return result


def _development_result(*,artifact_writer,report,products,draft,plan,entry,_consume_original=None,
        original_input_access=None,original_evidence=None):
    """Project one actual ordinary original context without recursively reading structure."""
    if _consume_original is not None:
        from empirical_lawhood.api.selected_e3_access import SelectedE3OriginalInputAccess
        if type(original_input_access) is not SelectedE3OriginalInputAccess or type(original_evidence) is not r.SelectedE3E4Evidence:
            raise PermissionError('original DEV scientific consumer requires its actual access and packet evidence')
    plan_pin = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    from functools import partial
    from empirical_lawhood.kernel.evidence import VisibilityCeiling
    from empirical_lawhood.runtime.artifacts import most_restrictive_outcome_access
    record = partial(_record, original_input_access=original_input_access,
        product_lookup=product_record_index(products))
    tasks = unique_index(plan.tasks, lambda task: task.task_id, label='execution task')
    protocols = unique_index(entry.bank.response_selection.protocols,
        lambda value: value.public_source.root.root_id, label='response protocol')
    panels_by_group = unique_index(entry.bank.response_selection.panels, lambda row: row[0], label='response panel')
    cases = []
    for case in entry.programme.cases:
        node = owner.local_node(case.root_id, "collect")
        completed = record(artifact_writer, products, node, r.SelectedE3E4CaseResult)
        if completed is not None:
            if (completed.root_id, completed.source, completed.group_id) != (case.root_id, case.source, case.independent_group_id):
                raise ValueError("selected E4 read substitutes an actual completed case/source/group")
            cases.append(completed)
            continue
        # Read original small native metadata only; no raw future array access
        # or reconstruction from an asserted success flag occurs in this path.
        observed_native = []
        for phase, kind in (("continue", r.SelectedE3E4FullHistory), ("prefix", r.SelectedE3E4PrefixHistory), ("responses", r.SelectedE3E4Responses)):
            task = owner.local_node(case.root_id, phase)
            value = record(artifact_writer, products, task, kind)
            event = None if value is None else (value.native[0] if phase == "responses" and value.native else
                None if phase == "responses" else value.native)
            if value is not None and value.source != case.source:
                raise ValueError("selected E4 read replaces an original native case subject")
            if event is not None:
                observed_native.append(ScheduledProgrammeNativeDisposition(phase, "COMPLETED", event.definition.identity,
                    ObjectIdentity.from_record(event.receipt.task_id + ".completion", event.completion),
                    ObjectIdentity.from_record(event.receipt.receipt_id, event.receipt), ()))
            elif value is not None and phase == "responses":
                observed_native.append(ScheduledProgrammeNativeDisposition(phase, "NOT_USED", None, None, None,
                    ("actual-retained-native-nonuse-" + value.disposition.lower(),)))
            else:
                if original_input_access is not None:
                    original_input_access.require_current()
                current_task = tasks[task]
                contacts = ExternalNativeEffectContactStore(plane=artifact_writer, execution_plan=plan_pin,
                    visibility_ceiling=VisibilityCeiling.most_restrictive(*(value.visibility_ceiling for value in current_task.outputs)),
                    outcome_access=most_restrictive_outcome_access(current_task.capability.requested_outcome_access,
                        *(value.outcome_access for value in current_task.outputs)))
                contact = contacts.read(report["run_id"], task)
                observed_native.append(ScheduledProgrammeNativeDisposition(phase, "UNKNOWN" if contact is not None else "UNENTERED",
                    None, None, None, ("actual-contact-without-complete-scientific-product",) if contact is not None else ("actual-native-unentered",)))
        account = record(artifact_writer, products, owner.local_node(case.root_id, "account"), r.SelectedE3E4AccountSeal)
        score = record(artifact_writer, products, owner.local_node(case.root_id, "response-score"), r.ScheduledResponseScore)
        numerical = record(artifact_writer, products, owner.local_node(case.root_id, "full-numerical"), r.SelectedE3E4NumericalAssessment)
        if account is not None and (account.source != case.source or account.design != entry.programme.forecast_design
                or account.original_package != entry.bank.forecast_design.package.original_package
                or account.original_calibration != entry.bank.forecast_design.package.calibration):
            raise ValueError("selected E4 incomplete read replaces an actual pre-future selected account")
        if score is not None and (score.source != case.source or account is None or score.error_forecast != account.identity):
            raise ValueError("selected E4 incomplete read replaces actual source/account/score lineage")
        if numerical is not None and (numerical.source != case.source or numerical.phase != "full"):
            raise ValueError("selected E4 incomplete read replaces actual full numerical assessment")
        protocol = protocols[case.root_id]
        panels = panels_by_group[case.independent_group_id][1]
        from empirical_lawhood.adapters.methods.matrix_scheduled_history.paired_target_reduction import target_contract
        contract = target_contract(protocol)
        targets = (None,) * r.selected_target_shape(contract)[2] if score is None else science.paired_targets(score, protocol, panels)
        cases.append(incomplete_case(case, products=products, task_census=report["task_census"], native=tuple(observed_native),
            account=account, score=score, full_numerical=numerical, paired_targets=targets, target_contract=contract))
    reduction = science.reduce_cases(entry.programme, tuple(cases), record_id="reduction." + entry.programme.programme_id)
    retained = record(artifact_writer, products, owner.global_node(entry.programme, "reduce"), r.SelectedE3E4DevelopmentReduction)
    if retained is not None and retained != reduction:
        raise ValueError("selected E4 read differs from actual original complete reduction")
    if _consume_original is not None:
        if (products.get("terminal") is None or tuple(row.root_id for row in cases)!=tuple(row.root_id for row in entry.programme.cases)):
            raise PermissionError("original DEV scientific consumer lacks a complete authenticated terminal case census")
        if original_input_access is not None:
            original_input_access.require_current()
        _consume_original(writer=artifact_writer,products=products,plan=plan,draft=draft,entry=entry,
            bank=entry.bank,cases=tuple(cases),run_id=report["run_id"],
            original_input_access=original_input_access,original_evidence=original_evidence)
    if original_input_access is not None:
        original_input_access.require_current()
    return {"run_id": report["run_id"], "packet_sha256": report["packet_sha256"], "operational_status": report["status"], "assigned_groups": len(entry.programme.group_ids),
        "assigned_cases": len(entry.programme.cases), "original_acquisition_task_count": len(plan.tasks), "scientific_standing": reduction.scientific_standing, "uncertainty_status": reduction.uncertainty_status,
        "qualification": "NOT_ESTABLISHED", "new_native_contact_count": 0,
        "original_comparator_training": original_comparator_training(entry.bank.forecast_design.package),
        "reduction": reduction.to_document(),
        **({"operational_native_continuation": report["operational_native_continuation"]}
            if "operational_native_continuation" in report else {})}


def incomplete_case(case, *, products, task_census, native, account=None, score=None, full_numerical=None, paired_targets=None, target_contract="PAIRED15"):
    """Project actual reader-shaped failures, which have no scientific receipt.

    The authenticated recursive reader supplies the latest task census and the
    separate original attempt/recovery records. Its successful scientific
    receipt map alone cannot establish the failure or its absence.
    """
    tasks = {owner.local_node(case.root_id, phase) for phase in owner.PHASES if phase not in ("entry", "reduce")}
    statuses = {value["task_id"]: value["operational_status"] for value in task_census if value["task_id"] in tasks}
    failed = "FAILED" in statuses.values()
    unknown = any(value.disposition == "UNKNOWN" for value in native)
    receipts = {value.receipt_id: value for value in (*products["receipts"].values(),
        *products.get("attempt_receipts", {}).values()) if value.task_id in tasks}
    events = tuple(sorted((ObjectIdentity.from_record(value.event_id, value) for value in products.get("recovery_events", {}).values()
        if value.task_id in tasks), key=lambda value: value.object_id))
    baseline = r.SelectedE3E4CaseResult.unentered(case, target_contract=target_contract)
    return replace(baseline, disposition="FAILED" if failed else "UNKNOWN" if unknown else "UNENTERED",
        numerical_disposition=("SATISFIED" if full_numerical.numerical_pass else "VIOLATED") if full_numerical is not None else
            "UNKNOWN" if statuses or unknown else "UNENTERED",
        score_disposition=score.disposition if score is not None else "FAILED" if failed else "UNKNOWN" if unknown else "UNENTERED",
        paired_log_targets=baseline.paired_log_targets if paired_targets is None else paired_targets,
        original_log_points=baseline.original_log_points if account is None else account.log_points,
        forecast=None if account is None else account.identity, score=None if score is None else r.identity(score),
        full_assessment=None if full_numerical is None else r.identity(full_numerical),
        ordinary_receipts=tuple(sorted((ObjectIdentity.from_record(value.receipt_id, value) for value in receipts.values()),
            key=lambda value: value.object_id)), native=native, operational_events=events,
        reason_codes=("complete-original-case-not-retained",))
