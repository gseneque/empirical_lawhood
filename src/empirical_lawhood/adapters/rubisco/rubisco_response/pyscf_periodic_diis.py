# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Empirical Lawhood project.
# Extrapolation formulas derive from PySCF 2.14.0 lib/diis.py (Apache-2.0).
"""Keep complete DIIS vectors on disk and check one MRRR failure recovery.

Normal DIIS arithmetic follows the original implementation. Full error and
Fock vectors use PySCF's temporary HDF5 storage instead of its per-vector
in-memory threshold. Its internal-eigensolver
failure uses symmetric QR on the unchanged finite matrix, with explicit
eigenpair checks. The original dependence threshold and mixing remain intact.
No SCF cycle, native call, or scientific attempt is replayed here.
"""
from hashlib import sha256


def bind_checked_diis(mean_field, *, observe=None):
    """Bind disk-backed CDIIS without altering installed modules or mixing."""
    import numpy as np
    from pyscf.lib import diis as original_diis
    from pyscf.scf.diis import CDIIS
    from empirical_lawhood.methods.electronic_structure.diis import checked_diis_weights, accumulate_diis_block
    original_class = mean_field.DIIS
    if original_class is not CDIIS or isinstance(getattr(mean_field, 'diis', None), original_diis.DIIS):
        raise ValueError('periodic checked disk storage requires a new original CDIIS instance')

    class CheckedDIIS(original_class):
        def _store(self, key, value):
            # The stock threshold is per vector; many individually small
            # full-basis vectors can together retain hundreds of MiB. Keep
            # every vector, its dtype and the original circular slot keys.
            # H5TmpFile uses the worker's selected PySCF scratch directory.
            if self._buffer:
                raise ValueError('periodic CDIIS cannot mix disk storage with restored in-memory vectors')
            if self._diisfile is None:
                self._diisfile = original_diis.misc.H5TmpFile(self.filename, 'w')
            if key in self._diisfile:
                self._diisfile[key][:] = value
            else:
                self._diisfile[key] = value
            self._diisfile.flush()
            _record(observe, dict(event='diis-vector-storage', policy='FULL_VECTORS_ON_DISK',
                key=key, shape=list(value.shape), dtype=str(value.dtype), bytes=int(value.nbytes),
                stored_vectors=len(self._diisfile),
                stored_bytes=sum(int(item.size*item.dtype.itemsize) for item in self._diisfile.values()),
                in_memory_vector_count=len(self._buffer)))

        def extrapolate(self, nd=None):
            try:
                return super().extrapolate(nd)
            except np.linalg.LinAlgError as error:
                if str(error) != 'Internal Error.':
                    raise
                number = self.get_num_vec() if nd is None else nd
                matrix = self._H[:number+1, :number+1]
                _record(observe, dict(event='diis-eigensolver-error', driver='evr',
                    error_type=type(error).__name__, error=str(error),
                    matrix_shape=list(matrix.shape), matrix_dtype=str(matrix.dtype),
                    matrix_sha256=sha256(matrix.tobytes(order='C')).hexdigest(),
                    matrix_real=matrix.real.tolist(), matrix_imaginary=matrix.imag.tolist()))
                try:
                    weights, diagnostics = checked_diis_weights(matrix)
                except ValueError as invalid:
                    raise invalid from error
                _record(observe, dict(event='diis-eigensolver-recovery', driver='ev',
                    matrix_sha256=sha256(matrix.tobytes(order='C')).hexdigest(), **diagnostics))
                # Native vector access and block order remain with the storage adapter.
                value = None
                for index, weight in enumerate(weights[1:]):
                    vector = self.get_vec(index)
                    if value is None:
                        value = np.zeros(vector.size, weights.dtype)
                    for start in range(0, vector.size, original_diis.BLOCK_SIZE):
                        end = min(vector.size, start+original_diis.BLOCK_SIZE)
                        accumulate_diis_block(value[start:end], vector[start:end], weight)
                return value

    mean_field.DIIS = CheckedDIIS
    return mean_field


def _record(observe, row):
    if observe is not None:
        observe(row)
