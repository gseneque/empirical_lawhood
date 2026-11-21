# SPDX-License-Identifier: MPL-2.0
"""Historical settings are exact read operands, never new native authority."""

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from types import SimpleNamespace
from typing import ClassVar

import pytest

from empirical_lawhood.domains.rubisco.rubisco_response.periodic_force_contracts import (
    OriginalPeriodicMMSettings,
    PeriodicMMSettings,
    PeriodicMMSettingsRecord,
    UnversionedGeometryPeriodicMMSettings,
    periodic_geometry_policy,
    require_current_periodic_mm_settings,
)
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.records.serialization import CanonicalRecord, CanonicalizationError


ORIGINAL = b'{"schema":"empirical-lawhood/rubisco-response/periodic-mm-settings","value":{"constraints":"NONE_NATURAL_MASSES","cutoff_angstrom":{"decimal":"9"},"dispersion_tail":false,"ewald_relative_tolerance":{"decimal":"0.000001"},"nonbonded_method":"Ewald","remove_center_of_mass":false,"settings_id":"settings.exposed.legacy-mm","vdw_switch":false},"version":"1.0.0"}\n'


@dataclass(frozen=True, slots=True)
class Envelope(CanonicalRecord):
    SCHEMA: ClassVar[str] = 'empirical-lawhood/test/retained-mm-envelope'
    settings: PeriodicMMSettingsRecord


def encode(document):
    return json.dumps(document, sort_keys=True, separators=(',', ':')).encode() + b'\n'


def nested(raw):
    return encode(dict(schema=Envelope.SCHEMA, version='1.0.0', value=dict(settings=json.loads(raw))))


def test_original_revision_one_roundtrips_without_inventing_a_policy():
    raw = nested(ORIGINAL)
    record = decode_canonical_bytes(raw, Envelope, maximum_bytes=4096)
    assert type(record.settings) is OriginalPeriodicMMSettings
    assert record.settings.canonical_bytes() == ORIGINAL
    assert record.settings.fingerprint() == sha256(ORIGINAL).hexdigest()
    assert record.canonical_bytes() == raw
    assert not hasattr(record.settings, 'geometry_quality')
    with pytest.raises(ValueError, match='declare no geometry policy'):
        periodic_geometry_policy(record.settings)
    with pytest.raises(ValueError, match='requires periodic MM settings revision 2.0.0'):
        require_current_periodic_mm_settings(record.settings)


def test_interim_explicit_policy_keeps_its_original_revision_and_identity():
    # The interim writer used the expanded shape with version one. Its exact
    # explicit policy remains available for original readback, never defaulted.
    current = PeriodicMMSettings('settings.exposed.legacy-mm', 'Ewald', Decimal(9), Decimal('0.000001'))
    original = current.to_document()
    original['version'] = '1.0.0'
    raw = encode(original)
    record = decode_canonical_bytes(nested(raw), Envelope, maximum_bytes=16384).settings
    assert type(record) is UnversionedGeometryPeriodicMMSettings
    assert record.canonical_bytes() == raw
    assert record.fingerprint() == sha256(raw).hexdigest()
    assert periodic_geometry_policy(record) == current.geometry_quality
    with pytest.raises(ValueError, match='requires periodic MM settings revision 2.0.0'):
        require_current_periodic_mm_settings(record)


def test_current_policy_selection_has_its_own_revision_and_closed_decoder():
    selected = PeriodicMMSettings('settings.exposed.current-mm', 'Ewald', Decimal(9), Decimal('0.000001'))
    assert selected.to_document()['version'] == '2.0.0'
    decoded = decode_canonical_bytes(nested(selected.canonical_bytes()), Envelope, maximum_bytes=16384).settings
    assert type(decoded) is PeriodicMMSettings
    assert decoded == selected
    require_current_periodic_mm_settings(decoded)
    assert periodic_geometry_policy(decoded) == selected.geometry_quality


@pytest.mark.parametrize('change', ('unknown-revision', 'missing-current-policy', 'unknown-field', 'null-policy'))
def test_retained_union_does_not_relax_version_or_field_checks(change):
    value = json.loads(ORIGINAL)
    if change == 'unknown-revision':
        value['version'] = '9.0.0'
    elif change == 'missing-current-policy':
        value['version'] = '2.0.0'
    elif change == 'unknown-field':
        value['value']['invented'] = False
    else:
        value['value']['geometry_quality'] = None
    with pytest.raises(CanonicalizationError):
        decode_canonical_bytes(nested(encode(value)), Envelope, maximum_bytes=4096)


RUNNERS = (
    ('periodic_probe_operation', 'PeriodicProbeRunner', 4),
    ('periodic_control_operation', 'PeriodicControlRunner', 3),
    ('active_relaxation_operation', 'ActiveRelaxationRunner', 4),
    ('active_preparation_operation', 'ActivePreparationPrefixRunner', 4),
    ('preparation_response_operation', 'PreparationResponseRunner', 4),
    ('periodic_trajectory_operation', 'ReferenceTrajectoryRunner', 4),
    ('periodic_equilibrium_operation', 'ReferenceEquilibriumRunner', 4),
    ('gas_relaxation_operation', 'GasRelaxationRunner', 3),
)


@pytest.mark.parametrize('module_name,runner_name,arity', RUNNERS)
@pytest.mark.parametrize('kind', (OriginalPeriodicMMSettings, UnversionedGeometryPeriodicMMSettings))
@pytest.mark.parametrize('entry', ('preflight', 'execute_with_native_subwork'))
def test_every_native_owner_refuses_legacy_before_stock_or_contact(module_name, runner_name, arity, kind, entry, monkeypatch):
    owner = importlib.import_module('empirical_lawhood.domains.rubisco.rubisco_response.' + module_name)
    settings = kind('settings.exposed.legacy-mm', 'Ewald', Decimal(9), Decimal('0.000001'))
    prototype = SimpleNamespace(molecular=settings)
    selection = SimpleNamespace(molecular=settings, prototype=prototype)
    config = SimpleNamespace(selection=selection, prototype=prototype,
        original=SimpleNamespace(selection=selection, prototype=prototype), point=prototype)
    monkeypatch.setattr(owner, '_decode', lambda *args, **kwargs: (config,) + (None,)*(arity-1))
    monkeypatch.setattr(owner, 'authenticate_periodic_engine', lambda *args, **kwargs: pytest.fail('legacy settings reached stock inspection'))
    closed = []
    context = SimpleNamespace(input_ports=(SimpleNamespace(close=lambda: closed.append(True)),))
    runner = getattr(owner, runner_name)()
    with pytest.raises(ValueError, match='requires periodic MM settings revision 2.0.0'):
        if entry == 'preflight':
            runner.preflight(context)
        else:
            runner.execute_with_native_subwork(context, object())
    assert closed == ([] if entry == 'preflight' else [True])


def test_shared_native_coordinate_entry_refuses_before_diagnostics_or_engines():
    from empirical_lawhood.domains.rubisco.rubisco_response.periodic_probe_native import _execute_periodic_at_coordinates
    settings = decode_canonical_bytes(ORIGINAL, OriginalPeriodicMMSettings, maximum_bytes=4096)
    with pytest.raises(ValueError, match='requires periodic MM settings revision 2.0.0'):
        _execute_periodic_at_coordinates(representation=None, selection=None, settings=None,
            mm_settings=settings, cell=None, raw_topology=b'', raw_coordinates=b'', coordinates=None, root=None)
