# SPDX-License-Identifier: MPL-2.0
"""Pure compact score projection; custody stays in the calling controller."""

from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_bindings as owner
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e3_e4_records as r
from empirical_lawhood.adapters.methods.matrix_scheduled_history import selected_e4_programme as p
from empirical_lawhood.kernel.decoded_record_store import decoded_record_scope
from empirical_lawhood.kernel.decoding import record_validation_scope

from .matrix_selected_e3_e4_read import _decode_record_bytes, _record_bytes
from .matrix_read_indexes import product_record_index


def _project_score(value):
    payload, protocol, panels, root_id = value
    # Validation memoization belongs to one case, including in a reused
    # process. Full diagnostic records never return to the controller.
    with decoded_record_scope(), record_validation_scope():
        score = _decode_record_bytes(payload, r.ScheduledResponseScore)
        return None if score is None else p.SelectedE4ScoreProjection.from_record(
            score, protocol, panels, record_id='score-projection.' + root_id)


def original_score_projections(*, writer, products, programme, bank, original_input_access=None, product_lookup=None):
    """Return every case in its original order, including missing scores."""
    index = bank.source_index()
    if product_lookup is None:
        product_lookup = product_record_index(products)

    def inputs():
        for case in programme.cases:
            source = bank.source(case.root_id, index=index)
            protocol, panels = bank.response_selection.validate_source(source)
            payload = _record_bytes(writer, products, owner.local_node(case.root_id, 'response-score'),
                r.ScheduledResponseScore, original_input_access=original_input_access, product_lookup=product_lookup)
            yield payload, protocol, panels, case.root_id

    pool = getattr(getattr(writer, '_read_verification', None), 'canonical_pool', None)
    values = tuple(map(_project_score, inputs())) if pool is None else pool.project_ordered(_project_score, inputs())
    if original_input_access is not None:
        original_input_access.require_current()
    return values
