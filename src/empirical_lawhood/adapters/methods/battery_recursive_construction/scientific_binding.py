# SPDX-License-Identifier: MPL-2.0
"""Pure bindings between the closed battery protocol and authored claims."""

from decimal import Decimal

from empirical_lawhood.kernel.evidence import ClaimSpec, EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import ConditionRole, ContributionRole, DevelopmentStudySpec
from empirical_lawhood.kernel.worlds import WorldKind

from .contracts import BatteryOperation, BatteryOperationConfig, BatterySourceContract


QUESTION_A = "Do exact-state/input channels faithfully supply hold continuation, and are SOC/capacity/temperature sufficient in the two assigned histories?"
QUESTION_B = "What equal-charge history contrast and current-proportionality defect occur on a newly supplied SPMe instance under four declared future current words?"


FURTHER_CRITERION = (
    "The complete assigned word census has assessed new-instance continuation and supports a bounded further voltage finding.",
    "Any missing/failed instance, incomplete nested control census, solver disagreement or illegitimate channel use.",
    ContributionRole.INSTANCE_PRODUCT, 1,
)


def _criterion(config):
    if config.operation is BatteryOperation.ASSESS:
        if config.wave == "A":
            return (
                "Exact internal state and source-input ledger at 300 s faithfully supply the assigned hold continuation.",
                "Any state/input substitution, incomplete clocks or restart discrepancy above the frozen voltage/capacity/temperature bounds.",
                ContributionRole.INSTANCE_PRODUCT, 0,
            )
        return (
            f"The new shared checkpoint faithfully supplies the changed future {config.future_word}, assessed on the actual instance.",
            "Assigned reference/full mismatch, failed conservation control, state substitution or incomplete continuation.",
            ContributionRole.INSTANCE_PRODUCT, 1,
        )
    if config.operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
        consumer = "C1" if config.operation is BatteryOperation.ADMIT_C1 else "C2"
        return (
            f"Assessed procedure can be admitted as a design operand within {consumer}'s predeclared allowed channels, retaining new-instance obligations.",
            "Missing actual procedure assessment, model/source/layout substitution, or required channel outside the consumer policy.",
            ContributionRole.DESIGN_OPERAND, 0,
        )
    if config.operation is BatteryOperation.VOLTAGE:
        return FURTHER_CRITERION
    raise ValueError("battery operation does not assess an authored scientific requirement")


def _validate_requirement(requirement, connection, *, criterion, source, unit_id, ports):
    condition, falsifier, role, prerequisite_count = criterion
    scope = requirement.scope
    expected_scope = {
        "system_id": "chen2020-spme", "world_id": "battery-recursive-numerical-world",
        "source_id": source.source_id, "source_config_sha256": source.fingerprint(),
        "quantity_ids": ("capacity", "temperature", "voltage"), "native_units": ("A.h", "K", "V"),
        "receiver_id": "spme-native-terminal", "clock_id": "model-seconds", "instance_id": unit_id,
        "population_id": None, "information_cutoff": None, "available_by": Decimal(300),
        "valid_from": Decimal(300), "valid_until": Decimal(600), "uncertainty_contract": None,
        "coordinate_meaning": condition,
    }
    if scope is None or any(getattr(scope, name) != expected for name, expected in expected_scope.items()):
        raise ValueError("battery requirement scientific scope differs from its frozen operation")
    if (requirement.condition != condition or requirement.falsifier != falsifier
            or connection.falsifier != falsifier
            or requirement.condition_role is not ConditionRole.INFORMATIONAL
            or requirement.permitted_roles != (role,) or connection.evidence_role is not role
            or requirement.background_assumption_ids != ("exposed-deterministic-model",)
            or len(requirement.further_requirement_ids) != prerequisite_count
            or requirement.resource_commitment is not None):
        raise ValueError("battery requirement criterion or falsifier differs from its frozen operation")
    if (connection.requirement_id != requirement.requirement_id
            or connection.assessment_operation_id != requirement.assessment_operation_id):
        raise ValueError("battery scientific connection names another requirement or assessor")
    if connection.consumer_input_id not in ports:
        raise ValueError("battery requirement names another scientific consumer port")


def validate_battery_scientific_requirement(config, requirement, connection):
    """Validate scientific meaning while leaving authored graph labels editable.

    Used for both the config-bound claim and each separately authored voltage
    prerequisite. Identity equality alone cannot validate units or criteria.
    """
    if config.operation is BatteryOperation.ASSESS:
        ports = ("checkpoint",)
    elif config.operation is BatteryOperation.VOLTAGE:
        ports = tuple(f"assessment-{word}" for word in ("early1", "early3", "hold", "late1"))
    else:
        ports = ("procedure",)
    _validate_requirement(requirement, connection, criterion=_criterion(config), source=config.source,
                          unit_id=config.unit_id, ports=ports)


def validate_battery_further_requirement(requirement, connection):
    """Validate a retained further-product projection under its closed B scope.

    A further product has a fixed source and preparation in this protocol. This
    checks that declaration without inventing config records or deriving science
    from editable graph labels. Actual config/root binding is checked separately.
    """
    _validate_requirement(requirement, connection, criterion=FURTHER_CRITERION,
                          source=BatterySourceContract(), unit_id="battery-preparation-b",
                          ports=tuple(f"assessment-{word}" for word in ("early1", "early3", "hold", "late1")))


def validate_battery_scientific_binding(definition, config):
    """Check the registered operation and its exact closed scientific scope."""
    if (config.operation is not definition.operation
            or (definition.wave is not None and config.wave != definition.wave)):
        raise ValueError("battery configuration differs from its registered operation or wave")
    assessed = config.operation in {
        BatteryOperation.ASSESS, BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2, BatteryOperation.VOLTAGE,
    }
    if not assessed:
        if config.requirement is not None or config.connection is not None:
            raise ValueError("battery non-assessment operation carries an undeclared scientific claim")
        return
    if config.requirement is None or config.connection is None:
        raise ValueError("battery assessment lacks its committed scientific requirement")
    validate_battery_scientific_requirement(config, config.requirement, config.connection)
    if config.operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
        parent = config.connection.supplier_contribution
        if parent is None or parent.object_fingerprint != config.contribution_sha256:
            raise ValueError("battery admission differs from its exact selected contribution parent")


def _supplier_operands(config, port):
    """Expected producer meaning, independent of authored node/edge labels."""
    operation = config.operation
    if port == "checkpoint":
        return BatteryOperation.CHECKPOINT, config.history, None
    if operation in {BatteryOperation.REFERENCE, BatteryOperation.FULL, BatteryOperation.TIGHTER} and port == "admission":
        return BatteryOperation.ADMIT_C1, config.history, None
    if operation is BatteryOperation.ASSESS and port in {"reference", "full", "soc"}:
        return BatteryOperation(port.upper()), config.history, config.future_word
    if operation is BatteryOperation.PROCEDURE:
        kind, history = port.split("-", 1)
        return (BatteryOperation.CHECKPOINT if kind == "checkpoint" else BatteryOperation.ASSESS), history, "hold"
    if operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2} and port == "summary":
        return BatteryOperation.PROJECT, config.history, None
    if operation is BatteryOperation.VOLTAGE:
        if port in {"c1", "c2"}:
            return (BatteryOperation.ADMIT_C1 if port == "c1" else BatteryOperation.ADMIT_C2), config.history, None
        if port.startswith("assessment-"):
            return BatteryOperation.ASSESS, config.history, port.removeprefix("assessment-")
        word, route = port.split("-", 1)
        return BatteryOperation(route.upper()), config.history, word
    if port == "procedure" and operation in {BatteryOperation.IMPORT, BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
        return BatteryOperation.IMPORT, config.history, None
    raise ValueError("battery input has no frozen scientific producer meaning")


def _internal_supplier(context, records, node, port):
    links = tuple(link for link in context.links
                  if link.consumer_node_id == node and link.consumer_input_id == port)
    if len(links) != 1 or links[0].producer_node_id not in records:
        raise ValueError("battery scientific prerequisite lacks its actual internal supplier")
    return links[0].producer_node_id, records[links[0].producer_node_id]


def _validate_assessed_dependencies(config, context, records):
    requirements = tuple(requirement for requirement in context.requirements
                         if requirement.assessment_operation_id == context.node_id)
    if config.operation is BatteryOperation.ASSESS:
        if requirements != (config.requirement,):
            raise ValueError("battery restart assessor changes its complete requirement census")
        full_node, _ = _internal_supplier(context, records, context.node_id, "full")
        checkpoint_node, _ = _internal_supplier(context, records, context.node_id, "checkpoint")
        if (config.requirement.consumer_operation_id != full_node
                or config.connection.supplier_operation_id != checkpoint_node):
            raise ValueError("battery restart requirement differs from its actual assessed consumer or checkpoint supplier")
        if config.wave == "B":
            _, admission = _internal_supplier(context, records, full_node, "admission")
            if (not isinstance(admission, BatteryOperationConfig)
                    or admission.operation is not BatteryOperation.ADMIT_C1
                    or admission.requirement is None
                    or config.requirement.further_requirement_ids != (admission.requirement.requirement_id,)):
                raise ValueError("battery instance prerequisite differs from its actual C1 admission")
    elif config.operation in {BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}:
        if requirements != (config.requirement,) or config.requirement.consumer_operation_id != context.node_id:
            raise ValueError("battery admission assessor changes its complete requirement census")
    elif config.operation is BatteryOperation.VOLTAGE:
        if len(requirements) != 4 or any(requirement.consumer_operation_id != context.node_id for requirement in requirements):
            raise ValueError("battery further assessor changes its complete four-word requirement census")
        for requirement in requirements:
            connections = tuple(connection for connection in context.connections
                                if connection.requirement_id == requirement.requirement_id)
            if len(connections) != 1:
                raise ValueError("battery further prerequisite lacks its unique actual connection")
            _, assessment = _internal_supplier(context, records, context.node_id, connections[0].consumer_input_id)
            if (not isinstance(assessment, BatteryOperationConfig)
                    or assessment.operation is not BatteryOperation.ASSESS
                    or assessment.requirement is None
                    or requirement.further_requirement_ids != (assessment.requirement.requirement_id,)):
                raise ValueError("battery further prerequisite differs from its actual word instance assessment")


def validate_battery_scientific_root(config, context):
    """Bind the actual root and selected suppliers to the closed protocol.

    The fixed embedded requirement scope cannot establish that a caller's root
    names the same system, world, source or views. Similarly, schema equality
    does not prove that an internal supplier has the assigned history/word.
    """
    root = context.root
    views = ("coarse",) if config.wave == "A" else ("coarse", "tighter")
    question = QUESTION_A if config.wave == "A" else QUESTION_B
    if (not isinstance(root, DevelopmentStudySpec)
            or root.system != ObjectIdentity.from_record("chen2020-spme", config.source)
            or root.world_id != "battery-recursive-numerical-world"
            or root.world_kind is not WorldKind.NUMERICAL_SIMULATOR
            or root.assigned_unit_ids != (config.unit_id,)
            or root.numerical_view_ids != views
            or root.scientific_operands != (ObjectIdentity.from_record(config.source.source_id, config.source),)
            or root.question != question
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY):
        raise ValueError("battery scientific root changes its frozen system, world, source, preparation or views")
    expected_claim = {
        "world_id": root.world_id, "relation_id": "battery-recursive-state-and-voltage",
        "proposition": question,
        "estimand": "Complete declared native discrepancies and signed voltage contrasts; no population inference.",
        "physical_independent_unit_id": config.unit_id, "requested_rung": None,
        "evidence_ceiling": EvidenceCeiling.NON_PROMOTABLE,
        "outcome_access": OutcomeAccess.DEVELOPMENT_VISIBLE,
        "visibility_ceiling": VisibilityCeiling.DEVELOPMENT_ONLY,
        "promotion_rule": "Never promotes development completion to scientific qualification.",
        "assumption_ids": ("exposed-deterministic-model",), "derivation_parent_ids": (),
        "parent_visibility_ceilings": (), "numerical_view_ids": views, "extensions": (),
    }
    if len(root.claims) != 1 or any(getattr(root.claims[0], name) != value for name, value in expected_claim.items()):
        raise ValueError("battery root claim changes its closed proposition, quantifier, assumptions or development boundary")
    records = {row.node_id: row.record for row in context.config_inputs}
    if records.get(context.node_id) != config:
        raise ValueError("battery scientific root lacks its actual selected configuration")
    for link in context.links:
        if link.consumer_node_id != context.node_id:
            continue
        port = link.consumer_input_id
        role = ("MODEL" if port in {"manifest", "procedure", "admission", "c1", "c2"} else
                "OUTCOME" if config.operation is BatteryOperation.VOLTAGE
                or (config.operation is BatteryOperation.PROCEDURE and port.startswith("assessment-")) else "HISTORY")
        if link.scientific_role != role:
            raise ValueError("battery scientific input changes its frozen evidence role")
        if link.producer_node_id is None:
            if (config.operation not in {BatteryOperation.IMPORT, BatteryOperation.ADMIT_C1, BatteryOperation.ADMIT_C2}
                    or link.consumer_input_id not in {"manifest", "procedure"}):
                raise ValueError("battery selected instance input requires its new internal scientific supplier")
            continue
        supplier = records.get(link.producer_node_id)
        if not isinstance(supplier, BatteryOperationConfig):
            raise ValueError("battery selected scientific supplier has another configuration type")
        expected_operation, history, word = _supplier_operands(config, link.consumer_input_id)
        if (link.producer_output_id != "product" or supplier.operation is not expected_operation
                or supplier.wave != config.wave or supplier.unit_id != config.unit_id
                or supplier.history != history or supplier.source != config.source
                or supplier.protocol_sha256 != config.protocol_sha256
                or (word is not None and supplier.future_word != word)):
            raise ValueError("battery selected scientific supplier changes its operation, source, preparation, history or future word")
        if (config.contribution_sha256 is not None and supplier.contribution_sha256 is not None
                and config.contribution_sha256 != supplier.contribution_sha256):
            raise ValueError("battery selected scientific supplier changes its contribution parent")
    _validate_assessed_dependencies(config, context, records)


def resolve_battery_scientific_claim(config, context, requirement, connection) -> ClaimSpec:
    """Resolve a scoped connection to its exact declared scientific root claim.

    Maintained connection aliases identify an assessed requirement within the
    aggregate question. They are meaningful only with that actual selected
    requirement, its closed native criterion and the exact current root claim.
    An arbitrary stable ID or another question's claim supplies none of these.
    """
    if (not isinstance(config, BatteryOperationConfig)
            or requirement.assessment_operation_id != context.node_id
            or connection.assessment_operation_id != context.node_id
            or requirement not in context.requirements
            or connection not in context.connections):
        raise ValueError("battery scientific claim lacks its actual selected requirement and assessor")
    validate_battery_scientific_root(config, context)
    validate_battery_scientific_requirement(config, requirement, connection)
    claim = context.root.claims[0]
    if connection.claim_id not in {claim.claim_id, f"{requirement.requirement_id}.claim"}:
        raise ValueError("battery scientific connection claim does not resolve to its exact declared root claim")
    return claim
