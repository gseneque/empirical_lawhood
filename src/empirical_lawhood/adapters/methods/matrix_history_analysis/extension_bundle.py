# SPDX-License-Identifier: MPL-2.0
"""Cold E2 copied-input facade; no E1 findings or scientific authority."""
from empirical_lawhood.runtime.extension_bundles import ExtensionBundleContribution,ExtensionContributionKind
from empirical_lawhood.runtime.experiment_preparation import ExperimentProtocolDeclaration
from .records import MatrixHistoryAllocation,MatrixHistoryAnalysisConfig
from .experiment_preparation import PROTOCOL_ID,MatrixHistoryProgrammeSpecification,MatrixHistoryProgrammePlan,prepare,bind_inputs

EXTENSION_BUNDLE_CONTRIBUTION=ExtensionBundleContribution('method.matrix-history-analysis-programme','1.0.0',
    ExtensionContributionKind.METHOD,(),(),(),(),(),(),(),(),(),(),False,False)
EXPERIMENT_PROTOCOL_DECLARATIONS=(ExperimentProtocolDeclaration(PROTOCOL_ID,MatrixHistoryProgrammeSpecification,prepare,
    'matrix-history-descriptive-programme',example_paths=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json',),
    maximum_config_bytes=None,input_record_types=(MatrixHistoryAllocation,MatrixHistoryAnalysisConfig),bind_inputs=bind_inputs,
    programme_record_type=MatrixHistoryProgrammePlan),)
