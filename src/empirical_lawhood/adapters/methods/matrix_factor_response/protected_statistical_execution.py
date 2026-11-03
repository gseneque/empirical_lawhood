# SPDX-License-Identifier: MPL-2.0
"""Common statistical orchestration; each facade binds its exact record family."""
from dataclasses import dataclass
from collections.abc import Callable
from empirical_lawhood.kernel.serialization import validate_stable_id
from empirical_lawhood.runtime.artifacts import ReceiptCheck
from empirical_lawhood.runtime.execution import RunnerResult, TaskOutputPayload


@dataclass(frozen=True, slots=True)
class StatisticalExecutionContract:
    decode: Callable
    fit: Callable
    freeze: Callable
    forecast: Callable
    calibrate: Callable
    assess: Callable
    identity: Callable
    statistical_task_id: Callable
    feature_task_id: Callable
    current_dependency: Callable


def execute_statistical(self, context, contract):
    try:
        config, specification, allocation, records, contracts = contract.decode(context, self.phase, self.manifest)
        one = lambda name: records[name][0][0]
        def task(operation, mode="", root=None):
            return contract.statistical_task_id(config.specification, config.allocation, operation, mode=mode, root=root)
        for name, rows in records.items():
            if name in ("specification", "allocation") or self.phase == "fit":
                continue
            for record, port, edge in rows:
                output = "product"
                if name in ("models", "prefit-join"):
                    producer, output = task("fit"), "prefit-join" if name == "prefit-join" else "product"
                elif name == "calibration":
                    producer = task("calibrate")
                elif name == "model-freeze" or name == "frozen" and (self.phase == "calibrate" or config.mode == "calibration"):
                    producer = task("freeze", "model")
                elif name == "frozen":
                    producer = task("freeze", "calibration")
                elif name == "feature":
                    if record.public_source.root != config.root:
                        raise ValueError("protected E3 forecast changes its actual seedless root")
                    producer = contract.feature_task_id(config.root.root_id)
                elif name == "forecasts":
                    producer = task("forecast", "calibration" if self.phase == "calibrate" else "evaluation", record.feature.public_source.root)
                else:
                    producer = self.outcome_task_id(record.feature.public_source.root.root_id)
                    validate_stable_id(producer)
                    output = "outcome"
                contract.current_dependency(context, edge, port, producer, output)
        result_id = "result." + context.task_id
        joined = None
        if self.phase == "fit":
            product, joined = contract.fit(config, specification, allocation, records, contracts, result_id, context=context)
        elif self.phase == "model-freeze":
            if one("models").reservation_join != one("prefit-join").identity:
                raise ValueError("protected E3 model freeze loses its actual current fit/prefit producer coupling")
            product = contract.freeze(specification, allocation, one("models"), record_id=result_id)
        elif self.phase == "calibration-freeze":
            product = contract.freeze(specification, allocation, one("models"), record_id=result_id,
                model_freeze=one("model-freeze"), calibration=one("calibration"))
        elif self.phase == "forecast":
            if config.mode == "evaluation" and (one("frozen").model_freeze != contract.identity(one("model-freeze"))
                    or one("calibration").model_freeze != contract.identity(one("model-freeze"))
                    or one("model-freeze").calibration is not None):
                raise ValueError("protected E3 CONF forecast changes its actual original model freeze")
            product = contract.forecast(specification, allocation, one("models"), one("frozen"), one("feature"),
                role=config.mode, record_id=result_id, calibration=one("calibration") if config.mode == "evaluation" else None)
        else:
            forecasts = tuple(row[0] for row in records["forecasts"])
            outcomes = tuple(row[0] for row in records["outcomes"])
            product = (contract.calibrate(specification, allocation, one("models"), one("frozen"), forecasts, outcomes,
                record_id=result_id) if self.phase == "calibrate" else contract.assess(specification, allocation,
                    one("frozen"), forecasts, outcomes, record_id=result_id))
        payloads = {"product": product.canonical_bytes()}
        if joined is not None:
            payloads["prefit-join"] = joined.canonical_bytes()
        return RunnerResult(tuple(TaskOutputPayload(port.output_id, payloads[port.output_id.rsplit(".", 1)[-1]])
            for port in context.output_ports), (ReceiptCheck("protected-e3-statistical-current-receipts-and-complete-original-join", True, ()),))
    finally:
        for port in context.input_ports:
            port.close()
