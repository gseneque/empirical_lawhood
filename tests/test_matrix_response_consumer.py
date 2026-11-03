# SPDX-License-Identifier: MPL-2.0
"""Finite-grid arithmetic over disclosed complete-roster inputs; no qualification."""
from dataclasses import replace
from decimal import Decimal as D, localcontext
from types import SimpleNamespace
import pytest
from empirical_lawhood.adapters.methods.matrix_factor_response import response_consumer as consumer
from empirical_lawhood.adapters.methods.matrix_factor_response.records import PREDICTORS
from empirical_lawhood.adapters.methods.matrix_factor_response.response_frontier import MatrixResponseRootFrontier
from empirical_lawhood.adapters.methods.matrix_factor_response.response_population_statistics import HORIZONS, ROOT_IDS, population_statistics
from empirical_lawhood.kernel.provenance import ObjectIdentity
from tests.test_matrix_response_population_statistics import report, spec as spec  # noqa: F401


def obj(name, schema="empirical-lawhood/tests/exposed-consumer"):
    return ObjectIdentity(name, schema, "1.0.0", "a" * 64)


@pytest.fixture(scope="module")
def statistics(spec):
    initial = report(spec)
    rows = []
    for bound in initial.bounds:
        root = ROOT_IDS.index(bound.root_id)
        horizon = HORIZONS.index(bound.horizon_step)
        values = None
        if bound.predictor == "FACTOR" and root == 0:
            values = (D(".009"), D(".01"), D(".0100001"))
        elif bound.predictor == "FULL_COUPLED" and root == 0:
            values = (D(".011"),) * 3
        elif bound.predictor == "FACTOR" and root == 3:
            values = (D(".001"), D(".002"), D(".003"))
        if values is not None:
            bound = replace(bound, disposition="CROSSCHECKED_FINITE", bound_kind="FINITE_POINT",
                lower_loss=values[horizon], upper_loss=values[horizon],
                frontier=obj("frontier." + bound.root_id, MatrixResponseRootFrontier.SCHEMA))
        elif bound.predictor == "FACTOR" and root == 1:
            bound = replace(bound, disposition="MEASUREMENT_UNRESOLVED",
                lower_loss=(D(0), D(".009"), D(".012"))[horizon],
                upper_loss=(D(".02"), D(".011"), None)[horizon])
        elif bound.predictor == "FACTOR" and root == 4:
            bound = replace(bound, disposition="REFUSED", bound_kind="KNOWN_NONUSE_INFINITY",
                lower_loss=None, upper_loss=None)
        elif bound.predictor == "FACTOR" and root == 6:
            bound = replace(bound, disposition="UNKNOWN_CONTACT")
        rows.append(bound)
    return population_statistics(spec, (tuple(rows),), report_id="software.consumer.statistics")


@pytest.fixture(scope="module")
def cells(statistics):
    rows = []
    for bound in statistics.bounds:
        classification, definite, possible = consumer.response_adequacy_values(
            bound.bound_kind, bound.lower_loss, bound.upper_loss, D(".01"))
        rows.append(SimpleNamespace(root_id=bound.root_id, predictor=bound.predictor, horizon_step=bound.horizon_step,
            classification=classification, definitely_adequate=definite, possibly_adequate=possible,
            source_disposition=bound.disposition))
    return tuple(rows)


def test_complete_original_roster_retains_nonuse_unknown_and_inclusive_accuracy(cells):
    assert len(cells) == 256 * 5 * 3
    assert {(row.root_id, row.predictor, row.horizon_step) for row in cells} == {
        (root, predictor, horizon) for root in ROOT_IDS for predictor in PREDICTORS for horizon in HORIZONS}
    rows = [row for row in cells if row.root_id == ROOT_IDS[0] and row.predictor == "FACTOR"]
    assert [row.classification for row in rows] == ["FINITE_ADEQUATE", "FINITE_ADEQUATE", "FINITE_INADEQUATE"]
    unresolved = [row for row in cells if row.root_id == ROOT_IDS[1] and row.predictor == "FACTOR"]
    assert [row.classification for row in unresolved] == ["UNRESOLVED", "UNRESOLVED", "UNRESOLVED_INADEQUATE"]
    assert not unresolved[-1].possibly_adequate
    assert {row.classification for row in cells if row.root_id == ROOT_IDS[4] and row.predictor == "FACTOR"} == {"KNOWN_NONUSE"}


def test_first_failure_interval_censoring_and_unknown_remain_distinct(cells):
    def lifetime(index):
        return consumer.response_lifetime_values(tuple(row for row in cells
            if row.root_id == ROOT_IDS[index] and row.predictor == "FACTOR"))
    assert lifetime(0)[:5] == (64, 128, 128, None, "FIRST_FAILURE_ON_LATTICE")
    assert lifetime(1)[:5] == (None, 16, 128, None, "INTERVAL_CENSORED_FAILURE")
    assert lifetime(3)[:5] == (128, None, None, None, "RIGHT_CENSORED_AT_LAST_HORIZON")
    assert lifetime(4)[3:5] == (16, "KNOWN_NONUSE")
    assert lifetime(5)[4] == "UNAVAILABLE"
    assert lifetime(6)[4] == "UNKNOWN_CONTACT"


def test_accuracy_classification_keeps_exact_fraction_boundary_at_low_decimal_precision():
    with localcontext() as context:
        context.prec = 2
        assert consumer.response_adequacy_values("FINITE_POINT", D(".01"), D(".01"), D(".01")) == ("FINITE_ADEQUATE", True, True)
        assert consumer.response_adequacy_values("FINITE_POINT", D(".0100000001"), D(".0100000001"), D(".01")) == ("FINITE_INADEQUATE", False, False)
        assert consumer.response_adequacy_values("UNRESOLVED_INTERVAL", D(".009"), None, D(".01")) == ("UNRESOLVED", False, True)
        assert consumer.response_adequacy_values("KNOWN_NONUSE_INFINITY", None, None, D(".01")) == ("KNOWN_NONUSE", False, False)
