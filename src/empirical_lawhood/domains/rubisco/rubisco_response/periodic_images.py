# SPDX-License-Identifier: MPL-2.0
"""Explicit electronic-field images for an orthorhombic periodic cell.

The classical coordinates and complete particle population remain unchanged.
This primitive admits no QM region, potential, native operation or trajectory.
"""


def localize_periodic_field(qm_coordinates, mm_coordinates, lattice):
    """Put each MM field site in the cell centred on the complete QM centroid.

    All three operands must use the same Cartesian length unit. QM coordinates
    must already describe the complete unwrapped region, including link caps.
    Returned integer image shifts do not alter the derivative with respect to
    an original coordinate away from image boundaries. Only electronic field
    coordinates are imaged; classical bonded coordinates must not be replaced.
    """
    import numpy as np

    qm = np.asarray(qm_coordinates, dtype=float)
    field = np.asarray(mm_coordinates, dtype=float)
    box = np.asarray(lattice, dtype=float)
    if (qm.ndim != 2 or qm.shape[1:] != (3,) or not len(qm)
            or field.ndim != 2 or field.shape[1:] != (3,) or not len(field)
            or not np.isfinite(qm).all() or not np.isfinite(field).all()):
        raise ValueError('Complete finite nonempty QM and MM Cartesian populations required')
    if (box.shape != (3, 3) or not np.isfinite(box).all()
            or np.any(np.diag(box) <= 0)
            or not np.array_equal(box, np.diag(np.diag(box)))):
        raise ValueError('A finite positive orthorhombic lattice is required')
    center = np.mean(qm, axis=0)
    fractional = (field-center)/np.diag(box)
    if not np.isfinite(fractional).all() or np.max(np.abs(fractional)) >= 2**48:
        raise ValueError('Periodic image arithmetic exceeds reliable integer resolution')
    images = np.floor(fractional+0.5).astype(np.int64)
    localized = field-images*np.diag(box)
    if not np.isfinite(localized).all():
        raise ValueError('Periodic field localization produced a nonfinite coordinate')
    return localized, images
