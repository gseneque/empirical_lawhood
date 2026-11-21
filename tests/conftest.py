# SPDX-License-Identifier: MPL-2.0
"""Portable tests and explicit, mandatory integration profiles.

The numerical worker setup is adapted from the source project's test harness.
Synthetic fixtures exercise software contracts and confer no research authority.
"""

from __future__ import annotations

import importlib.metadata
import os

import pytest

pytest_plugins = ("scripts.test_purposes",)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Set native worker limits before collecting numerical test modules."""

    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "1"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--fail-on-skip",
        action="store_true",
        help="Require every selected integration check; missing inputs/dependencies fail the job.",
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    for marker in item.iter_markers("native"):
        for distribution in marker.args:
            try:
                importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                pytest.skip(f"optional native distribution {distribution!r} is not installed")


@pytest.fixture(scope="session")
def rubisco_molprobity_prefix():
    from pathlib import Path
    from empirical_lawhood.adapters.rubisco.rubisco_response.molprobity_runtime import verify_runtime

    selected = os.environ.get("EL_MOLPROBITY_TEST_PREFIX")
    receipt = os.environ.get("EL_MOLPROBITY_TEST_RECEIPT_SHA256")
    if not selected or not receipt:
        pytest.skip("Select the CCTBX installation and the digest from its original installation return")
    prefix = Path(selected)
    verify_runtime(prefix, receipt_sha256=receipt)
    try:
        yield prefix
    finally:
        verify_runtime(prefix, receipt_sha256=receipt)


class _RequiredChecks:
    @staticmethod
    def _require_result(report) -> None:
        if report.skipped:
            reason = str(report.longrepr)
            report.outcome = "failed"
            report.longrepr = f"Required release-profile check skipped: {reason}"

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        self._require_result(outcome.get_result())

    @pytest.hookimpl(hookwrapper=True)
    def pytest_make_collect_report(self, collector):
        outcome = yield
        self._require_result(outcome.get_result())


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--fail-on-skip"):
        config.pluginmanager.register(_RequiredChecks(), "required-release-checks")
