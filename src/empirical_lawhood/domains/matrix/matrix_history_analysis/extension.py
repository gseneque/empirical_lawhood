# SPDX-License-Identifier: MPL-2.0
"""Authoritative scientific extension declaration and native implementation roles."""
from __future__ import annotations

# SPDX-License-Identifier: MPL-2.0
# Scientific registration and configuration.
from empirical_lawhood.execution.extension_bundles import ExtensionBundleContribution, ExtensionContributionKind
from empirical_lawhood.execution.experiment_preparation import ExperimentProtocolDeclaration
from empirical_lawhood.domains.matrix.matrix_history_analysis.records import MatrixHistoryAllocation, MatrixHistoryAnalysisConfig
from empirical_lawhood.domains.matrix.matrix_history_analysis.experiment_preparation import PROTOCOL_ID, MatrixHistoryProgrammeSpecification, MatrixHistoryProgrammePlan, prepare, bind_inputs

_DISCOVERY_CONTRIBUTION=ExtensionBundleContribution('method.matrix-history-analysis-programme','1.0.0',
    ExtensionContributionKind.METHOD,(),(),(),(),(),(),(),(),(),(),False,False)
_PROTOCOLS=(ExperimentProtocolDeclaration(PROTOCOL_ID,MatrixHistoryProgrammeSpecification,prepare,
    'matrix-history-descriptive-programme',example_paths=('programmes/foundations/emergent-structure/workflows/matrix-history-analysis/programme.json',),
    maximum_config_bytes=None,input_record_types=(MatrixHistoryAllocation,MatrixHistoryAnalysisConfig),bind_inputs=bind_inputs,
    programme_record_type=MatrixHistoryProgrammePlan),)




from empirical_lawhood.execution.extensions import ExtensionDefinition

EXTENSION = ExtensionDefinition(
    discovery=_DISCOVERY_CONTRIBUTION,
    protocols=_PROTOCOLS,
)

__all__ = ['EXTENSION']
