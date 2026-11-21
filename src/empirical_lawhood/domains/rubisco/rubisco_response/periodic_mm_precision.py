"""Reusable scientific records, designs and calculations extracted from native binding.

Native acquisition and external-format effects belong to the corresponding adapter.
Original scientific schemas and numerical definitions are preserved.
"""

from hashlib import sha256
import io
import json


PREFIX = 'mm-precision-'


ARRAY_NAMES = tuple(f'{platform}-{quantity}' for platform in ('cuda', 'reference')
    for quantity in ('energy-kj-mol', 'forces-kj-mol-nm'))


def assess_molecular_precision(raw_members, *, physical_atom_count, coordinate_sha256, remainder_sha256):
    """Compare authenticated original arrays; perform no native evaluation."""
    import numpy as np
    expected = {PREFIX+'request.json', PREFIX+'completion.json', *(PREFIX+name+'.npy' for name in ARRAY_NAMES)}
    if set(raw_members) != expected:
        raise ValueError('molecular precision requires its complete original member denominator')
    request = json.loads(raw_members[PREFIX+'request.json'])
    completion = json.loads(raw_members[PREFIX+'completion.json'])
    if (request.get('version') != '1.0.0' or completion.get('version') != '1.0.0'
            or request.get('physical_atom_count') != physical_atom_count
            or request.get('coordinate_sha256') != coordinate_sha256
            or request.get('remainder_parameter_sha256') != remainder_sha256
            or request.get('scope') != 'SAME_GEOMETRY_COMPLETE_MM_CUDA_REFERENCE'
            or request.get('electronic_evaluations') != 0 or completion.get('electronic_evaluations') != 0
            or request.get('cuda_properties') != {'Precision': 'double', 'DeviceIndex': '0', 'DeterministicForces': 'true'}
            or completion.get('platforms') != ['CUDA', 'Reference'] or completion.get('completed_mm_evaluations') != 2
            or completion.get('original_system_unchanged') is not True
            or completion.get('request_sha256') != sha256(raw_members[PREFIX+'request.json']).hexdigest()):
        raise ValueError('molecular precision substitutes its original physical or numerical operands')
    arrays = {}
    for name in ARRAY_NAMES:
        stream = io.BytesIO(raw_members[PREFIX+name+'.npy'])
        value = np.load(stream, allow_pickle=False)
        shape = () if name.endswith('energy-kj-mol') else (physical_atom_count, 3)
        if stream.read(1) or value.dtype.str != '<f8' or value.shape != shape or not np.isfinite(value).all():
            raise ValueError('molecular precision changes complete finite binary64 MM operands')
        arrays[name] = value
    difference = arrays['cuda-forces-kj-mol-nm']-arrays['reference-forces-kj-mol-nm']
    return dict(status='COMPARED', physical_atom_count=physical_atom_count,
        energy_change_kj_mol=float(arrays['cuda-energy-kj-mol']-arrays['reference-energy-kj-mol']),
        maximum_force_change_kj_mol_nm=float(np.max(np.abs(difference))),
        rms_force_component_change_kj_mol_nm=float(np.sqrt(np.mean(difference*difference))),
        matched_pme=request['matched_pme'], wall_seconds=completion['wall_seconds'],
        completed_mm_evaluations=2, new_native_calls=0, electronic_evaluations=0,
        comparison_scope='PARAMETER_STORAGE_AND_PLATFORM_ARITHMETIC_COMBINED',
        chemical_model_adequacy='NOT_ESTABLISHED', parameter_rounding_isolated=False)
