"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from empirical_lawhood.domains.materials.superconductivity.material_control_contracts import ControlClass


class WorkflowKind(StrEnum):
    POSITIVE = "POSITIVE"
    PHONON_STABILITY = "PHONON_STABILITY"
    SCF_CLASS = "SCF_CLASS"


class WorkflowSource(StrEnum):
    EPW_SUPERCONDUCTING_REFERENCE = "EPW_SUPERCONDUCTING_REFERENCE"
    SSSP_CONTROL = "SSSP_CONTROL"


@dataclass(frozen=True, slots=True)
class MaterialControlWorkflowProfile:
    profile_id: str
    source: WorkflowSource
    structure_id: str
    view_id: str
    control_class: ControlClass
    kind: WorkflowKind
    source_root: str
    prefix: str
    cpu_cores: int
    memory_bytes: int


@dataclass(frozen=True, slots=True)
class MaterialControlWorkflowRequest:
    request_id: str
    run_id: str
    task_id: str
    profile_id: str
    wall_time_seconds: int
    output_bytes: int


@dataclass(frozen=True, slots=True)
class MaterialControlWorkflowOperands:
    exit_code: int
    timed_out: bool
    terminal_step_id: str
    wall_time_seconds: Decimal
    peak_scratch_bytes: int
    scf_completed: bool
    scf_converged: bool
    total_energy_Ry: Decimal
    scf_accuracy_Ry: Decimal
    scf_repeat_evaluable: bool
    scf_repeat_residual_Ry: Decimal
    fermi_evaluable: bool
    fermi_energy_eV: Decimal
    band_gap_eV: Decimal
    phonon_evaluable: bool
    minimum_phonon_frequency_cm1: Decimal
    epw_evaluable: bool
    electron_phonon_lambda: Decimal
    tc_estimate_K: Decimal
    gap_min_meV: Decimal
    gap_max_meV: Decimal
    raw_archive_path: Path
    raw_archive_sha256: str
    raw_archive_bytes: int
    raw_hdf5_path: Path
    raw_hdf5_sha256: str
    raw_hdf5_bytes: int
    reason_codes: tuple[str, ...]
