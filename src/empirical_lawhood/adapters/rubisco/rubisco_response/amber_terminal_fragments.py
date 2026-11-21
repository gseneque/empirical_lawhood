# SPDX-License-Identifier: MPL-2.0
"""One bounded LEaP stock-sequence call per missing LSU end, before parent preparation."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from empirical_lawhood.domains.rubisco.rubisco_response.gp_initial_topology_operation import amber_command
from empirical_lawhood.domains.rubisco.rubisco_response.terminal_fragment_placement import (
    MAX_FRAGMENT_SECONDS,
    MAXIMUM_BUNDLE_BYTES,
    METHOD,
    TerminalCandidateRejected,
    fragment_script,
    met_template_pin,
    plans,
    replay_terminal_fragments,
    terminal_stock_pins,
)
from empirical_lawhood.storage.bounded_io import read_bounded_bytes


def run_sequence(engine, sequence, scratch):
    root = Path(engine.root)
    script = fragment_script(sequence)
    (scratch / "fragment.leap").write_text(script, encoding="ascii")
    argv = [*amber_command(engine), "-s"]
    for kind in ("prep", "lib", "parm", "cmd"):
        argv.extend(("-I", str(root / "toolchain/dat/leap" / kind)))
    argv.extend(("-f", "fragment.leap"))
    record = dict(
        script=script, return_code=None, timed_out=False, stdout="", stderr="", topology="", restart=""
    )
    with (scratch / "stdout").open("xb") as stdout, (scratch / "stderr").open("xb") as stderr:
        try:
            done = subprocess.run(
                argv,
                cwd=scratch,
                env={
                    "PATH": "/usr/bin:/bin",
                    "AMBERHOME": str(root / "toolchain"),
                    "LD_LIBRARY_PATH": str(root / engine.library_directory),
                    "OMP_NUM_THREADS": "1",
                    "LC_ALL": "C",
                },
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=MAX_FRAGMENT_SECONDS,
                check=False,
            )
            record["return_code"] = done.returncode
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
        except OSError as error:
            record["launch_error"] = str(error)
    for key, name in (
        ("stdout", "stdout"),
        ("stderr", "stderr"),
        ("topology", "fragment.prmtop"),
        ("restart", "fragment.inpcrd"),
    ):
        path = scratch / name
        if path.is_file():
            record[key] = read_bounded_bytes(path, maximum_bytes=MAXIMUM_BUNDLE_BYTES // 4).decode("ascii")
    return record


def _checked_stock(root, row):
    path, count, digest = row
    raw = read_bounded_bytes(Path(root) / path, maximum_bytes=count)
    if len(raw) != count or sha256(raw).hexdigest() != digest:
        raise ValueError("A selected native terminal-fragment stock changed before or during use")
    return raw


def initialize_amber_terminal_fragments(source, directory):
    directory = Path(directory)
    output = directory / "terminal-fragments.json"
    with output.open("xb"):
        pass
    data = dict(
        method=METHOD,
        source=source.identity.to_document(),
        amber_engine=source.amber_engine.identity.to_document(),
        numerical_engine=source.numeric_engine.fingerprint(),
        fragments={},
    )

    def publish():
        raw = (json.dumps(data, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n").encode(
            "ascii"
        )
        if len(raw) > MAXIMUM_BUNDLE_BYTES:
            raise ValueError("Native terminal fragment receipt exceeds its authored ceiling")
        tmp = directory / "terminal-fragments.pending"
        tmp.write_bytes(raw)
        tmp.replace(output)
        return raw

    try:
        stocks = data["stock_pins"] = terminal_stock_pins(source.amber_engine)
        met = data["met_template_pin"] = met_template_pin(source.numeric_engine)
        data["stock_bytes"] = {
            row[0]: _checked_stock(source.amber_engine.root, row).decode("ascii") for row in stocks
        }
        data["met_template"] = _checked_stock(source.numeric_engine.site_packages, met).decode("ascii")
        selected, _, _ = plans(json.loads(source.origin_json))
        for name, sequence in selected.items():
            with TemporaryDirectory(prefix="stock-peptide-", dir=directory) as scratch:
                data["fragments"][name] = run_sequence(source.amber_engine, sequence, Path(scratch))
            publish()
            if data["fragments"][name]["return_code"] != 0:
                raise ValueError("Selected Amber sequence fragment failed: " + name)
        for row in stocks:
            _checked_stock(source.amber_engine.root, row)
        _checked_stock(source.numeric_engine.site_packages, met)
        return replay_terminal_fragments(source, publish())
    except Exception as error:
        data["refusal"] = dict(error_type=type(error).__name__, message=str(error))
        if isinstance(error, TerminalCandidateRejected):
            data["refusal"]["candidate_diagnostics"] = error.diagnostics
        publish()
        raise
