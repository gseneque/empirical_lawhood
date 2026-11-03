# SPDX-License-Identifier: MPL-2.0
"""Independent selection-integrity adversaries over exposed canonical inputs."""

from dataclasses import replace

import pytest

from empirical_lawhood.kernel.provenance import ObjectIdentity
from empirical_lawhood.adapters.physical.virtual_cell import runtime
from empirical_lawhood.adapters.physical.virtual_cell.config import SELECTION_CAPABILITY_KEY
from empirical_lawhood.adapters.physical.virtual_cell.custody_transport_v2 import CanonicalEvidenceV2
from empirical_lawhood.adapters.physical.virtual_cell.records_v2 import ModelDevelopmentRecordV2, ModelSelectionRecordV2
from empirical_lawhood.adapters.physical.virtual_cell import task_runner_v2 as tasks
from tests.test_virtual_cell_custody_v2 import fixture
from tests.test_virtual_cell_task_runner_v2 import _context, _runner


@pytest.mark.parametrize("damage", ("winner", "selection-rule"))
def test_actual_selection_refuses_identity_consistent_unjustified_tournament(damage, monkeypatch):
    """Valid hashes cannot turn an arbitrary eligible candidate into the winner.

    Every fixture candidate has the same validation score, standard error and
    parameter count. The declared capacity/ID tie-break therefore selects
    baseline-no-change. No physical source, receiver or authority is represented.
    """
    case = fixture()
    tournament = case.records[case.development.tournament]
    assert tournament.selected_candidate_id == "baseline-no-change"
    assert len({(row.official_score, row.official_score_standard_error, row.parameter_count)
        for row in tournament.entries}) == 1
    if damage == "winner":
        altered = replace(tournament, selected_candidate_id="baseline-weighted-common-response")
    else:
        altered = replace(tournament, selection_rule="caller-changed-selection-rule")
    reference = ObjectIdentity.from_record(altered.tournament_id, altered)
    development = replace(case.development, tournament=reference)
    records = [(reference if key == case.development.tournament else key,
        altered if key == case.development.tournament else value)
        for key, value in case.records.items()
        if type(value) not in (ModelDevelopmentRecordV2, ModelSelectionRecordV2)]
    custody = CanonicalEvidenceV2.from_records(records)
    panel = next(value for value in case.records.values() if type(value) is runtime.FalsifierPanel)
    runner, manifest = _runner(case, SELECTION_CAPABILITY_KEY)
    context = _context(case, manifest,
        (("development", development), ("panel", panel), ("prior.custody", custody)),
        (("model-selection", ModelSelectionRecordV2),))
    # Only optional receiver availability is doubled. Real canonical ports,
    # corrected custody views and the inherited selection stage all execute.
    monkeypatch.setattr(tasks, "require_receiver_ready_v2", lambda **kwargs: None)
    with pytest.raises(ValueError, match="tournament|selection|winner|rule"):
        runner.execute(context)
