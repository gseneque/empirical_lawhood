# SPDX-License-Identifier: MPL-2.0
"""Ordinary parent publication over original nested bytes, including recovery."""

from empirical_lawhood.methods.isolated_native_starter.calculation import independent_sum

from decimal import Decimal
from hashlib import sha256
import os

from empirical_lawhood.storage.bounded_io import read_bounded_bytes
from empirical_lawhood.science.records.decoding import decode_canonical_bytes
from empirical_lawhood.science.inquiry.recursive_inquiry import InquiryCost
from empirical_lawhood.science.records.status import OperationalStatus
from empirical_lawhood.storage.contracts.artifacts import ReceiptCheck
from empirical_lawhood.execution.native_subwork import NativeSubworkRoster

from empirical_lawhood.adapters.isolated_native_starter.records import MAX_LOG_BYTES, MAX_RESULT_BYTES, ProcessLog, SquareNativeResult, SquareResult
from empirical_lawhood.adapters.isolated_native_starter.work import CALCULATION, METADATA, guarded_scratch, launcher_definition, load_inputs


def publish(progress, entry, name, raw, *, maximum_bytes=MAX_RESULT_BYTES):
    return progress.publish_output(entry, name, (raw,), maximum_bytes=maximum_bytes,
        expected_size_bytes=len(raw), expected_physical_sha256=sha256(raw).hexdigest())


class Runner:
    def __init__(self, *, manifest):
        self.manifest = manifest

    def execute(self, context):
        raise ValueError("isolated starter requires ordinary native progress and streaming output")

    def preflight(self, context):
        config, _, _ = load_inputs(context, self.manifest)
        contract = context.prepared_invocation
        if contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("isolated starter requires actual isolated preparation before parent contact")
        if contract.native_work.isolated_selection.interpreter_path != config.specification.worker.interpreter_path:
            raise ValueError("isolated starter changes its frozen worker interpreter")

    def execute_streaming_with_native_subwork(self, context, native_subwork, emitter, progress=None):
        from empirical_lawhood.execution.local.isolated_native_subwork import run_isolated_native_entry

        config, operand, _ = load_inputs(context, self.manifest)
        contract = context.prepared_invocation
        if contract is None or contract.native_work is None or contract.native_work.isolated_selection is None:
            raise ValueError("isolated starter requires its actual prepared specialist")
        contract.validate_context(context)
        work = contract.native_work
        if native_subwork.parent_contact != work.expected_parent:
            raise ValueError("isolated starter changes its original live parent")
        calculation = next(row for row in work.definitions if row.subwork_id == CALCULATION)
        metadata = next(row for row in work.definitions if row.subwork_id == METADATA)
        # Recovery uses the same original definitions and read-only coordinator
        # port. No invocation, interpreter, begin or contact is needed here.
        recovered = native_subwork.recover(calculation)
        reused = recovered is not None
        if not reused:
            native_subwork.freeze_roster(work.rosters[0], definitions=work.definitions)
            root = guarded_scratch(config.specification.worker) / "entered"
            root.mkdir(exist_ok=False)
            selected = work.isolated_selection
            parent_entry = native_subwork.begin(metadata)
            native_subwork.contact(parent_entry)
            manifest = publish(native_subwork, parent_entry, "process.selection", selected.canonical_bytes())
            launcher = launcher_definition(metadata, selected, manifest)
            native_subwork.freeze_roster(NativeSubworkRoster(launcher.roster_id, native_subwork.parent_contact,
                (launcher.identity,), metadata.identity), parent_entry=parent_entry, definitions=(launcher,))
            entry = native_subwork.begin(launcher)
            with (root / "stdout.txt").open("xb") as stdout, (root / "stderr.txt").open("xb") as stderr:
                returned = run_isolated_native_entry(selected, native_subwork, lifecycle_entry=entry,
                    start_output_id="process.start", return_output_id="process.return",
                    environment=dict(config.specification.worker.environment), cwd=root, stdout=stdout, stderr=stderr,
                    prepared_contract=contract, entry_preflight="preflight_selected_child")
            for stream in ("stderr", "stdout"):
                raw = read_bounded_bytes(root / (stream + ".txt"), maximum_bytes=MAX_LOG_BYTES)
                log = ProcessLog.from_bytes(config.node_id + ".process." + stream, stream, raw)
                publish(native_subwork, entry, "process." + stream, log.canonical_bytes())
            status = OperationalStatus.SUCCEEDED if returned.returncode == 0 else OperationalStatus.FAILED
            native_subwork.complete(entry, operational_status=status, cost=InquiryCost(None, None, None),
                cost_scope="Exclusive launcher costs unknown; original process.return retains inclusive child and relay clocks overlapping the calculation",
                reason_codes=() if returned.returncode == 0 else ("EXPOSED_STARTER_CHILD_INTERRUPTION",))
            native_subwork.complete(parent_entry, operational_status=OperationalStatus.SUCCEEDED,
                cost=InquiryCost(None, None, None), cost_scope="Selection and publication overhead not independently measured")
            if not returned.handshake_completed or returned.returncode != 0:
                raise RuntimeError("exposed starter interruption; original process return and nested states remain retained")
        else:
            if native_subwork.recover(metadata) is None:
                raise ValueError("isolated starter parent publication lacks its complete original metadata")
        chunks, size = [], 0
        for chunk in native_subwork.iter_completed_output(calculation, "native.result", maximum_chunk_bytes=MAX_RESULT_BYTES):
            size += len(chunk)
            if size > MAX_RESULT_BYTES:
                raise ValueError("isolated starter retained result exceeds its complete byte allowance")
            chunks.append(chunk)
        native = decode_canonical_bytes(b"".join(chunks), SquareNativeResult, maximum_bytes=MAX_RESULT_BYTES)
        if (native.configuration != config.identity or native.operand != operand.identity
                or native.last_integer != operand.last_integer):
            raise ValueError("isolated starter changes the original completed numerical operands")
        expected = independent_sum(operand.last_integer)
        result = SquareResult(config.node_id + ".product", config, native, expected,
            "SATISFIED" if native.sum_of_squares == expected else "FALSIFIED")
        if config.specification.worker.fault == "before-parent-completion" and not reused:
            os._exit(94)
        emitter.write(result.record_id, result.canonical_bytes())
        if progress is not None:
            progress.advance(Decimal(1))
        return (ReceiptCheck("isolated-starter-original-completed-native-bytes", True, ()),)
