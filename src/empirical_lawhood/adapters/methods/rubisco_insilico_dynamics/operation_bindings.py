# SPDX-License-Identifier: MPL-2.0
"""Cold full-model preparation registrations; native tools enter only execute."""

from hashlib import sha256
from empirical_lawhood.adapters.methods.rubisco_nomination_preparation.contracts import (
    NominationDossier,
)
from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.decoding import decode_canonical_bytes
from empirical_lawhood.kernel.evidence import (
    ClaimSpec,
    EvidenceCeiling,
    OutcomeAccess,
    VisibilityCeiling,
)
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.recursive_requirements import (
    AssessmentPhase,
    DevelopmentStudySpec,
    RequirementSupplyAssessment,
)
from empirical_lawhood.kernel.worlds import WorldKind
from empirical_lawhood.runtime.artifacts import ArtifactProfile, ReceiptCheck
from empirical_lawhood.runtime.capabilities import CapabilityKind, CapabilityPermission
from empirical_lawhood.runtime.execution import (
    RunnerResult,
    TaskOutputPayload,
    WorkerInputKind,
)
from empirical_lawhood.runtime.plans import OutputTemplate, ScientificStage
from empirical_lawhood.runtime.recursive_compiler import (
    RecursivePortContract,
)
from . import contracts as c
from empirical_lawhood.adapters.methods.rubisco_insilico_structure import (
    contracts as sc,
)

MEDIA = "application/json"
BUDGET = ResourceBudget(1, None, 0, None, None, None)
OPERATIONS = ("assess-preparation", "prepare")


def operation_inputs(operation):
    if operation not in OPERATIONS:
        raise ValueError("unknown preparation operation")
    base = (
        ("coordinates", sc.AssemblyCoordinates),
        ("inventory", sc.StructuralInventory),
        ("nomination", NominationDossier),
        ("source", c.PreparationSelection),
    )
    extra = (
        ("preparation", c.PreparationProduct),
        *((f"assets-{i:02d}", c.ModelAssets) for i in range(len(c.model_roster()))),
    )
    return tuple(sorted(base + (extra if operation == "assess-preparation" else ())))


def operation_outputs(operation):
    if operation not in OPERATIONS:
        raise ValueError("unknown preparation operation")
    return (
        (("assessment", c.PreparationAssessment),)
        if operation == "assess-preparation"
        else tuple(
            sorted(
                (
                    ("preparation", c.PreparationProduct),
                    *(
                        (f"assets-{i:02d}", c.ModelAssets)
                        for i in range(len(c.model_roster()))
                    ),
                )
            )
        )
    )


def development_root(config, *, study_id):
    # The assessed prerequisite is the actual nomination OUTCOME: compiler
    # claims must use its world/system. The new mapping endpoint remains the
    # separately registered c.scope(source), without transporting qualification.
    world = config.prior_nomination_scope.world_id
    view = "view." + c.NAMESPACE + ".full-model-preparation"
    claim = ClaimSpec(
        "claim." + c.NAMESPACE + ".preparation",
        world,
        "population.exposed-original-structures",
        c.QUESTION,
        "Complete controlled 24-model preparation census and assigned-parameter assessment; trajectories and kinetics remain unentered.",
        c.UNIT,
        None,
        EvidenceCeiling.NON_PROMOTABLE,
        OutcomeAccess.DEVELOPMENT_VISIBLE,
        VisibilityCeiling.DEVELOPMENT_ONLY,
        "Preparation assessment does not establish dynamics, kinetics or fresh biology.",
        ("no-kinetic-qualification", "preparation-only"),
        numerical_view_ids=(view,),
    )
    return DevelopmentStudySpec(
        study_id,
        c.QUESTION,
        ObjectIdentity.from_record(
            config.prior_nomination_scope.system_id, config.source
        ),
        world,
        WorldKind.ANALYTIC_REFERENCE,
        (c.UNIT,),
        (view,),
        (claim,),
        config.operands,
    )


def scientific_root_validator(config, context):
    config.__post_init__()
    node = c.NAMESPACE + "." + config.operation
    configs = {row.node_id: row.record for row in context.config_inputs}
    if (
        type(context.root) is not DevelopmentStudySpec
        or context.root != development_root(config, study_id=context.root.study_id)
        or context.node_id != node
        or context.stage is not ScientificStage.FALSIFY
        or context.unit_ids != (c.UNIT,)
        or context.selected_unit_ids != (c.UNIT,)
        or context.complete_unit_census != (config.operation == "prepare")
        or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
        or context.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
        or len(context.config_inputs) != 2
        or set(configs)
        != {c.NAMESPACE + ".prepare", c.NAMESPACE + ".assess-preparation"}
        or configs.get(node) != config
        or any(
            type(value) is not c.PreparationOperationConfig
            or value.source != config.source
            or value.prior_nomination_scope != config.prior_nomination_scope
            or value.operands != config.operands
            for value in configs.values()
        )
    ):
        raise ValueError(
            "model preparation changes exact scientific root/config/exposure"
        )
    from .recursive_translation import validate_requirement_config

    if len(context.requirements) != 1 or len(context.connections) != 1:
        raise ValueError("model preparation changes requirement/connection census")
    validate_requirement_config(config, context.requirements[0], context.connections[0])
    links = [r for r in context.links if r.consumer_node_id == node]
    for link in links:
        if link.consumer_input_id not in (
            "source",
            "nomination",
            "inventory",
            "coordinates",
        ) and (
            link.external_input_id is not None
            or link.producer_node_id != c.NAMESPACE + ".prepare"
            or link.producer_output_id != link.consumer_input_id
        ):
            raise ValueError(
                "preparation assessor changes exact native asset dependency"
            )
    roles = {
        name: (
            "SOURCE"
            if name == "source"
            else "OUTCOME"
            if name == "nomination"
            else "HISTORY"
        )
        for name, _ in operation_inputs(config.operation)
    }
    if (
        len(links) != len(roles)
        or {r.consumer_input_id for r in links} != set(roles)
        or any(r.scientific_role != roles[r.consumer_input_id] for r in links)
        or any(
            r.external_input_id is None
            for r in links
            if r.consumer_input_id
            in ("source", "nomination", "inventory", "coordinates")
        )
        or len(context.requirements) != 1
        or context.requirements[0].scope != config.prior_nomination_scope
    ):
        raise ValueError("model preparation changes authentic nomination/operand roles")


def scientific_operand_sha256s(config):
    return tuple(sorted(r.object_fingerprint for r in config.operands))


def scientific_unit_ids(config):
    return (c.UNIT,)


def operation_declarations():
    from functools import partial
    from empirical_lawhood.runtime.recursive_provider import (
        RecursiveOperationDeclaration, RecursiveScientificHooks, RecursiveInquiryHooks, RecursiveExecutionProperties)
    from .ordinary_preparation import prepare_native_work
    from .recursive_translation import (describe_contributions, next_wave_builder, inquiry_outcome_projector,
        inquiry_evidence_projector, inquiry_endpoint_validator)
    return tuple(RecursiveOperationDeclaration(
        capability_key=c.NAMESPACE + "." + operation, capability_version="1.0.0",
        implementation_id=c.NAMESPACE + ".full-model-" + operation + "-v1",
        kind=CapabilityKind.SIMULATOR if operation == "prepare" else CapabilityKind.ANALYSIS,
        config_record_type=c.PreparationOperationConfig, stage=ScientificStage.FALSIFY,
        input_ports=tuple(RecursivePortContract(name, record.SCHEMA, MEDIA, None)
            for name, record in operation_inputs(operation)),
        outputs=tuple(OutputTemplate(name, record.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA, ".json")
            for name, record in operation_outputs(operation)),
        permissions=tuple(sorted((CapabilityPermission.READ_DEVELOPMENT, CapabilityPermission.READ_EXTERNAL_ARTIFACTS,
            CapabilityPermission.WRITE_EXTERNAL_ARTIFACTS))),
        evidence_ceiling=EvidenceCeiling.NON_PROMOTABLE, outcome_access=OutcomeAccess.DEVELOPMENT_VISIBLE,
        visibility_ceiling=VisibilityCeiling.DEVELOPMENT_ONLY, resources=BUDGET,
        conformance_check_ids=("exact-nomination-and-original-sequences", "full-l8s8-original-assembly",
            "full24-prepared-assets-no-kinetic-promotion"), runner_factory=partial(PreparationRunner, operation),
        record_codecs=output_codecs(), scientific_hooks=RecursiveScientificHooks(
            assessment_projector=project_assessments if operation == "assess-preparation" else None,
            scientific_operand_sha256s=scientific_operand_sha256s, scientific_unit_ids=scientific_unit_ids,
            native_effect_slot_ids=native_effect_slot_ids if operation == "prepare" else None,
            scientific_root_validator=scientific_root_validator),
        inquiry_hooks=RecursiveInquiryHooks(contribution_describer=describe_contributions,
            next_wave_builder=next_wave_builder, inquiry_outcome_projector=inquiry_outcome_projector,
            inquiry_evidence_projector=inquiry_evidence_projector, inquiry_endpoint_validator=inquiry_endpoint_validator),
        execution_properties=RecursiveExecutionProperties(native_effect=operation == "prepare",
            complete_unit_census=operation == "prepare", native_work_preparer=prepare_native_work if operation == "prepare" else None))
        for operation in OPERATIONS)


def operation_manifests():
    return tuple(row.manifest() for row in operation_declarations())


def operation_registrations():
    return tuple(row.registration() for row in operation_declarations())


def native_effect_slot_ids(config):
    config.__post_init__()
    return tuple(
        sorted(
            "native-slot."
            + c.NAMESPACE
            + "."
            + sha256(
                (config.source.fingerprint() + "|" + "|".join(row)).encode()
            ).hexdigest()[:24]
            for row in c.model_roster()
        )
    )


def output_codecs():
    return {
        record.SCHEMA: record
        for record in (
            c.PreparationOperationConfig,
            c.PreparationSelection,
            NominationDossier,
            sc.StructuralInventory,
            sc.AssemblyCoordinates,
            c.PreparationProduct,
            c.ModelAssets,
            c.PreparationAssessment,
        )
    }


class PreparationRunner:
    def __init__(self, operation):
        if operation not in OPERATIONS:
            raise ValueError("unknown preparation operation")
        self.operation = operation
        self.manifest = dict(zip(OPERATIONS, operation_manifests(), strict=True))[
            operation
        ]

    def validated_inputs(self, context):
        """Read the exact original config/source/history/dependency census."""
        from . import science

        node = c.NAMESPACE + "." + self.operation
        expected = operation_inputs(self.operation)
        schemas = {codec.SCHEMA: codec for _, codec in expected}
        schemas[c.PreparationOperationConfig.SCHEMA] = c.PreparationOperationConfig
        if (
            context.task_id != node
            or context.permissions != self.manifest.permissions
            or context.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
            or context.resource_budget != BUDGET
            or len(context.input_ports) != len(expected) + 1
        ):
            raise ValueError("preparation worker changes exact input census/access")
        decoded = []
        for port in context.input_ports:
            if (
                port.payload_schema not in schemas
                or port.media_type != MEDIA
                or port.outcome_access is not OutcomeAccess.DEVELOPMENT_VISIBLE
                or port.visibility_ceiling is not VisibilityCeiling.DEVELOPMENT_ONLY
            ):
                raise ValueError(
                    "preparation input changes exact canonical type/access"
                )
            raw = port.read()
            if len(raw) != port.size_bytes:
                raise ValueError("preparation truncates input materialization")
            decoded.append(
                (
                    port,
                    decode_canonical_bytes(
                        raw, schemas[port.payload_schema], maximum_bytes=None
                    ),
                )
            )
        matches = [
            (p, r) for p, r in decoded if type(r) is c.PreparationOperationConfig
        ]
        if len(matches) != 1:
            raise ValueError("preparation omits/duplicates selected config")
        config_port, config = matches[0]
        if (
            config_port.kind is not WorkerInputKind.EXTERNAL
            or config_port.artifact_id != context.config.artifact_id
        ):
            raise ValueError("preparation substitutes exact config materialization")
        used = {id(config_port)}
        values = {}
        for name, codec in expected:
            external = name in ("source", "nomination", "inventory", "coordinates")
            key = f"artifact.{context.run_id}.{c.NAMESPACE}.prepare.{name}"
            matches = [
                (p, r)
                for p, r in decoded
                if id(p) not in used
                and type(r) is codec
                and (
                    p.kind is WorkerInputKind.EXTERNAL
                    if external
                    else p.kind is WorkerInputKind.DEPENDENCY
                    and p.artifact_id == key
                )
            ]
            if len(matches) != 1:
                raise ValueError(
                    "preparation substitutes external custody or native output identity"
                )
            port, record = matches[0]
            used.add(id(port))
            values[name] = record
            if not external and not any(
                r.task_id == c.NAMESPACE + ".prepare"
                and port.materialization_id in r.output_materialization_ids
                for r in context.dependency_receipts
            ):
                raise ValueError(
                    "preparation output lacks its actual native dependency receipt"
                )
        producers = (
            set() if self.operation == "prepare" else {c.NAMESPACE + ".prepare"}
        )
        if (
            len(used) != len(decoded)
            or len(context.dependency_receipts) != len(producers)
            or {r.task_id for r in context.dependency_receipts} != producers
        ):
            raise ValueError(
                "preparation changes exact decoded input/dependency census"
            )
        source, nomination = values["source"], values["nomination"]
        if (
            config.operation != self.operation
            or config.config_id != context.config.config_id
            or config.fingerprint() != context.config.content_sha256
            or source != config.source
            or nomination.scope != config.prior_nomination_scope
            or tuple(
                sorted(
                    (
                        c.identity(values[name])
                        for name in (
                            "source",
                            "nomination",
                            "inventory",
                            "coordinates",
                        )
                    ),
                    key=lambda r: r.object_id,
                )
            )
            != config.operands
        ):
            raise ValueError(
                "preparation substitutes exact source or authenticated history"
            )
        science.validate_source(
            source, nomination, values["inventory"], values["coordinates"]
        )
        return config, values

    def preflight(self, context):
        if self.operation == "prepare":
            from .ordinary_preparation import prepare_native_work
            contract = context.prepared_invocation
            if contract is None:
                raise ValueError("SOFTWARE: original preparation needs its complete current specialist contract")
            work = prepare_native_work(runner=self, context=context, expected_parent=contract.expected_parent_contact)
            if work != contract.native_work or work.isolated_selection is None:
                raise ValueError("original preparation changes its frozen complete specialist selection")

    def execute(self, context):
        if self.operation == "prepare":
            raise ValueError("SOFTWARE: original preparation requires common prepared native progress")
        return self._execute(context, None)

    def execute_with_native_subwork(self, context, native_subwork, progress=None):
        contract = context.prepared_invocation
        if self.operation != "prepare" or contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("SOFTWARE: original preparation needs complete actual specialist preparation before contact")
        contract.validate_context(context)
        return self._execute(context, native_subwork)

    def _execute(self, context, native_subwork):
        from . import science

        try:
            config, values = self.validated_inputs(context)
            node = c.NAMESPACE + "." + self.operation
            source, nomination = values["source"], values["nomination"]
            if self.operation == "prepare":
                from . import native

                product, assets = native.prepare(
                    source,
                    nomination,
                    values["inventory"],
                    values["coordinates"],
                    workdir=source.native_workdir,
                    context=context,
                    native_subwork=native_subwork,
                )
                result = {
                    "preparation": product,
                    **{f"assets-{i:02d}": row for i, row in enumerate(assets)},
                }
                if (
                    len(assets) != len(c.model_roster())
                    or tuple(
                        (a.construct_id, a.joint_view_id, a.parameter_view)
                        for a in assets
                    )
                    != c.model_roster()
                ):
                    raise ValueError(
                        "native preparation changes full24 model asset census/order"
                    )
            else:
                assets = tuple(
                    values[f"assets-{i:02d}"] for i in range(len(c.model_roster()))
                )
                result = {
                    "assessment": science.assess_preparation(
                        source,
                        nomination,
                        values["inventory"],
                        values["coordinates"],
                        values["preparation"],
                        assets,
                    )
                }
            declared = operation_outputs(self.operation)
            if tuple(
                (p.output_id, p.payload_schema, p.profile, p.media_type)
                for p in context.output_ports
            ) != tuple(
                (node + "." + name, codec.SCHEMA, ArtifactProfile.CANONICAL_JSON, MEDIA)
                for name, codec in declared
            ) or set(result) != {name for name, _ in declared}:
                raise ValueError("preparation changes complete actual output census")
            for name, codec in declared:
                if type(result[name]) is not codec:
                    raise ValueError("preparation output changes canonical type")
                result[name].__post_init__()
            return RunnerResult(
                tuple(
                    TaskOutputPayload(node + "." + name, result[name].canonical_bytes())
                    for name, _ in declared
                ),
                (
                    ReceiptCheck(
                        "complete-model-preparation-no-trajectory-or-kinetics", True, ()
                    ),
                ),
            )
        finally:
            for port in context.input_ports:
                port.close()


def project_assessments(record, requirement, connection):
    from .recursive_translation import validate_requirement_assessment

    validate_requirement_assessment(record, requirement, connection)
    return tuple(
        RequirementSupplyAssessment(
            "assessment." + record.product_id + "." + phase.value.lower(),
            ObjectIdentity.from_record(requirement.requirement_id, requirement),
            ObjectIdentity.from_record(connection.connection_id, connection),
            phase,
            record.preparation_disposition,
            record.prior_nomination_scope.instance_id,
            (c.identity(record),),
            tuple(
                sorted(
                    {
                        reason
                        for _, _, reasons in record.model_dispositions
                        for reason in reasons
                    }
                )
            ),
        )
        for phase in AssessmentPhase
    )
