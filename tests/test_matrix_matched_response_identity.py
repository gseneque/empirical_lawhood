# SPDX-License-Identifier: MPL-2.0
"""Matched CAL/CONF response metadata over disclosed software records.

These tests use actual configured record types and both response metadata
guards. Array and causal metadata are exposed fixtures, not native
observations, source qualification or scientific evidence.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_methods as science
from empirical_lawhood.adapters.methods.matrix_factor_response import configured_protected_response_records as records
from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import ConfiguredProtectedE3PrefixHistory
from empirical_lawhood.adapters.methods.matrix_factor_response.origin_mechanics import MatrixIO48Construction, MatrixOriginResponseModel, model_predictors
from empirical_lawhood.adapters.methods.matrix_factor_response.response_scoring import DENSE_RESPONSE_HORIZONS
from empirical_lawhood.adapters.methods.matrix_scheduled_history.forecast import ScheduledPublicSource
from empirical_lawhood.adapters.methods.matrix_scheduled_history import response_records
from empirical_lawhood.kernel.matrix_inputs import MatrixArrayMember
from tests.test_matrix_configured_unknown_response import (
    case as metadata_case, configured_prefix_case, original_case as prefix_original_case,  # noqa: F401
)
from tests.test_matrix_matched_protected_e3 import original_case, matched_e3_products  # noqa: F401
from tests.test_matrix_e3_prefix_records import literal_history
from tests.test_matrix_e3_response_records import publication, qualification
from tests.test_matrix_configured_protected_e3 import causal as feature_source


@pytest.fixture(scope='module')
def legacy_case(prefix_original_case):  # noqa: F811
    # The imported configured-prefix fixture expects its own small original
    # fixture, whereas the fitted matched products use the selected-64 case.
    from tests.test_matrix_e3_protected_prefix_workers import case
    return case.__wrapped__(prefix_original_case)


def operands(original, fitted, template, role):
    unit = fitted.allocation.unit_ids(role)[0]
    source, _ = feature_source(original, unit, source_index=fitted.index)
    manifest = replace(original.manifest, provenances=(source.provenance,))
    public = ScheduledPublicSource.from_source(source)
    old = template.operands.records
    protocol = replace(old['protocol'], protocol_id='protocol.matched.identity.' + unit,
        public_source=public, templates=replace(old['protocol'].templates, source=public.source,
            producers=(public.source,)), horizon_steps=DENSE_RESPONSE_HORIZONS,
        mechanical_model=MatrixOriginResponseModel('model.matched.identity', response_records.physical_forecast_implementation(),
            MatrixIO48Construction('io48.matched.identity')))
    panels = tuple(replace(panel, panel_id='panel.' + panel.role.lower() + '.' + unit,
        independent_group_id=unit, streams=source.root.streams if panel.role == 'COMMON_NOISE_PANEL' else panel.streams)
        for panel in old['panels'])
    panels = tuple(sorted(panels, key=lambda row: row.panel_id))
    selection = replace(old['selection'], record_id='selection.matched.identity.' + unit,
        specification=fitted.specification.identity, source_manifest=science.identity(manifest),
        root_protocols=((source.root_id, records._object(protocol)),),
        group_panels=((unit, tuple(records._object(panel) for panel in panels)),))
    stub = SimpleNamespace(plane=original.plane)
    published = publication(stub, selection, 'matched.identity.' + unit)
    numerical = records.project_protected_e3_response_numerics(protocol, provenance=selection,
        publication=published, qualification=qualification(selection, published, 'matched.identity.' + unit))
    prefix_config = replace(old['prefix-config'],
        record_id='config.' + records.NAMESPACE + '.' + source.root_id + '.prefix',
        specification=fitted.specification.identity, source_manifest=science.identity(manifest), source=source.reference)
    from empirical_lawhood.adapters.methods.matrix_factor_response.configured_protected_prefix_records import protected_prefix_native_contract
    _, configuration, task, operation, closure, _ = protected_prefix_native_contract(
        prefix_config, manifest, specification=fitted.specification)
    _, arrays, checkpoint, native = literal_history(original.plane, source,
        configuration=configuration, task=task, operation=operation, sources=closure)
    history = ConfiguredProtectedE3PrefixHistory('history.matched.identity.' + unit,
        public.source, configuration, arrays, checkpoint, native)
    causal = replace(old['causal'], record_id='causal.matched.identity.' + unit,
        source=public.source, history=science.identity(history), root=source.root.root,
        policy=records._object(source.policy), disposition='UNEVALUABLE', frame_sha256=None,
        reason='PREFIX_NUMERICAL_CONTROLS_NOT_SATISFIED',
        arrays=replace(old['causal'].arrays, source=public.source,
            members=tuple(replace(member, finite_required=False) if member.name == 'frame' else member
                for member in old['causal'].arrays.members),
            producers=tuple(sorted((public.source, science.identity(history), old['causal'].witness,
                old['causal'].frame_assessment), key=lambda row: row.object_id))))
    physical_config = records.ConfiguredProtectedE3PhysicalForecastConfig(
        'config.' + records.NAMESPACE + '.' + source.root_id + '.physical-forecast',
        source.root_id, fitted.specification.identity, records._object(protocol), science.identity(numerical))
    producers = (public.source, science.identity(causal), records._object(protocol), science.identity(numerical))
    physical = replace(old['physical'], forecast_id='physical.matched.identity.' + unit,
        configuration=records._object(physical_config), source=public.source, causal_prefix=science.identity(causal),
        protocol=records._object(protocol), numerical_profile=science.identity(numerical),
        disposition='UNEVALUABLE', frame_sha256=None,
        mechanical_model=records._object(protocol.mechanical_model), arrays=replace(old['physical'].arrays,
            source=public.source, producers=tuple(sorted(producers, key=lambda row: row.object_id)),
            members=tuple(MatrixArrayMember(name, dtype, shape, 'c' * 64, finite_required=False)
                for name, (dtype, shape) in sorted(records._physical_members(protocol, 'UNEVALUABLE').items()))),
        dispositions=tuple((view, predictor, 'UNRESOLVED', 'prefix-unevaluable') for view in ('PRIMARY', 'FINE')
            for predictor in model_predictors(protocol.mechanical_model)))
    calibrated = role == 'evaluation'
    frozen = fitted.sealed if calibrated else fitted.frozen
    calibration = fitted.calibration if calibrated else None
    error = fitted.forecast(unit, role, frozen, calibration)
    feature = replace(error.feature, prefix=science.identity(causal), physical_forecast=records._object(physical),
        frame_sha256=causal.frame_sha256, disposition='UNAVAILABLE', values=(), fine_response_defect=None,
        evidence=tuple(sorted((science.identity(causal), causal.numerical,
            causal.witness, causal.frame_assessment, records._object(physical)), key=lambda row: row.object_id)))
    error = science.forecast_protected_e3(fitted.specification, fitted.allocation, fitted.models, frozen,
        feature, role=role, record_id=error.record_id, calibration=calibration)
    config = records.ConfiguredProtectedE3ResponseConfig(
        'config.' + records.NAMESPACE + '.' + source.root_id + '.responses', 'responses',
        fitted.specification.identity, science.identity(manifest), source.reference,
        science.identity(selection), records._object(protocol), science.identity(numerical))
    return config, dict(specification=fitted.specification, allocation=fitted.allocation, models=fitted.models,
        frozen=frozen, calibration=calibration, model_freeze=fitted.frozen if calibrated else None,
        causal=causal, physical=physical, protocol=protocol, error=error, descriptor=source.reference), dict(
        source=source, manifest=manifest, specification=fitted.specification, selection=selection,
        protocol=protocol, numerical_profile=numerical, panels=panels, history=history, causal=causal,
        physical=physical, error=error)


@pytest.mark.parametrize('role', ('calibration', 'evaluation'))
def test_matched_response_guards_bind_actual_forecast_id(original_case, matched_e3_products, metadata_case, role, tmp_path):  # noqa: F811
    from tests.test_matrix_factor_confirmation_eligibility import _matrix_plane
    original = SimpleNamespace(**{**vars(original_case), 'plane': _matrix_plane(tmp_path / 'plane')})
    config, fitted, native = operands(original, matched_e3_products, metadata_case, role)
    physical = fitted['physical']
    assert not hasattr(physical, 'record_id')
    records._error_forecast(**fitted)
    contract = records.protected_e3_response_native_contract(config, **native)
    assert records._object(physical) in contract[4]
    substituted = replace(physical, forecast_id=physical.forecast_id + '.foreign')
    with pytest.raises(ValueError, match='actual source/role/current feature/fitted freeze'):
        records._error_forecast(**{**fitted, 'physical': substituted})
    with pytest.raises(ValueError, match='actual current response operands'):
        records.protected_e3_response_native_contract(config, **{**native, 'physical': substituted})
