# SPDX-License-Identifier: MPL-2.0
"""Bounded source diagnostics; existing records supply no new authority."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.api.source_identity import compare_source_identities, observe_source_identity, read_source_identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    observe = commands.add_parser('observe')
    observe.add_argument('--project-root', type=Path)
    observe.add_argument('--output-dir', type=Path, required=True)
    compare = commands.add_parser('compare')
    compare.add_argument('--before', type=Path, required=True)
    compare.add_argument('--after', type=Path, required=True)
    compare.add_argument('--capability', nargs=2, action='append', default=[], metavar=('KEY', 'VERSION'))
    args = parser.parse_args()
    if args.command == 'observe':
        members = observe_source_identity(project_root=args.project_root).members()
        args.output_dir.mkdir(parents=True, exist_ok=False)
        for name, raw in members:
            with (args.output_dir / name).open('xb') as stream:
                stream.write(raw)
        print(json.dumps(dict(output_directory=str(args.output_dir.absolute()),
            members=tuple(name for name, _ in members), authority='NONE')))
    else:
        result = compare_source_identities(read_source_identity(args.before), read_source_identity(args.after),
            selected_capabilities=tuple(tuple(key) for key in args.capability))
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
