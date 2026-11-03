"""Closed configuration consumers; no registry entry grants execution or authority.

Module/class locators below are implementation-owned constants, never input values.
Consumer byte limits mirror their existing loaders; the exposed helper has a new
shape-check ceiling and the unsupported human template has no consuming limit.
Inputs are documentary inventory, not an installed-wheel checkout requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from collections.abc import Sequence

from empirical_lawhood.kernel.serialization import CanonicalRecord


@dataclass(frozen=True, slots=True)
class ConfigurationConsumer:
    consumer: str
    schema_id: str | None
    record_module: str | None
    record_name: str | None
    disposition: str
    maximum_bytes: int | None
    requires_canonical: bool
    command: str
    owner: str
    supplied_inputs: tuple[str, ...]
    configuration_capabilities: tuple = ()

    @property
    def authoring_maximum_bytes(self) -> int | None:
        if self.maximum_bytes is None:
            return None
        return min(4 * self.maximum_bytes, 128 * 1024**2)

    @property
    def preparation_allowed(self) -> bool:
        return self.disposition == "editable"

    @property
    def loader(self) -> str:
        if self.consumer == "prepared-prior-census":
            return "adapters.composition.prepared_response.native_authoring._prior_census"
        if self.consumer == "finite-prior-census":
            return "adapters.composition.finite_response_law.native_input._census"
        if self.disposition == "helper":
            return "documentary helper; no runner loader"
        if self.requires_canonical:
            return "kernel.decoding.decode_canonical_bytes"
        return "api.codecs.load_registered_authoring"

    def record_type(self) -> type[CanonicalRecord]:
        if self.record_module is None or self.record_name is None:
            raise ValueError("this consumer has no canonical record constructor")
        record = getattr(import_module(self.record_module), self.record_name)
        if not isinstance(record, type) or not issubclass(record, CanonicalRecord):
            raise TypeError("configuration registry contains a non-record owner")
        if record.SCHEMA != self.schema_id:
            raise ValueError("configuration registry schema differs from its owner")
        return record


# Closed role dispositions for installed experiment and shared configuration inputs.
_CONSUMER_ROWS = (
 ('operational-configuration', 'empirical-lawhood/runtime/operational-configuration', 'empirical_lawhood.runtime.operational_configuration', 'OperationalConfiguration', 'editable', 65536, False, '--operational-config', 'OperationalConfiguration', ('configs/operational.example.yaml',)),
 ('rubisco-kinetic-supply', 'empirical-lawhood/rubisco/kinetic-supply/joint-supply', 'empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply', 'JointKineticSupply', 'retained', None, True, 'campaign recursive-author', 'JointKineticSupply', ('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/supply.json',)),
 ('rubisco-kinetic-query', 'empirical-lawhood/simulators/rubisco-assay/query', 'empirical_lawhood.adapters.simulators.rubisco_assay.records', 'AssayQuery', 'retained', None, True, 'campaign recursive-author', 'AssayQuery', ('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/query.json',)),
 ('rubisco-kinetic-comparison', 'empirical-lawhood/rubisco/kinetic-supply/target-comparison', 'empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_supply', 'KineticTargetComparison', 'retained', None, True, 'campaign recursive-author', 'KineticTargetComparison', ('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/comparison.json',)),
 ('rubisco-kinetic-assumptions', 'empirical-lawhood/examples/disclosed-rubisco-kinetic-assumption', 'empirical_lawhood.adapters.methods.rubisco_prediction.kinetic_join.disclosed_examples', 'DisclosedAssumption', 'retained', None, True, 'campaign recursive-author', 'DisclosedAssumption', ('programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/assumptions.json',)),
 ('recursive-inquiry-decision', 'empirical-lawhood/runtime/inquiry-decision-request', 'empirical_lawhood.runtime.recursive_inquiry', 'InquiryDecisionRequest', 'editable', None, True, 'campaign recursive-inquiry-decide', 'InquiryDecisionRequest', ()),
 ('recursive-inquiry-decision-v2', 'empirical-lawhood/runtime/inquiry-decision-request', 'empirical_lawhood.runtime.recursive_inquiry', 'RobustInquiryDecisionRequest', 'editable', None, True, 'campaign recursive-inquiry-decide', 'RobustInquiryDecisionRequest', ()),
 ('recursive-inquiry-decision-v3', 'empirical-lawhood/runtime/inquiry-decision-request', 'empirical_lawhood.runtime.recursive_inquiry', 'WorkBoundInquiryDecisionRequest', 'editable', None, True, 'campaign recursive-inquiry-decide', 'WorkBoundInquiryDecisionRequest', ()),
 ('recursive-prospective', 'empirical-lawhood/runtime/recursive-prospective-authoring-spec', 'empirical_lawhood.runtime.recursive_prospective', 'RecursiveProspectiveAuthoringSpec', 'editable', 16777216, True, 'campaign recursive-author', 'RecursiveProspectiveAuthoringSpec', ()) ,
 ('recursive-inquiry', 'empirical-lawhood/planning/recursive-study-draft', 'empirical_lawhood.planning.recursive_authoring', 'RecursiveStudyDraft', 'editable', None, True, 'campaign recursive-author', 'RecursiveStudyDraft', ('programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original.json', 'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2.json', 'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3.json', 'programmes/energy/battery-charging/workflows/recursive-battery/battery-wave-a.json', 'programmes/materials/superconductivity/workflows/recursive-materials/materials-partial.json', 'programmes/biology/photosynthesis/workflows/rubisco-kinetic-join/draft.json')),
 ('rc-prerequisite-chain', 'empirical-lawhood/methods/rc-prerequisite-chain/config', 'empirical_lawhood.adapters.methods.rc_prerequisite_chain.contracts', 'RCPrerequisiteChainConfig', 'editable', 65536, True, 'campaign rc-chain-run', 'RCPrerequisiteChainConfig', ('programmes/foundations/measurement-and-response/workflows/rc-prerequisite-chain/input.json', 'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-original-scientific.json', 'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-menu-v2-scientific.json', 'programmes/foundations/measurement-and-response/workflows/recursive-rc/rc-budget-v3-scientific.json')),
 ('preparation-diagnostic-phase', 'empirical-lawhood/constructed-preparation-applicability/diagnostic-phase-input', 'empirical_lawhood.adapters.methods.constructed_preparation_applicability.diagnostic_records', 'PreparationDiagnosticPhaseInput', 'retained', 4194304, True, 'campaign preparation-diagnostic-phase-prepare', 'PreparationDiagnosticPhaseInput', ()),
 ('preparation-diagnostics', 'empirical-lawhood/constructed-preparation-applicability/diagnostic-input', 'empirical_lawhood.adapters.methods.constructed_preparation_applicability.diagnostic_records', 'PreparationDiagnosticInput', 'editable', 8388608, True, 'campaign preparation-diagnostics', 'PreparationDiagnosticInput', ()),
 ('matrix-geometry', 'empirical-lawhood/matrix-geometry/scan-input', 'empirical_lawhood.api.matrix_geometry', 'MatrixGeometryScanInput', 'editable', 8388608, True, 'campaign matrix-geometry-prove', 'MatrixGeometryScanInput', ('programmes/foundations/emergent-structure/workflows/matrix-geometry/input-current.json',)),
 ('selected-parent', 'empirical-lawhood/selected-events/parent-request', 'empirical_lawhood.api.selected_events', 'MatrixSelectedParentRequest', 'editable', 1048576, True, 'campaign selected-parent-reconstruct', 'MatrixSelectedParentRequest', ('programmes/foundations/emergent-structure/workflows/selected-events/parent-current.json',)),
 ('selected-events', 'empirical-lawhood/selected-events/input', 'empirical_lawhood.api.selected_events', 'MatrixSelectedEventInput', 'editable', 16777216, True, 'campaign selected-events-run', 'MatrixSelectedEventInput', ()),
 ('matrix-history-allocation', 'empirical-lawhood/matrix-history-analysis/allocation', 'empirical_lawhood.adapters.methods.matrix_history_analysis.records', 'MatrixHistoryAllocation', 'editable', 1048576, True, 'campaign matrix-history-allocation', 'MatrixHistoryAllocation', ('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/allocation.json',)),
 ('matrix-history-source', 'empirical-lawhood/matrix-history-analysis/source-config', 'empirical_lawhood.adapters.methods.matrix_history_analysis.records', 'MatrixHistorySourceConfig', 'editable', 1048576, True, 'campaign matrix-history-source-export', 'MatrixHistorySourceConfig', ('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/source-current.json',)),
 ('matrix-history-analysis', 'empirical-lawhood/matrix-history-analysis/analysis-config', 'empirical_lawhood.adapters.methods.matrix_history_analysis.records', 'MatrixHistoryAnalysisConfig', 'editable', 1048576, True, 'campaign matrix-history-analyze', 'MatrixHistoryAnalysisConfig', ('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/algebra-current.json', 'programmes/foundations/emergent-structure/workflows/matrix-history-analysis/passive-current.json')),
 ('matrix-transient-analysis', 'empirical-lawhood/methods/matrix-preparation-analysis/transient-analysis-config', 'empirical_lawhood.adapters.methods.matrix_preparation_analysis.records', 'TransientAnalysisConfig', 'editable', 65536, True, 'campaign matrix-transient-analyze', 'TransientAnalysisConfig', ('programmes/foundations/emergent-structure/workflows/matrix-transient/input.json',)),
 ('matrix-baseline-analysis', 'empirical-lawhood/methods/matrix-preparation-analysis/baseline-support-config', 'empirical_lawhood.adapters.methods.matrix_preparation_analysis.records', 'BaselineSupportConfig', 'editable', 65536, True, 'campaign matrix-baseline-analyze', 'BaselineSupportConfig', ('programmes/foundations/emergent-structure/workflows/matrix-transient/baseline.json',)),
 ('matrix-tangent', 'empirical-lawhood/methods/matrix-preparation-analysis/tangent-preparation-config', 'empirical_lawhood.adapters.methods.matrix_preparation_analysis.tangent_records', 'TangentPreparationConfig', 'editable', 4194304, True, 'campaign matrix-tangent-source-export', 'TangentPreparationConfig', ('programmes/foundations/emergent-structure/workflows/matrix-tangent/input-current.json',)),
('preparation-retained-result', 'empirical-lawhood/preparation-applicability/retained-result', 'empirical_lawhood.adapters.methods.preparation_applicability.result_access', 'PreparationApplicabilityRetainedResult', 'retained', 16777216, True, 'campaign preparation-result', 'PreparationApplicabilityRetainedResult', ()),
 ('preparation-native-conformance', 'empirical-lawhood/preparation-applicability/native-conformance', 'empirical_lawhood.adapters.methods.preparation_applicability.conformance', 'PreparationApplicabilityNativeConformance', 'retained', 1048576, True, 'campaign preparation-conformance', 'PreparationApplicabilityNativeConformance', ()),
 ('preparation-exposure-inspection', 'empirical-lawhood/preparation-applicability/exposure-inspection', 'empirical_lawhood.adapters.methods.preparation_applicability.issued_inputs', 'PreparationApplicabilityExposureInspection', 'retained', 4194304, True, 'campaign preparation-exposure-inspect', 'PreparationApplicabilityExposureInspection', ()),
 ('preparation-published-input', 'empirical-lawhood/preparation-applicability/published-input', 'empirical_lawhood.adapters.methods.preparation_applicability.issued_inputs', 'PreparationApplicabilityPublishedInput', 'retained', 16777216, True, 'campaign preparation-input-publish', 'PreparationApplicabilityPublishedInput', ()),
 ('preparation-panel-publication', 'empirical-lawhood/preparation-applicability/panel-publication', 'empirical_lawhood.adapters.methods.preparation_applicability.panel_inputs', 'PreparationApplicabilityPanelPublication', 'retained', 16777216, True, 'campaign preparation-panel-bind', 'PreparationApplicabilityPanelPublication', ()),
 ('finite-current-result', 'empirical-lawhood/composition/finite-response-law/current-result-input', 'empirical_lawhood.adapters.composition.finite_response_law.rerun_input', 'FiniteResponseLawCurrentResultInput', 'retained', 8388608, True, 'campaign finite-response-result', 'FiniteResponseLawCurrentResultInput', ()),
 ('rc-challenge-result', 'empirical-lawhood/simulator-morphism-challenges/retained-result', 'empirical_lawhood.adapters.simulator_morphism_challenges.retained_results', 'RCChallengeRetainedResult', 'retained', 16777216, True, 'campaign rc-challenge-result', 'RCChallengeRetainedResult', ()),
 ('rc-challenge-result-authority', 'empirical-lawhood/simulator-morphism-challenges/result-authority-context', 'empirical_lawhood.adapters.simulator_morphism_challenges.retained_results', 'RCChallengeResultAuthorityContext', 'retained', 1048576, True, 'campaign rc-challenge-result', 'RCChallengeResultAuthorityContext', ()),
 ('original-f', 'empirical-lawhood/methods/finite-response-law/original-finite-response-law', 'empirical_lawhood.adapters.methods.finite_response_law.original_f', 'OriginalFiniteResponseLaw', 'retained', 1048576, True, 'campaign original-f-check', 'OriginalFiniteResponseLaw', ()),
 ('current-nomination', 'empirical-lawhood/methods/finite-response-law/current-nomination-operand', 'empirical_lawhood.adapters.methods.finite_response_law.nominated_package', 'CurrentNominationOperand', 'retained', 1048576, True, 'campaign nomination-check', 'CurrentNominationOperand', ()),
 ('saved-matrix-arrays', 'empirical-lawhood/kernel/saved-matrix-arrays', 'empirical_lawhood.kernel.matrix_inputs', 'SavedMatrixArrays', 'retained', 4194304, True, 'campaign preparation-operands-export', 'SavedMatrixArrays', ()),
 ('preparation-source', 'empirical-lawhood/methods/finite-response-law/current-preparation-source-config', 'empirical_lawhood.adapters.methods.finite_response_law.transient_bridge_source_records', 'CurrentPreparationSourceConfig', 'editable', 65536, True, 'campaign preparation-source-export', 'CurrentPreparationSourceConfig', ('programmes/foundations/emergent-structure/workflows/matrix-inputs/preparation-source-current.json',)),
 ('matrix-source', 'empirical-lawhood/methods/finite-response-law/matrix-preparation-source-config', 'empirical_lawhood.adapters.methods.finite_response_law.transient_bridge_source_records', 'MatrixPreparationSourceConfig', 'editable', 65536, True, 'campaign matrix-source-export', 'MatrixPreparationSourceConfig', ('programmes/foundations/emergent-structure/workflows/matrix-inputs/matrix-source-current.json',)),
 ('rc-challenge-source', 'empirical-lawhood/simulator-morphism-challenges/source-export-config', 'empirical_lawhood.adapters.simulator_morphism_challenges.numeric_inputs', 'RCChallengeSourceExportConfig', 'editable', 1048576, True, 'campaign rc-challenge-source-export', 'RCChallengeSourceExportConfig', ('programmes/foundations/measurement-and-response/workflows/rc-challenges/source-export.json',)),
 ('rc-challenge-phase', 'empirical-lawhood/simulator-morphism-challenges/simulator-morphism-challenge-config', 'empirical_lawhood.adapters.simulator_morphism_challenges.contracts', 'SimulatorMorphismChallengeConfig', 'editable', 65536, True, 'campaign rc-challenge-author', 'SimulatorMorphismChallengeConfig', ('programmes/foundations/measurement-and-response/workflows/rc-challenges/canary.json', 'programmes/foundations/measurement-and-response/workflows/rc-challenges/nomination.json', 'programmes/foundations/measurement-and-response/workflows/rc-challenges/development.json', 'programmes/foundations/measurement-and-response/workflows/rc-challenges/evaluation.json')),
 ('finite-rerun', 'empirical-lawhood/composition/finite-response-law/rerun-input', 'empirical_lawhood.adapters.composition.finite_response_law.rerun_input', 'FiniteResponseLawRerunInput', 'editable', 4194304, True, 'campaign finite-response-author', 'FiniteResponseLawRerunInput', ('programmes/foundations/emergent-structure/workflows/finite-response-law/rerun-calibration.json',)),
 ('finite-current-allocation', 'empirical-lawhood/composition/finite-response-law/current-allocation', 'empirical_lawhood.adapters.composition.finite_response_law.rerun_input', 'FiniteResponseLawCurrentAllocation', 'editable', 1048576, True, 'campaign finite-response-author', 'FiniteResponseLawCurrentAllocation', ('programmes/foundations/emergent-structure/workflows/finite-response-law/current-calibration-allocation.json', 'programmes/foundations/emergent-structure/workflows/finite-response-law/current-evaluation-allocation.json')),
 ('finite-current-exposure', 'empirical-lawhood/composition/finite-response-law/current-exposure', 'empirical_lawhood.adapters.composition.finite_response_law.rerun_input', 'FiniteResponseLawCurrentExposure', 'retained', 4194304, True, 'campaign finite-response-author', 'FiniteResponseLawCurrentExposure', ('programmes/foundations/emergent-structure/workflows/finite-response-law/current-exposure.json',)),
 ('finite-current-parent', 'empirical-lawhood/composition/finite-response-law/current-parent', 'empirical_lawhood.adapters.composition.finite_response_law.rerun_input', 'FiniteResponseLawCurrentParent', 'retained', 8388608, True, 'campaign finite-response-author', 'FiniteResponseLawCurrentParent', ()),
 ('finite-runtime-context', 'empirical-lawhood/composition/finite-response-law/finite-response-law-runtime-context', 'empirical_lawhood.adapters.composition.finite_response_law.consumer_ports', 'FiniteResponseLawRuntimeContext', 'editable', 1048576, True, 'campaign finite-response-bind-runtime', 'FiniteResponseLawRuntimeContext', ()),
 ('preparation-applicability-selection', 'empirical-lawhood/composition/preparation-applicability/selection', 'empirical_lawhood.adapters.composition.preparation_applicability.selection', 'PreparationApplicabilitySelection', 'editable', 4194304, True, 'campaign preparation-author', 'PreparationApplicabilitySelection', ()),
 ('preparation-applicability-stage', 'empirical-lawhood/preparation-applicability/stage', 'empirical_lawhood.adapters.methods.preparation_applicability.config', 'PreparationApplicabilityStage', 'editable', 4194304, True, 'campaign preparation-author', 'PreparationApplicabilityStage', ()),
 ('preparation-applicability-source', 'empirical-lawhood/preparation-applicability/source', 'empirical_lawhood.adapters.methods.preparation_applicability.config', 'PreparationApplicabilitySource', 'editable', 1048576, True, 'campaign preparation-author', 'PreparationApplicabilitySource', ()),
 ('constructed-preparation-applicability-selection', 'empirical-lawhood/composition/constructed-preparation-applicability/selection', 'empirical_lawhood.adapters.composition.constructed_preparation_applicability.selection', 'ConstructedPreparationApplicabilitySelection', 'editable', 4194304, True, 'campaign preparation-author', 'ConstructedPreparationApplicabilitySelection', ()),
 ('constructed-preparation-applicability-stage', 'empirical-lawhood/constructed-preparation-applicability/stage', 'empirical_lawhood.adapters.methods.constructed_preparation_applicability.config', 'ConstructedPreparationStage', 'editable', 4194304, True, 'campaign preparation-author', 'ConstructedPreparationStage', ()),
 ('constructed-preparation-applicability-source', 'empirical-lawhood/constructed-preparation-applicability/source', 'empirical_lawhood.adapters.methods.constructed_preparation_applicability.config', 'ConstructedPreparationSource', 'editable', 1048576, True, 'campaign preparation-author', 'ConstructedPreparationSource', ()),
 ('rc-information',
  'empirical-lawhood/methods/rc-information/config',
  'empirical_lawhood.adapters.methods.rc_information.contracts',
  'RCInformationConfig',
  'editable',
  65536,
  True,
  'example rc-information',
  'RCInformationConfig',
  ('programmes/foundations/measurement-and-response/workflows/rc-information/input.json',)),
 ('matrix-allocation',
  'empirical-lawhood/kernel/matrix-allocation',
  'empirical_lawhood.kernel.matrix_inputs',
  'MatrixAllocation',
  'editable',
  1048576,
  True,
  'campaign preparation-operands-export',
  'MatrixAllocation',
  ('programmes/foundations/emergent-structure/workflows/matrix-inputs/allocation.json', 'programmes/foundations/emergent-structure/workflows/preparation-applicability/conformance-allocation.json')),
 ('rc-ladder-model',
  'empirical-lawhood/adapters/simulators/rc-ladder-response/resistor-capacitor-ladder-model-config',
  'empirical_lawhood.adapters.simulators.rc_ladder_response.contracts',
  'ResistorCapacitorLadderModelConfig',
  'editable',
  65536,
  True,
  'campaign rc-ladder-native-check',
  'ResistorCapacitorLadderModelConfig',
  ('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/model.json',)),
 ('finite-calibration-input',
  'empirical-lawhood/composition/finite-response-law/finite-response-law-calibration-input',
  'empirical_lawhood.adapters.composition.finite_response_law.native_input',
  'FiniteResponseLawCalibrationInput',
  'editable',
  16384,
  False,
  'campaign finite-response-input-check',
  'FiniteResponseLawCalibrationInput',
  ('programmes/foundations/emergent-structure/workflows/finite-response-law/finite-calibration-input.json',)),
 ('finite-stage-input',
  'empirical-lawhood/composition/finite-response-law/finite-response-law-stage-input',
  'empirical_lawhood.adapters.composition.finite_response_law.stage_input',
  'FiniteResponseLawStageInput',
  'editable',
  16384,
  False,
  'campaign finite-response-stage-input-check',
  'FiniteResponseLawStageInput',
  ('programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/calibration-stage-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/informative-composition-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/preparation-screen-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-continuation-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/prospective-evaluation-input.json',
   'programmes/foundations/emergent-structure/workflows/finite-response-law/supplemental-development-input.json')),
 ('prepared-prior-census',
  'empirical-lawhood/composition/prepared-response/prepared-exposure-inspection',
  None,
  None,
  'import',
  67108864,
  False,
  'campaign matrix-response-author --prior-inspection',
  '_prior_census',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/prepared-response-prior-exposure.json',)),
 ('prepared-dependent-input',
  'empirical-lawhood/composition/prepared-response/prepared-response-dependent-input',
  'empirical_lawhood.adapters.composition.prepared_response.dependent_input',
  'PreparedResponseDependentInput',
  'editable',
  16384,
  False,
  'campaign dependent-response-input-check',
  'PreparedResponseDependentInput',
  ('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-dependent-refinement-input.json',
   'programmes/foundations/emergent-structure/workflows/prepared-response/prepared-fresh-response-calibration-input.json')),
 ('matrix-response-authoring',
  'empirical-lawhood/composition/prepared-response/prepared-response-native-authoring-input',
  'empirical_lawhood.adapters.composition.prepared_response.native_authoring',
  'PreparedResponseNativeAuthoringInput',
  'editable',
  1048576,
  False,
  'campaign matrix-response-author',
  'PreparedResponseNativeAuthoringInput',
  ('programmes/foundations/emergent-structure/workflows/causal-response/causal-author.json',
   'programmes/foundations/emergent-structure/workflows/information-response/information-author.json',
   'programmes/foundations/emergent-structure/workflows/prepared-response/prepared-source-qualification-author.json')),
 ('reactor-assigned-profile',
  'empirical-lawhood/composition/reactor-prefix-response/assigned-reactor-authoring-profile',
  'empirical_lawhood.adapters.composition.reactor_prefix_response.fresh_authoring',
  'AssignedReactorAuthoringProfile',
  'retained',
  67108864,
  True,
  'campaign reactor-author',
  'AssignedReactorAuthoringProfile',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/reactor-assigned-exposed.json',)),
 ('reactor-fresh-profile',
  'empirical-lawhood/composition/reactor-prefix-response/fresh-reactor-authoring-profile',
  'empirical_lawhood.adapters.composition.reactor_prefix_response.fresh_authoring',
  'FreshReactorAuthoringProfile',
  'editable',
  67108864,
  True,
  'campaign reactor-author',
  'FreshReactorAuthoringProfile',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/profile.json',)),
 ('response-composition-input',
  'empirical-lawhood/composition/response-composition/response-composition-input',
  'empirical_lawhood.adapters.composition.response_composition.input',
  'ResponseCompositionInput',
  'editable',
  16384,
  False,
  'campaign response-composition-input-check',
  'ResponseCompositionInput',
  ('programmes/foundations/emergent-structure/workflows/causal-transfer-audit/analysis-input.json',)),
 ('exposed-inventory',
  'empirical-lawhood/examples/exposed-inventory',
  None,
  None,
  'helper',
  65536,
  False,
  'scripts/generate_operator_examples.py',
  'documentary helper',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/exposed-inventory.json',)),
 ('finite-prior-census',
  'empirical-lawhood/methods/finite-response-law/native-exposure-metadata',
  None,
  None,
  'import',
  134217728,
  False,
  'campaign finite-response-stage-input-check --prior-exposure',
  '_census',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/exposed-inputs/finite-response-prior-exposure.json',)),
 ('propulsion-reference',
  'empirical-lawhood/methods/synthetic-propulsion-development-input',
  'empirical_lawhood.adapters.methods.synthetic_propulsion_development_input',
  'SyntheticPropulsionDevelopmentInput',
  'editable',
  16384,
  False,
  'campaign propulsion-reference-check',
  'SyntheticPropulsionDevelopmentInput',
  ('programmes/foundations/measurement-and-response/workflows/propulsion-reliability-reference/config.json',)),
 ('glenn-import-selection',
  'empirical-lawhood/physical/glenn/glenn-input-quickstart',
  'empirical_lawhood.adapters.physical.glenn.quickstart',
  'GlennInputQuickstart',
  'editable',
  16384,
  False,
  'campaign glenn-import-check',
  'GlennInputQuickstart',
  ('programmes/foundations/measurement-and-response/workflows/laser-archive-inspection/config.json',)),
 ('fair-mast-selection',
  'empirical-lawhood/physical/mast-archive/fair-mast-public-selection',
  'empirical_lawhood.adapters.physical.mast_archive.fresh_source',
  'FairMastPublicSelection',
  'editable',
  65536,
  True,
  'source acquire',
  'FairMastPublicSelection',
  ('programmes/energy/fusion/workflows/fair-mast-source/fair-mast-level2.json',)),
 ('reaction-development',
  'empirical-lawhood/reaction-diffusion-development/reaction-diffusion-development-input',
  'empirical_lawhood.adapters.simulators.reaction_diffusion_development_input',
  'ReactionDiffusionDevelopmentInput',
  'editable',
  32768,
  False,
  'campaign reaction-response-native-check',
  'ReactionDiffusionDevelopmentInput',
  ('programmes/foundations/measurement-and-response/workflows/reaction-diffusion-response/config.json', 'programmes/foundations/measurement-and-response/workflows/reactor-flow-response/config.json')),
 ('scale-morphism-reference',
  'empirical-lawhood/reference-worlds/physical-scale-morphism/physical-scale-morphism-truth-suite-config',
  'empirical_lawhood.adapters.reference_worlds.physical_scale_morphism.contracts',
  'PhysicalScaleMorphismTruthSuiteConfig',
  'editable',
  16384,
  False,
  'campaign scale-morphism-reference-check',
  'PhysicalScaleMorphismTruthSuiteConfig',
  ('programmes/foundations/measurement-and-response/workflows/response-method-reference/config.json',)),
 ('operator-artifact-root-access',
  'empirical-lawhood/runtime/external-root-contract',
  'empirical_lawhood.runtime.artifacts',
  'ExternalRootContract',
  'editable',
  134217728,
  False,
  'campaign experiment-read --artifact-root-contract',
  'ExternalRootContract',
  ()),
 ('operator-storage',
  'empirical-lawhood/runtime/operator-storage-profile',
  'empirical_lawhood.runtime.operator_profile',
  'OperatorStorageProfile',
  'editable',
  134217728,
  False,
  'doctor',
  'OperatorStorageProfile',
  ('configs/operator-storage.example.json',)),
 ('material-control-input',
  'empirical-lawhood/simulators/ambient-pressure-superconductor/material-control-input-preflight',
  'empirical_lawhood.adapters.simulators.ambient_pressure_superconductor.material_control_input_preflight',
  'MaterialControlInputPreflight',
  'editable',
  32768,
  False,
  'campaign material-workflow-input-check',
  'MaterialControlInputPreflight',
  ('programmes/materials/superconductivity/workflows/material-control-inputs/control-inputs.json',)),
 ('lattice-method-authoring',
  'empirical-lawhood/simulators/ambient-pressure-superconductor/synthetic-material-response-method-config',
  'empirical_lawhood.adapters.simulators.ambient_pressure_superconductor.synthetic_material_method_contracts',
  'SyntheticMaterialResponseMethodConfig',
  'editable',
  131072,
  True,
  'campaign synthetic-material-author',
  'SyntheticMaterialResponseMethodConfig',
  ('programmes/materials/superconductivity/workflows/lattice-pairing-method/authoring.json',)),
 ('brian2-current',
  'empirical-lawhood/simulators/brian2-neuron-current-response/brian2-lif-native-config',
  'empirical_lawhood.adapters.simulators.brian2_neuron_current_response.contracts',
  'Brian2LIFNativeConfig',
  'editable',
  16384,
  True,
  'campaign brian2-native-check',
  'Brian2LIFNativeConfig',
  ('programmes/biology/cell-responses/workflows/neuron-current-response/config.json',)),
 ('finite-canary',
  'empirical-lawhood/simulators/finite-response-law/finite-response-law-canary',
  'empirical_lawhood.adapters.simulators.finite_response_law.native_quickstart',
  'FiniteResponseLawCanary',
  'editable',
  16384,
  False,
  'campaign finite-response-native-check',
  'FiniteResponseLawCanary',
  ('programmes/foundations/emergent-structure/workflows/finite-response-law/finite-canary.json',)),
 ('grid-development',
  'empirical-lawhood/simulators/grid2op-response/grid2-op-development-input',
  'empirical_lawhood.adapters.simulators.grid2op_response.native_quickstart',
  'Grid2OpDevelopmentInput',
  'editable',
  16384,
  False,
  'campaign grid2op-native-check',
  'Grid2OpDevelopmentInput',
  ('programmes/energy/electricity-grids/workflows/grid-response-inputs/config.json',)),
 ('tokamak-control',
  'empirical-lawhood/simulators/gym-torax-native/gym-torax-native-quickstart',
  'empirical_lawhood.adapters.simulators.gym_torax_native.native_quickstart',
  'GymToraxNativeQuickstart',
  'editable',
  16384,
  False,
  'campaign gym-torax-native-check',
  'GymToraxNativeQuickstart',
  ('programmes/energy/fusion/workflows/tokamak-control-response/config.json',)),
 ('prepared-canary',
  'empirical-lawhood/simulators/prepared-response/prepared-response-prepared-canary',
  'empirical_lawhood.adapters.simulators.prepared_response.native_quickstart',
  'PreparedResponsePreparedCanary',
  'editable',
  16384,
  False,
  'campaign prepared-response-native-check',
  'PreparedResponsePreparedCanary',
  ('programmes/foundations/emergent-structure/workflows/prepared-response/prepared-canary.json',)),
 ('battery-development',
  'empirical-lawhood/simulators/py-ba-mm-development-input',
  'empirical_lawhood.adapters.simulators.pybamm_development_input',
  'PyBaMMDevelopmentInput',
  'editable',
  16384,
  False,
  'campaign battery-native-check',
  'PyBaMMDevelopmentInput',
  ('programmes/energy/battery-charging/workflows/battery-response-and-restart/config.json',)),
 ('rc-ladder-study',
  'empirical-lawhood/simulators/rc-ladder-response/resistor-capacitor-ladder-study-config',
  'empirical_lawhood.adapters.simulators.rc_ladder_response.contracts',
  'ResistorCapacitorLadderStudyConfig',
  'editable',
  131072,
  True,
  'campaign circuit-author',
  'ResistorCapacitorLadderStudyConfig',
  ('programmes/foundations/measurement-and-response/workflows/rc-ladder-response/study.json',)),
 ('reactor-batch-input',
  'empirical-lawhood/simulators/reactor-prefix-response/reactor-batch-input',
  'empirical_lawhood.adapters.simulators.reactor_prefix_response.batch_input',
  'ReactorBatchInput',
  'editable',
  16384,
  False,
  'campaign reactor-batch-input-check',
  'ReactorBatchInput',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/batch-input.json',)),
 ('reactor-prepared-input',
  'empirical-lawhood/simulators/reactor-prefix-response/reactor-prepared-input',
  'empirical_lawhood.adapters.simulators.reactor_prefix_response.prepared_input',
  'ReactorPreparedInput',
  'editable',
  16384,
  False,
  'campaign reactor-prepared-input-check',
  'ReactorPreparedInput',
  ('programmes/foundations/measurement-and-response/workflows/reactor-response/causal-response-study-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/feed-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/finite-control-frontier-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/local-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/matched-replay-history-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/regime-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/selected-action-response-input.json',
   'programmes/foundations/measurement-and-response/workflows/reactor-response/staged-pulse-response-input.json')),
 ('tokamak-heat',
  'empirical-lawhood/simulators/torax-native/native-torax-quickstart',
  'empirical_lawhood.adapters.simulators.torax_native.native_quickstart',
  'NativeToraxQuickstart',
  'editable',
  32768,
  False,
  'campaign torax-native-check',
  'NativeToraxQuickstart',
  ('programmes/energy/fusion/workflows/tokamak-heat-response/config.json',)),
 ('electron-gas-reference',
  'empirical-lawhood/simulators/uniform-electron-gas-response/analytic-reference-config',
  'empirical_lawhood.adapters.simulators.uniform_electron_gas_response.native_quickstart',
  'UniformElectronGasAnalyticReferenceConfig',
  'editable',
  32768,
  True,
  'campaign electron-gas-reference-check',
  'UniformElectronGasAnalyticReferenceConfig',
  ('programmes/materials/superconductivity/workflows/electron-gas-response/config.json',)),
 ('evidence-provenance-template',
  None,
  None,
  None,
  'helper',
  None,
  False,
  'manual evidence provenance',
  'human-edited template',
  ('configs/templates/evidence-provenance.yaml',)))

_BASE_CONSUMERS = tuple(ConfigurationConsumer(*row) for row in _CONSUMER_ROWS)


def _configuration_consumers() -> tuple[ConfigurationConsumer, ...]:
    from empirical_lawhood.api.experiment_preparation import experiment_protocols

    extra = tuple(ConfigurationConsumer(
        declaration.consumer_id, declaration.specification_type.SCHEMA,
        declaration.specification_type.__module__, declaration.specification_type.__name__,
        "editable", declaration.maximum_config_bytes, True, "campaign experiment-prepare",
        declaration.specification_type.__name__, declaration.example_paths, declaration.configuration_capabilities)
        for declaration in experiment_protocols())
    inputs = tuple(ConfigurationConsumer(
        value.consumer_id, value.record_type.SCHEMA,
        value.record_type.__module__, value.record_type.__name__,
        "editable", value.maximum_config_bytes, False, "campaign experiment-prepare --sources",
        value.record_type.__name__, value.example_paths)
        for declaration in experiment_protocols() for value in declaration.configuration_inputs)
    result = (*_BASE_CONSUMERS, *extra)
    names = {consumer.consumer for consumer in result}
    if len(names) != len(result):
        raise ValueError("configuration consumers conflict with installed experiment declarations")
    shared = {}
    for consumer in inputs:
        previous = shared.setdefault(consumer.consumer, consumer)
        if consumer.consumer in names or previous != consumer:
            raise ValueError("configuration input consumers conflict with installed owning declarations")
    return (*result, *shared.values())


class _ConfigurationConsumers(Sequence):
    """Keep static imports cold while deriving domain consumers when requested."""

    def __len__(self):
        return len(_configuration_consumers())

    def __getitem__(self, index):
        return _configuration_consumers()[index]

    def __iter__(self):
        return iter(_configuration_consumers())


CONSUMERS = _ConfigurationConsumers()


def consumers_for_schema(schema_id: str) -> tuple[ConfigurationConsumer, ...]:
    return tuple(item for item in CONSUMERS if item.schema_id == schema_id)


def consumer_by_id(consumer: str) -> ConfigurationConsumer:
    for item in CONSUMERS:
        if item.consumer == consumer:
            return item
    raise ValueError(f"unknown configuration consumer: {consumer}")
