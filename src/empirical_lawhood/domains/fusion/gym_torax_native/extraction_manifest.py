"""Reusable scientific contracts and calculations; native effects are owned by the adapter."""

from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from empirical_lawhood.science.evidence.evidence import EvidenceCeiling, OutcomeAccess, VisibilityCeiling
from empirical_lawhood.science.records.serialization import CanonicalRecord, require_sorted_unique_ids, validate_relative_locator, validate_sha256, validate_stable_id


GYM_TORAX_SURGICAL_EXTRACTION_MANIFEST_ID = 'source-manifest.tokamak-control.current-native-source-closure'


_ENTRY_PATHS = (
    'src/empirical_lawhood/adapters/composition/tokamak_control_replication/__init__.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/__init__.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/extension.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/extraction_manifest.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/field_metadata.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/finite_action_recurrence_execution.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/finite_action_recurrence_recovery.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/finite_action_recurrence_science.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/native_quickstart.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/parameterised_binding.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/projection.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/provider.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/runtime.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/selected_parent_execution.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/selected_parent_science.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/source.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/source_assessment_adjudication.py',
    'src/empirical_lawhood/adapters/simulators/gym_torax_native/source_assessment_execution.py',
    'src/empirical_lawhood/design/controller_study.py',
    'src/empirical_lawhood/design/finite_action_alternate_branch_selection.py',
    'src/empirical_lawhood/design/finite_action_occurrence.py',
    'src/empirical_lawhood/design/finite_action_recurrence.py',
    'src/empirical_lawhood/design/native_hold_decision_cell_calibration.py',
    'src/empirical_lawhood/design/preissue_branch_selection.py',
    'src/empirical_lawhood/design/source_pipelines.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/action_word.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/diagnostic_contracts.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/extraction_manifest.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/field_metadata.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/field_metadata_contracts.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/finite_action_recurrence_evaluation_recovery.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/finite_action_recurrence_execution_records.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/finite_action_recurrence_protocol.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/finite_action_recurrence_recovery.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/finite_action_recurrence_science.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/metadata_barrier.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/native_episode.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/observation.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/projection.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/protocol_scientific_inputs.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/retained_inputs.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/selected_parent_execution_records.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/selected_parent_protocol.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/selected_parent_science.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_assessment_adjudication.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_assessment_execution_records.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_assessment_protocol.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_assessment_seeds.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_contracts.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/source_qualification.py',
    'src/empirical_lawhood/domains/fusion/gym_torax_native/system.py',
    'src/empirical_lawhood/domains/fusion/tokamak_control_replication/authoring/action_words.py',
    'src/empirical_lawhood/domains/fusion/tokamak_control_replication/authoring/campaign_design.py',
    'src/empirical_lawhood/domains/fusion/tokamak_control_replication/authoring/rosters.py',
    'src/empirical_lawhood/domains/fusion/tokamak_control_replication/authoring/scientific_inputs.py',
    'src/empirical_lawhood/execution/finite_action_recurrence.py',
    'src/empirical_lawhood/execution/gym_torax_custody.py',
    'src/empirical_lawhood/execution/native_hold_decision_cell_calibration.py',
    'src/empirical_lawhood/execution/native_time_grid.py',
    'src/empirical_lawhood/methods/confirmatory_finite_action.py',
    'src/empirical_lawhood/methods/confirmatory_finite_action_region_support.py',
    'src/empirical_lawhood/methods/confirmatory_finite_action_registration.py',
    'src/empirical_lawhood/methods/evidence_projection_templates.py',
    'src/empirical_lawhood/methods/qualification_profiles.py',
)




@dataclass(frozen=True, slots=True)
class GymToraxBoundedExtractionEntry(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-bounded-extraction-entry'

    entry_id: str
    target_relative_path: str
    target_file_sha256: str

    def __post_init__(self) -> None:
        validate_stable_id(self.entry_id, field_name="entry_id")
        validate_relative_locator(self.target_relative_path)
        validate_sha256(self.target_file_sha256, field_name="target_file_sha256")
        if self.target_relative_path not in _ENTRY_PATHS:
            raise ValueError("source entry is outside the target package roster")

@dataclass(frozen=True, slots=True)
class GymToraxBoundedExtractionManifest(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/simulators/gym-torax-native/gym-torax-bounded-extraction-manifest'

    manifest_id: str
    entries: tuple[GymToraxBoundedExtractionEntry, ...]
    outcome_access: OutcomeAccess
    visibility_ceiling: VisibilityCeiling
    evidence_ceiling: EvidenceCeiling
    grants_source_access: bool
    grants_execution_authority: bool
    grants_scientific_promotion: bool

    def __post_init__(self) -> None:
        validate_stable_id(self.manifest_id, field_name="manifest_id")
        if self.manifest_id != GYM_TORAX_SURGICAL_EXTRACTION_MANIFEST_ID:
            raise ValueError("unexpected target source manifest identity")
        require_sorted_unique_ids(self.entries, attribute="entry_id", field_name="entries")
        if tuple(sorted(row.target_relative_path for row in self.entries)) != tuple(sorted(_ENTRY_PATHS)):
            raise ValueError("target source file roster is not closed")
        if self.outcome_access is not OutcomeAccess.OUTCOME_BLIND:
            raise ValueError("target source manifest must remain outcome-blind")
        if self.visibility_ceiling is not VisibilityCeiling.PROSPECTIVE:
            raise ValueError("target source manifest must remain prospective")
        if self.evidence_ceiling is not EvidenceCeiling.NON_PROMOTABLE:
            raise ValueError("source bytes are not scientific evidence")
        if self.grants_source_access or self.grants_execution_authority or self.grants_scientific_promotion:
            raise ValueError("target source manifest cannot grant authority")
