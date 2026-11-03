# SPDX-License-Identifier: MPL-2.0
"""Selected receiver admission, before held physical source or scratch is opened.

This observes versions, pinned scorer source/bytecode and entry points. It
establishes no biological warrant, issue, execution or reveal permission.
"""

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version

from .config_v2 import VirtualCellPipelineSelectionV2
from .contracts import VirtualCellContractError
from .scorer_source_v2 import (
    authenticate_installed_scorer_source_v2,
    require_selected_scorer_contract_v2,
)


# Exact selected optional group in the existing uv.lock; no environment sync.
LOCKED_RECEIVER_DISTRIBUTIONS_V2 = (
    ("anndata", "0.11.4"),
    ("cell-eval", "0.6.6"),
    ("pdex", "0.1.26"),
    ("polars", "1.44.2"),
)


@dataclass(frozen=True, slots=True)
class ReceiverDependencyObservation:
    distribution: str
    required_version: str
    installed_version: str | None

    @property
    def ready(self):
        return self.installed_version == self.required_version


@dataclass(frozen=True, slots=True)
class ReceiverReadinessV2:
    dependencies: tuple[ReceiverDependencyObservation, ...]
    entry_point_errors: tuple[str, ...]

    @property
    def ready(self):
        return (
            all(value.ready for value in self.dependencies)
            and not self.entry_point_errors
        )

    @property
    def reasons(self):
        dependencies = tuple(
            f"{value.distribution}: {value.installed_version or 'MISSING'}; requires {value.required_version}"
            for value in self.dependencies
            if not value.ready
        )
        return (*dependencies, *self.entry_point_errors)


class ReceiverEnvironmentUnavailable(VirtualCellContractError):
    reason_code = "VIRTUAL_CELL_V2_RECEIVER_ENVIRONMENT_UNAVAILABLE"


def observe_receiver_readiness_v2(*, selection, original_config):
    if type(selection) is not VirtualCellPipelineSelectionV2:
        raise TypeError("receiver readiness requires its explicit v2 selection")
    selection.__post_init__()
    selection.validate_original(original_config)
    for contract in (
        original_config.metric_contract,
        original_config.model_selection.validation_metric_contract,
    ):
        require_selected_scorer_contract_v2(contract)
    dependencies = []
    errors = []
    for name, expected in LOCKED_RECEIVER_DISTRIBUTIONS_V2:
        try:
            observed = version(name)
        except PackageNotFoundError:
            observed = None
        except Exception as error:  # noqa: BLE001 - report every software prerequisite
            observed = None
            errors.append(f"{name} metadata: {type(error).__name__}")
        dependencies.append(ReceiverDependencyObservation(name, expected, observed))
    if not all(value.ready for value in dependencies):
        return ReceiverReadinessV2(tuple(dependencies), tuple(errors))

    try:
        authenticate_installed_scorer_source_v2(original_config.metric_contract)
    except Exception as error:  # noqa: BLE001 - software refusal precedes imports or source/scratch
        errors.append(f"official scorer source: {type(error).__name__}")
        return ReceiverReadinessV2(tuple(dependencies), tuple(errors))

    # Reuse the original version owner after the complete availability census.
    from .analysis import verify_official_evaluator_versions

    try:
        for contract in (
            original_config.metric_contract,
            original_config.model_selection.validation_metric_contract,
        ):
            verify_official_evaluator_versions(contract)
    except Exception as error:  # noqa: BLE001 - no source/scratch has been touched
        errors.append(f"official evaluator versions: {type(error).__name__}")
    for module_name, attribute in (
        ("anndata", "AnnData"),
        ("anndata._io.specs", "read_elem"),
        ("polars", "DataFrame"),
        ("cell_eval", "MetricsEvaluator"),
    ):
        try:
            if not callable(getattr(import_module(module_name), attribute, None)):
                raise TypeError("selected receiver entry point is unavailable")
        except Exception as error:  # noqa: BLE001 - retain the complete software census
            errors.append(f"{module_name}.{attribute}: {type(error).__name__}")
    return ReceiverReadinessV2(tuple(dependencies), tuple(errors))


def require_receiver_ready_v2(*, selection, original_config):
    observed = observe_receiver_readiness_v2(
        selection=selection, original_config=original_config
    )
    if not observed.ready:
        raise ReceiverEnvironmentUnavailable(
            "ENVIRONMENT: virtual-cell v2 receiver unavailable; "
            + "; ".join(observed.reasons)
        )
    return observed
