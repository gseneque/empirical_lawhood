# SPDX-License-Identifier: MPL-2.0
"""Complete-output memory admission; controls do not qualify an enzyme."""
import subprocess
import sys
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_jk as owner
from empirical_lawhood.domains.rubisco.rubisco_response.pyscf_cvhf_allocation import patch_complete_output_cache


def selection(**changes):
    values = dict(nao=2095, nbas=840, ncomp=1, contractions=2,
        maximum_threads=8, integral_workspace_elements=16500, available_bytes=2*2**30)
    return owner.select_jk_threads(**dict(values, **changes))


def test_complete_enzyme_dimensions_fit_the_recorded_headroom_at_selected_concurrency():
    for available in (2*2**30, 3*2**30, 4*2**30):
        value = selection(available_bytes=available)
        assert 1 <= value['threads'] <= 8
        assert value['fixed_workspace_bytes']+2*value['threads']*value['per_thread_workspace_bytes'] <= available
    restricted = selection(available_bytes=2*2**30)
    derivatives = selection(ncomp=3, available_bytes=2*2**30)
    spin = selection(ncomp=3, contractions=4, available_bytes=4*2**30)
    assert derivatives['threads'] < restricted['threads']
    assert spin['per_thread_workspace_bytes'] > derivatives['per_thread_workspace_bytes']


def test_thread_selection_keeps_the_actual_cpu_limit_and_has_no_hidden_eight_thread_ceiling():
    assert selection(maximum_threads=1)['threads'] == 1
    assert selection(maximum_threads=16, available_bytes=10*2**30)['threads'] == 16
    with pytest.raises(MemoryError, match='one complete J/K contraction thread'):
        selection(available_bytes=128*2**20)


@pytest.mark.parametrize('changes', ({'nao': 0}, {'ncomp': True}, {'contractions': -1},
    {'maximum_threads': 0}, {'integral_workspace_elements': -1}, {'available_bytes': -1}))
def test_invalid_memory_dimensions_refuse(changes):
    with pytest.raises(ValueError, match='positive dimensions'):
        selection(**changes)


def test_unmodified_or_misidentified_cvhf_build_refuses_before_contraction():
    with pytest.raises(ValueError, match='complete-output CVHF allocation build'):
        owner._require_complete_output_allocator(SimpleNamespace())
    class Marker:
        def __call__(self):
            return 0
    with pytest.raises(ValueError, match='marker disagrees'):
        owner._require_complete_output_allocator(SimpleNamespace(ELCVHFcomplete_output_cache_v1=Marker()))


def test_source_transform_refuses_unidentified_or_already_changed_source():
    for value in (b'', b'void CVHFallocate_JKArray() {}', 'not bytes'):
        with pytest.raises(ValueError, match='exact inspected PySCF'):
            patch_complete_output_cache(value)


def test_static_import_does_not_load_numerical_engines():
    result = subprocess.run([sys.executable, '-c',
        'import sys; from empirical_lawhood.adapters.rubisco.rubisco_response import pyscf_periodic_jk, pyscf_periodic_diis; '
        'assert not any(k=="pyscf" or k.startswith("pyscf.") or k=="numpy" for k in sys.modules)'],
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
