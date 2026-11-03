# SPDX-License-Identifier: MPL-2.0
"""Receipt-bound inquiry projection and decisions, independent of optional export."""

from hashlib import sha256
from pathlib import Path

from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
from empirical_lawhood.api.recursive_authoring import author_recursive_wave, implementation_binding, load_authored_wave
from empirical_lawhood.api.recursive_execution import (
    validate_recursive_worker_controls, _validate_terminal_product_format, read_recursive_wave, run_recursive_wave,
)
from empirical_lawhood.runtime.artifacts import artifact_custody_limits
from empirical_lawhood.infrastructure.bounded_io import read_bounded_bytes
from empirical_lawhood.infrastructure.development_native_custody import read_development_native_payload
from empirical_lawhood.infrastructure.task_receipts import decode_artifact_manifest
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.recursive_inquiry import (
    AcquisitionEvent, InquiryAttempt, InquiryAttemptStatus, InquiryCost, InquiryDecision,
    InquiryEvidence, InquirySpecification, InquiryState, InquirySuccessorIntent, identity,
)
from empirical_lawhood.kernel.recursive_inquiry_policy import (
    InquiryAttemptWorkBinding, RobustInquirySpecification, ScientificInquiryWork, WorkBoundInquiryState,
    WorkBoundInquiryDecision,
)
from empirical_lawhood.planning.campaigns import CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_inquiry import (
    InquiryAction, InquiryMenu, InquiryPolicy, choose_inquiry, make_successor_intent,
    validate_inquiry_join, validate_inquiry_revision,
)
from empirical_lawhood.planning.recursive_inquiry_policy import (
    RobustInquiryDecision, RobustInquiryMenu, RobustInquiryPolicy,
    choose_robust_inquiry, make_robust_successor_intent, validate_robust_inquiry_join,
    validate_robust_inquiry_revision,
)
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ArtifactWriteRequest
from empirical_lawhood.runtime.recursive_handoff import RecursiveImplementationBinding, RecursiveWaveMember
from empirical_lawhood.runtime.recursive_inquiry import (
    InquiryDecisionPacket, InquiryDecisionRequest, InquiryStateSources, InquirySuccessorAdmission,
    RobustInquiryDecisionPacket, RobustInquiryDecisionRequest,
    WorkBoundInquiryDecisionPacket, WorkBoundInquiryDecisionRequest,
)

_CODECS = {"specification.json": InquirySpecification, "state.json": InquiryState,
           "sources.json": InquiryStateSources, "menu.json": InquiryMenu, "policy.json": InquiryPolicy,
           "campaign.json": CampaignSpec, "right.json": DecisionRight, "decision.json": InquiryDecision,
           "implementation.json": RecursiveImplementationBinding, "intent.json": InquirySuccessorIntent}
_ROBUST_CODECS = dict(_CODECS, **{"specification.json": RobustInquirySpecification,
    "menu.json": RobustInquiryMenu, "policy.json": RobustInquiryPolicy,
    "decision.json": RobustInquiryDecision})
_WORK_BOUND_CODECS = dict(_ROBUST_CODECS, **{"state.json": WorkBoundInquiryState,
                                         "decision.json": WorkBoundInquiryDecision})


def _decode_versioned(payload, codecs, *, maximum_bytes):
    """Dispatch only closed installed schema/version pairs, then enforce exact bytes."""
    from empirical_lawhood.adapters._strict_json import loads_external_json
    document = loads_external_json(payload)
    if not isinstance(document, dict):
        raise ValueError("inquiry input requires a canonical record envelope")
    matches = [codec for codec in codecs
               if (codec.SCHEMA, codec.VERSION) == (document.get("schema"), document.get("version"))]
    if len(matches) != 1:
        raise ValueError("unsupported inquiry schema/version")
    return decode_canonical_bytes(payload, matches[0], maximum_bytes=maximum_bytes)


def decode_inquiry_decision_request(payload):
    return _decode_versioned(payload, (InquiryDecisionRequest, RobustInquiryDecisionRequest, WorkBoundInquiryDecisionRequest),
                             maximum_bytes=max(1, len(payload)))


def _policy_owners(specification, menu, policy, state=None):
    if (type(specification), type(menu), type(policy)) == (
        InquirySpecification, InquiryMenu, InquiryPolicy
    ):
        return choose_inquiry, make_successor_intent, InquiryDecisionPacket, validate_inquiry_join
    if (type(specification), type(menu), type(policy)) == (
        RobustInquirySpecification, RobustInquiryMenu, RobustInquiryPolicy
    ):
        packet = WorkBoundInquiryDecisionPacket if type(state) is WorkBoundInquiryState else RobustInquiryDecisionPacket
        return choose_robust_inquiry, make_robust_successor_intent, packet, validate_robust_inquiry_join
    raise ValueError("inquiry specification/menu/policy versions do not join")


def _publish(writer, directory, name, record, packet_id):
    root = Path(writer.root.contract.canonical_path)
    relative = Path(directory).relative_to(root).as_posix()
    return writer.write(ArtifactWriteRequest(packet_id + "." + name.removesuffix(".json"),
        relative + "/" + name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, "application/json",
        packet_id, relative, record.canonical_bytes(), VisibilityCeiling.DEVELOPMENT_ONLY,
        (), OutcomeAccess.DEVELOPMENT_VISIBLE))


def _read(writer, relative, codec):
    codecs = codec if isinstance(codec, tuple) else (codec,)
    path = writer.root.resolve(relative, for_write=False)
    manifest = decode_artifact_manifest(read_bounded_bytes(Path(str(path) + ".manifest.json"), maximum_bytes=artifact_custody_limits(writer).manifest_bytes), maximum_bytes=artifact_custody_limits(writer).manifest_bytes)
    if (manifest.materialization.relative_path != relative
            or any(manifest.logical.payload_schema != item.SCHEMA for item in codecs)
            or manifest.logical.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or manifest.logical.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("inquiry member changes its exact path, schema or evidence permissions")
    # The authenticated manifest supplies the exact read bound. A larger retained
    # state must not become unreadable at an unrelated fixed member-size ceiling.
    size = max(1, manifest.materialization.size_bytes)
    return _decode_versioned(read_development_native_payload(writer, manifest, maximum_bytes=size),
                             codecs, maximum_bytes=size)


def _merge(rows, record, object_id):
    if object_id in rows and rows[object_id] != record:
        raise ValueError("inquiry projection substitutes a retained identity")
    rows[object_id] = record


def _inquiry_history_sources(*, sources, root, artifact_writer):
    """Authenticate the predecessor DAG and retain its declared source witnesses."""
    histories, active = {}, set()

    def visit(relative):
        if relative in active:
            raise ValueError("inquiry predecessor history cycles")
        if relative in histories:
            return
        active.add(relative)
        _, records = read_inquiry_decision(directory=root / relative,
            artifact_writer=artifact_writer, revalidate_sources=False)
        for parent in records["sources.json"].previous_decision_paths:
            visit(parent)
        active.remove(relative)
        histories[relative] = records

    for relative in sources.previous_decision_paths:
        visit(relative)
    waves = {}
    for selected in (*[record["sources.json"] for record in histories.values()], sources):
        for wave in selected.waves:
            old = waves.get(wave.relative_path)
            if old is not None and old.packet != wave.packet:
                raise ValueError("inquiry history substitutes an authored wave packet")
            if old is None or wave.include_products:
                waves[wave.relative_path] = wave
    return histories, tuple(waves[path] for path in sorted(waves))


def _inquiry_parent_depth(*, payloads, draft, artifact_writer):
    """Derive depth from authenticated portable ancestry, never from a parent boolean."""
    if not draft.contribution_parents:
        return 1
    from empirical_lawhood.api.recursive_contributions import authenticate_recursive_contribution
    from empirical_lawhood.runtime.recursive_handoff import recursive_parent_closure_bindings
    bindings = recursive_parent_closure_bindings(payloads)

    def depth(directory, writer, ancestors):
        _, transport, manifest, _, _, view = authenticate_recursive_contribution(
            directory=directory, artifact_writer=writer)
        key = identity(manifest, manifest.contribution_id)
        if key in ancestors:
            raise ValueError("inquiry contribution ancestry cycles")
        parent_depths = []
        parent_keys = []
        for path in transport.parent_closure_relative_paths:
            parent_depth, parent_key = depth(view.root.resolve(path, for_write=False), view, (*ancestors, key))
            parent_depths.append(parent_depth)
            parent_keys.append(parent_key)
        if set(parent_keys) != set(manifest.predecessors):
            raise ValueError("inquiry ancestry does not join exact contribution predecessors")
        return 1 + max(parent_depths, default=0), key

    depths, keys = [], []
    for binding in bindings:
        parent_depth, parent_key = depth(artifact_writer.root.resolve(binding.relative_path, for_write=False),
                                        artifact_writer, ())
        if parent_key != binding.contribution:
            raise ValueError("inquiry wave changes authenticated predecessor")
        depths.append(parent_depth)
        keys.append(parent_key)
    expected = tuple(identity(parent, parent.contribution_id) for parent in draft.contribution_parents)
    if tuple(keys) != expected:
        raise ValueError("inquiry wave changes its exact complete contribution parents")
    return 1 + max(depths)


def _inquiry_successor_depth(*, histories, completed_waves, native_depths):
    """Join actual authored drafts to retained intents; replay adds no lineage edge."""
    parents = {key: set() for key in completed_waves}
    for records in histories.values():
        intent = records.get("intent.json")
        if intent is None:
            continue
        for target, draft in completed_waves.items():
            if draft != intent.draft:
                continue
            for source in records["sources.json"].waves:
                if source.include_products and source.packet in completed_waves and source.packet != target:
                    parents[target].add(source.packet)
    memo = {}

    def depth(key, active):
        if key in active:
            raise ValueError("inquiry successor wave ancestry cycles")
        if key not in memo:
            memo[key] = max(native_depths[key],
                1 + max((depth(parent, (*active, key)) for parent in parents[key]), default=0))
        return memo[key]

    return max((depth(key, ()) for key in parents), default=0)


def _refine_inquiry_cost(previous, measured):
    """Explicit authenticated measurement may fill unknowns, never rewrite known costs."""
    if (previous.event_id, previous.attempt_id, previous.receipt) != (measured.event_id, measured.attempt_id, measured.receipt):
        raise ValueError("measured event does not join the complete actual attempt census")
    for field in ("cpu_seconds", "wall_seconds", "retained_bytes"):
        old, new = getattr(previous.cost, field), getattr(measured.cost, field)
        if old is not None and old != new:
            raise ValueError("measured event substitutes retained known expense")
    return measured


def _inquiry_attempt_status(census, operational):
    from empirical_lawhood.runtime.execution import TaskBlockReason
    reason = str(census["reason_code"])
    if reason.startswith(TaskBlockReason.UNKNOWN_COMPLETION.value) or reason.startswith("UNKNOWN_COMPLETION"):
        return InquiryAttemptStatus.UNCERTAIN_CONTACT
    if census.get("recovery_event_status") == "MISSING_TERMINAL_PRIMARY_NONATTEMPT":
        return InquiryAttemptStatus.NONATTEMPT
    if getattr(operational, "disposition", None) == "NOT_ATTEMPTED":
        return InquiryAttemptStatus.NONATTEMPT
    return {"SUCCEEDED": InquiryAttemptStatus.COMPLETED, "FAILED": InquiryAttemptStatus.FAILED,
            "BLOCKED": InquiryAttemptStatus.BLOCKED}[census["operational_status"]]


def _inquiry_current_attempt_status(census, operational, native_observations):
    """Current contact knowledge does not amend the original attempt or retry hold."""
    recorded = _inquiry_attempt_status(census, operational)
    native = native_observations.get(census["attempt_id"])
    if native is None:
        return recorded
    from empirical_lawhood.infrastructure.native_parent_finalization import NativeParentReturn
    if type(native) is not NativeParentReturn:
        raise TypeError("inquiry current native facts require the authenticated parent census")
    if (native.work.expected_parent.attempt_id, native.work.expected_parent.task_id) != (
            census["attempt_id"], census["task_id"]):
        raise ValueError("inquiry current native observations substitute their original attempt")
    if native.uncertain_contact_definition_ids:
        return InquiryAttemptStatus.UNCERTAIN_CONTACT
    # Known nested returns do not supply a parent receipt or scientific result.
    # The immutable historical UNKNOWN stays in InquiryState and still holds
    # the same scientific work against replay in the planning policy.
    return InquiryAttemptStatus.BLOCKED if recorded is InquiryAttemptStatus.UNCERTAIN_CONTACT else recorded


def _inquiry_operational_witness(products, census):
    """Use original custody, including terminal-owned pre-entry observations."""
    attempt_id = census["attempt_id"]
    receipt = products["attempt_receipts"].get(attempt_id)
    if receipt is not None:
        return receipt, identity(receipt, receipt.receipt_id)
    event = products["recovery_events"].get(attempt_id)
    if event is not None:
        return event, identity(event, event.event_id)
    from empirical_lawhood.runtime.execution import TaskBlockKind, TaskBlockReason
    from empirical_lawhood.runtime.recovery import DevelopmentRunRecoveryTerminalEvent

    terminal = products.get("terminal")
    if (type(terminal) is not DevelopmentRunRecoveryTerminalEvent
            or census.get("recovery_event_status") != "MISSING_TERMINAL_PRIMARY_NONATTEMPT"):
        raise ValueError("inquiry attempt lacks its original receipt, recovery event or terminal observation")
    terminal.__post_init__()
    rows = tuple(row for row in terminal.attempts if row.attempt_id == attempt_id)
    if (len(rows) != 1 or census["operational_status"] != "BLOCKED"
            or (rows[0].task_id, rows[0].ordinal, rows[0].reason_code,
                rows[0].disposition.value, rows[0].receipt_id, rows[0].receipt_sha256)
            != (census["task_id"], census["ordinal"], census["reason_code"], "BLOCKED", None, None)
            or census.get("receipt_id") is not None or census.get("receipt_sha256") is not None
            or census.get("recovery_event") is not None
            or attempt_id != f"{terminal.run_id}.{rows[0].task_id}.block-{rows[0].ordinal:03d}"
            or TaskBlockReason(rows[0].reason_code).kind is not TaskBlockKind.RETRYABLE):
        raise ValueError("inquiry terminal observation changes its exact nonattempt custody")
    return terminal, identity(terminal, terminal.terminal_event_id)


def _inquiry_outcome_callbacks(draft):
    from empirical_lawhood.api.recursive_operations import operation_factories
    selected = {op.selection.selection_id for op in draft.operations if op.node_id in draft.selected_operation_ids}
    return tuple(dict.fromkeys(factory.inquiry_outcome_projector for factory in operation_factories()
        if factory.registration.selection.selection_id in selected and factory.inquiry_outcome_projector is not None))


def _validate_wave_endpoint(draft, specification, products):
    """Join the registered immutable design to the inquiry without relabelling stock."""
    from empirical_lawhood.api.recursive_operations import operation_factories
    selected = {op.selection.selection_id for op in draft.operations if op.node_id in draft.selected_operation_ids}
    callbacks = tuple(dict.fromkeys(factory.inquiry_endpoint_validator for factory in operation_factories()
        if factory.registration.selection.selection_id in selected and factory.inquiry_endpoint_validator is not None))
    if len(callbacks) != 1:
        raise ValueError("inquiry endpoint needs its unique registered domain assessment")
    # Source-only validation supplies no result: initial choice is separate from
    # an attempted assessment, and raw source meanings retain their own scopes.
    if type(specification) is not RobustInquirySpecification:
        callbacks[0](draft, specification.endpoint)
        return
    # Source meanings are original domain scopes. A supplier investigation may
    # support another question of the same target through an assessed connection.
    for requirement in specification.requirements:
        try:
            callbacks[0](draft, requirement.scope)
            return
        except ValueError:
            pass
    raise ValueError("inquiry wave is outside every declared target/prerequisite scope")


def _scientific_product_identity(draft, task_id, record):
    """Use the selected adapter's identity grammar; never guess scientific IDs."""
    from empirical_lawhood.api.recursive_operations import operation_factories
    selected = next(operation.selection.selection_id for operation in draft.operations
                    if operation.node_id == task_id and task_id in draft.selected_operation_ids)
    callbacks = tuple(factory.inquiry_record_identity for factory in operation_factories()
                      if factory.registration.selection.selection_id == selected)
    if len(callbacks) != 1 or callbacks[0] is None:
        raise ValueError("robust inquiry requires its registered scientific product identity")
    product = callbacks[0](record)
    if product != identity(record, product.object_id):
        raise ValueError("inquiry adapter substitutes an authenticated scientific product identity")
    return product


def _project_supply_findings(*, specification, products, stock, source):
    """Retain existing code-owned phase assessments, with their actual evidence.

    These are projections of authenticated products through the registered
    assessment owner, not new experiments or new qualification receipts.
    """
    from empirical_lawhood.kernel.recursive_requirements import ContributionRole
    requirements = {identity(row, row.requirement_id): row for row in specification.requirements}
    for assessment in products["connection_assessments"]:
        requirement = requirements.get(assessment.requirement)
        if requirement is None:
            raise ValueError("inquiry drops an actual assessed scientific requirement")
        witnesses = tuple(row for row in stock.values() if row.product in assessment.evidence)
        if {row.product for row in witnesses} != set(assessment.evidence):
            raise ValueError("inquiry phase assessment lacks its original authenticated scientific evidence")
        product = identity(assessment, assessment.assessment_id)
        row = InquiryEvidence("stock." + sha256((source.packet.object_fingerprint + product.object_fingerprint).encode()).hexdigest()[:24],
            product, None, requirement.scope, ContributionRole.RETAINED_ANALYSIS_INPUT,
            tuple(sorted({unit for witness in witnesses for unit in witness.independent_unit_ids})),
            tuple(sorted({view for witness in witnesses for view in witness.nested_view_ids})),
            source_contract=source.packet)
        _merge(stock, row, row.evidence_id)


def _revision_predecessor(specification, sources, artifact_writer, histories=None):
    if specification.predecessor_specification is None:
        return None
    root = Path(artifact_writer.root.contract.canonical_path)
    candidates = []
    for path in sources.previous_decision_paths:
        records = histories[path] if histories is not None else read_inquiry_decision(
            directory=root / path, artifact_writer=artifact_writer, revalidate_sources=False)[1]
        previous = records["specification.json"]
        if identity(previous, previous.specification_id) == specification.predecessor_specification:
            candidates.append((previous, records["state.json"]))
    if len(candidates) != 1:
        raise ValueError("inquiry revision requires one exact direct predecessor decision")
    return candidates[0]


def _validate_revised_inputs(specification, state, sources, policy, artifact_writer):
    predecessor = _revision_predecessor(specification, sources, artifact_writer)
    if predecessor is not None:
        validate_revision = (validate_robust_inquiry_revision
                             if type(specification) is RobustInquirySpecification and type(predecessor[0]) is RobustInquirySpecification
                             else validate_inquiry_revision)
        validate_revision(previous_specification=predecessor[0], previous_state=predecessor[1],
            specification=specification, state=state, policy=policy)


def _project_scientific_work(draft, task_id):
    """Use the selected installed domain owner; missing semantics stay unknown."""
    from empirical_lawhood.api.recursive_operations import operation_factories
    operations = tuple(op for op in draft.operations if op.node_id == task_id
                       and op.node_id in draft.selected_operation_ids)
    if len(operations) != 1:
        raise ValueError("inquiry work changes its actual selected operation")
    factories = tuple(factory for factory in operation_factories()
                      if factory.registration.selection == operations[0].selection)
    if len(factories) != 1:
        raise ValueError("inquiry work lacks its unique installed operation owner")
    callback = factories[0].inquiry_work_projector
    if callback is None:
        return None
    work = callback(draft, task_id)
    if type(work) is not ScientificInquiryWork:
        raise ValueError("inquiry work owner returned no exact typed scientific identity")
    work.__post_init__()
    return work


def project_inquiry_state(*, specification, state_id, information_cutoff, sources, artifact_writer,
                          state_version=None):
    """Project declared eligible custody; missing attempt expenditure stays unknown."""
    root = Path(artifact_writer.root.contract.canonical_path)
    robust = type(specification) is RobustInquirySpecification
    version = state_version or (WorkBoundInquiryState.VERSION if robust else InquiryState.VERSION)
    if version not in {InquiryState.VERSION, WorkBoundInquiryState.VERSION} or (not robust and version != InquiryState.VERSION):
        raise ValueError("unsupported inquiry state projection version")
    stock, attempts, events, previous, work_bindings = {}, {}, {}, {}, {}
    depth_count = 0
    histories, waves = _inquiry_history_sources(sources=sources, root=root, artifact_writer=artifact_writer)
    for records in histories.values():
        old = records["state.json"]
        decision = records["decision.json"]
        _merge(previous, identity(decision, decision.decision_id), decision.decision_id)
        for row in old.previous_decisions:
            _merge(previous, row, row.object_id)
        for values, rows, key in ((old.stock, stock, "evidence_id"), (old.operational_census, attempts, "attempt_id")):
            for row in values:
                _merge(rows, row, getattr(row, key))
        for event in old.cost_events:
            if event.event_id in events:
                prior = events[event.event_id]
                # Histories arrive oldest first. A descendant refinement must carry
                # its explicit measurement path in its immutable source declaration.
                if event != prior:
                    paths = records["sources.json"].measured_event_paths
                    witnesses = [_read(artifact_writer, path, AcquisitionEvent) for path in paths]
                    if event not in witnesses:
                        raise ValueError("carried expense refinement lacks explicit measurement provenance")
                    event = _refine_inquiry_cost(prior, event)
            events[event.event_id] = event
        if isinstance(old, WorkBoundInquiryState):
            for binding in old.attempt_work_bindings:
                _merge(work_bindings, binding, binding.attempt_id)
    completed, completed_waves, native_depths = {}, {}, {}
    for source in waves:
        directory = root / source.relative_path
        packet, draft, _, payloads = load_authored_wave(directory=directory, artifact_writer=artifact_writer)
        if source.packet != identity(packet, packet.packet_id):
            raise ValueError("inquiry source changes its exact authored packet")
        from empirical_lawhood.api.recursive_inquiry_evidence import project_wave_evidence_bindings
        from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins, RecursiveInputOriginKind
        products = report = plan = None
        if source.include_products:
            report, products, _, plan = read_recursive_wave(directory=directory, artifact_writer=artifact_writer, include_products=True)
        bindings = project_wave_evidence_bindings(draft=draft, payloads=payloads, products=products)
        _validate_wave_endpoint(draft, specification, products)
        origins = {}
        if "origins.json" in payloads:
            declared = decode_canonical_bytes(payloads["origins.json"], RecursiveInputOrigins,
                maximum_bytes=max(1, len(payloads["origins.json"])))
            declared.validate_draft(draft)
            origins = {origin.input_id: origin for origin in declared.inputs}
        selected_ids = {link.external_input_id for link in draft.links
                        if link.consumer_node_id in draft.selected_operation_ids and link.external_input_id is not None}
        members = {member.filename: member for member in packet.members}
        for external in draft.external_inputs:
            if external.input_id not in selected_ids:
                continue
            filename = "external-" + sha256(external.input_id.encode()).hexdigest()[:24] + ".json"
            member = members[filename]
            binding = bindings[external.input_id]
            product_identity, producing_receipt, source_contract = member.identity, None, source.packet
            origin = origins.get(external.input_id)
            if origin is not None and origin.kind is RecursiveInputOriginKind.CONTRIBUTION:
                parent = next(parent for parent in draft.contribution_parents
                              if identity(parent, parent.contribution_id) == origin.parent)
                product = next(product for product in parent.products if product.product_id == origin.product_id)
                product_identity, producing_receipt, source_contract = product.record, origin.producing_receipt, None
            row = InquiryEvidence("stock." + sha256((packet.fingerprint() + external.input_id).encode()).hexdigest()[:24],
                product_identity, producing_receipt, binding.scope, binding.role,
                binding.independent_unit_ids, binding.nested_view_ids, source_contract=source_contract)
            _merge(stock, row, row.evidence_id)
        if not source.include_products:
            continue
        run_id = report["run_id"]
        old_packet = completed.get(run_id)
        if old_packet is not None and old_packet != source.packet:
            raise ValueError("completed inquiry run has substituted authored packet")
        completed[run_id] = source.packet
        operation_ids = {op.node_id: op.config_identity for op in draft.operations}
        completed_waves[source.packet] = packet.draft
        native_depths[source.packet] = _inquiry_parent_depth(payloads=payloads, draft=draft, artifact_writer=artifact_writer)
        for census in products["operational_census"]:
            attempt_id, task_id = census["attempt_id"], census["task_id"]
            receipt = products["attempt_receipts"].get(attempt_id)
            operational, receipt_identity = _inquiry_operational_witness(products, census)
            status = _inquiry_attempt_status(census, operational)
            output_ids = []
            if receipt is not None:
                for logical in receipt.output_logical_artifacts:
                    output_id = next(spec.output_id for task in plan.tasks if task.task_id == task_id
                                     for spec in task.outputs if spec.logical_artifact_id == logical.logical_artifact_id)
                    record = products["records"][task_id][output_id]
                    product_identity = identity(record, logical.logical_artifact_id)
                    output_ids.append(product_identity)
                    binding = bindings[output_id]
                    row = InquiryEvidence("stock." + sha256((receipt.fingerprint() + logical.logical_artifact_id).encode()).hexdigest()[:24],
                        product_identity, receipt_identity, binding.scope, binding.role,
                        binding.independent_unit_ids, binding.nested_view_ids)
                    _merge(stock, row, row.evidence_id)
                    if type(specification) is RobustInquirySpecification:
                        scientific = _scientific_product_identity(draft, task_id, record)
                        if scientific != product_identity:
                            alias = InquiryEvidence("stock." + sha256((receipt.fingerprint() + scientific.object_id).encode()).hexdigest()[:24],
                                scientific, receipt_identity, binding.scope, binding.role,
                                binding.independent_unit_ids, binding.nested_view_ids)
                            _merge(stock, alias, alias.evidence_id)
                            output_ids.append(scientific)
            attempt = InquiryAttempt(attempt_id, operation_ids[task_id], status, receipt_identity,
                tuple(sorted(output_ids, key=lambda v: v.object_id)), census["reason_code"] or "completed")
            _merge(attempts, attempt, attempt_id)
            if version == WorkBoundInquiryState.VERSION:
                task = next(task for task in plan.tasks if task.task_id == task_id)
                binding = InquiryAttemptWorkBinding(attempt_id, operation_ids[task_id],
                    _project_scientific_work(draft, task_id), source.packet,
                    identity(plan, plan.execution_plan_id), identity(task, task.task_id), receipt_identity)
                _merge(work_bindings, binding, attempt_id)
            event = AcquisitionEvent("event." + attempt_id, attempt_id, receipt_identity, InquiryCost(None, None, None))
            if event.event_id not in events:
                events[event.event_id] = event
            elif events[event.event_id].receipt != receipt_identity:
                raise ValueError("inquiry history changes an attempt receipt")
        if type(specification) is RobustInquirySpecification:
            _project_supply_findings(specification=specification, products=products, stock=stock, source=source)
    depth_count = _inquiry_successor_depth(histories=histories, completed_waves=completed_waves, native_depths=native_depths)
    for relative in sources.measured_event_paths:
        event = _read(artifact_writer, relative, AcquisitionEvent)
        if event.event_id not in events or (event.attempt_id, event.receipt) != (events[event.event_id].attempt_id, events[event.event_id].receipt):
            raise ValueError("measured event does not join the complete actual attempt census")
        events[event.event_id] = _refine_inquiry_cost(events[event.event_id], event)
    predecessor = _revision_predecessor(specification, sources, artifact_writer, histories)
    values = (state_id, identity(specification, specification.specification_id), information_cutoff,
        tuple(stock[key] for key in sorted(stock)), tuple(attempts[key] for key in sorted(attempts)),
        tuple(previous[key] for key in sorted(previous)), tuple(events[key] for key in sorted(events)),
        len(completed), depth_count)
    parent = None if predecessor is None else identity(predecessor[1], predecessor[1].state_id)
    if version == InquiryState.VERSION:
        return InquiryState(*values, revision_parent=parent)
    for attempt in attempts.values():
        if attempt.attempt_id not in work_bindings:
            work_bindings[attempt.attempt_id] = InquiryAttemptWorkBinding(attempt.attempt_id,
                attempt.operation, None, None, None, None, attempt.receipt)
    return WorkBoundInquiryState(*values, revision_parent=parent,
        attempt_work_bindings=tuple(work_bindings[key] for key in sorted(work_bindings)))


def _outcome(specification, sources, artifact_writer):
    outcomes = []
    root = Path(artifact_writer.root.contract.canonical_path)
    for source in sources.waves:
        if not source.include_products:
            continue
        _, products, draft, _ = read_recursive_wave(directory=root / source.relative_path,
            artifact_writer=artifact_writer, include_products=True)
        if not any(op.config_identity == specification.distinguishing_assessment for op in draft.operations
                   if op.node_id in draft.selected_operation_ids):
            continue
        if type(specification) is RobustInquirySpecification:
            from empirical_lawhood.kernel.recursive_inquiry_policy import ScientificOutcomeKind
            census = products["operational_census"]
            statuses = {_inquiry_current_attempt_status(row, _inquiry_operational_witness(products, row)[0],
                            products.get("native_observations", {}))
                        for row in census}
            kind = (ScientificOutcomeKind.UNCERTAIN_CONTACT if InquiryAttemptStatus.UNCERTAIN_CONTACT in statuses
                    else ScientificOutcomeKind.OPERATIONAL_FAILURE if statuses & {InquiryAttemptStatus.FAILED, InquiryAttemptStatus.BLOCKED}
                    else ScientificOutcomeKind.MISSING if statuses == {InquiryAttemptStatus.NONATTEMPT} else None)
            if kind is not None:
                mapped = tuple(row.outcome_id for row in specification.outcomes if row.kind is kind)
                if len(mapped) != 1:
                    raise ValueError("actual operational outcome needs its unique frozen outcome mapping")
                outcomes.append(mapped[0])
                continue
        for callback in _inquiry_outcome_callbacks(draft):
            outcomes.append(callback(draft, specification, products))
    if not outcomes and not any(source.include_products for source in sources.waves):
        return "initial"
    if len(set(outcomes)) != 1:
        raise ValueError("inquiry needs one unambiguous registered domain outcome projection")
    return outcomes[0]


def _validate_current_menu_work(*, state, sources, menu, artifact_writer):
    """Recompute each current ACT from actual prospective or registered draft science."""
    if not isinstance(state, WorkBoundInquiryState):
        return
    root = Path(artifact_writer.root.contract.canonical_path)
    _, waves = _inquiry_history_sources(sources=sources, root=root, artifact_writer=artifact_writer)
    candidates, suppliers = {}, []
    for source in waves:
        _, draft, _, _ = load_authored_wave(directory=root / source.relative_path, artifact_writer=artifact_writer)
        candidates[identity(draft, draft.draft_id)] = draft
        if source.include_products:
            suppliers.append(root / source.relative_path)
    for alternative in menu.alternatives:
        if alternative.action is not InquiryAction.ACT:
            continue
        draft = candidates.get(alternative.successor_draft)
        if draft is None:
            for supplier in suppliers:
                try:
                    preview = preview_inquiry_successor(supplier_directory=supplier, artifact_writer=artifact_writer)
                except ValueError:
                    continue
                candidates[identity(preview, preview.draft_id)] = preview
            draft = candidates.get(alternative.successor_draft)
        if draft is None:
            raise ValueError("current ACT needs an authenticated prospective draft or registered continuation")
        designated = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids
                           and op.config_identity == alternative.successor_config
                           and op.selection.selection_id == alternative.capability_id)
        if (len(designated) != 1 or len(draft.selected_operation_ids) != alternative.planned_operation_count
                or _project_scientific_work(draft, designated[0].node_id) != alternative.work):
            raise ValueError("current ACT changes its registered configuration/scientific work semantics")
        if alternative.reuse_completion is not None:
            _read_inquiry_completion(state=state, sources=sources, selected=alternative, artifact_writer=artifact_writer)


def commit_inquiry_decision(*, specification, state, sources, menu, policy, campaign, right,
                            actor_id, project_root, artifact_writer, output_dir, human_choice=None,
                            human_reason=None):
    choose, successor_intent, packet_type, _ = _policy_owners(specification, menu, policy, state)
    if type(specification) is RobustInquirySpecification and type(state) is not WorkBoundInquiryState:
        raise ValueError("legacy robust inquiry state is archival; reproject a work-bound version-three request before commitment")
    extra = {}
    if type(specification) is RobustInquirySpecification:
        extra["human_reason"] = human_reason
    elif human_reason is not None:
        raise ValueError("version-one inquiry does not contain a human reason")
    destination = preflight_authoring_output_directory(directory=Path(output_dir), repo_root=Path(project_root), artifact_writer=artifact_writer)
    actual = project_inquiry_state(specification=specification, state_id=state.state_id,
        information_cutoff=state.information_cutoff, sources=sources, artifact_writer=artifact_writer,
        state_version=state.VERSION)
    if actual != state:
        raise ValueError("inquiry state differs from current authenticated inputs")
    _validate_current_menu_work(state=state, sources=sources, menu=menu, artifact_writer=artifact_writer)
    _validate_revised_inputs(specification, state, sources, policy, artifact_writer)
    outcome_id = _outcome(specification, sources, artifact_writer)
    decision = choose(decision_id="decision." + sha256((state.fingerprint() + menu.fingerprint() + policy.fingerprint()).encode()).hexdigest()[:24],
        specification=specification, state=state, menu=menu, policy=policy, campaign=campaign,
        right=right, actor_id=actor_id, outcome_id=outcome_id, human_choice=human_choice, **extra)
    records = {"specification.json": specification, "state.json": state, "sources.json": sources,
               "menu.json": menu, "policy.json": policy, "campaign.json": campaign, "right.json": right,
               "decision.json": decision, "implementation.json": implementation_binding(project_root)}
    alternative = next(a for a in menu.alternatives if a.alternative_id == decision.selected_alternative_id)
    if alternative.action is InquiryAction.ACT:
        records["intent.json"] = successor_intent(intent_id="intent." + decision.fingerprint()[:24],
            decision=decision, specification=specification, menu=menu)
    members = tuple(RecursiveWaveMember(name, identity(record, "inquiry-member." + name.removesuffix(".json")), record.canonical_size_bytes())
                    for name, record in sorted(records.items()))
    packet = packet_type("inquiry-packet." + decision.fingerprint()[:24], members)
    if implementation_binding(project_root) != records["implementation.json"]:
        raise ValueError("inquiry implementation changed during decision persistence")
    destination.mkdir(parents=True)
    for name, record in (*sorted(records.items()), ("inquiry-packet.json", packet)):
        _publish(artifact_writer, destination, name, record, packet.packet_id)
    return packet, records


def read_inquiry_decision(*, directory, artifact_writer, revalidate_sources=True):
    root = Path(artifact_writer.root.contract.canonical_path)
    directory = Path(directory)
    relative = directory.relative_to(root).as_posix()
    packet = _read(artifact_writer, relative + "/inquiry-packet.json", (InquiryDecisionPacket, RobustInquiryDecisionPacket, WorkBoundInquiryDecisionPacket))
    codecs = (_CODECS if type(packet) is InquiryDecisionPacket else _WORK_BOUND_CODECS
              if type(packet) is WorkBoundInquiryDecisionPacket else _ROBUST_CODECS)
    records = {}
    for member in packet.members:
        record = _read(artifact_writer, relative + "/" + member.filename, codecs[member.filename])
        if (record.canonical_size_bytes() != member.size_bytes
                or identity(record, member.identity.object_id) != member.identity):
            raise ValueError("inquiry decision member differs from its committed identity")
        records[member.filename] = record
    _, _, expected_packet, validate_join = _policy_owners(records["specification.json"], records["menu.json"], records["policy.json"], records["state.json"])
    if type(packet) is not expected_packet:
        raise ValueError("inquiry packet changes the member versions")
    if revalidate_sources and type(packet) is RobustInquiryDecisionPacket:
        raise ValueError("legacy robust inquiry decision is archival; use explicit historical reading or a work-bound version-three decision")
    extra = ({"historical": not revalidate_sources} if type(packet) is InquiryDecisionPacket
             else {"validate_authority": revalidate_sources, "historical": not revalidate_sources})
    validate_join(decision=records["decision.json"], specification=records["specification.json"],
        state=records["state.json"], menu=records["menu.json"], policy=records["policy.json"],
        campaign=records["campaign.json"], right=records["right.json"], intent=records.get("intent.json"),
        **extra)
    selected = next(a for a in records["menu.json"].alternatives
                    if a.alternative_id == records["decision.json"].selected_alternative_id)
    if (selected.action is InquiryAction.ACT) != ("intent.json" in records):
        raise ValueError("inquiry decision changes its required successor intent census")
    if revalidate_sources:
        state = records["state.json"]
        actual = project_inquiry_state(specification=records["specification.json"], state_id=state.state_id,
            information_cutoff=state.information_cutoff, sources=records["sources.json"], artifact_writer=artifact_writer,
            state_version=state.VERSION)
        if actual != state or _outcome(records["specification.json"], records["sources.json"], artifact_writer) != records["decision.json"].outcome_id:
            raise ValueError("inquiry decision has stale or substituted scientific inputs")
        _validate_current_menu_work(state=state, sources=records["sources.json"], menu=records["menu.json"], artifact_writer=artifact_writer)
        _validate_revised_inputs(records["specification.json"], state, records["sources.json"],
                                 records["policy.json"], artifact_writer)
    return packet, records


def recover_inquiry_completion(*, decision_directory, artifact_writer):
    """Read the exact selected completed work, with no scheduler or new entry."""
    packet, records = read_inquiry_decision(directory=decision_directory, artifact_writer=artifact_writer)
    selected = next(row for row in records["menu.json"].alternatives
                    if row.alternative_id == records["decision.json"].selected_alternative_id)
    return {"decision_packet_sha256": packet.fingerprint(), **_read_inquiry_completion(
        state=records["state.json"], sources=records["sources.json"], selected=selected, artifact_writer=artifact_writer)}


def _read_inquiry_completion(*, state, sources, selected, artifact_writer):
    """One exact current-admission and recovery join over existing receipt readers."""
    completion = getattr(selected, "reuse_completion", None)
    if not isinstance(state, WorkBoundInquiryState) or completion is None:
        raise ValueError("completion recovery needs a current selected authenticated REUSE/ADOPT")
    attempt = next((row for row in state.operational_census if row.attempt_id == completion.attempt_id), None)
    binding = next((row for row in state.attempt_work_bindings if row.attempt_id == completion.attempt_id), None)
    if (attempt is None or binding is None or attempt.status is not InquiryAttemptStatus.COMPLETED or completion.work != binding.work
            or completion.work != selected.work
            or completion.receipt != attempt.receipt or completion.products != attempt.products
            or binding.configuration != selected.successor_config):
        raise ValueError("completion recovery changes its exact actual work/configuration/receipt/products")
    root = Path(artifact_writer.root.contract.canonical_path)
    _, waves = _inquiry_history_sources(sources=sources, root=root, artifact_writer=artifact_writer)
    matches = tuple(source for source in waves if source.include_products and source.packet == binding.authored_wave)
    if len(matches) != 1:
        raise ValueError("completion recovery lacks its unique exact retained authored wave")
    directory = root / matches[0].relative_path
    authored, draft, source, _ = load_authored_wave(directory=directory, artifact_writer=artifact_writer)
    report, products, _, plan = read_recursive_wave(directory=directory, artifact_writer=artifact_writer, include_products=True)
    task = next((row for row in plan.tasks if identity(row, row.task_id) == binding.execution_task), None)
    receipt = products["attempt_receipts"].get(completion.attempt_id)
    if (task is None or receipt is None or identity(receipt, receipt.receipt_id) != completion.receipt
            or identity(authored, authored.packet_id) != binding.authored_wave
            or identity(plan, plan.execution_plan_id) != binding.execution_plan
            or identity(draft, draft.draft_id) != selected.successor_draft
            or _project_scientific_work(draft, task.task_id) != completion.work):
        raise ValueError("completion recovery substitutes its original task/plan/draft/receipt/work")
    return {"status": "RECOVERED_COMPLETION",
        "completion": completion.to_document(), "authored_wave": authored.to_document(),
        "producing_implementation": source.to_document(), "task_receipt": receipt.to_document(),
        "original_operational_census": products["operational_census"],
        "original_wave_report": report, "products": {
            output_id: record.to_document() for output_id, record in products["records"][task.task_id].items()},
        "new_native_contact_count": 0, "new_operation_count": 0, "new_wave_count": 0,
        "fresh_independent_units": 0, "read_cpu_seconds": None, "read_wall_seconds": None, "read_peak_rss_bytes": None,
        "scientific_authority": "NONE", "qualification": "NOT_ESTABLISHED"}


def _refuse_reuse_entry(records):
    selected = next(row for row in records["menu.json"].alternatives
                    if row.alternative_id == records["decision.json"].selected_alternative_id)
    if getattr(selected, "reuse_completion", None) is not None:
        raise ValueError("selected completed work requires read-only completion recovery; fresh task entry is refused")


def preview_inquiry_successor(*, supplier_directory, artifact_writer):
    """Invoke the existing registered builder without exporting or deciding."""
    from empirical_lawhood.api.recursive_contributions import _callbacks, _described
    _, products, draft, _ = read_recursive_wave(directory=supplier_directory, artifact_writer=artifact_writer, include_products=True)
    manifest = _described(draft, products)
    successors = tuple(value for callback in _callbacks(draft, products, "next_wave_builder")
                       if (value := callback(draft, manifest, products)) is not None)
    if len(successors) != 1:
        raise ValueError("inquiry lacks its unique registered successor builder")
    return successors[0]


def retain_measured_attempt_cost(*, authoring_directory, cpu_seconds, wall_seconds,
                                retained_bytes, artifact_writer, output_dir):
    """Bind trusted-local invocation measurements to one actual attempted operation.

    Caller measurements must cover the complete declared invocation window;
    capacities and planner estimates are not measurements. Multiple attempts
    cannot be assigned an aggregate measurement by this selected contract.
    """
    _, products, _, _ = read_recursive_wave(directory=authoring_directory,
        artifact_writer=artifact_writer, include_products=True)
    census = products["operational_census"]
    if len(census) != 1:
        raise ValueError("aggregate invocation cost cannot identify several attempt costs")
    attempt_id = census[0]["attempt_id"]
    _, witness = _inquiry_operational_witness(products, census[0])
    event = AcquisitionEvent("event." + attempt_id, attempt_id,
        witness,
        InquiryCost(cpu_seconds, wall_seconds, retained_bytes))
    destination = Path(output_dir)
    artifact_writer.root.resolve(destination.relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix(), for_write=True)
    if destination.exists():
        raise FileExistsError("measured invocation cost must retain a new exact destination")
    destination.mkdir(parents=True)
    _publish(artifact_writer, destination, "measured-attempt-cost.json", event, "measurement." + event.fingerprint()[:24])
    return event


def _validate_intent_draft(intent, draft, origins):
    operations = tuple(op for op in draft.operations if op.node_id in draft.selected_operation_ids)
    designated = tuple(op for op in operations if op.config_identity == intent.configuration
                       and op.selection.selection_id == intent.capability_id)
    if (identity(draft, draft.draft_id) != intent.draft or len(designated) != 1
            or identity(origins, "inquiry-input-origins") != intent.input_origins):
        raise ValueError("inquiry intent substitutes its registered draft/configuration/input origins/capability")


def _validate_successor_allowances(records, draft):
    """Verify the complete prospective wave at admission, including old v1 policies."""
    _refuse_reuse_entry(records)
    selected = next(row for row in records["menu.json"].alternatives
                    if row.alternative_id == records["decision.json"].selected_alternative_id)
    count = len(draft.selected_operation_ids)
    if type(records["specification.json"]) is RobustInquirySpecification and count != selected.planned_operation_count:
        raise ValueError("inquiry successor changes the complete prospective operation census")
    if isinstance(records["state.json"], WorkBoundInquiryState):
        designated = next(op for op in draft.operations if op.config_identity == selected.successor_config
                          and op.node_id in draft.selected_operation_ids)
        actual_work = _project_scientific_work(draft, designated.node_id)
        if actual_work is None or actual_work != selected.work:
            raise ValueError("inquiry successor changes its registered scientific work semantics")
    policy, state = records["policy.json"], records["state.json"]
    if policy.max_operations is not None and len(state.operational_census) + count > policy.max_operations:
        raise ValueError("inquiry successor exceeds its explicit finite operation allowance")


def _validate_human_fork(*, draft, records, supplier_directory, contribution_dir=None, contribution_dirs=None, origins, artifact_writer):
    """Bind an explicitly chosen new inquiry to actual supplier custody.

    A new human-directed menu can change the scientific question/consumer while
    retaining the original source outcome and its portable parent. It does not
    alter an earlier registered successor or grant a repeat of native effects.
    """
    if not records["decision.json"].human_directed:
        raise ValueError("human inquiry fork requires an explicit persisted human-directed ACT choice")
    if (contribution_dir is None and contribution_dirs is None) or not draft.contribution_parents:
        raise ValueError("human inquiry fork requires authenticated actual contribution parents")
    origins.validate_draft(draft)
    root = Path(artifact_writer.root.contract.canonical_path)
    selected = Path(supplier_directory).resolve(strict=True)
    if not selected.is_relative_to(root) or any(p.is_symlink() for p in (Path(supplier_directory), *Path(supplier_directory).parents)):
        raise ValueError("human inquiry fork supplier is outside its exact guarded custody")
    packet, old_draft, _, _ = load_authored_wave(directory=selected, artifact_writer=artifact_writer)
    if identity(draft, draft.draft_id) == identity(old_draft, old_draft.draft_id):
        raise ValueError("human inquiry fork must declare a distinct new inquiry draft")
    sources = tuple(source for source in records["sources.json"].waves if source.include_products
                    and source.packet == identity(packet, packet.packet_id)
                    and source.relative_path == selected.relative_to(root).as_posix())
    if len(sources) != 1:
        raise ValueError("human inquiry fork supplier is absent from its exact retained decision sources")
    from empirical_lawhood.api.recursive_contributions import _described, authenticate_recursive_parents
    report, products, retained_draft, _ = read_recursive_wave(directory=selected, artifact_writer=artifact_writer, include_products=True)
    if report["status"] != "SUCCEEDED":
        raise ValueError("human inquiry fork needs its actual completed supplier outcome")
    actual_parent = _described(retained_draft, products)
    parents = authenticate_recursive_parents(draft=draft, artifact_writer=artifact_writer,
                                            directory=contribution_dir, directories=contribution_dirs)
    if sum(parent[2] == actual_parent for parent in parents) != 1:
        raise ValueError("human inquiry fork changes its actual receipt-backed supplier parent")
    return draft


def author_inquiry_successor(*, decision_directory, origins,
                             project_root, artifact_writer, output_dir, supplier_directory=None,
                             initial_draft=None, human_fork_draft=None, input_bindings=(), contribution_dir=None, contribution_dirs=None):
    packet, records = read_inquiry_decision(directory=decision_directory, artifact_writer=artifact_writer)
    intent = records.get("intent.json")
    if intent is None:
        raise ValueError("HOLD/STOP decision has no executable successor")
    _refuse_reuse_entry(records)
    if human_fork_draft is not None and (supplier_directory is None or initial_draft is not None):
        raise ValueError("human inquiry fork requires its supplier directory and forbids an initial draft")
    if (supplier_directory is None) == (initial_draft is None):
        raise ValueError("inquiry authoring requires exactly one supplier or initial draft")
    if initial_draft is not None:
        if (any(source.include_products for source in records["sources.json"].waves)
                or initial_draft.contribution_parents or contribution_dir is not None or contribution_dirs is not None):
            raise ValueError("initial inquiry authoring cannot conceal a completed supplier or contribution parent")
        draft = initial_draft
    elif human_fork_draft is not None:
        draft = _validate_human_fork(draft=human_fork_draft, records=records, supplier_directory=supplier_directory,
            contribution_dir=contribution_dir, contribution_dirs=contribution_dirs, origins=origins, artifact_writer=artifact_writer)
    else:
        draft = preview_inquiry_successor(supplier_directory=supplier_directory, artifact_writer=artifact_writer)
    _validate_intent_draft(intent, draft, origins)
    _validate_successor_allowances(records, draft)
    report = author_recursive_wave(draft=draft, project_root=project_root, artifact_writer=artifact_writer,
        output_dir=output_dir, input_bindings=input_bindings, contribution_dir=contribution_dir,
        contribution_dirs=contribution_dirs, origins=origins)
    authored, _, _, _ = load_authored_wave(directory=output_dir, artifact_writer=artifact_writer)
    relative = Path(decision_directory).relative_to(Path(artifact_writer.root.contract.canonical_path)).as_posix()
    admission = InquirySuccessorAdmission(relative, identity(packet, packet.packet_id), identity(intent, intent.intent_id), identity(authored, authored.packet_id))
    _publish(artifact_writer, output_dir, "inquiry-admission.json", admission, packet.packet_id)
    return report


def run_inquiry_successor(*, directory, project_root, artifact_writer, terminal_product_format="documents",
                          maximum_parallel_tasks=1, parallel_resource_capacity=None):
    _validate_terminal_product_format(terminal_product_format)
    validate_recursive_worker_controls(maximum_parallel_tasks, parallel_resource_capacity)
    root = Path(artifact_writer.root.contract.canonical_path)
    relative = Path(directory).relative_to(root).as_posix()
    admission = _read(artifact_writer, relative + "/inquiry-admission.json", InquirySuccessorAdmission)
    packet, records = read_inquiry_decision(directory=root / admission.decision_relative_path, artifact_writer=artifact_writer)
    _refuse_reuse_entry(records)
    authored, draft, source, payloads = load_authored_wave(directory=directory, artifact_writer=artifact_writer)
    intent = records.get("intent.json")
    if (intent is None or admission.decision_packet != identity(packet, packet.packet_id)
            or admission.intent != identity(intent, intent.intent_id)
            or admission.authored_wave != identity(authored, authored.packet_id)
            or identity(draft, draft.draft_id) != intent.draft
            or source != records["implementation.json"]):
        raise ValueError("inquiry execution changes the exact persisted decision/intent/draft/source join")
    from empirical_lawhood.planning.recursive_input_origins import RecursiveInputOrigins
    if "origins.json" not in payloads:
        raise ValueError("inquiry execution lacks its committed explicit input origins")
    origins = decode_canonical_bytes(payloads["origins.json"], RecursiveInputOrigins,
        maximum_bytes=max(1, len(payloads["origins.json"])))
    _validate_intent_draft(intent, draft, origins)
    _validate_successor_allowances(records, draft)
    return run_recursive_wave(directory=directory, project_root=project_root, artifact_writer=artifact_writer,
                              terminal_product_format=terminal_product_format,
                              maximum_parallel_tasks=maximum_parallel_tasks,
                              parallel_resource_capacity=parallel_resource_capacity)
