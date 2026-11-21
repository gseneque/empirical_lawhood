"""Render the shared workflow table from the installed workflow facts.

SPDX-License-Identifier: MPL-2.0
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from empirical_lawhood.api.workflows import list_workflows
from empirical_lawhood.adapters.composition.generated_workflows import WORKFLOW_DECLARATIONS
from empirical_lawhood.cli.workflows import workflow_details

START = "<!-- BEGIN GENERATED WORKFLOWS -->"
END = "<!-- END GENERATED WORKFLOWS -->"
ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "docs/reference/workflows.md"



def render_table() -> str:
    workflows = list_workflows()
    states = {row.workflow.workflow_id: row.display_state for row in WORKFLOW_DECLARATIONS}
    if set(states) != {workflow.workflow_id for workflow in workflows}:
        raise ValueError("Workflow presentation states must cover the exact closed inventory")
    lines = [
        "| Workflow / boundary | Current state | Commands and input roles | Environment / first stop / evidence ceiling |",
        "|---|---|---|---|",
    ]
    for workflow in workflows:
        facts = workflow_details(workflow)
        commands = "<br>".join(
            f"`{entry['command']}` ({entry['boundary']})"
            for entry in facts["operations"]
        )
        inputs = "; ".join(
            f"`{Path(item.path).name}`: {item.role}" for item in workflow.inputs
        )
        guide = Path(os.path.relpath(ROOT / workflow.guide, DESTINATION.parent)).as_posix()
        lines.append(
            f"| [{workflow.title}]({guide})<br>{workflow.kind} | "
            f"{states[workflow.workflow_id]} | {commands}<br>{inputs} | {workflow.environment}<br>"
            f"{workflow.first_missing_prerequisite}<br>{workflow.scientific_ceiling} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = DESTINATION
    text = path.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Workflow reference must have exactly one generated table region")
    before, remainder = text.split(START)
    _, after = remainder.split(END)
    generated = before + START + "\n\n" + render_table() + "\n" + END + after
    if args.check:
        if generated != text:
            print("Workflow index differs; run scripts/generate_workflow_index.py")
            return 1
    else:
        path.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
