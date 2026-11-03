# SPDX-License-Identifier: MPL-2.0
"""In-memory declaration/provider/protocol checks, without native entry."""

from empirical_lawhood.adapters.methods.matrix_experimental_programme import executable_binding as executable
from empirical_lawhood.adapters.methods.matrix_experimental_programme import extension_bundle as extension
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_functional_bindings as method
from empirical_lawhood.adapters.methods.matrix_experimental_programme import prepared_functional_experiment as protocol
from empirical_lawhood.adapters.methods.matrix_storage_codecs import MATRIX_STORAGE_CODECS
from empirical_lawhood.runtime.experiment_preparation import ExecutionSelection
from tests.test_matrix_prepared_functional_contracts import reference
from empirical_lawhood.planning.campaigns import CampaignSpec


def test_complete_opportunity_uses_the_installed_declaration_and_provider_projections():
    manifests = {row.capability_key: row for row in extension.MANIFESTS}
    providers = {row.binding.capability_key: row for row in executable.EXECUTABLE_BINDING_FACTORIES}
    for declaration in method.operation_declarations():
        assert manifests[declaration.capability_key] == declaration.manifest()
        factory = providers[declaration.capability_key]
        assert factory.binding == declaration.provider_factory().binding
        assert factory.registration == declaration.registration()
        runner = factory.runner_factory()
        assert runner.manifest == factory.manifest == declaration.manifest()
        assert runner.manifest.capability_key.startswith(method.NAMESPACE + ".")
        assert callable(getattr(runner, "execute_with_native_subwork", None)) == factory.registration.native_effect
    assert len(manifests) == len(extension.MANIFESTS)
    assert len(providers) == len(executable.EXECUTABLE_BINDING_FACTORIES)


def test_registered_protocol_reports_original_missing_files_and_complete_roster_without_lowering():
    declaration = next(row for row in extension.EXPERIMENT_PROTOCOL_DECLARATIONS if row.protocol_id == protocol.PROTOCOL_ID)
    assert declaration.specification_type is protocol.MatrixPreparedFunctionalExperimentSpecification
    assert declaration.input_storage_codecs == MATRIX_STORAGE_CODECS
    specification = protocol.MatrixPreparedFunctionalExperimentSpecification("experiment.registered-missing",
        reference("selection.registered-missing", method.MatrixPreparedFunctionalSelection),
        reference("assay.registered-missing", protocol.MatrixPreparedAssayProgramme),
        reference("campaign.registered-missing", CampaignSpec), 16, 48)
    inputs = declaration.bind_inputs(specification, {})
    result = declaration.prepare(specification, scientific_inputs=inputs.scientific_inputs,
        method_inputs=inputs.method_inputs, execution=ExecutionSelection())
    assert not result.executable and result.draft is None
    assert sum(count for _, count in result.census.operation_counts) == 434
    assert result.census.native_effect_count == 96
    assert {row.source_key for row in result.dependencies if row.code.endswith(".missing")} == {"selection", "assay", "campaign"}
