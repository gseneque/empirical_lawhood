# SPDX-License-Identifier: MPL-2.0
"""Reproduce frozen exposed recursive inputs; acquire no native evidence."""

import argparse
from dataclasses import replace
from pathlib import Path

from empirical_lawhood.adapters.composition.recursive_examples import materials_partial_draft, rc_scientific_examples
from empirical_lawhood.adapters.methods.rc_prerequisite_chain.recursive_translation import rc_recursive_draft

ROOT = Path(__file__).resolve().parents[1]


def _historical_exposed_draft(draft):
    # These checked-in examples retain their original canonical identities.
    # Their finite graph allowances are historical operands, not the current
    # builders' unrestricted defaults or a limit on newly authored inquiries.
    return replace(draft, maximum_objects=256, maximum_links=1024, maximum_depth=32)


def examples():
    records = {"materials-partial.json": _historical_exposed_draft(materials_partial_draft())}
    for name, config in rc_scientific_examples().items():
        records[f"rc-{name}.json"] = _historical_exposed_draft(
            rc_recursive_draft(config, draft_id=f"draft.rc-chain.{name}")
        )
        records[f"rc-{name}-scientific.json"] = config
    from empirical_lawhood.adapters.methods.battery_recursive_construction.examples import battery_wave_a_draft
    records["battery-wave-a.json"] = _historical_exposed_draft(battery_wave_a_draft())
    roots = {
        "materials": "programmes/materials/superconductivity/workflows/recursive-materials",
        "rc": "programmes/foundations/measurement-and-response/workflows/recursive-rc",
        "battery": "programmes/energy/battery-charging/workflows/recursive-battery",
    }
    return {f"{roots[name.split('-')[0]]}/{name}": record.canonical_bytes()
            for name, record in records.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for relative, raw in examples().items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != raw:
                raise SystemExit(f"recursive example drifted: {relative}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


if __name__ == "__main__":
    main()
