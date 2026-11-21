# SPDX-License-Identifier: MPL-2.0
"""Validate current authored choices without rewriting retained record bytes."""

from .records import json_text
from empirical_lawhood.domains.matrix.classical_series.records import json_object


def require_assigned_receiver_inputs(settings, assignments):
    """Resolve physical coordinates, case assignments and operands used by this specification."""
    if 'receiver_study' not in settings:
        return
    from .receiver_campaign import owner
    modules = {module for assignment in assignments for module in assignment.modules}
    if modules.intersection(('M3', 'M4', 'M5')) and settings['receiver_study']['instrument'] is None:
        raise ValueError('The assigned signed matrix receiver requires the original SCI02-C instrument')
    coordinates = {row['id'] for row in settings['native']['coordinates']}
    for module in modules:
        cases = owner(module).case_ids(settings, module)
        if not cases or len(set(cases)) != len(cases):
            raise ValueError(f'{module} must specify a complete, unique receiver case census')
        if module in ('M3', 'M4') and not set(cases) <= coordinates:
            raise ValueError(f'{module} selected a missing physical coordinate')
    if 'M5' in modules and 'nominal' not in coordinates:
        raise ValueError('The M5 paired H64 response requires its nominal source')


def require_current_settings(settings_json):
    """Require the complete canonical current declaration at an entry boundary.

    Record decoding retains its original bytes and identity. New preparation,
    graph compilation and scientific execution must additionally establish that
    every current choice is explicit and valid. Defaults are never inserted into
    an already frozen specification or operation by this check.
    """
    from .science import normalise_settings

    original = json_object(settings_json)
    normalized = normalise_settings(original)
    if json_text(normalized) != settings_json:
        raise ValueError('Current model-free entry requires complete normalized scientific settings')
    return original
