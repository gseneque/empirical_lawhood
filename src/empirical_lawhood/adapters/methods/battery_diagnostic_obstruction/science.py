# SPDX-License-Identifier: MPL-2.0
"""Pure retained-history joins; no native provider or absent scientific result."""

from hashlib import sha256
import json
from math import isfinite
import re
from empirical_lawhood.adapters.methods.battery_dfn_precision_diagnostic.contracts import (
    DiagnosticSource,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry import (
    science as original_science,
)
from empirical_lawhood.adapters.methods.battery_thermal_inquiry.contracts import (
    BatteryInquirySupply,
    scope as original_scope,
)
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import AssessmentDisposition as A
from empirical_lawhood.runtime.artifacts import ArtifactManifest
from empirical_lawhood.runtime.native_effects import NativeEffectContact
from empirical_lawhood.runtime.plans import DevelopmentExecutionPlan
from empirical_lawhood.runtime.recovery import (
    DevelopmentRunRecoveryIndex,
    DevelopmentRunRecoveryTerminalEvent,
    TaskRecoveryEvent,
)
from . import contracts as c

CODECS = {
    "contact": NativeEffectContact,
    "event": TaskRecoveryEvent,
    "index": DevelopmentRunRecoveryIndex,
    "plan": DevelopmentExecutionPlan,
    "terminal": DevelopmentRunRecoveryTerminalEvent,
}


def scope(source):
    """History concerns the original model/source; it supplies no new endpoint."""
    return original_scope(source.diagnostic_source.original)


def validate_source(source):
    if type(source) is not c.ObstructionSource:
        raise ValueError("obstruction requires its new typed source")
    source.__post_init__()
    members = {r.relative_path: r for r in source.complete_custody}
    records = {}
    for r in source.records:
        raw, raw_manifest = r.raw_utf8.encode(), r.manifest_raw_utf8.encode()
        for path, data in (
            (r.relative_path, raw),
            (r.relative_path + ".manifest.json", raw_manifest),
        ):
            member = members.get(path)
            if member is None or (member.size_bytes, member.sha256) != (
                len(data),
                sha256(data).hexdigest(),
            ):
                raise ValueError(
                    "obstruction primary record/manifest differs from full original custody census"
                )
        manifest = decode_canonical_bytes(
            raw_manifest, ArtifactManifest, maximum_bytes=None
        )
        if (
            manifest.materialization.relative_path != r.relative_path
            or manifest.materialization.physical_sha256 != sha256(raw).hexdigest()
            or manifest.materialization.size_bytes != len(raw)
            or manifest.logical.content_sha256 != sha256(raw).hexdigest()
            or manifest.logical.payload_schema != CODECS[r.role].SCHEMA
        ):
            raise ValueError(
                "obstruction primary history loses exact retained manifest/materialization joins"
            )
        records[r.role] = decode_canonical_bytes(
            raw, CODECS[r.role], maximum_bytes=None
        )
    plan, index, contact, terminal, event = (
        records[key] for key in ("plan", "index", "contact", "terminal", "event")
    )
    index.validate_plan(plan)
    if len(plan.tasks) != 1 or len(index.tasks) != 1:
        raise ValueError("obstruction substitutes exact singleton diagnostic plan")
    task = plan.tasks[0]
    if (
        task.task_id != "battery-dfn-precision-diagnostic.diagnose"
        or task.capability.capability_key != task.task_id
    ):
        raise ValueError("obstruction retypes unrelated native history as diagnostic")
    plan_identity = ObjectIdentity.from_record(plan.execution_plan_id, plan)
    index_identity = ObjectIdentity.from_record(index.recovery_index_id, index)
    if (
        contact.execution_plan != plan_identity
        or contact.execution_task != ObjectIdentity.from_record(task.task_id, task)
        or contact.run_id != index.run_id
        or contact.task_id != task.task_id
        or contact.implementation_commit != plan.implementation_commit
        or terminal.run_id != index.run_id
        or terminal.recovery_index != index_identity
        or terminal.operational_status != "BLOCKED"
        or terminal.completed_task_ids
        or terminal.failed_task_ids
        or terminal.blocked_task_ids != (task.task_id,)
        or len(terminal.attempts) != 1
    ):
        raise ValueError(
            "obstruction contact/plan/terminal are substituted or claim completion"
        )
    attempted = terminal.attempts[0]
    binding = index.tasks[0]
    if (
        len(binding.attempts) != 1
        or attempted.attempt_id != binding.attempts[0].attempt_id
        or contact.attempt_id != attempted.attempt_id
        or attempted.ordinal != 1
        or attempted.disposition.value != "BLOCKED"
        or attempted.reason_code != "unknown-completion"
        or attempted.receipt_id is not None
        or attempted.receipt_sha256 is not None
        or event.run_id != index.run_id
        or event.task_id != task.task_id
        or event.attempt_id != attempted.attempt_id
        or event.recovery_index != index_identity
        or event.attempt_ordinal != 1
        or event.disposition.value != "BLOCKED"
        or event.receipt_id is not None
        or event.output_materialization_ids
        or "unknown-completion" not in event.reason_codes
    ):
        raise ValueError(
            "obstruction loses authentic exact attempt and unknown-completion journal"
        )
    if binding.attempts[0].receipt_relative_path in members or any(
        output.relative_path in members for output in task.outputs
    ):
        raise ValueError(
            "obstruction cannot claim missing receipt/result when present in complete custody"
        )
    contacts = [
        path
        for path in members
        if path.startswith("runs/" + index.run_id + "/native-contacts/")
        and path.endswith(".json")
        and "/" not in path.split("/native-contacts/",1)[1]
        and not path.endswith(".manifest.json")
    ]
    if contacts != [
        next(r.relative_path for r in source.records if r.role == "contact")
    ]:
        raise ValueError(
            "obstruction hides or duplicates current native contact census"
        )
    inputs = {
        r.expected_payload_schema: r.expected_content_sha256
        for r in task.external_inputs
    }
    if (
        inputs.get(BatteryInquirySupply.SCHEMA)
        != source.prior_supply.object_fingerprint
        or inputs.get(DiagnosticSource.SCHEMA) != source.diagnostic_source.fingerprint()
    ):
        raise ValueError(
            "obstruction plan substitutes actual original source or negative supply"
        )
    expected_inputs = {r.logical_artifact_id: r for r in task.external_inputs}
    actual_inputs = {r.logical.logical_artifact_id: r for r in source.input_manifests}
    if (
        len(actual_inputs) != len(source.input_manifests)
        or actual_inputs.keys() != expected_inputs.keys()
    ):
        raise ValueError(
            "obstruction omits or duplicates complete actual native input materializations"
        )
    if (
        tuple(
            sorted(r.materialization.materialization_id for r in actual_inputs.values())
        )
        != contact.input_materialization_ids
    ):
        raise ValueError(
            "obstruction native contact substitutes actual input materialization census"
        )
    if contact.dependency_receipt_ids or task.dependency_task_ids:
        raise ValueError("obstruction adds undeclared diagnostic dependencies")
    for key, manifest in actual_inputs.items():
        expected = expected_inputs[key]
        member = members.get(manifest.materialization.relative_path)
        manifest_raw = manifest.canonical_bytes()
        manifest_member = members.get(
            manifest.materialization.relative_path + ".manifest.json"
        )
        if manifest_member is None or (
            manifest_member.size_bytes,
            manifest_member.sha256,
        ) != (len(manifest_raw), sha256(manifest_raw).hexdigest()):
            raise ValueError(
                "obstruction native input manifest differs from original sidecar bytes"
            )
        if (
            manifest.logical.payload_schema != expected.expected_payload_schema
            or manifest.logical.content_sha256 != expected.expected_content_sha256
            or manifest.materialization.physical_sha256
            != manifest.logical.content_sha256
            or member is None
            or (member.size_bytes, member.sha256)
            != (
                manifest.materialization.size_bytes,
                manifest.materialization.physical_sha256,
            )
        ):
            raise ValueError(
                "obstruction native input materialization differs from actual plan/full custody"
            )
    cost = json.loads(source.invocation_cost_raw_utf8)
    if (
        cost["full_durable_copy_exact"] is not True
        or cost["operational_member_count"] != len(members)
        or cost["operational_retained_bytes"]
        != sum(r.size_bytes for r in members.values())
        or cost["native_contacts"] != 1
    ):
        raise ValueError(
            "obstruction requires final exact custody/cost census of entered native invocation"
        )
    for field in ("cpu_seconds", "wall_seconds"):
        if (
            type(cost[field]) not in (float, int)
            or not isfinite(cost[field])
            or cost[field] < 0
        ):
            raise ValueError(
                "obstruction invocation cost must retain measured finite nonnegative windows"
            )
    if not re.search(
        r"global_oom[^\n]*pid=([1-9][0-9]*)", source.kernel_excerpt_raw_utf8
    ):
        raise ValueError(
            "selected kernel excerpt omits its host global OOM/PID evidence"
        )
    return records


def assess(source, prior):
    records = validate_source(source)
    if (
        type(prior) is not BatteryInquirySupply
        or c.identity(prior) != source.prior_supply
    ):
        raise ValueError(
            "obstruction substitutes authentic original negative MODEL supply"
        )
    prior.__post_init__()
    original_science.validate_supply(prior)
    if (
        prior.source != source.diagnostic_source.original
        or prior.disposition is not A.UNEVALUABLE
    ):
        raise ValueError(
            "obstruction promotes or substitutes original unresolved36/9 procedure"
        )
    if len(prior.traces) != 36 or len(prior.check.reference_checks) != 9:
        raise ValueError(
            "obstruction prunes original complete negative scientific denominator"
        )
    return c.ObstructionAssessment(
        "product." + c.NAMESPACE + ".history",
        source,
        c.identity(prior),
        records["index"].run_id,
        ObjectIdentity.from_record(records["plan"].execution_plan_id, records["plan"]),
        ObjectIdentity.from_record(
            "native-contact."
            + records["contact"].run_id
            + "."
            + records["contact"].task_id,
            records["contact"],
        ),
        ObjectIdentity.from_record(
            records["terminal"].terminal_event_id, records["terminal"]
        ),
    )


def validate_assessment(record):
    if type(record) is not c.ObstructionAssessment:
        raise ValueError(
            "history requires genuine obstruction assessment, not DiagnosticResult"
        )
    record.__post_init__()
    records = validate_source(record.source)
    expected = c.ObstructionAssessment(
        record.product_id,
        record.source,
        record.source.prior_supply,
        records["index"].run_id,
        ObjectIdentity.from_record(records["plan"].execution_plan_id, records["plan"]),
        ObjectIdentity.from_record(
            "native-contact."
            + records["contact"].run_id
            + "."
            + records["contact"].task_id,
            records["contact"],
        ),
        ObjectIdentity.from_record(
            records["terminal"].terminal_event_id, records["terminal"]
        ),
    )
    if record != expected:
        raise ValueError(
            "obstruction assessment changes its complete authentic history projection"
        )


def source_from_records(
    *,
    source_id,
    diagnostic_source,
    prior_supply,
    records,
    complete_custody,
    input_manifests,
    invocation_report_sha256,
    invocation_cost_raw_utf8,
    kernel_excerpt_raw_utf8,
):
    """Construct only from previously authenticated complete original custody.

    This pure constructor does not authenticate caller filesystem claims. The
    supported API intake must read the original guarded records/manifests,
    complete final inventory/report/cost and preserve exact original bytes.
    """
    source = c.ObstructionSource(
        source_id,
        diagnostic_source,
        prior_supply if type(prior_supply) is ObjectIdentity else c.identity(prior_supply),
        tuple(sorted(records, key=lambda r: r.role)),
        tuple(sorted(complete_custody, key=lambda r: r.relative_path)),
        tuple(sorted(input_manifests, key=lambda r: r.logical.logical_artifact_id)),
        invocation_report_sha256,
        invocation_cost_raw_utf8,
        kernel_excerpt_raw_utf8,
        sha256(kernel_excerpt_raw_utf8.encode()).hexdigest(),
    )
    validate_source(source)
    return source
