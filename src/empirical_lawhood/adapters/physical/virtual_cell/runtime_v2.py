# SPDX-License-Identifier: MPL-2.0
"""Selected admitted-array methods; no outcome access authority.

These methods consume caller-admitted arrays. They do not open physical sources,
derive a grant or install a programme. The actual nine-stage composition lives
in task_runner_v2 and performs software admission before held data or scratch.
"""

from dataclasses import dataclass

from .config_v2 import VirtualCellPipelineSelectionV2
from .contracts import (
    ProvenanceBoundVirtualCellPipelineConfig,
    VirtualCellContractError,
)
from .receiver_readiness_v2 import require_receiver_ready_v2


@dataclass(frozen=True, slots=True)
class VirtualCellSelectedMethodsV2:
    original_config: ProvenanceBoundVirtualCellPipelineConfig
    selection: VirtualCellPipelineSelectionV2

    def __post_init__(self):
        if type(self.selection) is not VirtualCellPipelineSelectionV2:
            raise TypeError("corrected methods require their explicit v2 selection")
        self.selection.__post_init__()
        self.selection.validate_original(self.original_config)

    def preflight(self):
        """Admit selected software without held physical source or scratch I/O."""
        self.__post_init__()
        return require_receiver_ready_v2(
            selection=self.selection, original_config=self.original_config
        )

    def write_prediction(
        self,
        *,
        path,
        roster,
        gene_ids,
        predicted_deltas,
        control_reservoir,
        control_reservoir_sha256,
    ):
        """Delegate raw actions to the selected donor, retaining original budgets."""
        self.preflight()
        from .dataset import ControlReservoirArrays
        from .prediction import PredictionRoster
        from .prediction_v2 import write_shared_template_shift_v2_prediction_h5ad

        if (
            type(roster) is not PredictionRoster
            or type(control_reservoir) is not ControlReservoirArrays
        ):
            raise TypeError(
                "corrected prediction requires its actual roster and control reservoir"
            )
        roster.__post_init__()
        control_reservoir.__post_init__()
        compiler = self.selection.compiler_contract
        if (
            roster.total_cell_limit != compiler.total_cell_limit
            or roster.control_cells != compiler.control_cells
            or roster.control_label
            != self.original_config.response_summary.comparator_label
            or any(
                value.allocated_cells < compiler.minimum_cells_per_target
                for value in roster.targets
            )
            or len(control_reservoir.row_ids) > compiler.control_reservoir_cells
        ):
            raise ValueError(
                "corrected prediction changes its selected row allocation or control budget"
            )
        if (
            control_reservoir.normalization
            != self.original_config.response_summary.normalization
            or control_reservoir.normalization_target_sum
            != float(self.original_config.response_summary.normalization_target_sum)
        ):
            raise ValueError(
                "corrected prediction changes the original control normalization"
            )
        return write_shared_template_shift_v2_prediction_h5ad(
            path=path,
            roster=roster,
            gene_ids=gene_ids,
            predicted_deltas=predicted_deltas,
            control_reservoir=control_reservoir,
            control_reservoir_sha256=control_reservoir_sha256,
            seed=compiler.compiler_seed,
            selection=self.selection.compiler,
        )

    def evaluate_validation(self, *, predicted, real, scratch_directory, num_threads):
        """Evaluate already-admitted development arrays with the original baseline."""
        self.preflight()
        from .evaluation import evaluate_official_2025_v2

        return evaluate_official_2025_v2(
            predicted=predicted,
            real=real,
            metric_contract=self.original_config.model_selection.validation_metric_contract,
            metric_gauge=self.selection.metric_gauge,
            scratch_directory=scratch_directory,
            num_threads=num_threads,
            control_label=self.original_config.response_summary.comparator_label,
            perturbation_column=self.original_config.response_summary.target_field,
        )

    def evaluate_final(self, **_kwargs):
        raise VirtualCellContractError(
            "SOFTWARE: corrected final evaluation requires an owning TaskRunner joining "
            "the exact sealed source, prediction freeze and original reveal permissions"
        )
