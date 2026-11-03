# SPDX-License-Identifier: MPL-2.0
"""Actual registered publication dispatch over disclosed original-byte fixtures."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from empirical_lawhood.adapters.methods.matrix_factor_response import protected_statistical_bindings as statistics
from empirical_lawhood.adapters.methods.matrix_factor_response.protected_original_publications import ORIGINAL_PUBLICATION_REQUIREMENT
from empirical_lawhood.api.recursive_publications import authenticate_draft_publications
from empirical_lawhood.planning.recursive_authoring import RecursiveOperationSpec
from tests.test_matrix_e3_original_publications import case as case  # noqa: F401
from tests.test_matrix_e3_statistical_bindings import config, exposed_root, response_task


@pytest.mark.parametrize("with_originals", (True, False))
def test_registered_fit_publication_gate_replays_original_custody(case, with_originals):
    fit = config(case, "fit")
    if with_originals:
        fit = replace(fit, original_publications=case.originals)
    declaration = statistics.statistical_declarations(publication_requirement=ORIGINAL_PUBLICATION_REQUIREMENT,
        scientific_root_validator=exposed_root, outcome_task_id=response_task)[0]
    registration = declaration.registration()
    node_id = fit.record_id.removeprefix("config.")
    operation = RecursiveOperationSpec.from_config(node_id=node_id, selection=registration.selection,
        config_id=fit.record_id, config=fit, obligation_ids=("obligation.originals.complete",),
        resource_budget=statistics.BUDGET)
    # The publication dispatcher consumes the selected operation projection.
    # This object supplies no candidate, issue, execution or source qualification.
    draft = SimpleNamespace(operations=(operation,), selected_operation_ids=(node_id,))
    if with_originals:
        assert authenticate_draft_publications(draft=draft, registrations=(registration,),
            artifact_writer=case.plane) is None
    else:
        with pytest.raises(ValueError, match="global original-publication custody"):
            authenticate_draft_publications(draft=draft, registrations=(registration,), artifact_writer=case.plane)
