"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from typing import Final
from empirical_lawhood.domains.materials.superconductivity.material_control_contracts import ControlClass
from empirical_lawhood.domains.materials.superconductivity.workflow_contracts import (
    MaterialControlWorkflowProfile,
    WorkflowKind,
    WorkflowSource,
)


def _profile(
    profile_id: str,
    *,
    source: WorkflowSource,
    structure_id: str,
    view_id: str,
    control_class: ControlClass,
    kind: WorkflowKind,
    source_root: str,
    prefix: str,
) -> MaterialControlWorkflowProfile:
    return MaterialControlWorkflowProfile(
        profile_id=profile_id,
        source=source,
        structure_id=structure_id,
        view_id=view_id,
        control_class=control_class,
        kind=kind,
        source_root=source_root,
        prefix=prefix,
        cpu_cores=8,
        memory_bytes=24 * 1024**3,
    )


_TUTORIAL_PROFILES: Final = (
    _profile(
        'workflow.material-control-tutorial04-mgb2',
        source=WorkflowSource.EPW_SUPERCONDUCTING_REFERENCE,
        structure_id='structure.calibration-mgb2-alb2',
        view_id="view.epw-tutorial04-pbe-pseudodojo-workflow-reference",
        control_class=ControlClass.POSITIVE_ANISOTROPIC,
        kind=WorkflowKind.POSITIVE,
        source_root="tutorial04",
        prefix="mgb2",
    ),
    _profile(
        'workflow.material-control-tutorial04-pb',
        source=WorkflowSource.EPW_SUPERCONDUCTING_REFERENCE,
        structure_id='structure.calibration-pb-fcc',
        view_id="view.epw-tutorial04-pbe-pseudodojo-workflow-reference",
        control_class=ControlClass.POSITIVE_ISOTROPIC,
        kind=WorkflowKind.POSITIVE,
        source_root="tutorial04",
        prefix="pb",
    ),
)


def _science_profiles() -> tuple[MaterialControlWorkflowProfile, ...]:
    rows = (
        (
            'calibration-c-diamond',
            'structure.calibration-c-diamond',
            ControlClass.INSULATOR,
            WorkflowKind.SCF_CLASS,
            "diamond",
        ),
        (
            'calibration-cu-fcc',
            'structure.calibration-cu-fcc',
            ControlClass.NORMAL_METAL,
            WorkflowKind.SCF_CLASS,
            "cu",
        ),
        (
            'calibration-mgb2-alb2',
            'structure.calibration-mgb2-alb2',
            ControlClass.POSITIVE_ANISOTROPIC,
            WorkflowKind.POSITIVE,
            "mgb2",
        ),
        (
            'calibration-pb-fcc',
            'structure.calibration-pb-fcc',
            ControlClass.POSITIVE_ISOTROPIC,
            WorkflowKind.POSITIVE,
            "pb",
        ),
        (
            'calibration-pb-sc-compressed',
            'structure.calibration-pb-sc-compressed',
            ControlClass.DYNAMICALLY_UNSTABLE,
            WorkflowKind.PHONON_STABILITY,
            "pbsc",
        ),
    )
    result: list[MaterialControlWorkflowProfile] = []
    for view_id in ("view.pbe-efficiency-base", "view.pbe-precision-refined"):
        view_name = view_id.removeprefix("view.")
        for case, structure_id, control_class, kind, prefix in rows:
            result.append(
                _profile(
                    f'workflow.material-control-{view_name}-{case}',
                    source=WorkflowSource.SSSP_CONTROL,
                    structure_id=structure_id,
                    view_id=view_id,
                    control_class=control_class,
                    kind=kind,
                    source_root=f'material-control-control-inputs/{view_name}/{case}',
                    prefix=prefix,
                )
            )
    return tuple(result)


MATERIAL_CONTROL_WORKFLOW_PROFILES: Final = tuple(
    sorted(_TUTORIAL_PROFILES + _science_profiles(), key=lambda value: value.profile_id)
)


_PROFILE_BY_ID: Final = {value.profile_id: value for value in MATERIAL_CONTROL_WORKFLOW_PROFILES}
