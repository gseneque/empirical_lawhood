# SPDX-License-Identifier: MPL-2.0
"""Exact E4 prior prediction and additive current acquisition plan joins."""

from . import programme_acquisition_bindings as acquisition
from .compact_records import NAMESPACE as COMPACT_NAMESPACE
from .revision_forecast_bindings import ScheduledRevisionForecastConfig, operation_manifests as forecast_manifests
from .revision_future_bindings import (
    BLIND, PROSPECTIVE, ROLES, ScheduledRevisionFutureScope, ScheduledRevisionSealCustody,
    _EXTRA_PORTS, forecast_task_id, operation_registrations,
)


def validate_revision_acquisition_variant(programme, wave, plan, scope, *, registrations=None):
    """An explicit closed variant, retaining original task/config/native subjects."""
    if type(scope) is not ScheduledRevisionFutureScope or scope.programme != programme:
        raise ValueError("revision acquisition variant substitutes its actual frozen scientific scope")
    scope.__post_init__()
    registrations = {row.selection.capability_key: row for row in (operation_registrations() if registrations is None else registrations)}
    expected = {COMPACT_NAMESPACE + "." + case + "." + role for case in wave.root_ids for role in ROLES}
    actual = tuple(task for task in plan.tasks if task.capability.capability_key in registrations)
    if {task.task_id for task in actual} != expected or len(actual) != len(expected):
        raise ValueError("revision acquisition variant omits an original future task or aliases its installed owner")
    scope_digest = scope.identity.object_fingerprint
    for task in actual:
        role = task.task_id.rsplit(".", 1)[-1]
        registration = registrations[task.capability.capability_key]
        if (task.capability.config.config_id != "config." + task.task_id
                or task.capability.config.config_schema != acquisition.compact.config_type(role).SCHEMA):
            raise ValueError("revision acquisition variant changes an original mathematical configuration identity")
        incoming = task.scientific_inputs
        for name, kind in _EXTRA_PORTS:
            matches = tuple(row for row in incoming if row.consumer_input_id == name)
            if (len(matches) != 1 or matches[0].producer_task_id is not None or matches[0].external_input_id is None
                    or (matches[0].payload_schema, matches[0].media_type, matches[0].outcome_access, matches[0].visibility_ceiling)
                        != (kind.SCHEMA, "application/json", BLIND, PROSPECTIVE)):
                raise ValueError("revision acquisition variant drops the actual earlier-wave prerequisite port census")
            specs = tuple(row for row in task.external_inputs if row.logical_artifact_id == matches[0].operational_logical_artifact_id)
            if len(specs) != 1 or specs[0].expected_content_sha256 is None:
                raise ValueError("revision acquisition variant leaves prior source bytes unpinned")
            if name == "revision-scope" and specs[0].expected_content_sha256 != scope_digest:
                raise ValueError("revision acquisition variant substitutes the selected shared frozen scope")
        for port in registration.input_ports:
            count = sum(port.matches(row.consumer_input_id) for row in incoming)
            if count < port.minimum_count or port.maximum_count is not None and count > port.maximum_count:
                raise ValueError("revision acquisition variant drops an original/native or added scientific input")
        if any(not any(port.matches(row.consumer_input_id) for port in registration.input_ports) for row in incoming):
            raise ValueError("revision acquisition variant adds an undeclared executable scientific input")


def prior_seal_scope_validator(*, parent_evidence, binding, package, execution_plan):
    """Validate original issued pure producer after the shared API replay."""
    scope, custody = parent_evidence
    if (type(scope) is not ScheduledRevisionFutureScope or type(custody) is not ScheduledRevisionSealCustody
            or binding != custody.prior_execution):
        raise PermissionError("revision seal replay substitutes its exact requested prior custody")
    custody.__post_init__()
    scope.__post_init__()
    seal = custody.forecast
    if seal != scope.forecast(seal.case_id, record_id=seal.record_id):
        raise PermissionError("prior revision producer changes the original frozen model/target/case prediction")
    wave = next((row for row in scope.programme.waves if seal.case_id in row.root_ids), None)
    expected = {forecast_task_id(case_id) for case_id in wave.root_ids}
    if {task.task_id for task in execution_plan.tasks} != expected:
        raise PermissionError("prior revision producer omits a complete assigned whole-group seal wave")
    selected, = forecast_manifests()
    scope_pin = scope.identity
    for task in execution_plan.tasks:
        if (task.capability.capability_key != selected.capability_key
                or task.capability.capability_version != selected.capability_version
                or task.capability_implementation_sha256 != selected.implementation_sha256
                or task.capability.config.config_schema != ScheduledRevisionForecastConfig.SCHEMA
                or task.capability.config.config_schema_sha256 != selected.config_schema_sha256):
            raise PermissionError("prior revision producer substitutes the actual installed pure forecast declaration")
        links = tuple(row for row in task.scientific_inputs if row.consumer_input_id == "revision-scope")
        if (len(task.scientific_inputs) != 1 or len(links) != 1 or links[0].producer_task_id is not None
                or links[0].external_input_id is None or links[0].payload_schema != scope.SCHEMA):
            raise PermissionError("prior revision predictor receives future data or loses the actual frozen source")
        inputs = tuple(row for row in task.external_inputs if row.logical_artifact_id == links[0].operational_logical_artifact_id)
        if (len(inputs) != 1 or inputs[0].expected_content_sha256 != scope_pin.object_fingerprint
                or inputs[0].expected_outcome_access is not BLIND or inputs[0].expected_visibility_ceiling is not PROSPECTIVE):
            raise PermissionError("prior revision predictor substitutes exact original frozen scientific scope bytes")
    producer, = (task for task in execution_plan.tasks if task.task_id == binding.task_id)
    expected_config = ScheduledRevisionForecastConfig("config." + binding.task_id, scope_pin,
        seal.case_id, seal.independent_group_id, seal.record_id)
    if (producer.capability.config.config_id != expected_config.config_id
            or producer.capability.config.content_sha256 != expected_config.fingerprint()
            or binding.record != seal.identity or binding.task_id != forecast_task_id(seal.case_id)):
        raise PermissionError("prior revision predictor substitutes the original producing configuration or exact seal")
