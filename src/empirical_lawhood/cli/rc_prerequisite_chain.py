"""Explicit numerical prerequisite-chain entry points and retained presentation.

SPDX-License-Identifier: MPL-2.0
"""

from pathlib import Path
from typing import Annotated

import typer

from empirical_lawhood.cli.attempts import ATTEMPT_DIRECTORY_OPTION, attempt_stage, retained_command


def register_rc_chain_commands(app: typer.Typer) -> None:
    from empirical_lawhood.cli import integrations as h
    from empirical_lawhood.cli.paper_analysis_integrations import _commit

    @app.command("rc-chain-prove")
    @retained_command("campaign rc-chain-prove", closed_output=True, native=False)
    def prove(
        input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
    ) -> None:
        """Inspect the frozen complete RC design and work bounds without native contact."""
        from empirical_lawhood.api.rc_prerequisite_chain import prove_rc_chain

        try:
            config = h._configuration(input, "rc-prerequisite-chain")
            attempt_stage("rc_chain_design_proof", native_contact="none")
            report = prove_rc_chain(config)
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("rc-chain-run")
    @retained_command("campaign rc-chain-run", closed_output=True, native=True)
    def run(
        input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
    ) -> None:
        """Execute the exposed RC roster, retaining and reusing exact completed unit receipts."""
        from empirical_lawhood.api.rc_prerequisite_chain import run_rc_chain

        try:
            root, _, plane = h._storage()
            config = h._configuration(input, "rc-prerequisite-chain")
            attempt_stage("rc_chain_execution_preflight", native_contact="not_entered")
            report = run_rc_chain(
                config=config,
                artifact_writer=plane,
                project_root=root,
                implementation_commit=_commit(root),
                progress=lambda done, total: attempt_stage(
                    f"rc_chain_units_{done}_of_{total}", native_contact="development_native"
                ),
            )
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)

    @app.command("rc-chain-result")
    @retained_command("campaign rc-chain-result", closed_output=True, native=False)
    def result(
        input: Annotated[Path, typer.Option("--input", exists=True, dir_okay=False)],
        attempt_dir: Annotated[Path | None, ATTEMPT_DIRECTORY_OPTION] = None,
    ) -> None:
        """Authenticate the complete RC result and producing evidence without reacquisition."""
        from empirical_lawhood.api.rc_prerequisite_chain import read_rc_chain

        try:
            _, _, plane = h._storage(read_only=True)
            config = h._configuration(input, "rc-prerequisite-chain")
            attempt_stage("rc_chain_retained_result_read", native_contact="none")
            report = read_rc_chain(
                config=config,
                artifact_writer=plane,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            h._error(error)
        h._report(report)
