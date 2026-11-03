# SPDX-License-Identifier: MPL-2.0
"""Derive corrected authoring from the existing source-bound public bundle.

This projection creates ordinary authoring/configuration metadata. Original
scientific records, source declarations, authority requirements and packages
remain intact; no execution or outcome-access grant is created.
"""

from dataclasses import dataclass, replace
from hashlib import sha256

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.planning.experiment_entry import ExperimentEntryPackage, StudyDefinition
from empirical_lawhood.planning.formal_analysis import FormalGapSourceCapabilityInventory
from empirical_lawhood.planning.formal_gaps import FormalGapCoverage
from empirical_lawhood.planning.study_authoring import CapabilitySelection, DesignInputRecord, MaterializationQualificationReceipt, SourceMaterializationRole, StudyDraft
from empirical_lawhood.runtime.capabilities import CapabilityRegistry
from empirical_lawhood.runtime.candidate_compiler import CandidateCompilationContext, StandardCandidateCompilationContext, StudyTemplate
from empirical_lawhood.runtime.candidate_composition import CandidateCapabilityCatalog
from empirical_lawhood.runtime.source_resolution import SourceMaterializationConfig

from .authoring import VirtualCellAuthoringBundle, virtual_cell_formal_coverage
from .config_v2 import VirtualCellPipelineSelectionV2
from .contracts import VirtualCellContractError
from .ports_v2 import ORIGINAL_CONFIG_INPUT_ID_V2, project_template_v2, virtual_cell_capability_registry_v2
from .protocol import virtual_cell_candidate_catalog


@dataclass(frozen=True, slots=True)
class VirtualCellAuthoringBundleV2:
    original: VirtualCellAuthoringBundle
    selection: VirtualCellPipelineSelectionV2
    registry: CapabilityRegistry
    template: StudyTemplate
    development_template: StudyTemplate
    catalog: CandidateCapabilityCatalog
    source_configs: tuple[SourceMaterializationConfig, ...]
    qualifications: tuple[MaterializationQualificationReceipt, ...]
    draft: StudyDraft
    development_draft: StudyDraft
    formal_coverage: FormalGapCoverage
    development_formal_coverage: FormalGapCoverage
    entry_package: ExperimentEntryPackage
    development_entry_package: ExperimentEntryPackage
    package: StudyDefinition
    development_package: StudyDefinition
    inventory: FormalGapSourceCapabilityInventory
    context: CandidateCompilationContext
    standard_context: StandardCandidateCompilationContext

    @property
    def candidate_input_payloads(self):
        values = {sha256(payload).hexdigest(): payload for payload in (
            *self.original.candidate_input_payloads, self.selection.canonical_bytes(),
            *(value.canonical_bytes() for value in self.source_configs),
            *(value.canonical_bytes() for value in self.qualifications))}
        return tuple(values[key] for key in sorted(values))


def project_authoring_bundle_v2(original, *, selection, selection_design_input=None):
    """Derive all supported v2 projections, with no manual graph/binding edits."""
    if type(original) is not VirtualCellAuthoringBundle:
        raise TypeError("corrected authoring requires the actual original public bundle")
    if type(selection) is not VirtualCellPipelineSelectionV2:
        raise TypeError("corrected authoring requires its actual versioned selection")
    selection.validate_original(original.config)
    if type(selection_design_input) is not DesignInputRecord:
        raise VirtualCellContractError(
            "PROVENANCE: corrected authoring requires an explicit current selection design input; "
            "historical cutoff, exposure and operator metadata cannot be inferred from the original pipeline"
        )
    selection_design_input.__post_init__()
    if (selection_design_input.object_identity != selection.identity
            or selection_design_input.materialization_sha256 != selection.fingerprint()
            or selection_design_input.input_id in {value.input_id for value in original.draft.design_inputs}):
        raise ValueError("corrected selection provenance changes exact identity or relabels an original design role")
    registry = virtual_cell_capability_registry_v2({value.capability_key: value.implementation_sha256
        for value in original.registry.capabilities})
    template = project_template_v2(original.template, registry=registry,
        original_config=original.config, selection=selection)
    development_template = project_template_v2(original.development_template, registry=registry,
        original_config=original.config, selection=selection)
    catalog = replace(virtual_cell_candidate_catalog(registry=registry,
        templates=(template, development_template)), catalog_id=original.catalog.catalog_id + "-v2")

    # The original pipeline bytes are a separately selected, outcome-blind
    # numerical input. Their existing design identity is never relabeled v2.
    base_ref = original.draft.source_materializations[0]
    base_config = next(value for value in original.source_configs if value.source_id == base_ref.source_id)
    base_qualification = next(value for value in original.qualifications if value.source_id == base_ref.source_id)
    config_identity = ObjectIdentity.from_record(original.config.config_id, original.config)
    config = replace(base_config, config_id="source-config." + ORIGINAL_CONFIG_INPUT_ID_V2,
        source_id=ORIGINAL_CONFIG_INPUT_ID_V2, role=SourceMaterializationRole.NUMERICAL_CONFIGURATION,
        content_sha256=original.config.fingerprint(), expected_size_bytes=len(original.config.canonical_bytes()),
        maximum_bytes=max(len(original.config.canonical_bytes()), 1024**2),
        payload_schema=original.config.SCHEMA, media_type="application/json")
    qualification = replace(base_qualification, receipt_id="qualification." + ORIGINAL_CONFIG_INPUT_ID_V2,
        source_id=ORIGINAL_CONFIG_INPUT_ID_V2, materialization=config_identity,
        content_sha256=original.config.fingerprint())
    reference = replace(base_ref, source_id=ORIGINAL_CONFIG_INPUT_ID_V2,
        role=SourceMaterializationRole.NUMERICAL_CONFIGURATION, materialization=config_identity,
        content_sha256=original.config.fingerprint(), source_config_sha256=config.fingerprint(),
        qualification_receipt=ObjectIdentity.from_record(qualification.receipt_id, qualification))
    source_configs = tuple(sorted((*original.source_configs, config), key=lambda value: value.source_id))
    qualifications = tuple(sorted((*original.qualifications, qualification), key=lambda value: value.receipt_id))
    source_refs = tuple(sorted((*original.draft.source_materializations, reference), key=lambda value: value.source_id))
    # A new corrected method is current evidence. Preserve caller-supplied
    # exposure, cutoff, unit/seed lineage and operator exactly; the standard
    # compiler decides whether it is compatible with the original experiment.
    design_inputs = tuple(sorted((*original.draft.design_inputs, selection_design_input), key=lambda value: value.input_id))

    def draft_for(prior, selected_template):
        keys = {value.capability_key for value in selected_template.protocol.steps}
        return replace(prior, draft_id=prior.draft_id + "-v2", dag_template_key=selected_template.template_key,
            design_inputs=design_inputs, design_origin=replace(prior.design_origin,
                origin_id=prior.design_origin.origin_id + "-v2", declared_input_ids=tuple(value.input_id for value in design_inputs)),
            source_materializations=source_refs, capability_selections=tuple(CapabilitySelection(
                value.capability_key, value.capability_version, value.implementation_sha256)
                for value in registry.capabilities if value.capability_key in keys))

    draft = draft_for(original.draft, template)
    development_draft = draft_for(original.development_draft, development_template)

    def entry_for(prior_entry, selected_draft):
        coverage = virtual_cell_formal_coverage(register=prior_entry.register,
            denominator_id=original.system.system_id, candidate_act_id=selected_draft.draft_id,
            coverage_id=prior_entry.coverage.coverage_id + "-v2")
        checklist = replace(prior_entry.checklist, checklist_id=prior_entry.checklist.checklist_id + "-v2",
            draft=ObjectIdentity.from_record(selected_draft.draft_id, selected_draft),
            formal_gap_coverage=ObjectIdentity.from_record(coverage.coverage_id, coverage))
        return replace(prior_entry, package_id=prior_entry.package_id + "-v2", coverage=coverage, checklist=checklist)

    entry = entry_for(original.entry_package, draft)
    development_entry = entry_for(original.development_entry_package, development_draft)
    package = StudyDefinition(original.package.package_id + "-v2", draft, entry)
    development_package = StudyDefinition(original.development_package.package_id + "-v2", development_draft, development_entry)
    inventory = replace(original.inventory, inventory_id=original.inventory.inventory_id + "-v2",
        source_materializations=tuple(sorted((value.materialization for value in source_refs), key=lambda value: value.object_id)))
    context = replace(original.context, context_id=original.context.context_id + "-v2", registry=registry,
        templates=tuple(sorted((template, development_template), key=lambda value: value.template_key)),
        qualifications=qualifications, known_design_inputs=design_inputs)
    standard_context = replace(original.standard_context, context_id=original.standard_context.context_id + "-v2",
        base=context, source_inventories=(inventory,))
    return VirtualCellAuthoringBundleV2(original, selection, registry, template, development_template, catalog,
        source_configs, qualifications, draft, development_draft, entry.coverage, development_entry.coverage,
        entry, development_entry, package, development_package, inventory, context, standard_context)
