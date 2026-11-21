"""Methionine side-chain initialization on explicit Cartesian coordinates."""
import math
import numpy as np

def rotate_methionine_chi1(coordinates, requested_angle):
    """Return rotated N/CA/CB/CG/SD/CE coordinates and the original chi1.

    Coordinates retain the caller's length unit; the angle is in radians.
    The N-CA-CB frame remains fixed and only CG, SD and CE rotate.
    """
    positions = np.asarray(coordinates, dtype=float).copy()
    if positions.shape != (6, 3):
        raise ValueError("methionine geometry requires six three-dimensional atom positions")
    atoms = {name: index for index, name in enumerate(("N", "CA", "CB", "CG", "SD", "CE"))}
    angle = requested_angle
    p0, p1, p2, p3 = (positions[atoms[name]] for name in ("N", "CA", "CB", "CG"))
    axis = p2 - p1
    axis /= np.linalg.norm(axis)
    v, w = p0 - p1, p3 - p2
    v -= np.dot(v, axis) * axis
    w -= np.dot(w, axis) * axis
    current = math.atan2(np.dot(np.cross(axis, v), w), np.dot(v, w))
    delta = angle - current
    for name in ("CG", "SD", "CE"):
        offset = positions[atoms[name]] - p2
        positions[atoms[name]] = (
            p2
            + offset * math.cos(delta)
            + np.cross(axis, offset) * math.sin(delta)
            + axis * np.dot(axis, offset) * (1 - math.cos(delta))
        )
    return positions, current
