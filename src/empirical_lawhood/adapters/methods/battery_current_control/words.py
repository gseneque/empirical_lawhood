# SPDX-License-Identifier: MPL-2.0
"""The selected 900-second constant current word, not delivery evidence."""

from decimal import Decimal
from empirical_lawhood.adapters.methods.battery_thermal_service.contracts import BatteryThermalConfig
from empirical_lawhood.kernel.action_contracts import ActionChannelBinding, ActionDeliveryStage, ActionOccurrence, ActionOccurrenceGroup, ActionOccurrenceOrder, ActionStageEvent, ActionStageQuantityBinding, OccurrenceActionWord, ActionWordMode, ActionWordSupportStatus
from empirical_lawhood.kernel.references import ExecutableReference
from empirical_lawhood.kernel.time import ClockCoordinate, ClockTransport, ClockTransportAvailability, ClockTransportKind, ClockTransportMonotonicity, CoordinateOrigin


def coordinate(t: Decimal) -> ClockCoordinate:
    return ClockCoordinate("battery-service-clock", t, "s", "battery-service-time", CoordinateOrigin.EPISODE_RELATIVE)


def current_word(config: BatteryThermalConfig, evaluator: ExecutableReference) -> OccurrenceActionWord:
    stem = f"{config.unit_id}.{config.view}.{config.word}"
    stages = tuple(ActionStageQuantityBinding(stage, f"battery-current-{stage.value.lower()}", "battery-service-clock", "s", "battery-service-time", CoordinateOrigin.EPISODE_RELATIVE) for stage in ActionDeliveryStage)
    channel = ActionChannelBinding(f"{stem}.channel", "battery-current-in", "battery-current", stages, "A", "pybamm-terminal-current", "positive-discharge-negative-charge", f"{stem}.support", f"{stem}.delivery")

    def event(stage):
        return ActionStageEvent(stage, f"battery-current-{stage.value.lower()}", config.current_a, "A", "pybamm-terminal-current", "positive-discharge-negative-charge", coordinate(Decimal(0)))

    def transport(suffix):
        return ClockTransport(f"{stem}.{suffix}", "battery-service-clock", "battery-service-clock", "s", "s", "battery-service-time", "battery-service-time", CoordinateOrigin.EPISODE_RELATIVE, CoordinateOrigin.EPISODE_RELATIVE, ClockTransportKind.IDENTITY, ClockTransportAvailability.AVAILABLE, Decimal(1), Decimal(0), Decimal(0), Decimal(0), Decimal(900), ClockTransportMonotonicity.STRICTLY_INCREASING, evaluator, ())

    occurrence = ActionOccurrence(f"{stem}.occurrence", channel, *(event(stage) for stage in ActionDeliveryStage), transport("requested-accepted"), transport("accepted-applied"), transport("applied-realized"), Decimal(900), "s")
    return OccurrenceActionWord(stem, ActionWordMode.SEQUENTIAL, (occurrence,), (ActionOccurrenceGroup(f"{stem}.group", (ActionOccurrenceOrder(occurrence.occurrence_id, transport("order")),)),), "battery-service-clock", "s", "battery-service-time", CoordinateOrigin.EPISODE_RELATIVE, config.source.denominator_id, config.unit_id, "battery-native-current", "battery-service-900s", (f"{stem}.identity-prefix", f"{stem}.prefix"), ActionWordSupportStatus.SUPPORTED, ())
