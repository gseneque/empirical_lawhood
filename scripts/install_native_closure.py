# SPDX-License-Identifier: MPL-2.0
"""Restore a versioned native closure without modifying retained source custody."""

import argparse
import json
from pathlib import Path

from empirical_lawhood.storage.native_installation import restore_closure, verified_native_installation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--source", type=Path, help="Original closure to restore")
    command.add_argument("--verify-installed", type=Path, metavar="PREFIX", help="Authenticate an existing installation")
    parser.add_argument("--destination", type=Path, help="Fresh destination for a restore")
    parser.add_argument("--manifest-sha256", help="Independent manifest digest for an installed check")
    args = parser.parse_args()
    if args.verify_installed is not None:
        if args.destination is not None or not args.manifest_sha256:
            parser.error("--verify-installed requires --manifest-sha256 and takes no destination")
        with verified_native_installation(args.verify_installed, manifest_path=args.manifest,
                                          manifest_sha256=args.manifest_sha256) as receipt:
            result = receipt
    else:
        if args.destination is None or args.manifest_sha256 is not None:
            parser.error("--source requires --destination")
        result = restore_closure(manifest_path=args.manifest, source=args.source, destination=args.destination)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
