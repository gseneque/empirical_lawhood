# SPDX-License-Identifier: MPL-2.0
"""Battery finite admission uses the installed author/compiler/runtime route."""

from empirical_lawhood.adapters.control.controller_authoring import DeliveryControllerAuthor, DeliveryControllerAuthoringRequest
from empirical_lawhood.adapters.control.finite_bindings import finite_implementation_payloads
from empirical_lawhood.adapters.control.finite_campaign import finite_control_services
from empirical_lawhood.adapters.control.composition import ControllerStudyComposition
from empirical_lawhood.planning.controller_study import DeliveryControllerStudy, ImplementationRole
from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import BatteryThermalConfig
from empirical_lawhood.kernel.provenance import ObjectIdentity
from dataclasses import replace
from .contracts import BatteryCurrentControlConfiguration, current_recipe
from .delivery import BatteryCurrentReceiptDelivery


def implementation_payloads():
    configurations = tuple(
        BatteryCurrentControlConfiguration(f"battery-current-control.{role.value.lower()}.config", role)
        for role in ImplementationRole if role is not ImplementationRole.OUTCOME_EVALUATOR
    )
    return finite_implementation_payloads(
        tuple((config.config_id, config.role, config) for config in configurations),
        delivery_owner="BatteryCurrentReceiptDelivery",
        implementation_namespace="empirical-lawhood.battery-current-control.selected-v1",
    )


def author_battery_controller(request: DeliveryControllerAuthoringRequest, *, configuration: BatteryThermalConfig) -> DeliveryControllerStudy:
    """No admission or HOLD evidence is manufactured by this author seam."""
    if request.implementations != tuple(binding for binding, _ in implementation_payloads()) or request.prospective_evaluation is not None:
        raise ValueError("battery controller changes its installed admission-only owners")
    from .delivery import validate_current_word
    recipe = current_recipe(configuration)
    if request.instance_binding.frozen_recipe != ObjectIdentity.from_record(recipe.recipe_id, recipe):
        raise ValueError("battery controller changes the frozen source/model/config/preparation")
    for binding in request.action_bindings:
        matching = next((fibre for fibre in request.admission.corpus.plan.action_fibres if fibre.action_word == binding.action_word), None)
        if matching is None:
            raise ValueError("battery action has no exact independently evidenced admission fibre")
        # The exact source/config preparation is supplied as the frozen recipe,
        # not inferred from a requested action or a useful capacity response.
        word = binding.action_word
        is_hold = word.occurrences[0].requested.value == 0
        validate_current_word(word, replace(configuration, word="native-hold900" if is_hold else "standard-cc900"))
    # Full causal/corpus/instance checks belong to the existing author and sole
    # compiler. This domain seam cannot authorize missing HOLD evidence.
    return DeliveryControllerAuthor.author(request)


def battery_control_services(study: DeliveryControllerStudy, delivery: BatteryCurrentReceiptDelivery) -> ControllerStudyComposition:
    expected = tuple(binding for binding, _ in implementation_payloads())
    if study.implementations != expected or delivery.implementation_binding != next(binding for binding in expected if binding.role is ImplementationRole.DELIVERY):
        raise ValueError("battery controller substitutes its registered owner configuration")
    if study.instance_binding.frozen_recipe != ObjectIdentity.from_record(delivery.recipe.recipe_id, delivery.recipe):
        raise ValueError("battery controller changes the immutable source/model/preparation/view recipe")
    from .delivery import validate_current_word
    config = BatteryThermalConfig("battery-current-recipe.validation", "acquire", delivery.recipe.protocol_sha256, delivery.recipe.unit_id, delivery.recipe.initial_temperature_k, view=delivery.recipe.view, initial_soc=delivery.recipe.initial_soc, source=delivery.recipe.source)
    for binding in study.action_bindings:
        validate_current_word(binding.action_word, replace(config, word="native-hold900" if binding.action_word.occurrences[0].requested.value == 0 else "standard-cc900"))
    return finite_control_services(study, None, delivery)
