# SPDX-License-Identifier: MPL-2.0
"""Orthogonal verification-purpose classification; no fixtures or native effects."""

from __future__ import annotations

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "conformance: software control; no independent numerical-oracle claim")
    config.addinivalue_line("markers", "numerical(oracle): correctness against the named independent mathematical reference; no scientific qualification")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep verification purpose independent of cost and native-input profiles.

    Numerical classification is explicit at the test, with its reference named.
    Other checks make the conservative software-conformance claim. This neither
    upgrades an assertion into an independent oracle nor grants qualification.
    """
    purposes = {}
    for item in items:
        numerical = tuple(item.iter_markers("numerical"))
        if numerical:
            if (len(numerical) != 1 or numerical[0].args
                    or set(numerical[0].kwargs) != {"oracle"}
                    or not isinstance(numerical[0].kwargs["oracle"], str)
                    or not numerical[0].kwargs["oracle"].strip()
                    or item.get_closest_marker("conformance") is not None):
                raise pytest.UsageError(
                    f"{item.nodeid}: numerical requires one nonempty oracle= reference "
                    "and cannot also be classified as conformance")
            purposes[item.nodeid] = {"purpose": "numerical", "oracle": numerical[0].kwargs["oracle"]}
        else:
            item.add_marker(pytest.mark.conformance)
            purposes[item.nodeid] = {"purpose": "conformance", "oracle": None}
    config._el_test_purposes = purposes
