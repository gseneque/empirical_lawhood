#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Archive a selected dirty producing checkout without execution or publication."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource
import time
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', required=True, type=Path)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--record', required=True, type=Path)
    parser.add_argument('--include', action='append', default=[])
    args = parser.parse_args()
    from empirical_lawhood.api.recursive_authoring import implementation_binding
    start = time.monotonic()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    start_cpu = usage.ru_utime + usage.ru_stime
    project = args.project_root.resolve(strict=True)
    source = implementation_binding(project)
    members = {f'src/empirical_lawhood/{name}': digest for name, digest in source.package_sources}
    for name in ('pyproject.toml', 'uv.lock', *args.include):
        path = project / name
        if path.is_symlink() or not path.resolve(strict=True).is_relative_to(project):
            raise ValueError('selected producing member is a link or lies outside the checkout')
        members[name] = sha256(path.read_bytes()).hexdigest()
    rows = []
    with zipfile.ZipFile(args.archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, digest in sorted(members.items()):
            raw = (project / name).read_bytes()
            if sha256(raw).hexdigest() != digest:
                raise ValueError('producing source drift: ' + name)
            bundle.writestr(name, raw)
            rows.append({'path': name, 'bytes': len(raw), 'sha256': digest})
        raw = json.dumps(source.to_document(), indent=2, sort_keys=True).encode() + b'\n'
        bundle.writestr('implementation.json', raw)
        rows.append({'path': 'implementation.json', 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()})
    with zipfile.ZipFile(args.archive) as bundle:
        if len(bundle.namelist()) != len(rows):
            raise ValueError('producing source archive denominator mismatch')
        for row in rows:
            raw = bundle.read(row['path'])
            if len(raw) != row['bytes'] or sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('producing source archive member mismatch')
    if implementation_binding(project) != source:
        raise ValueError('actual producing implementation changed during snapshot')
    usage = resource.getrusage(resource.RUSAGE_SELF)
    record = {'project_root': str(project), 'implementation': source.to_document(),
              'archive': str(args.archive), 'bytes': args.archive.stat().st_size,
              'sha256': sha256(args.archive.read_bytes()).hexdigest(), 'members': rows,
              'verified_member_count': len(rows), 'native_contacts': 0,
              'measured_cpu_seconds': usage.ru_utime + usage.ru_stime - start_cpu,
              'measured_wall_seconds': time.monotonic() - start,
              'unmeasured_tail': 'Preflight record writes and process exit'}
    with args.record.open('x') as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k: record[k] for k in ('archive', 'bytes', 'sha256', 'verified_member_count',
                                            'measured_cpu_seconds', 'measured_wall_seconds')}))


if __name__ == '__main__':
    main()
