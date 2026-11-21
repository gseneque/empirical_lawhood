# SPDX-License-Identifier: MPL-2.0
"""Small selected-interpreter calculation after the existing ready/proceed gate."""

from empirical_lawhood.methods.isolated_native_starter.calculation import sum_of_squares

from decimal import Decimal
from hashlib import sha256
import os
import resource
import sys
import time

from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.execution.native_subwork import NativeSubworkRoster, invoke_native_subwork

from empirical_lawhood.adapters.isolated_native_starter.records import MAX_RESULT_BYTES, SquareNativeResult
from empirical_lawhood.adapters.isolated_native_starter.work import CALCULATION, decode_invocation


def preflight_selected_child(*, invocation, expected_parent, prepared_contract):
    """Observe the actual dependency; no arithmetic, progress or native contact."""
    config, _, _ = decode_invocation(invocation, expected_parent, prepared_contract)
    import numpy as np
    if sys.platform != "linux" or np.__version__ != config.specification.worker.numpy_version:
        raise ValueError("isolated starter requires its selected Linux and exact NumPy dependency")
    return prepared_contract.native_work


def calculate(operand):
    """The only numerical implementation; the ordinary parent owns its falsifier."""
    import numpy as np
    cpu, wall = time.process_time_ns(), time.monotonic_ns()
    answer = sum_of_squares(operand.last_integer)
    measured_cpu = Decimal(time.process_time_ns() - cpu).scaleb(-9)
    measured_wall = Decimal(time.monotonic_ns() - wall).scaleb(-9)
    return answer, np.__version__, measured_cpu, measured_wall


def selected_child(progress, invocation):
    contract = invocation.prepared_invocation
    if contract is None:
        raise ValueError("isolated starter requires its original prepared invocation")
    config, operand, definitions = decode_invocation(invocation, progress.parent_contact, contract)
    progress.freeze_roster(NativeSubworkRoster("selected.native-subwork", progress.parent_contact,
        tuple(row.identity for row in definitions)), definitions=definitions)
    definition = next(row for row in definitions if row.subwork_id == CALCULATION)
    entry = progress.begin(definition)
    fault = config.specification.worker.fault
    if fault == "before-contact":
        os._exit(91)
    progress.contact(entry)
    if fault == "after-contact":
        os._exit(92)
    value, version, cpu, wall = invoke_native_subwork(progress, entry, calculate, operand)
    result = SquareNativeResult(config.node_id + ".native", config.identity, operand.identity,
        operand.last_integer, value, version, cpu, wall, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    raw = result.canonical_bytes()
    progress.publish_output(entry, "native.result", (raw,), maximum_bytes=MAX_RESULT_BYTES,
        expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())
    progress.complete(entry, operational_status=OperationalStatus.SUCCEEDED,
        cost=InquiryCost(cpu, wall, Decimal(len(raw))),
        cost_scope="Selected NumPy call clocks only; output payload bytes only; process lifetime RSS is a separate component",
        peak_rss_bytes=result.process_lifetime_peak_rss_bytes)
    if fault == "after-nested-completion":
        os._exit(93)
