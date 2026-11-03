# SPDX-License-Identifier: MPL-2.0
"""Derived prospective factorial phases over exact original scientific inputs.

The bank is a bounded immutable artifact reference here. The public Matrix
entry authenticates its actual record and original qualified calibration;
compilation, candidate publication and these projections grant no authority.
"""

from dataclasses import dataclass, replace

from empirical_lawhood.kernel.authority import ResourceBudget
from empirical_lawhood.kernel.evidence import OutcomeAccess, VisibilityCeiling
from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.kernel.references import ArtifactIdentity
from empirical_lawhood.kernel.serialization import CanonicalRecord
from empirical_lawhood.planning.recursive_authoring import (
    RecursiveExternalInput, RecursiveInputLink, RecursiveOperationSpec, RecursiveStudyDraft,
)
from empirical_lawhood.planning.study_authoring import StudyDraft
from empirical_lawhood.runtime.candidate_compiler import required_candidate_obligation_ids
from empirical_lawhood.runtime.capabilities import CapabilityConfigRef
from empirical_lawhood.runtime.plans import ProtocolStepTemplate, ProtocolTemplate

from .programme_factorial_confirmation import (
    ScheduledFactorialConfirmationConfig, ScheduledFactorialCriteriaBinding, ScheduledFactorialCriteriaConfig,
    ScheduledFactorialConfirmationSealConfig, assess_node_id, confirmation_input_seal,
    freeze_node_id, input_seal_node_id, operation_declarations,
)
from .programme_factorial_confirmation_custody import require_original_criteria_design
from .programme_selection import ScheduledRevisionDataBank
from .programme_reduction import ScheduledProgrammeReduction


@dataclass(frozen=True, slots=True)
class ScheduledFactorialProspectiveStudy:
    draft: RecursiveStudyDraft
    input_records: tuple[tuple[str, CanonicalRecord], ...]
    bank_artifact: ArtifactIdentity
    execution_dependencies: tuple[str, ...] = ()

    @property
    def executable(self):
        """Software graph closure only; actual scientific grants remain separate."""
        return not self.execution_dependencies


def _lower(config, *, root, bank_artifact, operational_budget, reduction=None, data=None, paired_artifacts=None):
    freezing = type(config) is ScheduledFactorialCriteriaConfig
    sealing = type(config) is ScheduledFactorialConfirmationSealConfig
    assessing = type(config) is ScheduledFactorialConfirmationConfig
    if not (freezing or sealing or assessing):
        raise TypeError("protected factorial lowering requires its exact phase configuration")
    config.__post_init__()
    if type(root) is not StudyDraft or root.system is None or root.campaign is None or root.experiment is None:
        raise TypeError("protected factorial lowering requires the original prospective scientific root")
    if (type(bank_artifact) is not ArtifactIdentity or bank_artifact.artifact_id != config.bank.object_id
            or bank_artifact.payload_schema != config.bank.object_schema
            or bank_artifact.sha256 != config.bank.object_fingerprint or bank_artifact.media_type != "application/json"
            or type(bank_artifact.size_bytes) is not int or bank_artifact.size_bytes <= 0):
        raise ValueError("protected factorial lowering substitutes the exact original bounded bank artifact")
    declaration = operation_declarations()[0 if freezing else 2 if sealing else 1]
    bank_port = next(value for value in declaration.input_ports if value.port_id == "bank")
    if bank_port.maximum_size_bytes is not None and bank_artifact.size_bytes > bank_port.maximum_size_bytes:
        raise ValueError("protected factorial source exceeds its exact declared bank port byte bound")
    if type(operational_budget) is not ResourceBudget or not declaration.resources.contains(operational_budget):
        raise ValueError("protected factorial lowering changes the selected contained operational budget")
    if config.specification.identity not in {value.object_identity for value in root.design_inputs}:
        raise ValueError("protected factorial lowering omits the original declared statistical specification")
    if not freezing:
        require_original_criteria_design(root, config.criteria)
    records = {"programme": config.programme, "specification": config.specification}
    references = {}
    if not freezing:
        records["criteria"] = config.criteria
    if assessing:
        for name, record, identity, kind, field in (
            ("reduction", reduction, config.reduction, ScheduledProgrammeReduction, "reduction_id"),
            ("data", data, config.data, ScheduledRevisionDataBank, "bank_id"),
        ):
            reference = None if paired_artifacts is None else paired_artifacts.get(name)
            if reference is not None:
                if (identity is None or record is not None or type(reference) is not ArtifactIdentity
                        or reference.artifact_id != identity.object_id or reference.payload_schema != identity.object_schema
                        or reference.sha256 != identity.object_fingerprint or reference.media_type != "application/json"
                        or type(reference.size_bytes) is not int or reference.size_bytes <= 0):
                    raise ValueError("protected factorial lowering changes its original paired artifact reference")
                references[name] = reference
                continue
            if (identity is None) != (record is None) or record is not None and (
                    type(record) is not kind or ObjectIdentity.from_record(getattr(record, field), record) != identity):
                raise ValueError("protected factorial lowering substitutes its exact original paired " + name)
            if record is not None:
                record.__post_init__()
                records[name] = record
        if paired_artifacts is not None and set(paired_artifacts) != set(references):
            raise ValueError("protected factorial lowering introduces an undeclared paired artifact")
    elif reduction is not None or data is not None or paired_artifacts:
        raise ValueError("blind factorial freeze cannot consume acquired paired outcomes")
    node = (freeze_node_id(config.specification) if freezing else input_seal_node_id(config.specification)
        if sealing else assess_node_id(config.specification))
    registration, manifest = declaration.registration(), declaration.manifest()
    config_ref = CapabilityConfigRef(config.config_id, config.SCHEMA, manifest.config_schema_sha256,
        config.fingerprint(), config.config_id)
    own_obligation = "obligation." + node + ".original-factorial-design"
    step = ProtocolStepTemplate(node, declaration.stage, manifest.capability_key, manifest.capability_version,
        config_ref, (), declaration.outputs, declaration.permissions, declaration.outcome_access,
        declaration.visibility_ceiling, operational_budget, (), declaration.execution_properties.barrier, 1,
        (own_obligation,))
    obligations = required_candidate_obligation_ids(root.experiment,
        ProtocolTemplate("template."+node, "1.0.0", (step,), False, False, True))
    operation = RecursiveOperationSpec.from_config(node_id=node, selection=registration.selection,
        config_id=config.config_id, config=config, obligation_ids=obligations, resource_budget=operational_budget)
    external = [RecursiveExternalInput("external."+bank_artifact.artifact_id, bank_artifact.artifact_id,
        bank_artifact.payload_schema, bank_artifact.media_type, bank_artifact.size_bytes,
        OutcomeAccess.OUTCOME_BLIND, VisibilityCeiling.PROSPECTIVE, bank_artifact.sha256, "SOURCE")]
    links = [RecursiveInputLink("edge."+node+".bank", node, "bank", None, None,
        "external."+bank_artifact.artifact_id, "SOURCE")]
    inputs = []
    for name, record in sorted(records.items()):
        identity = (record.identity if name != "reduction" else
            ObjectIdentity.from_record(record.reduction_id, record))
        logical_id = identity.object_id
        input_id = "external."+logical_id
        sealed = name in ("data", "reduction")
        raw = record.canonical_bytes()
        port = next(value for value in declaration.input_ports if value.port_id == name)
        if port.maximum_size_bytes is not None and len(raw) > port.maximum_size_bytes:
            raise ValueError("protected factorial source exceeds its exact declared port byte bound")
        external.append(RecursiveExternalInput(input_id, logical_id, identity.object_schema, "application/json",
            len(raw), OutcomeAccess.EVALUATION_SEALED if sealed else OutcomeAccess.OUTCOME_BLIND,
            VisibilityCeiling.PROSPECTIVE, identity.object_fingerprint, "SOURCE"))
        links.append(RecursiveInputLink("edge."+node+"."+name, node, name, None, None, input_id, "SOURCE"))
        inputs.append((logical_id, record))
    for name, reference in sorted(references.items()):
        port = next(value for value in declaration.input_ports if value.port_id == name)
        if port.maximum_size_bytes is not None and reference.size_bytes > port.maximum_size_bytes:
            raise ValueError("protected factorial source exceeds its exact declared port byte bound")
        input_id = "external."+reference.artifact_id
        external.append(RecursiveExternalInput(input_id, reference.artifact_id, reference.payload_schema,
            "application/json", reference.size_bytes, OutcomeAccess.EVALUATION_SEALED,
            VisibilityCeiling.PROSPECTIVE, reference.sha256, "SOURCE"))
        links.append(RecursiveInputLink("edge."+node+"."+name, node, name, None, None, input_id, "SOURCE"))
    campaign = replace(root.campaign, budget=operational_budget,
        authority_policy=ObjectIdentity.from_record(root.system.authority_policy.policy_id, root.system.authority_policy))
    selected_root = replace(root, campaign=campaign)
    draft = RecursiveStudyDraft("draft."+node, root.question, campaign, (), (), (), (operation,),
        tuple(sorted(external, key=lambda row: row.input_id)), tuple(sorted(links, key=lambda row: row.edge_id)),
        (node,), prospective_draft=selected_root)
    if assessing:
        seal = _lower(confirmation_input_seal(config).configuration, root=root, bank_artifact=bank_artifact,
            operational_budget=operational_budget)
        owned = set(operation.obligation_ids)
        seal_operations = tuple(replace(value, obligation_ids=tuple(key for key in value.obligation_ids if key not in owned))
            for value in seal.draft.operations)
        edge = RecursiveInputLink("edge."+node+".input-seal", node, "input-seal", input_seal_node_id(config.specification),
            "product", None, "SOURCE")
        draft = replace(draft,
            operations=tuple(sorted((*draft.operations, *seal_operations), key=lambda value: value.node_id)),
            external_inputs=tuple(sorted(set((*draft.external_inputs, *seal.draft.external_inputs)), key=lambda value: value.input_id)),
            links=tuple(sorted((*draft.links, *seal.draft.links, edge), key=lambda value: value.edge_id)),
            selected_operation_ids=tuple(sorted((*draft.selected_operation_ids, *seal.draft.selected_operation_ids))))
        campaign = replace(draft.campaign, budget=ResourceBudget.aggregate(value.resource_budget for value in draft.operations))
        draft = replace(draft, campaign=campaign, prospective_draft=replace(draft.prospective_draft, campaign=campaign))
        inputs = list(set((*inputs, *seal.input_records)))
    return ScheduledFactorialProspectiveStudy(draft, tuple(sorted(inputs)), bank_artifact)


def validate_factorial_prospective_draft(config, draft, bank_artifact):
    """Reproduce the graph; actual paired bytes remain a public source premise.

    The original configuration fixes paired identities. Their bounded physical
    sizes come from the selected source contracts, which ordinary prospective
    author/load independently authenticate against the exact actual bytes.
    """
    paired = None
    if type(config) is ScheduledFactorialConfirmationConfig and config.data is not None:
        external = {value.input_id: value for value in draft.external_inputs}
        paired = {}
        for name in ("reduction", "data"):
            links = tuple(value for value in draft.links if value.consumer_node_id == assess_node_id(config.specification)
                and value.consumer_input_id == name)
            if len(links) != 1 or links[0].external_input_id not in external:
                raise ValueError("protected factorial declaration omits an exact original paired source")
            value = external[links[0].external_input_id]
            paired[name] = ArtifactIdentity(value.logical_artifact_id, "original-factorial-paired-source",
                value.payload_schema, value.expected_content_sha256, value.media_type, value.maximum_size_bytes)
    expected_count = 1 if type(config) is ScheduledFactorialCriteriaConfig else 2
    if len(draft.operations) != expected_count:
        raise ValueError("protected factorial declaration requires its exact criteria phase or sealed confirmation pair")
    selected = tuple(value for value in draft.operations if value.config_identity == config.identity)
    if len(selected) != 1:
        raise ValueError("protected factorial declaration omits its exact original configuration")
    expected = _lower(config, root=draft.prospective_draft, bank_artifact=bank_artifact,
        operational_budget=selected[0].resource_budget, paired_artifacts=paired)
    if draft != expected.draft:
        raise ValueError("protected factorial declaration changes its derived original graph or input bindings")


def lower_factorial_criteria(*, root, programme, specification, qualified_parent, bank_artifact, operational_budget):
    """Derive the blind criteria task; no outcome is an input to this phase."""
    config = ScheduledFactorialCriteriaConfig("config."+freeze_node_id(specification), programme,
        specification, programme.bank, qualified_parent)
    return _lower(config, root=root, bank_artifact=bank_artifact, operational_budget=operational_budget)


def lower_factorial_confirmation(*, root, criteria, acquisitions, bank_artifact, operational_budget,
        reduction=None, data=None):
    """Derive assessment after the exact original criteria/receipt chronology.

    Paired outcomes may be selected by exact artifact identity and positive
    byte size without reading them to construct the blind input-design seal.
    Actual publication and evaluator preparation authenticate their bytes.
    """
    if type(criteria) is not ScheduledFactorialCriteriaBinding:
        raise TypeError("factorial confirmation requires its original ordinary criteria binding")
    criteria.__post_init__()
    original = criteria.record.configuration
    references, records, identities = {}, {}, {}
    for name, value, kind, field in (("reduction", reduction, ScheduledProgrammeReduction, "reduction_id"),
            ("data", data, ScheduledRevisionDataBank, "bank_id")):
        if type(value) is ArtifactIdentity:
            references[name] = value
            identities[name] = ObjectIdentity(value.artifact_id, value.payload_schema, kind.VERSION, value.sha256)
            records[name] = None
        elif value is None or type(value) is kind:
            identities[name] = None if value is None else ObjectIdentity.from_record(getattr(value, field), value)
            records[name] = value
        else:
            raise TypeError("factorial confirmation requires its exact paired record or bounded artifact identity")
    config = ScheduledFactorialConfirmationConfig("config."+assess_node_id(original.specification), original.programme,
        original.specification, original.bank, criteria, acquisitions,
        identities["reduction"], identities["data"])
    return _lower(config, root=root, bank_artifact=bank_artifact, operational_budget=operational_budget,
        reduction=records["reduction"], data=records["data"], paired_artifacts=references or None)
