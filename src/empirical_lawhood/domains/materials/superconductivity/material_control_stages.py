"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from empirical_lawhood.domains.materials.superconductivity.workflow_profiles import MATERIAL_CONTROL_WORKFLOW_PROFILES


CONFIG_ARTIFACT_ID = 'config-artifact.ambient-pressure-superconductor-material-control'


SOURCE_CONTRACT_ARTIFACT_ID = 'source-contract.ambient-pressure-superconductor-material-control-control-bundle'


SOURCE_STEP = 'material-control-source-qualification'


METHOD_STEP = 'material-control-gauge-covariant-response-method-qualification'


CONSTRUCTIVE_SEARCH_CONFORMANCE_STEP = 'material-control-constructive-search-search-world-conformance'


CLOSEOUT_STEP = 'material-control-science-freeze-closeout'


_WORKFLOW_SEQUENCE = (
    'workflow.material-control-tutorial04-pb',
    'workflow.material-control-tutorial04-mgb2',
    'workflow.material-control-pbe-efficiency-base-calibration-pb-fcc',
    'workflow.material-control-pbe-precision-refined-calibration-pb-fcc',
    'workflow.material-control-pbe-efficiency-base-calibration-mgb2-alb2',
    'workflow.material-control-pbe-precision-refined-calibration-mgb2-alb2',
    'workflow.material-control-pbe-efficiency-base-calibration-cu-fcc',
    'workflow.material-control-pbe-precision-refined-calibration-cu-fcc',
    'workflow.material-control-pbe-efficiency-base-calibration-c-diamond',
    'workflow.material-control-pbe-precision-refined-calibration-c-diamond',
    'workflow.material-control-pbe-efficiency-base-calibration-pb-sc-compressed',
    'workflow.material-control-pbe-precision-refined-calibration-pb-sc-compressed',
)


_PROFILE_BY_ID = {value.profile_id: value for value in MATERIAL_CONTROL_WORKFLOW_PROFILES}


if set(_WORKFLOW_SEQUENCE) != set(_PROFILE_BY_ID):
    raise ValueError('material control workflow execution sequence differs from its closed profile set')


def _workflow_step_id(index: int, profile_id: str) -> str:
    return f"material-control-workflow-{index:02d}-{profile_id.removeprefix('workflow.material-control-')}"


WORKFLOW_TASKS = {
    _workflow_step_id(index, profile_id): _PROFILE_BY_ID[profile_id]
    for index, profile_id in enumerate(_WORKFLOW_SEQUENCE, start=1)
}


PROFILE_TASKS = {value.profile_id: key for key, value in WORKFLOW_TASKS.items()}


PANEL_TASKS = {
    'material-control-panel-c-diamond': 'structure.calibration-c-diamond',
    'material-control-panel-cu-fcc': 'structure.calibration-cu-fcc',
    'material-control-panel-mgb2-alb2': 'structure.calibration-mgb2-alb2',
    'material-control-panel-pb-fcc': 'structure.calibration-pb-fcc',
    'material-control-panel-pb-sc-compressed': 'structure.calibration-pb-sc-compressed',
}
