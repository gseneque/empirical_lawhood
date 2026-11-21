# SPDX-License-Identifier: MPL-2.0
"""Narrow analysis-only changes supported by retained native M2 arrays."""

MEMORY_ANALYSIS_FIELDS = frozenset({
    "lags", "history_orders", "observation_dimensions", "bin_edges",
    "maximum_cells", "minimum_support", "receiver_oscillation", "tolerance",
    "binning_allowance", "tail_allowance", "protocol_age_ticks", "optional_diagnostics",
    "segment_boundaries_samples", "segment_transition_policy",
})


def validate_reanalysis_settings(original, current, modules):
    """Validate complete normalized settings and return whether they differ.

Only M2 may alter its analysis of already retained q/velocity/force arrays.
No physical acquisition, clock, chart, seed, record, ladder or budget changes
are permitted. These are exposed post-hoc choices, not a fresh confirmation.
"""
    if type(original) is not dict or type(current) is not dict:
        raise ValueError("retained analysis requires complete matching settings schemas")
    if original == current:
        return False
    if set(modules) != {"M2"}:
        raise ValueError("changed retained analysis settings require M2-only selection")
    old_fields, new_fields = set(original), set(current)
    if old_fields != new_fields and not (
            'receiver_study' not in original and new_fields == old_fields | {'receiver_study'}):
        raise ValueError("retained analysis requires complete matching settings schemas")
    if 'receiver_study' in current:
        from .receiver_campaign import REVISION
        receiver = current['receiver_study']
        if type(receiver) is not dict or receiver.get('revision') != REVISION:
            raise ValueError('The common-future reanalysis requires its declared receiver revision')
        original_coordinates = (original['receiver_study']['M2']['coordinates'] if 'receiver_study' in original
                                else [coordinate['id'] for coordinate in original['native']['coordinates']])
        if receiver['M2']['coordinates'] != original_coordinates:
            raise ValueError('Retained M2 must assess every originally acquired coordinate')
        if 'receiver_study' in original and (
                {k: v for k, v in original['receiver_study'].items() if k != 'M2'} !=
                {k: v for k, v in receiver.items() if k != 'M2'}):
            raise ValueError('Retained M2 cannot revise other module selections or original operands')
        choice = receiver['M2']
        age, future, past = (choice[k] for k in (
            'origin_record_age_ticks', 'future_lag_ticks', 'history_lag_ticks'))
        if (any(t % original['memory']['stride'] for t in (age, future, past))
                or age < past or age + future > original['memory']['record_ticks']):
            raise ValueError('The original M2 record must contain the declared history, origin, and future')
    for key in original:
        if key not in {"alpha", "memory", "receiver_study"} and original[key] != current[key]:
            raise ValueError("retained M2 analysis changes an acquisition setting: " + key)
    old, new = original.get("memory"), current.get("memory")
    if type(old) is not dict or type(new) is not dict or set(old) != set(new):
        raise ValueError("retained M2 analysis requires the complete original memory settings")
    forbidden = sorted(key for key in old if key not in MEMORY_ANALYSIS_FIELDS and old[key] != new[key])
    if forbidden:
        raise ValueError("retained M2 analysis changes an acquisition setting: memory." + forbidden[0])
    return True
