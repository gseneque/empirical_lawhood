"""Array-level coarse active-line grid-topology receiver."""

def connected_substation_components(n_sub: int, line_status, line_origins, line_extremities) -> int:
    """Count components on the native active-line substation graph.

    The busbar-resolved state remains separately bound by ``topo_vect``.  This
    receiver is intentionally a coarser declared gauge, not a replacement for
    the native topology observation.
    """

    n_sub = int(n_sub)
    parents = list(range(n_sub))

    def find(value: int) -> int:
        while parents[value] != value:
            parents[value] = parents[parents[value]]
            value = parents[value]
        return value

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for active, origin, extremity in zip(
        line_status,
        line_origins,
        line_extremities,
        strict=True,
    ):
        if bool(active):
            union(int(origin), int(extremity))
    return len({find(value) for value in range(n_sub)})

