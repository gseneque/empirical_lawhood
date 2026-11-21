"""Native acquisition, external-format translation and custody integration."""

from __future__ import annotations
from empirical_lawhood.science.identity.provenance import ObjectIdentity
from empirical_lawhood.domains.fusion.prepared_base import PreparedBaseCellSubstitution, PreparedBaseEpisode
from empirical_lawhood.adapters.simulators.prepared_base import acquire_episode

from empirical_lawhood.domains.fusion.preparation_path_sensitivity import (
    PreparationPathSensitivityBatch as _science_PreparationPathSensitivityBatch,
    PreparationPathSensitivityConfig as _science_PreparationPathSensitivityConfig,
    PreparationPathSensitivityStage as _science_PreparationPathSensitivityStage,
    _TECHNICAL,
)

def acquire_preparation_path_sensitivity(config: _science_PreparationPathSensitivityConfig) -> _science_PreparationPathSensitivityBatch:
    episodes: list[PreparedBaseEpisode] = []
    active: list[str] = []
    excluded: list[str] = []
    substitutions: list[PreparedBaseCellSubstitution] = []
    reserves = iter(config.reserve_cell_ids)
    for intended_id in config.primary_cell_ids:
        current_id = intended_id
        while True:
            local = []
            technical = False
            for view in config.views:
                episode = acquire_episode(
                    config=config,  # type: ignore[arg-type]
                    cell_id=current_id,
                    word_id=config.words[0].word_id,
                    view_id=view.view_id,
                )
                local.append(episode)
                episodes.append(episode)
                if episode.disposition in _TECHNICAL:
                    technical = True
                    break
            if not technical:
                active.append(current_id)
                break
            excluded.append(current_id)
            try:
                replacement = next(reserves)
            except StopIteration:
                break
            substitutions.append(
                PreparedBaseCellSubstitution(
                    substitution_id=(
                        f"substitution.preparation-path-sensitivity.{intended_id.removeprefix('cell.')}."
                        f"{replacement.removeprefix('cell.')}"
                    ),
                    intended_cell_id=intended_id,
                    replacement_cell_id=replacement,
                    excluded_episode_ids=tuple(sorted(value.episode_id for value in local)),
                    reason_codes=tuple(
                        sorted({reason for value in local for reason in value.reason_codes})
                    )
                    or ("TECHNICAL_BUNDLE_FAILURE",),
                    receiver_outcome_released_to_evaluator=False,
                )
            )
            current_id = replacement
    return _science_PreparationPathSensitivityBatch(
        batch_id=(
            'batch.preparation-path-sensitivity-density-current-qualification'
            if config.stage is _science_PreparationPathSensitivityStage.QUALIFICATION
            else 'batch.preparation-path-sensitivity-density-current-evaluation'
        ),
        config=ObjectIdentity.from_record(config.config_id, config),
        stage=config.stage,
        episodes=tuple(sorted(episodes, key=lambda value: value.episode_id)),
        active_cell_ids=tuple(sorted(active)),
        excluded_cell_ids=tuple(sorted(excluded)),
        substitutions=tuple(sorted(substitutions, key=lambda value: value.substitution_id)),
        expected_active_cell_count=len(config.primary_cell_ids),
        complete_active_roster=len(active) == len(config.primary_cell_ids),
        outcome_access=config.outcome_access,
    )
