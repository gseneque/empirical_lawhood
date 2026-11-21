# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Empirical Lawhood project.
# Patch fragments derive from PySCF 2.14.0 (Apache-2.0).
"""Exact-source correction for unused complete-output J/K cache capacity.

PySCF's original direct driver reserves up to 3.2 GB per OpenMP thread.
Each JKArray stores each output tile at most once before a write-back.
It therefore needs no more elements than its complete output matrix.
The contraction, integral screening, tile partition and write-back stay intact.
This pure transform does not build, load or alter an installed environment.
"""
from hashlib import sha256


ORIGINAL_NR_DIRECT_SHA256 = '9c181daa8ce689e312e548694f47a2935105094fab1e685e82b4bf485e0639c4'
ALLOCATION_MARKER = 'ELCVHFcomplete_output_cache_v1'


def patch_complete_output_cache(original):
    if type(original) is not bytes or sha256(original).hexdigest() != ORIGINAL_NR_DIRECT_SHA256:
        raise ValueError('CVHF allocation correction requires the exact inspected PySCF 2.14.0 source')
    source = original.decode('utf-8')
    old = '''        jkarray->data = malloc(sizeof(double) * (size_limit + 136*136));
        if (jkarray->data == NULL) {
                fprintf(stderr, "malloc(%zu) failed in CVHFallocate_JKArray\\n",
                        sizeof(double) * (size_limit + 136*136));'''
    new = '''        /* Empirical Lawhood: an output tile is cached at most once.
         * Retain the upstream capacity when it is smaller, but never reserve
         * unused elements beyond the complete output matrix. No integral or
         * contraction is omitted and the original write-back rule is intact.
         */
        size_t complete_elements = (*op->data_size)(shls_slice, ao_loc) * (size_t)ncomp;
        size_t allocation_elements = MIN((size_t)size_limit + 136*136, complete_elements);
        jkarray->data = malloc(sizeof(double) * allocation_elements);
        if (jkarray->data == NULL) {
                fprintf(stderr, "malloc(%zu) failed in CVHFallocate_JKArray\\n",
                        sizeof(double) * allocation_elements);'''
    assert source.count(old) == 1
    source = source.replace(old, new)
    old = '        int keys_max = size_limit / (AO_BLOCK_SIZE*AO_BLOCK_SIZE*ncomp);'
    new = '''        /* Every possible tile key, including partially filled edge tiles. */
        size_t keys_max = (size_t)nblock * nblock;'''
    assert source.count(old) == 1
    source = source.replace(old, new)
    source += '''
/* Build marker for the source-bound complete-output allocation correction. */
int ELCVHFcomplete_output_cache_v1(void) { return 1; }
'''
    return source.encode('utf-8')
