"""Optional operational ceilings, independent of exact scientific identities."""

def minimum_byte_limit(*limits):
    """Intersect explicit ceilings; None adds no arbitrary implementation cap."""
    selected = [value for value in limits if value is not None]
    if any(type(value) is not int or value < 0 for value in selected):
        raise ValueError("operational byte ceilings require nonnegative integers or None")
    return min(selected) if selected else None

def byte_limit_within(selected, owner):
    """A consumer may tighten an explicit owner ceiling, never enlarge it."""
    return owner is None or selected is not None and selected <= owner
