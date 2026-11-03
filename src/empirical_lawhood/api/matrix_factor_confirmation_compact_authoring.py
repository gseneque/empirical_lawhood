# SPDX-License-Identifier: MPL-2.0
"""Bind declarative E1 resources with the existing prospective candidate owner."""
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.methods.matrix_factor_confirmation import compact_preparation as domain
from empirical_lawhood.adapters.methods.matrix_factor_confirmation.compact_publications import authenticate_manifest_publications
from empirical_lawhood.runtime.experiment_preparation import DependencyKind,ExperimentPreparation
from empirical_lawhood.runtime.experiment_resources import bind_execution_resources


def prepare_authoring(preparation,*,project_root,artifact_writer,output_dir):
    from empirical_lawhood.api.authoring_handoff import preflight_authoring_output_directory
    from empirical_lawhood.api.prospective_experiment import preview_prepared_prospective_experiment_candidate
    if type(preparation) is not ExperimentPreparation or type(preparation.specification_record) is not domain.E1CompactExperimentSpecification:
        raise TypeError('compact E1 authoring requires its actual public typed preparation')
    selected=tuple(record for _,record in preparation.design_records if type(record) in domain.selection_types())
    if len(selected)!=1:raise ValueError('compact E1 authoring requires exactly one original scientific selection')
    selection,=selected
    if type(selection) is domain.E1CompactExperimentSelection:return preparation
    ordinary=domain.prepare(preparation.specification_record,execution=preparation.execution,method_inputs=selection)
    if ordinary!=preparation:raise ValueError('compact E1 authoring changes the original immutable preparation')
    if (len(preparation.dependencies)!=1 or preparation.dependencies[0].kind is not DependencyKind.SOFTWARE
            or preparation.dependencies[0].code!=domain.RESOURCE_BINDING_DEPENDENCY):
        raise ValueError('compact E1 authoring retains actual missing source/scientific/formal/entry/resource prerequisites')
    design=domain.derive_design_inputs(preparation)
    resources=domain.derive_resource_selection(selection,preparation.draft)
    authenticate_manifest_publications(artifact_writer,selection.manifest)
    preflight_authoring_output_directory(directory=Path(output_dir),repo_root=Path(project_root),artifact_writer=artifact_writer)
    preview=preview_prepared_prospective_experiment_candidate(preparation=preparation,design_inputs=design,
        source_configs=selection.source_configs,project_root=project_root,artifact_writer=artifact_writer)
    bound=bind_execution_resources(resources,issued_extensions=preview.issued_extensions)
    return replace(preparation,dependencies=(),prospective_spec=design.bind_resources(bound),
        source_configs=selection.source_configs,prospective_candidate_preview=preview)
