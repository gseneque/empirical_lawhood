"""Board-specific linear RC-ladder numerical capability for physical scale morphism."""

from importlib import import_module

_EXPORTS = {
    'ResistorCapacitorLadderActionSegment': ('.contracts', 'ResistorCapacitorLadderActionSegment'),
    'ResistorCapacitorLadderModelConfig': ('.contracts', 'ResistorCapacitorLadderModelConfig'),
    'ResistorCapacitorLadderNumericalSummary': ('.contracts', 'ResistorCapacitorLadderNumericalSummary'),
    'ResistorCapacitorLadderOperator': ('.mna', 'ResistorCapacitorLadderOperator'),
    'ResistorCapacitorLadderTrajectory': ('.matrix_exponential', 'ResistorCapacitorLadderTrajectory'),
    'build_operator': ('.mna', 'build_operator'),
    'slowest_decay_rate': ('.mna', 'slowest_decay_rate'),
    'solve_matrix_exponential': ('.matrix_exponential', 'solve_matrix_exponential'),
}

__all__ = [
    'ResistorCapacitorLadderActionSegment',
    'ResistorCapacitorLadderModelConfig',
    'ResistorCapacitorLadderNumericalSummary',
    'ResistorCapacitorLadderOperator',
    'ResistorCapacitorLadderTrajectory',
    "build_operator",
    "slowest_decay_rate",
    "solve_matrix_exponential",
]


def __getattr__(name: str):
    """Preserve public exports while importing numerical owners on demand."""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
