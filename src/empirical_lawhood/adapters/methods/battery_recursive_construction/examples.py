"""Concrete authored waves and scientific contribution publication projections."""

from dataclasses import replace
from decimal import Decimal

from empirical_lawhood.kernel.authority import AuthorityAction, AuthorityPolicy, ResourceBudget, SourceAccessClass
from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentDisposition, ConditionRole, ContributionRole, DevelopmentStudySpec,
    ScientificConditionScope, ScientificConnectionSpec, ScientificRequirementSpec,
)
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.scientific_contributions import ContributionManifest, ContributionProduct
from empirical_lawhood.kernel.status import LifecycleStatus, OperationalStatus
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.planning.campaigns import CampaignLane, CampaignNode, CampaignNodeKind, CampaignSpec, DecisionRight
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft, SupplierProposal,
)
from empirical_lawhood.planning.study_authoring import UnresolvedDecision

from .contracts import (
    BatteryFurtherProduct, BatteryOperation, BatteryOperationConfig, BatteryProcedureContribution,
    BatteryRestartAssessment,
    BatterySourceContract, MAX_PRODUCT_BYTES,
)
from .executable_binding import DEFINITIONS, MEDIA, RESOURCE, operation_registrations
from .science import identity

D = Decimal
WORLD = "battery-recursive-numerical-world"
SYSTEM = "chen2020-spme"
QUESTION_A = "Do exact-state/input channels faithfully supply hold continuation, and are SOC/capacity/temperature sufficient in the two assigned histories?"
QUESTION_B = "What equal-charge history contrast and current-proportionality defect occur on a newly supplied SPMe instance under four declared future current words?"


def _scope(wave, meaning, *, source=None):
    source = BatterySourceContract() if source is None else source
    return ScientificConditionScope(
        SYSTEM, WORLD, source.source_id, ("capacity", "temperature", "voltage"), ("A.h", "K", "V"),
        "spme-native-terminal", "model-seconds", meaning, source_config_sha256=source.fingerprint(),
        instance_id=f"battery-preparation-{wave.lower()}", available_by=D(300), valid_from=D(300), valid_until=D(600),
    )


def _pair(req_id, consumer, supplier, port, assessor, wave, condition, falsifier, role=ContributionRole.INSTANCE_PRODUCT, further=()):
    requirement = ScientificRequirementSpec(
        req_id, consumer, ConditionRole.INFORMATIONAL, "Supply a faithful numerical operand for the declared consumer.", condition,
        _scope(wave, condition), assessor, falsifier, (role,), tuple(sorted(further)), ("exposed-deterministic-model",),
    )
    connection = ScientificConnectionSpec(f"{req_id}.connection", req_id, supplier, "product", port, assessor,
                                          f"{req_id}.claim", role, falsifier)
    return requirement, connection


def _operation(node, registered_name, wave, *, history="early", word="hold", pair=None, contribution=None):
    registration = next(value for value in operation_registrations() if value.selection.capability_key == f"battery-recursive.{registered_name}")
    operation = next(value.operation for value in DEFINITIONS if value.name == registered_name)
    config = BatteryOperationConfig(f"{node}.config", operation, wave, history, word,
                                   requirement=None if pair is None else pair[0], connection=None if pair is None else pair[1],
                                   contribution_sha256=None if contribution is None else contribution.fingerprint())
    return RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection, config_id=config.config_id,
                                              config=config, obligation_ids=(f"{node}.obligation",), resource_budget=RESOURCE,
                                              resource_lock_ids=("battery-native-single-worker",) if registration.native_effect else ())


def _link(consumer, port, producer=None, *, external=None, pair=None, role="HISTORY"):
    return RecursiveInputLink(
        f"edge.{consumer}.{port}", consumer, port, producer, "product" if producer else None, external, role,
        None if pair is None else pair[0].requirement_id, None if pair is None else pair[1].connection_id,
    )


def _study(wave, operations, pairs, links, *, external_inputs=(), parents=(), unavailable=True):
    source = BatterySourceContract()
    question = QUESTION_A if wave == "A" else QUESTION_B
    claim = ClaimSpec(f"battery.wave-{wave.lower()}.development-claim", WORLD, "battery-recursive-state-and-voltage", question,
                      "Complete declared native discrepancies and signed voltage contrasts; no population inference.",
                      f"battery-preparation-{wave.lower()}", None, EvidenceCeiling.NON_PROMOTABLE,
                      OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
                      "Never promotes development completion to scientific qualification.", ("exposed-deterministic-model",),
                      numerical_view_ids=("coarse",) if wave == "A" else ("coarse", "tighter"))
    scientific = DevelopmentStudySpec(f"battery.wave-{wave.lower()}.study", question, ObjectIdentity.from_record(SYSTEM, source),
                                       WORLD, WorldKind.NUMERICAL_SIMULATOR, (f"battery-preparation-{wave.lower()}",),
                                       claim.numerical_view_ids, (claim,), (ObjectIdentity.from_record(source.source_id, source),))
    budget = ResourceBudget(1, 2 * 1024**3, 0, 3600, 64 * 1024**2, 64 * 1024**2)
    # Campaign bookkeeping declares ordinary numerical development intent. This
    # policy is never an issue, execution authorization or qualification receipt.
    policy = AuthorityPolicy("battery-recursive.development-policy", "human.project-owner", "researcher.battery-development",
                             ("battery-recursive.development",), frozenset({WorldKind.NUMERICAL_SIMULATOR}),
                             frozenset({AuthorityAction.SIMULATION_EXECUTION}), frozenset({SourceAccessClass.NONE}),
                             ("frozen-source-and-protocol",), frozenset(), budget, OutcomeAccess.DEVELOPMENT_VISIBLE)
    root = CampaignNode(f"battery.wave-{wave.lower()}.proposal", CampaignNodeKind.ANALYSIS_PROPOSAL,
                        CampaignLane.EXPLORATORY, ObjectIdentity.from_record(scientific.study_id, scientific), (), LifecycleStatus.ACTIVE)
    campaign = CampaignSpec(f"battery.wave-{wave.lower()}.campaign", question, (SYSTEM,), (WORLD,), (claim.claim_id,), budget,
                            ObjectIdentity.from_record(policy.policy_id, policy),
                            (DecisionRight("battery-recursive.development-right", AuthorityAction.SIMULATION_EXECUTION,
                                           policy.delegate_id, policy.policy_id, True),),
                            (root,), (root.node_id,), (root.node_id,), (), LifecycleStatus.ACTIVE)
    suppliers = [SupplierProposal(f"{r.requirement_id}.selected-supplier", r.requirement_id, (c.supplier_operation_id,),
                                  r.further_requirement_ids, True, "Explicitly selected declared supplier; actual adequacy remains assessed.")
                 for r, c in pairs if c.supplier_operation_id is not None]
    if unavailable and pairs:
        suppliers.append(SupplierProposal("battery.terminal-voltage-only.unavailable", pairs[0][0].requirement_id, (), (), False,
                                          "Terminal-voltage-only reconstruction has no registered inverse procedure or sufficient premises in this protocol.",
                                          ("NO_REGISTERED_TERMINAL_VOLTAGE_INVERSE",)))
    return RecursiveStudyDraft(f"battery.wave-{wave.lower()}", question, campaign,
                               tuple(sorted((p[0] for p in pairs), key=lambda v: v.requirement_id)),
                               tuple(sorted((p[1] for p in pairs), key=lambda v: v.connection_id)),
                               tuple(sorted(suppliers, key=lambda v: v.proposal_id)),
                               tuple(sorted(operations, key=lambda v: v.node_id)), tuple(sorted(external_inputs, key=lambda v: v.input_id)),
                               tuple(sorted(links, key=lambda v: v.edge_id)), tuple(sorted(op.node_id for op in operations)),
                               development_study=scientific, contribution_parents=parents)


def battery_wave_a_draft():
    operations, pairs, links = [], [], []
    for history in ("early", "late"):
        prefix = f"battery.a.{history}"
        checkpoint, full, assessor = f"{prefix}.checkpoint", f"{prefix}.full", f"{prefix}.assess"
        pair = _pair(f"requirement.{prefix}.exact-state", full, checkpoint, "checkpoint", assessor, "A",
                     "Exact internal state and source-input ledger at 300 s faithfully supply the assigned hold continuation.",
                     "Any state/input substitution, incomplete clocks or restart discrepancy above the frozen voltage/capacity/temperature bounds.")
        pairs.append(pair)
        operations.append(_operation(checkpoint, "checkpoint", "A", history=history))
        for route in ("reference", "full", "soc"):
            node = f"{prefix}.{route}"
            operations.append(_operation(node, f"a-{route}", "A", history=history))
            links.append(_link(node, "checkpoint", checkpoint, pair=pair if route == "full" else None))
        operations.append(_operation(assessor, "a-assess", "A", history=history, pair=pair))
        for port, producer in (("checkpoint", checkpoint), ("reference", f"{prefix}.reference"), ("full", full), ("soc", f"{prefix}.soc")):
            links.append(_link(assessor, port, producer))
    procedure = "battery.a.procedure"
    operations.append(_operation(procedure, "procedure", "A"))
    for history in ("early", "late"):
        links.extend((_link(procedure, f"checkpoint-{history}", f"battery.a.{history}.checkpoint"),
                      _link(procedure, f"assessment-{history}", f"battery.a.{history}.assess", role="OUTCOME")))
    return _study("A", operations, pairs, links)


def battery_wave_b_draft(manifest: ContributionManifest, procedure: BatteryProcedureContribution):
    procedure_products = [product for product in manifest.products if product.record == identity(procedure)]
    if len(procedure_products) != 1:
        raise ValueError("next wave requires the actual procedure product in its authenticated parent")
    operations, pairs, links = [], [], []
    checkpoint, projection = "battery.b.checkpoint", "battery.b.projection"
    operations.extend((_operation(checkpoint, "checkpoint", "B"), _operation(projection, "projection", "B")))
    links.append(_link(projection, "checkpoint", checkpoint))
    external = (
        RecursiveExternalInput("battery.parent.manifest", "battery.parent.manifest", ContributionManifest.SCHEMA, MEDIA,
                               MAX_PRODUCT_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
                               manifest.fingerprint(), "MODEL"),
        RecursiveExternalInput("battery.parent.procedure", "battery.parent.procedure", BatteryProcedureContribution.SCHEMA, MEDIA,
                               MAX_PRODUCT_BYTES, OutcomeAccess.DEVELOPMENT_VISIBLE, VisibilityCeiling.DEVELOPMENT_ONLY,
                               procedure.fingerprint(), "MODEL"),
    )
    for consumer in ("C1", "C2"):
        node = f"battery.b.admit-{consumer.lower()}"
        internal_pair = _pair(f"requirement.battery.b.{consumer.lower()}-procedure", node, "battery.parent", "procedure", node, "B",
                     f"Assessed procedure can be admitted as a design operand within {consumer}'s predeclared allowed channels, retaining new-instance obligations.",
                     "Missing actual procedure assessment, model/source/layout substitution, or required channel outside the consumer policy.",
                     ContributionRole.DESIGN_OPERAND)
        pair = (internal_pair[0], replace(internal_pair[1], supplier_operation_id=None, supplier_output_id=None,
                                         supplier_contribution=ObjectIdentity.from_record(manifest.contribution_id, manifest),
                                         supplier_product_id=procedure_products[0].product_id,
                                         external_input_id="battery.parent.procedure"))
        pairs.append(pair)
        operations.append(_operation(node, f"admit-{consumer.lower()}", "B", pair=pair, contribution=manifest))
        links.extend((_link(node, "procedure", external="battery.parent.procedure", pair=pair, role="MODEL"),
                      _link(node, "manifest", external="battery.parent.manifest", role="MODEL"),
                      _link(node, "summary", projection)))
    c1_req = "requirement.battery.b.c1-procedure"
    for word in ("early1", "early3", "hold", "late1"):
        prefix = f"battery.b.{word}"
        full, assessor = f"{prefix}.full", f"{prefix}.assess"
        pair = _pair(f"requirement.{prefix}.instance", full, checkpoint, "checkpoint", assessor, "B",
                     f"The new shared checkpoint faithfully supplies the changed future {word}, assessed on the actual instance.",
                     "Assigned reference/full mismatch, failed conservation control, state substitution or incomplete continuation.",
                     further=(c1_req,))
        pairs.append(pair)
        for route in ("reference", "full", "tighter"):
            node = f"{prefix}.{route}"
            operations.append(_operation(node, f"b-{route}", "B", word=word, contribution=manifest))
            links.extend((_link(node, "checkpoint", checkpoint, pair=pair if route == "full" else None),
                          _link(node, "admission", "battery.b.admit-c1", role="MODEL")))
        operations.append(_operation(assessor, "b-assess", "B", word=word, pair=pair))
        links.extend((_link(assessor, "checkpoint", checkpoint), _link(assessor, "full", full),
                      _link(assessor, "reference", f"{prefix}.reference")))
    product = "battery.b.voltage"
    joined_pairs = []
    for word in ("early1", "early3", "hold", "late1"):
        pair = _pair(f"requirement.battery.b.product-{word}", product, f"battery.b.{word}.assess", f"assessment-{word}", product, "B",
                     "The complete assigned word census has assessed new-instance continuation and supports a bounded further voltage finding.",
                     "Any missing/failed instance, incomplete nested control census, solver disagreement or illegitimate channel use.",
                     further=(f"requirement.battery.b.{word}.instance",))
        pairs.append(pair)
        joined_pairs.append(pair)
        links.append(_link(product, f"assessment-{word}", f"battery.b.{word}.assess", pair=pair, role="OUTCOME"))
        for route in ("reference", "full", "tighter"):
            links.append(_link(product, f"{word}-{route}", f"battery.b.{word}.{route}", role="OUTCOME"))
    operations.append(_operation(product, "voltage", "B", pair=joined_pairs[0], contribution=manifest))
    links.extend((_link(product, "c1", "battery.b.admit-c1", role="MODEL"),
                  _link(product, "c2", "battery.b.admit-c2", role="MODEL")))
    return _study("B", operations, pairs, links, external_inputs=external, parents=(manifest,))


def battery_wave_b_partial_draft():
    """Keep the committed scientific question pending the actual Wave A parent."""
    draft = _study("B", (), (), (), unavailable=False)
    requirement = ScientificRequirementSpec(
        "requirement.battery.b.pending-procedure", "battery.b.admit-c1", ConditionRole.EVIDENTIAL,
        "Import the actual assessed Wave A contribution before constructing a new Wave B execution.",
        "An authentic exact procedure product and its producing receipt/output closure must be available.",
        _scope("B", "Fixed new preparation SOC0.70 and changed future words, pending actual assessed parent."),
        "battery.b.admit-c1", "Missing actual contribution identity or custody refuses the selected execution.",
        (ContributionRole.DESIGN_OPERAND,), background_assumption_ids=("exposed-deterministic-model",),
    )
    alternative = SupplierProposal("battery.b.pending-actual-parent", requirement.requirement_id, (), (), False,
                                    "Wave A has not produced this copied example's actual contribution yet; export its authenticated closure after execution.",
                                    ("ACTUAL_CONTRIBUTION_NOT_BOUND",))
    return replace(draft, requirements=(requirement,), suppliers=(alternative,),
                   unresolved_decisions=(UnresolvedDecision("battery.b.bind-actual-parent", "contribution_parents",
                   "Bind the actual assessed procedure or retain its negative terminal result before selecting Wave B.",
                   ("bind-authenticated-parent", "retain-negative-terminal")),))


def _remaining_requirements(scope):
    return tuple(ScientificRequirementSpec(f"battery.procedure.remaining.{name}", "battery.future-consumer", ConditionRole.EVIDENTIAL,
                "Assess the actual new use rather than promote old hold evidence.", condition, replace(scope, instance_id=None),
                "battery.future-instance-assessment", "New instance or future continuation fails the frozen numerical contract.",
                (ContributionRole.INSTANCE_PRODUCT,), background_assumption_ids=("exposed-deterministic-model",))
                 for name, condition in (("changed-future-fidelity", "Actual changed future needs new numerical continuation evidence."),
                                         ("new-instance-supply", "Actual newly acquired state needs independent instance supply assessment.")))


def describe_contributions(draft, authenticated_products):
    """Publish only already authenticated actual products, preserving original bytes."""
    entries = [(task, output, record) for task, outputs in authenticated_products["records"].items()
               for output, record in outputs.items()]
    terminal = _contribution_terminal(draft, entries)
    if terminal is None:
        return ()
    config, product = terminal
    if any(authenticated_products["receipts"][task].operational_status is not OperationalStatus.SUCCEEDED for task, _, _ in entries):
        raise ValueError("contribution requires actual successful publication receipts, including scientific negatives")
    actual_assessments = {identity(record) for _, _, record in entries if isinstance(record, BatteryRestartAssessment)}
    if config.wave == "A":
        procedure = product
        scope = procedure.scope
        if (procedure.source != config.source or scope.system_id != SYSTEM or scope.world_id != WORLD
            or scope.source_id != config.source.source_id or scope.source_config_sha256 != config.source.fingerprint()
            or scope.instance_id != config.unit_id or scope.valid_from != D(300) or scope.valid_until != D(600)
            or scope.quantity_ids != ("capacity", "temperature", "voltage") or scope.native_units != ("A.h", "K", "V")
            or scope.receiver_id != "spme-native-terminal" or scope.clock_id != "model-seconds"):
            raise ValueError("actual procedure scope differs from its declared scientific source and instance")
        if set(procedure.assessments) != actual_assessments:
            raise ValueError("procedure contribution is missing or adding its actual assessment census")
        scope, assessments = procedure.scope, procedure.assessments
        finding, question = procedure.finding, QUESTION_A
        remaining = _remaining_requirements(scope)
    else:
        if set(product.restart_assessment_census) != actual_assessments or product.assigned_unit_ids != (config.unit_id,):
            raise ValueError("further contribution is missing or changing its actual assessment and instance census")
        scope = _scope("B", "Complete assessed new-instance current-word voltage inquiry; development-only numerical world.", source=config.source)
        assessments = product.restart_assessment_census
        finding = "; ".join(f"{c.contrast_id}: {c.finding}, coarse={c.coarse_V} V, tighter={c.tighter_V} V" for c in product.contrast_results)
        question = QUESTION_B
        remaining = tuple(r for r in draft.requirements if r.requirement_id == "requirement.battery.b.c2-procedure") if product.c1_c2_joint_disposition is not AssessmentDisposition.SATISFIED else ()
    products = []
    for task, output, record in entries:
        if not type(record).__module__.startswith(__package__):
            continue
        receipt = authenticated_products["receipts"][task]
        record_identity = identity(record)
        logicals = [value for value in receipt.output_logical_artifacts if value.payload_schema == record.SCHEMA and value.content_sha256 == record.fingerprint()]
        if len(logicals) != 1:
            raise ValueError("contribution record is not a unique receipt-bound output")
        artifact_id = logicals[0].logical_artifact_id
        artifact = authenticated_products["outputs"][artifact_id]
        if record_identity.object_fingerprint != artifact.logical.content_sha256:
            raise ValueError("contribution product does not match authenticated artifact bytes")
        role = ContributionRole.DESIGN_OPERAND if isinstance(record, BatteryProcedureContribution) else (
               ContributionRole.INSTANCE_PRODUCT if isinstance(record, BatteryFurtherProduct) else ContributionRole.RETAINED_ANALYSIS_INPUT)
        products.append(ContributionProduct(f"product.{task}.{record_identity.object_id}", record_identity,
                         ArtifactIdentity(artifact_id, "scientific-product", record.SCHEMA, record.fingerprint(),
                                          artifact.logical.media_type, artifact.materialization.size_bytes),
                         ObjectIdentity.from_record(receipt.receipt_id, receipt), role, EvidenceCeiling.NON_PROMOTABLE,
                         artifact.logical.outcome_access, artifact.logical.visibility_ceiling))
    manifest = ContributionManifest(f"contribution.{draft.draft_id}", question, finding, scope,
                                    tuple(sorted(products, key=lambda v: v.product_id)), assessments, remaining,
                                    tuple(ObjectIdentity.from_record(p.contribution_id, p) for p in draft.contribution_parents))
    return (manifest,)


def _contribution_terminal(draft, entries):
    """Authored labels do not select the scientific wave or product meaning."""
    configs = [(operation.node_id, decode_canonical_bytes(operation.config_payload.encode(), BatteryOperationConfig,
                maximum_bytes=MAX_PRODUCT_BYTES)) for operation in draft.operations
               if operation.node_id in draft.selected_operation_ids and operation.config_identity.object_schema == BatteryOperationConfig.SCHEMA]
    terminals = [(node, config) for node, config in configs
                 if config.operation in {BatteryOperation.PROCEDURE, BatteryOperation.VOLTAGE}]
    terminal_products = [(task, record) for task, _, record in entries
                         if isinstance(record, (BatteryProcedureContribution, BatteryFurtherProduct))]
    if not terminals and not terminal_products:
        return None
    if len(terminals) != 1 or len(terminal_products) != 1:
        raise ValueError("battery contribution requires one unique declared terminal and actual product")
    node, config = terminals[0]
    task, product = terminal_products[0]
    expected_wave = "A" if isinstance(product, BatteryProcedureContribution) else "B"
    expected_operation = BatteryOperation.PROCEDURE if expected_wave == "A" else BatteryOperation.VOLTAGE
    if (node != task or config.operation is not expected_operation or config.wave != expected_wave
        or any(value.wave != expected_wave or value.source != config.source for _, value in configs)
        or any(record.source != config.source for _, _, record in entries
               if type(record).__module__.startswith(__package__) and hasattr(record, "source"))):
        raise ValueError("battery contribution changes its actual terminal role, wave or declared source")
    return config, product


def next_wave_builder(draft, manifest, authenticated_products):
    """Bind a new question to the actual assessed parent, retaining its scope."""
    if describe_contributions(draft, authenticated_products) != (manifest,):
        raise ValueError("next wave changes its exact authenticated contribution")
    entries = [(task, output, record) for task, outputs in authenticated_products["records"].items()
               for output, record in outputs.items()]
    config, product = _contribution_terminal(draft, entries)
    return battery_wave_b_draft(manifest, product) if config.wave == "A" else None
