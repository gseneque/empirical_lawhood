"""Explicit one-sampling-interval native software conformance; no response/Q claim."""

from pathlib import Path

from empirical_lawhood.api.authoring_handoff import preflight_output_directory, write_exclusive_record
from empirical_lawhood.api.authoring_output import report_incomplete_output


def preparation_native_conformance(*, roots, output_dir: Path, conformance_id: str):
    """Exercise the actual native marcher on three explicit source kinds/two views.

    This bounded software check does not acquire a4096prefix, prepare a4496
    handoff, assay responses, qualify a constructor, issue or publish a law.
    """
    if tuple(root.cohort for root in roots)!=("q2","cir1","constructed"):
        raise ValueError("native conformance requires explicit q2/cir1/constructed allocations")
    if any(root.source_prefix is not None for root in roots):
        raise ValueError("native conformance cannot import a state")
    output_dir=preflight_output_directory(directory=output_dir)
    from empirical_lawhood.adapters.simulators.preparation_applicability.conformance import run_native_conformance
    report = run_native_conformance(roots=roots, conformance_id=conformance_id)
    output_dir.mkdir(parents=True,exist_ok=False)
    with report_incomplete_output(output_dir):
        write_exclusive_record(output_dir,"native-conformance.canonical.json",report)
    return report
