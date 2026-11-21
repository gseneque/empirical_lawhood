# SPDX-License-Identifier: MPL-2.0
"""Bind the original SCI02-C instrument to editable receiver-study definitions."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from empirical_lawhood.api.investigations import create_investigation_service
from empirical_lawhood.api.model_free_matrix import select_sci02c_instrument, load_definition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project-root', 'output-directory'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('original-authoring-directory', 'read-profile', 'artifact-root-contract'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--definition', action='append', type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists() or len({p.name for p in args.definition}) != len(args.definition):
        parser.error('Select a fresh output directory and distinct definition names')
    definitions = {path.name: json.loads(path.read_bytes()) for path in args.definition}
    selections = [raw['settings']['receiver_study']['instrument'] for raw in definitions.values()]
    if any(value is not None and value != 'SELECT_ORIGINAL_SCI02C' for value in selections):
        parser.error('Select an editable template with a declared instrument requirement')
    instrument = None
    if 'SELECT_ORIGINAL_SCI02C' in selections:
        if None in (args.original_authoring_directory, args.read_profile, args.artifact_root_contract):
            parser.error('The signed H64 receiver requires the original authored directory, read profile and artifact root contract')
        service = create_investigation_service(project_root=args.project_root, operator_profile=args.read_profile,
                                               artifact_root_contract=args.artifact_root_contract)
        instrument = select_sci02c_instrument(directory=args.original_authoring_directory, artifact_writer=service.artifact_writer)
    outputs = {}
    for name, raw in definitions.items():
        if raw['settings']['receiver_study']['instrument'] is not None:
            raw['settings']['receiver_study']['instrument'] = instrument
        outputs[name] = json.dumps(raw, indent=2, sort_keys=True, allow_nan=False) + '\n'
    destination = args.output_directory
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        staged = Path(temporary)
        for name, data in outputs.items():
            path = staged / name
            path.write_text(data, encoding='utf-8')
            load_definition(path)
        destination.mkdir()
        published = []
        try:
            for name in outputs:
                target = destination / name
                with target.open('xb') as stream:
                    published.append(target)
                    stream.write((staged / name).read_bytes())
        except BaseException:
            for target in published:
                target.unlink()
            destination.rmdir()
            raise
    print(json.dumps({'original_packet_sha256': None if instrument is None else instrument['packet_sha256'],
                      'physical_design_sha256': None if instrument is None else instrument['physical_design_sha256'],
                      'definitions': [str(args.output_directory / name) for name in outputs]}))


if __name__ == '__main__':
    main()
